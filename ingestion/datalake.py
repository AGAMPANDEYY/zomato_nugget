from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import os
from dotenv import load_dotenv
load_dotenv()

class DataLake:
    def __init__(self, db_name: str = "restaurant_data", collection_name: str = "scraped_content"):
        # Get the MongoDB Atlas URI from environment variables or hardcode it
        atlas_uri = os.getenv("MONGODB_URI")

        try:
            # Establish connection to MongoDB Atlas
            self.client = MongoClient(atlas_uri)
            print("Connected to MongoDB Atlas.")
        except ConnectionFailure:
            print("Could not connect to MongoDB Atlas. Please check your connection string and credentials.")
            raise  # Reraise the exception if connection fails

        self.db = self.client[db_name]
        self.collection = self.db[collection_name]

    def create_collection(self):
        # MongoDB creates collections automatically when inserting documents
        # This method ensures the collection exists
        if self.collection.name not in self.db.list_collection_names():
            self.db.create_collection(self.collection.name)
        return self.collection

    def append_rows(self, rows: list[dict]):
        if rows:
            self.collection.insert_many(rows)
        else:
            print("No data to insert.")
    def find_rows(self, query: dict, projection: dict = None, limit: int = 10) -> list[dict]:
        """
        Fetch documents based on a query dictionary.

        Args:
            query (dict): MongoDB query filter, e.g., {"url": "https://example.com"}
            projection (dict): Fields to include/exclude, e.g., {"_id": 0, "url": 1}
            limit (int): Max number of results to return

        Returns:
            list[dict]: List of documents matching the query
        """
        try:
            results = list(self.collection.find(query, projection).limit(limit))
            print(f"Found {len(results)} matching documents.")
            return results
        except Exception as e:
            print(f" Error while querying: {e}")
            return []
    def get_all_documents(self):
        return list(self.collection.find({}))  # Optional: exclude _id
