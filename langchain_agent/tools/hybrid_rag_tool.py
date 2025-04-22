import os
import json
from langchain.tools import tool
from dotenv import load_dotenv
from retrieval.hybridrag import HybridRAG
from utils.embeddings import create_embeddings

load_dotenv()

hybrid_rag = HybridRAG()

@tool("ZomatoRAG", description="Retrieve restaurant info via hybrid RAG (semantic + graph)")
def rag_retriever(query: str) -> str:
    query_embeddings = create_embeddings(query)
    results = hybrid_rag.query_hybrid(query, query_embeddings)
    return json.dumps(results)
