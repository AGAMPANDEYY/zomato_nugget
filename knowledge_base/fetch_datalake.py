import json
from pyiceberg.catalog import load_catalog
from ingestion.datalake import DataLake
import pyarrow as pa
import os 
import logging
from dotenv import load_dotenv
load_dotenv()

class DataLakeFetcher:

    """
    This class is used to fetch records from the Iceberg table in the data lake.
    It uses the PyIceberg library to load the catalog and table, and then scans the table to fetch records.
    It returnes list of records as dictionaries.
    """
    def __init__(self):
        CATALOG_NAME = os.getenv("CATALOG_NAME")
        WAREHOUSE_PATH = os.getenv("WAREHOUSE_PATH")
        NAMESPACE = os.getenv("NAMESPACE")
        TABLE_NAME = os.getenv("TABLE_NAME")
        TABLE_IDENTIFIER = [NAMESPACE, TABLE_NAME]  
        DB_NAME=os.getenv("DB_NAME")
        COLLECTION_NAME= os.getenv("COLLECTION_NAME")
        MONGODB_URI= os.getenv("MONGODB_URI")

        self.catalog_name= CATALOG_NAME
        self.warehouse_path= WAREHOUSE_PATH
        self.table_name= TABLE_NAME # This is for apache iceberg if used 
        if not self.table_name:
            raise ValueError("Environment variable TABLE_NAME must be set")
        self.table_identifier= TABLE_IDENTIFIER
        self.db_name=DB_NAME
        self.collection_name=COLLECTION_NAME
        self.mongodb_uri=MONGODB_URI


    # --- Data Lake Access: Load records from the Iceberg table --- 
    def fetch_records_from_iceberg(self):
        """Load all records from the Iceberg table into a list of dicts."""
        try:
            # 1. Load the catalog
            catalog = load_catalog(
                name=self.catalog_name,
                type="hadoop",
                warehouse=self.warehouse_path
            )
            logging.info(f"Loaded Iceberg catalog '{self.catalog_name}' at '{self.warehouse_path}'")
            
            # 2. Load the table
            table = catalog.load_table(self.table_identifier)
            logging.info(f"Loaded table: {'.'.join(self.table_identifier)}")
            
            # 3. Scan to RecordBatches
            scanner = table.new_scan()\
                           .plan()\
                           .build()
            batches = scanner.to_pyarrow()  # returns a pyarrow.Table
            pa_table: pa.Table = batches
            
            # 4. Convert to Python dicts
            #    to_pydict returns {column: [values,...]}

            column_dicts = pa_table.to_pydict()
            #    transpose into list of row-dicts
            records = [
                {col: column_dicts[col][i] for col in column_dicts}
                for i in range(pa_table.num_rows)
            ]
            
            logging.info(f"Fetched {len(records)} records from Iceberg")
            return records

        except Exception as e:
            logging.error(f"Error fetching from Iceberg: {e}", exc_info=True)
            return []
        
    # --- MongoDB Atlas Access ---
    def fetch_records_from_mongodbatlas(self):
        """Fetch records from MongoDB Atlas collection."""
        try:
            datalake = DataLake(db_name=self.db_name, collection_name=self.collection_name)
            documents = datalake.get_all_documents()
            datalake.client.close() 
            logging.info(f"Fetched {len(documents)} records from MongoDB Atlas")
            # Structure data into a dictionary with restaurant names as keys
            records = {}

            for doc in documents:
                restaurant = doc.get('restaurant_name')
                if restaurant:
                    records[restaurant] = doc
                else:
                    logging.warning("Document missing 'restaurant_name' field.")
            return records
        except Exception as e:
            logging.error(f"Error fetching from MongoDB Atlas: {e}", exc_info=True)
            return {}