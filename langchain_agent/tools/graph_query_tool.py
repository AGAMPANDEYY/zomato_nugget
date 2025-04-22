import os
import json
from langchain.tools import tool
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

neo4j_driver = GraphDatabase.driver(
    os.getenv("NEO4J_URI", "bolt://localhost:7687"),
    auth=(os.getenv("NEO4J_USER", "neo4j"), os.getenv("NEO4J_PASSWORD", "password"))
)

@tool("GraphQuery", description="Query Neo4j for custom relational data")
def graph_query(cypher_query: str) -> str:
    with neo4j_driver.session() as session:
        result = session.run(cypher_query)
        records = [record.data() for record in result]
    return json.dumps(records)
