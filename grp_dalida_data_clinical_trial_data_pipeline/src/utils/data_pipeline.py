# src/utils/data_pipeline.py
import json
import os

# Function to load config
def load_config():
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'config.json')
    with open(config_path, 'r') as file:
        return json.load(file)

config = load_config()
duckdb_file_path = config.get('duckdb_file_path')

import dlt
from dlt import pipeline as dlt_pipeline

class DataPipeline:
    def __init__(self, pipeline_name, destination, dataset_name):
        self.pipeline = dlt_pipeline(pipeline_name=pipeline_name, destination=dlt.destinations.duckdb(duckdb_file_path), dataset_name=dataset_name)

    def load_data(self, data, table_name):
        self.pipeline.run(data, table_name=table_name)