"""
processed restaurant data into both a vector database (Weaviate) and a graph database (Neo4j) so that your eventual RAG system can combine semantic search with relationship (graph) queries for extra context. This “hybrid” approach gives you the best of both worlds:

Weaviate excels at semantic search (via embeddings) so that unstructured text such as menu descriptions, reviews, and other freeform content is matched by similarity.
Neo4j (or your choice of graph DB) captures structured relationships (for instance, which restaurants serve which dishes, or which ingredients are used) that lets you perform complex relational queries.

Below is the code with inline comments explaining each step.

"""
import weaviate
from weaviate.classes.init import Auth
import weaviate.classes as wvc
from weaviate.classes.config import Property, DataType, Configure
from neo4j import GraphDatabase
import json
import os 
import uuid
import hashlib
import weaviate.util
from dotenv import load_dotenv
from sentence_transformers import CrossEncoder
from llama_index.core import VectorStoreIndex
from llama_index.vector_stores.weaviate import WeaviateVectorStore
from flashrank import Ranker, RerankRequest

load_dotenv()

# -------------------- WEAVIATE SETUP --------------------
# Define your Weaviate endpoint (can be local or cloud)
WEAVIATE_URL= os.getenv("WEAVIATE_URL")  # e.g., "http://localhost:8080" or your cloud URL
WEAVIATE_API_KEY=os.getenv("WEAVIATE_API_KEY")
NEO4J_URI = os.getenv("NEO4J_URI")  # e.g., "bolt://localhost:7687"
NEO4J_USER = os.getenv("NEO4J_USER")  # e.g., "neo4j"
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")  # e.g., "password"

class HybridRAG:
    """
    A class to manage the hybrid RAG system using Weaviate and Neo4j.
    """
    def __init__(self):
        self.weaviate_client = weaviate.connect_to_weaviate_cloud(cluster_url=WEAVIATE_URL, auth_credentials=Auth.api_key(WEAVIATE_API_KEY))
        self.neo4j_driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        # --------------------- WEAVIATE CONNECTION & LlamaIndex Setup ----------------------

            # -------------------- HYBRID QUERY PIPELINE + ReRank--------------------
    def query_hybrid(self, user_query, user_query_embedding, limit=3, rerank_limit=10, reranker=None):
        """
        Proper Hybrid Search: Uses Weaviate's hybrid search combining vector similarity and BM25 keyword matching with the provided embedding.
        Robust Reranking:

        Fetches more initial results than needed for better reranking
        Implements error handling if the reranker can't be imported
        Uses the CrossEncoder properly with pairs of (query, document)
        Sorts results by rerank score before enrichment


        Neo4j Enrichment Fixes:

        Prioritizes the best-ranked chunks for graph enrichment
        Improved graph query with conditional WHERE clause to ensure proper relationships
        Better handling of NULL values in graph results


        Improved Result Handling:

        Maintains scores throughout the process
        Combines the original semantic content with graph-derived information
        Returns a clean list of text chunks for RAG


        Parameterization:

        Added rerank_limit to control how many initial results to fetch for reranking
        Properly uses the provided limit parameter for final results
        """
        # Step 1: Semantic search in Weaviate with hybrid search
        # First fetch more results than we need for reranking
        coll = self.weaviate_client.collections.get("RestaurantChunk")
        vector_results = coll.query.hybrid(
            query=user_query,
            vector=user_query_embedding,
            alpha=0.25,  # Balance between vector and keyword search (adjust as needed)
            limit=rerank_limit  # Get more results initially for reranking
        )
        
        # Extract chunk IDs and initial context
        initial_results = []
        chunk_ids = []
        
        for obj in vector_results.objects:
            # Get metadata and text content from each result
            metadata = obj.properties
            chunk_id = metadata.get("chunk_id")
            text_content = metadata.get("text", metadata.get("markdown", ""))
            score = obj.metadata.score  # Get the hybrid search score
            
            # Store all information for reranking
            if text_content:
                initial_results.append({
                    "chunk_id": chunk_id,
                    "text": text_content,
                    "score": score,
                    "metadata": metadata
                })
                if chunk_id:
                    chunk_ids.append(chunk_id)
        
        # Step 2: Rerank the results using the cross-encoder
        if len(initial_results) > 0:
            try:
                if reranker is None:
                    from transformers import AutoModelForSequenceClassification

                    reranker = AutoModelForSequenceClassification.from_pretrained(
                            'BAAI/bge-reranker-base',
                            torch_dtype="auto",
                            trust_remote_code=True,
                        )
        
                # Prepare pairs for reranking
                pairs = [(user_query, result["text"]) for result in initial_results]
                
                # Get reranking scores
                rerankrequest = RerankRequest(query=user_query, passages=initial_results)
                rerank_scores = reranker.rerank(rerankrequest)
                #rerank_scores = reranker.compute_score(pairs)
                
                # Add reranking scores to results
                for i, score in enumerate(rerank_scores):
                    #initial_results[i]["rerank_score"] = float(score) ---> For huggingfacehub rerankers
                    score=score.get("score")
                    initial_results[i]["score"] = float(score)  # Assuming the first score is the relevant one
                
                # Sort by reranking score
                initial_results = sorted(initial_results, key=lambda x: x["score"], reverse=True)
                
            except ImportError:
                print("Cross-encoder not available. Using original ranking.")
                # If reranker is not available, sort by original score
                initial_results = sorted(initial_results, key=lambda x: x["score"], reverse=True)
        
        # Step 3: Enrich with related content from Neo4j
        enriched_results = []
        
        with self.neo4j_driver.session() as session:
            # For prioritized chunk IDs, find related information in the graph
            for result in initial_results[:limit]:
                chunk_id = result.get("chunk_id")
                if not chunk_id:
                    continue
                    
                # Find the chunk and its connections
                graph_query = """
                MATCH (c:Chunk {id: $chunk_id})
                OPTIONAL MATCH (r:Restaurant)-[:HAS_CHUNK]->(c)
                OPTIONAL MATCH (d:Dish)-[:HAS_CHUNK]->(c)
                OPTIONAL MATCH (r:Restaurant)-[s:SERVES]->(d2:Dish)
                WHERE r IS NOT NULL
                RETURN c.markdown AS chunk_text, 
                    r.name AS restaurant_name,
                    COLLECT(DISTINCT {name: d.name}) AS related_dishes,
                    COLLECT(DISTINCT {name: d2.name, price: s.price}) AS menu_items
                """
                graph_result = session.run(graph_query, chunk_id=chunk_id).single()
                
                if graph_result:
                    # Get the original chunk text
                    chunk_text = result["text"]
                    
                    # Create a summary of related information
                    restaurant = graph_result["restaurant_name"]
                    dishes = graph_result["related_dishes"]
                    menu = graph_result["menu_items"]
                    
                    graph_context = ""
                    if restaurant:
                        graph_context += f"Restaurant: {restaurant}\n"
                        
                        if dishes and dishes[0].get("name"):
                            dish_names = [d["name"] for d in dishes if d.get("name")]
                            if dish_names:
                                graph_context += f"Featured dish(es): {', '.join(dish_names)}\n"
                        
                        if menu and menu[0].get("name"):
                            menu_items = [f"{m['name']} (₹{m['price']})" for m in menu if m.get("name") and m.get("price")]
                            if menu_items:
                                graph_context += f"Menu includes: {', '.join(menu_items)}\n"
                    
                    # Combine the original text with the graph context
                    combined_text = f"{chunk_text}\n\n{graph_context}" if graph_context else chunk_text
                    enriched_results.append({
                        "text": combined_text,
                        "score": result.get("rerank_score", result.get("score", 0)),
                        "chunk_id": chunk_id
                    })
        
        # Step 4: Extract just the text for final results
        final_context = [result["text"] for result in enriched_results[:limit]]
    
        return final_context
    
    def close(self):
        if self.neo4j_driver:
            self.neo4j_driver.close()
        if self.weaviate_client:
            self.weaviate_client.close()

