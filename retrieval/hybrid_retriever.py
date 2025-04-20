"""
Develop a query engine that seamlessly integrates semantic search results from Weaviate with relational data from Neo4j.

Design a query orchestration layer that first retrieves semantically relevant data from Weaviate.

Use identifiers from the semantic results to fetch related relational data from Neo4j.

Merge and rank the combined results based on relevance and user context
"""
import os
import weaviate
from weaviate.auth import Auth
from llama_index.core import VectorStoreIndex
from llama_index.vector_stores.weaviate import WeaviateVectorStore
from neo4j import GraphDatabase
from llama_index.core import StorageContext
from llama_index.core.retrievers import BM25Retriever
from llama_index.core.postprocessor import SentenceTransformerRerank

# --------------------- WEAVIATE CONNECTION & LlamaIndex Setup ----------------------

def connect_weaviate() -> weaviate.WeaviateClient:
    """Connect to Weaviate with cloud or local configuration."""
    if "WEAVIATE_URL" in os.environ and "WEAVIATE_API_KEY" in os.environ:
        return weaviate.connect_to_weaviate_cloud(
            cluster_url=os.environ["WEAVIATE_URL"],
            auth_credentials=Auth.api_key(os.environ["WEAVIATE_API_KEY"])
        )
    return weaviate.connect_to_local(
        host=os.getenv("WEAVIATE_HOST", "localhost"),
        port=int(os.getenv("WEAVIATE_PORT", 8080)),
        grpc_port=int(os.getenv("WEAVIATE_GRPC_PORT", 50051))
    )

client = connect_weaviate()
vector_store = WeaviateVectorStore(
    weaviate_client=client,
    index_name="Your_Existing_Index"  # Replace with your actual index name
)
loaded_index = VectorStoreIndex.from_vector_store(vector_store)

retriever = loaded_index.as_retriever(
  dense_similarity_top_k=3,
  sparse_similarity_top_k=3,
  alpha=0.5,
  enable_reranking=True, 
  rerank_top_n=3,
)

# --------------------- NEO4J CONNECTION & GRAPH RETRIEVAL ----------------------

def connect_neo4j():
    """
    Create a Neo4j driver instance using environment variable configuration.
    Ensure that environment variables NEO4J_URI, NEO4J_USER, and NEO4J_PASSWORD are set.
    """
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "password")
    driver = GraphDatabase.driver(uri, auth=(user, password))
    return driver

neo4j_driver = connect_neo4j()

def fetch_graph_context(restaurant_name: str) -> dict:
    """
    Query Neo4j to retrieve additional context for a restaurant.
    For example, fetch the dishes served by the restaurant.
    
    Args:
        restaurant_name (str): The name of the restaurant as obtained from vector retrieval.
    
    Returns:
        dict: A dictionary containing the restaurant name and a list of its dishes.
    """
    query = """
    MATCH (r:Restaurant {name: $rest_name})-[:SERVES]->(d:Dish)
    RETURN r.name AS restaurant, collect({dish: d.name, description: d.description, price: d.price}) AS dishes
    """
    with neo4j_driver.session() as session:
        result = session.run(query, rest_name=restaurant_name)
        record = result.single()
        if record:
            return record.data()
        return {}

# --------------------- HYBRID RETRIEVAL PROCESS ----------------------

def hybrid_retrieve(query: str) -> dict:
    """
    Perform hybrid retrieval by:
      1. Querying the vector store via LlamaIndex to retrieve semantically relevant nodes.
      2. For each retrieved result (assumed to be a restaurant), fetching additional context from Neo4j.
      3. Merging the semantic and relational data into a single response.
    
    Args:
        query (str): The user query.
    
    Returns:
        dict: Aggregated results combining vector and graph contexts.
    """
    # Step 1: Retrieve semantic nodes from Weaviate (LlamaIndex vector index)
    vector_results = retriever.retrieve(query)
    
    hybrid_results = []
    for node in vector_results:
        # Example: Assume each node has a "name" field in its metadata.
        metadata = node.get("metadata", {})
        restaurant_name = metadata.get("name")
        if not restaurant_name:
            # Alternatively, you might parse the text to extract restaurant names.
            restaurant_name = node.get("text").split("\n")[0].replace("Name:", "").strip()
        
        # Step 2: Query Neo4j for related information
        graph_context = fetch_graph_context(restaurant_name)
        # Merge results: add graph context under a new key
        node["graph_context"] = graph_context
        
        hybrid_results.append(node)
    
    return {"query": query, "results": hybrid_results}

# --------------------- SAMPLE QUERY EXECUTION ----------------------

def run_hybrid_retrieval(query: str):
    # Example vector search query:
    query = "At which restaurant can I get the cheapest paneer tikka?"
    # Obtain results from the vector store
    vector_nodes = retriever.retrieve(query)
    print("Vector Retrieval Results:")
    for idx, node in enumerate(vector_nodes, 1):
        print(f"{idx}.", node)
    
    # Perform hybrid retrieval to also include Neo4j graph context
    aggregated_results = hybrid_retrieve(query)
    import json
    print("Hybrid Retrieval (Vector + Graph) Results:")
    print(json.dumps(aggregated_results, indent=4))
    return aggregated_results