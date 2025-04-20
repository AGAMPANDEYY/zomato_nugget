"""
processed restaurant data into both a vector database (Weaviate) and a graph database (Neo4j) so that your eventual RAG system can combine semantic search with relationship (graph) queries for extra context. This “hybrid” approach gives you the best of both worlds:

Weaviate excels at semantic search (via embeddings) so that unstructured text such as menu descriptions, reviews, and other freeform content is matched by similarity.
Neo4j (or your choice of graph DB) captures structured relationships (for instance, which restaurants serve which dishes, or which ingredients are used) that lets you perform complex relational queries.

Below is the code with inline comments explaining each step.

"""
import weaviate
from neo4j import GraphDatabase
import json
import os 
from dotenv import load_dotenv

load_dotenv()

# -------------------- WEAVIATE SETUP --------------------
# Define your Weaviate endpoint (can be local or cloud)
WEAVIATE_URL= os.getenv("WEAVIATE_URL")  # e.g., "http://localhost:8080" or your cloud URL
NEO4J_URI = os.getenv("NEO4J_URI")  # e.g., "bolt://localhost:7687"
NEO4J_USER = os.getenv("NEO4J_USER")  # e.g., "neo4j"
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")  # e.g., "password"

class HybridRAG:
    """
    A class to manage the hybrid RAG system using Weaviate and Neo4j.
    """
    def __init__(self):
        self.weaviate_client = weaviate.Client(WEAVIATE_URL)
        self.neo4j_driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        # 1. Create or update schemas in both databases:
        self.create_weaviate_schema()
        self.create_neo4j_schema()

    def create_weaviate_schema(self):
        """
        Create a simple schema for restaurants and dishes.
        This schema holds unstructured text (menu content) and other metadata.
        """
        schema = {
            "classes": [
                {
                    "class": "Restaurant",
                    "description": "Restaurant details and aggregated menu text",
                    "properties": [
                        {"name": "name", "dataType": ["string"]},
                        {"name": "address", "dataType": ["string"]},
                        {"name": "cuisine", "dataType": ["string"]},
                        {"name": "rating", "dataType": ["number"]},
                        {"name": "menuText", "dataType": ["text"]}  # full or chunked menu info
                    ]
                },
                {
                    "class": "Dish",
                    "description": "Individual dish entries",
                    "properties": [
                        {"name": "name", "dataType": ["string"]},
                        {"name": "description", "dataType": ["text"]},
                        {"name": "price", "dataType": ["number"]},
                        {"name": "dietary_tags", "dataType": ["string[]"]}
                    ]
                }
            ]
        }
        # Optionally clear any existing schema (for demo purposes)
        self.weaviate_client.schema.delete_all()
        self.weaviate_client.schema.create(schema)

    def push_vector_data(self,data):
        """
        Push a list of data objects into Weaviate.
        Each object in 'data' should be a dictionary with keys:
        - "class": the Weaviate class ("Restaurant" or "Dish")
        - "properties": a dict with the object properties
        """
        for item in data:
            class_name = item.get("class")
            props = item.get("properties")
            self.weaviate_client.data_object.create(props, class_name)

    # -------------------- NEO4J SETUP --------------------

    def create_neo4j_schema(self):
        """
        Create basic uniqueness constraints for our nodes.
        """
        with self.neo4j_driver.session() as session:
            session.run("CREATE CONSTRAINT restaurant_unique IF NOT EXISTS ON (r:Restaurant) ASSERT r.name IS UNIQUE")
            session.run("CREATE CONSTRAINT dish_unique IF NOT EXISTS ON (d:Dish) ASSERT d.name IS UNIQUE")

    def push_graph_data(self,graph_data):
        """
        Push structured graph data to Neo4j.
        The 'graph_data' dict should have:
        - "restaurants": list of dicts (each containing name, address, cuisine, rating)
        - "dishes": list of dicts (each containing name, description, price, dietary_tags)
        - "relations": list of dicts (each with keys: "restaurant", "dish", "")
        """
        with self.neo4j_driver.session() as session:
            # Create Restaurant nodes
            for rest in graph_data.get("restaurants", []):
                session.run(
                    "MERGE (r:Restaurant {name: $name}) "
                    "SET r.address = $address, r.cuisine = $cuisine, r.rating = $rating",
                    rest
                )
            # Create Dish nodes
            for dish in graph_data.get("dishes", []):
                session.run(
                    "MERGE (d:Dish {name: $name}) "
                    "SET d.description = $description, d.price = $price, d.dietary_tags = $dietary_tags",
                    dish
                )
            # Create relationships (assume SERVES relationship)
            for rel in graph_data.get("relations", []):
                session.run(
                    "MATCH (r:Restaurant {name: $restaurant}), (d:Dish {name: $dish}) "
                    "MERGE (r)-[:SERVES]->(d)",
                    rel
                )

    # -------------------- HYBRID QUERY PIPELINE --------------------
    def query_hybrid(self,user_query):
        """
        Process a user query by first performing a semantic search using Weaviate,
        then enriching the results with relational context from Neo4j.
        Returns aggregated context suitable for RAG-style response generation.
        """
        # --- Step 1: Vector Search in Weaviate ---
        # In a real system, generate an embedding for user_query.
        # Here we simulate using nearVector API (Weaviate can generate embeddings internally
        # if configured or you can supply one.)
        near_vector = {"concepts": [user_query]}  # simplistic input for demonstration
        vector_results = self.weaviate_client.query.get("Restaurant", ["name", "address", "cuisine", "rating", "menuText"]) \
                                    .with_near_vector(near_vector).with_limit(5).do()
        restaurants = vector_results.get("data", {}).get("Get", {}).get("Restaurant", [])
        
        # --- Step 2: Graph Enrichment in Neo4j ---
        aggregated_results = []
        with self.neo4j_driver.session() as session:
            for rest in restaurants:
                rest_name = rest.get("name")
                # Retrieve related dishes from Neo4j for each restaurant
                query = (
                    "MATCH (r:Restaurant {name: $name})-[:SERVES]->(d:Dish) "
                    "RETURN d.name AS dish, d.description AS description, d.price AS price, d.dietary_tags AS dietary_tags"
                )
                result = session.run(query, name=rest_name)
                dishes = [{"dish": record["dish"],
                        "description": record["description"],
                        "price": record["price"],
                        "dietary_tags": record["dietary_tags"]} for record in result]
                rest["dishes"] = dishes
                aggregated_results.append(rest)
        return aggregated_results

# -------------------- MAIN PIPELINE --------------------


    
    # 2. Prepare and push sample data into Weaviate (the vector DB):
    vector_data = [
        {
            "class": "Restaurant",
            "properties": {
                "name": "Bikanervala Restaurant",
                "address": "123 Main Street",
                "cuisine": "North Indian",
                "rating": 4.2,
                "menuText": "Appetizers: Paneer Tikka, Samosa; Main Course: Butter Chicken, Dal Makhani."
            }
        },
        {
            "class": "Dish",
            "properties": {
                "name": "Paneer Tikka",
                "description": "Spicy grilled paneer dish with bell peppers.",
                "price": 250,
                "dietary_tags": ["vegetarian"]
            }
        }
    ]
    push_vector_data(vector_data)
    
    # 3. Prepare and push sample structured graph data into Neo4j:
    graph_data = {
        "restaurants": [
            {"name": "Bikanervala Restaurant", "address": "123 Main Street", "cuisine": "North Indian", "rating": 4.2}
        ],
        "dishes": [
            {"name": "Paneer Tikka", "description": "Spicy grilled paneer dish with peppers.", "price": 250, "dietary_tags": ["vegetarian"]},
            {"name": "Butter Chicken", "description": "Creamy, rich tomato-based chicken curry.", "price": 350, "dietary_tags": []}
        ],
        "relations": [
            {"restaurant": "Bikanervala Restaurant", "dish": "Paneer Tikka"},
            {"restaurant": "Bikanervala Restaurant", "dish": "Butter Chicken"}
        ]
    }
    push_graph_data(graph_data)
    
    # 4. Example query: combine vector search and graph enrichment.
    user_query = "Show me restaurants that serve spicy dishes"
    hybrid_results = query_hybrid(user_query)
    print("Hybrid Query Results:")
    print(json.dumps(hybrid_results, indent=4))