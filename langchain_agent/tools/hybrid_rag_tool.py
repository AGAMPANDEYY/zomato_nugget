import os
import json
from langchain.tools import tool
from dotenv import load_dotenv
from knowledge_base.hybrid_rag import HybridRAG

load_dotenv()

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
    results = hybrid_rag.hybrid_retrieve(query)
    return json.dumps(results)
