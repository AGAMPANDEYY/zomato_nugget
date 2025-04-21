import os
import json
from dotenv import load_dotenv
import weaviate
from weaviate.auth import Auth
from neo4j import GraphDatabase
from llama_index.core import VectorStoreIndex
from llama_index.vector_stores.weaviate import WeaviateVectorStore
from langchain.agents import initialize_agent, AgentType, Tool
from langchain.tools import tool
from langchain.memory import ConversationBufferMemory
from knowledge_base.hybrid_rag import HybridRAG
from langchain_community.utilities import SerpAPIWrapper  # :contentReference[oaicite:6]{index=6}
from crawler_scraper.scrapers.crawl4ai_fetcher import Crawl4AIFetcher  # your ScraperRouter with Crawl4AIFetcher
from knowledge_base.normalize_records import normalize_records
from knowledge_base.chunking import chunk_record
import asyncio, json


from langchain.llms import HuggingFaceHub
from langchain_huggingface import HuggingFaceEndpoint
from langchain.chains import LLMChain
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langgraph.prebuilt import create_react_agent

# Load environment variables
dotenv_path = os.getenv('DOTENV_PATH', None)
if dotenv_path:
    load_dotenv(dotenv_path)
else:
    load_dotenv()

# -------------------- HYBRID RAG SETUP --------------------
hybrid_rag = HybridRAG(
    weaviate_index=os.getenv("WEAVIATE_INDEX", "Restaurant"),
    weaviate_url=os.getenv("WEAVIATE_URL"),
    weaviate_api_key=os.getenv("WEAVIATE_API_KEY"),
    neo4j_uri=os.getenv("NEO4J_URI"),
    neo4j_user=os.getenv("NEO4J_USER"),
    neo4j_password=os.getenv("NEO4J_PASSWORD")
)

@tool(name="ZomatoRAG", description="Retrieve restaurant info via hybrid RAG (semantic + graph)")
def rag_retriever(query: str) -> str:
    """
    Retrieve enriched restaurant information using the HybridRAG pipeline.
    Returns JSON string of results.
    """
    results = hybrid_rag.hybrid_retrieve(query)
    return json.dumps(results)

# -------------------- GRAPH QUERY TOOL --------------------
# If direct graph queries are needed beyond HybridRAG
neo4j_driver = GraphDatabase.driver(
    os.getenv("NEO4J_URI", "bolt://localhost:7687"),
    auth=(os.getenv("NEO4J_USER", "neo4j"), os.getenv("NEO4J_PASSWORD", "password"))
)

@tool(name="GraphQuery", description="Query Neo4j for custom relational data")
def graph_query(cypher_query: str) -> str:
    """
    Execute a Cypher query against Neo4j and return results as JSON.
    """
    with neo4j_driver.session() as session:
        result = session.run(cypher_query)
        records = [record.data() for record in result]
    return json.dumps(records)

# -------------------- LIVE MENU CHECK TOOL with Crawl4AI--------------------
# Initialize once
searcher = SerpAPIWrapper()

@Tool(name="DynamicScrape", description="Dynamically scrape pages via Crawl4AI for fresh restaurant context")
def dynamic_scrape(query: str) -> str:
    """
    1. Use SerpAPI to find top URLs matching the query.
    2. Fetch each via Crawl4AI only.
    3. Normalize + chunk the raw content, then return aggregated context.
    """
    # 1. Discover URLs
    results = searcher.run(query + " site:mcdonalds.com OR pizzahut.com menu spice level")  # tweak filters
    urls = [r["link"] for r in json.loads(results)["organic_results"][:3]]
    
    # 2. Fetch content via Crawl4AI
    raw = []
    for url in urls:
        html = Crawl4AIFetcher(url)  # Crawl4AIFetcher picks URL type
        raw.append((url, html))
    
    # 3. Normalize & chunk
    normalized = asyncio.run(normalize_records({"Crawl4AIFetcher": raw}))
    chunks = []
    for rec in normalized:
        chunks.extend(chunk_record(rec, strategy="semantic"))  # or pick multiple strategies
    
    # 4. Return as one big context blob (or JSON)
    aggregate = "\n\n".join([c["text"] for c in chunks])
    return aggregate



# -------------------- AGENT INITIALIZATION --------------------
# LLM and conversation memory setup

hf_llm = HuggingFaceEndpoint(
    repo_id="bitext/Mistral-7B-Restaurants",
    model_kwargs={"temperature": 0.3, "max_length": 512},
    huggingfacehub_api_token=os.getenv("HUGGINGFACE_API_KEY")
)

system_prompt=os.load_yaml("system_prompt.yaml")

memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

# Assemble tools
tools = [rag_retriever, graph_query, dynamic_scrape]
prompt= ChatPromptTemplate.from_messages(
     [
    {"role": "system", "content": system_prompt}
])
memory = InMemoryChatMessageHistory(session_id="test-session")


agent = create_tool_calling_agent(hf_llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools)
agent_with_chat_history = RunnableWithMessageHistory(
    agent_executor,
    # This is needed because in most real world scenarios, a session id is needed
    # It isn't really used here because we are using a simple in memory ChatMessageHistory
    lambda session_id: memory,
    input_messages_key="input",
    history_messages_key="chat_history",
)


config = {"configurable": {"session_id": "test-session"}}


agent_with_chat_history.invoke(
        {"input": "Which restaurant Pizzahut or Dominos has spicier pizza?"}, config
    )["output"]