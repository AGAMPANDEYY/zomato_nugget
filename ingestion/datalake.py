"""
Using NoSQL database to store data in a data lake. The data here is unstructured and semi-structured.
Json and Markdown also Images will be stored in the data lake.

This would help 

"""

# PyIceberg and Parquet are used to store data in the data lake.

from pyiceberg.catalog import load_catalog
from pyiceberg.schema import Schema
from pyiceberg.types import NestedField, StringType ,TimestampType
from pyiceberg.partitioning import PartitionSpec
import pyarrow as pa


class DataLake:
    def __init__(self, catalog_name, warehouse_path):
        self.catalog = load_catalog(
            name=catalog_name,
            type="hadoop",
            warehouse=warehouse_path
        )
        self.schema= Schema(
                NestedField.required(0, "id", StringType()),
                NestedField.required(1, "scraper_name", StringType()),
                NestedField.required(2, "url", StringType()),
                NestedField.required(3, "content", StringType()),
                NestedField.required(4, "timestamp", TimestampType(), doc="Crawl time")
            )
        
        # creating table identifier
        self.table_identifier = ["restaurant_data", "scraped_content"]


    def create_table(self, table_identifier):
        if not self.catalog.table_exists(table_identifier):
            table= self.catalog.create_table(
                identifier=table_identifier,
                schema=self.schema,
                partition_spec=PartitionSpec.builder_for(self.schema).day("timestamp").build()
            )
        else:
            table= self.catalog.load_table(table_identifier)
        return table

    def append_rows(self, table, rows):
        arrow_table = pa.Table.from_pylist(rows, schema=table.schema().as_arrow())
        table.append(arrow_table)
