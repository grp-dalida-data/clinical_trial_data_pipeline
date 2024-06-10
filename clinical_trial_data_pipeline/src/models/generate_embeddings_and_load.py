import sys
import os
import duckdb
import pandas as pd
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
import json

# Add the src directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from utils.data_pipeline import DataPipeline
except ModuleNotFoundError as e:
    print(f"Error importing DataPipeline: {e}")
    sys.exit(1)

try:
    from utils.logger import setup_logger
except ModuleNotFoundError as e:
    print(f"Error importing logger: {e}")
    sys.exit(1)

# Load environment variables from .env file
load_dotenv()

logger = setup_logger(__name__)

# Get the DuckDB path from the environment variable
db_file_path = os.getenv('DUCKDB_PATH')
if not db_file_path:
    print("DUCKDB_PATH environment variable is not set.")
    sys.exit(1)

try:
    # Load the data from DuckDB
    logger.info('Connecting to DuckDB and loading data')
    con = duckdb.connect(database=db_file_path)
    query = """
    SELECT nct_id, brief_title, custom_criteria
    FROM main_data_clinical_trial_data_duckdb.custom_eligibility_criteria;
    """
    df = con.execute(query).fetchdf()
    logger.info('Data loaded from DuckDB')

    # Initialize the SentenceTransformer model
    model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

    # Generate embeddings for the custom_criteria column
    logger.info('Generating embeddings for the custom_criteria column')
    df['criteria_embeddings'] = df['custom_criteria'].apply(lambda text: model.encode([text])[0].tolist())
    logger.info('Embeddings generated for the custom_criteria column')

    # Convert embeddings to JSON strings
    df['criteria_embeddings'] = df['criteria_embeddings'].apply(json.dumps)
    logger.info('Converted embeddings to JSON strings')

    # Prepare the data for DLT
    data = df[['nct_id', 'brief_title', 'criteria_embeddings']].to_dict(orient='records')

    # Initialize the DataPipeline
    pipeline = DataPipeline(pipeline_name="embedding_pipeline", db_file_path=db_file_path, dataset_name="main_data_clinical_trial_data_duckdb")

    # Load data into DuckDB using DLT
    logger.info('Loading embeddings into DuckDB')
    pipeline.load_data(data, table_name="criteria_embeddings")
    logger.info('Finished loading embeddings into DuckDB')

    # Close the DuckDB connection
    con.close()

except Exception as e:
    logger.error(f"An error occurred: {e}")
    sys.exit(1)
