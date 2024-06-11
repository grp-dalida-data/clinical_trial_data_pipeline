import sys
import os
import json
import torch
import duckdb
import torch.nn.functional as F
from flask import Flask, request, render_template
from transformers import AutoTokenizer, AutoModel
from dotenv import load_dotenv

# Add the src directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from utils.logger import setup_logger
except ModuleNotFoundError as e:
    print(f"Error importing logger: {e}")
    sys.exit(1)

# Load environment variables from .env file
load_dotenv()

logger = setup_logger(__name__)

# Initialize Flask app
app = Flask(__name__, template_folder='templates', static_folder='../static')

# Load model from HuggingFace Hub
tokenizer = AutoTokenizer.from_pretrained('sentence-transformers/all-MiniLM-L6-v2')
model = AutoModel.from_pretrained('sentence-transformers/all-MiniLM-L6-v2')

# Mean Pooling - Take attention mask into account for correct averaging
def mean_pooling(model_output, attention_mask):
    token_embeddings = model_output[0]  # First element of model_output contains all token embeddings
    input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
    return torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)

# Function to compute sentence embeddings
def compute_embeddings(sentences):
    encoded_input = tokenizer(sentences, padding=True, truncation=True, return_tensors='pt')
    with torch.no_grad():
        model_output = model(**encoded_input)
    sentence_embeddings = mean_pooling(model_output, encoded_input['attention_mask'])
    sentence_embeddings = F.normalize(sentence_embeddings, p=2, dim=1)
    return sentence_embeddings

# Check if the DuckDB file exists
db_file_path = '/app/src/data/clinical_trial_data.duckdb'
if not db_file_path:
    app.logger.error("DUCKDB_PATH environment variable is not set.")
    sys.exit(1)

db_exists = os.path.exists(db_file_path)
stored_embeddings = None

if db_exists:
    con = duckdb.connect(database=db_file_path)
    query = """
    SELECT nct_id, brief_title, criteria_embeddings
    FROM main_data_clinical_trial_data_duckdb.criteria_embeddings;
    """
    df = con.execute(query).fetchdf()
    if not df.empty:
        df['criteria_embeddings'] = df['criteria_embeddings'].apply(json.loads)
        stored_embeddings = torch.tensor(df['criteria_embeddings'].tolist())
    else:
        app.logger.warning("No data found in the filtered_studies table.")
    con.close()
else:
    app.logger.warning("DuckDB file does not exist. The app will run without the data.")

@app.route('/')
def index():
    if not db_exists or stored_embeddings is None:
        return render_template('no_data.html')
    return render_template('index.html')

@app.route('/list-files')
def list_files():
    directory = '/app/src/data'
    try:
        files = os.listdir(directory)
        app.logger.info(f"Files in {directory}: {files}")
        return render_template('list_files.html', files=files)
    except FileNotFoundError as e:
        app.logger.error(f"Error listing files: {e}")
        return render_template('no_data.html', error="Directory not found")

@app.route('/directory-info')
def directory_info():
    current_directory = os.getcwd()
    parent_directory = os.path.abspath(os.path.join(current_directory, 'src/data'))
    try:
        parent_contents = os.listdir(parent_directory)
        app.logger.info(f"Current directory: {current_directory}")
        app.logger.info(f"Parent directory: {parent_directory}")
        app.logger.info(f"Contents of parent directory: {parent_contents}")
        return render_template('directory_info.html', current_directory=current_directory, parent_directory=parent_directory, parent_contents=parent_contents)
    except FileNotFoundError as e:
        app.logger.error(f"Error listing parent directory contents: {e}")
        return render_template('no_data.html', error="Directory not found")

@app.route('/result', methods=['POST'])
def result():
    if not db_exists or stored_embeddings is None:
        return render_template('no_data.html', error="No data available")
    user_input_sentence = request.form['sentence']
    user_input_embedding = compute_embeddings([user_input_sentence])
    cosine_similarities = F.cosine_similarity(user_input_embedding.unsqueeze(1), stored_embeddings.unsqueeze(0), dim=2)
    highest_similarity_idx = torch.argmax(cosine_similarities).item()  # Ensure this is an integer
    most_similar_nct_id = df.iloc[highest_similarity_idx]['nct_id']
    most_similar_brief_title = df.iloc[highest_similarity_idx]['brief_title']
    return render_template('index.html', nct_id=most_similar_nct_id, brief_title=most_similar_brief_title)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('FLASK_RUN_PORT', 5001)), debug=True)