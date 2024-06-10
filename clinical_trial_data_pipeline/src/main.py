# src/main.py
import json
import os
import sys
import time
from tqdm import tqdm
from utils.api_client import APIClient
from models.entity_extractor import EntityExtractor
from utils.data_pipeline import DataPipeline
from utils.logger import setup_logger
from utils.age_utils import normalize_ages

from dotenv import load_dotenv
# Load environment variables from the .env file
load_dotenv()

# Function to load config
def load_config():
    config_path = os.path.join(os.path.dirname(__file__), 'config', 'config.json')
    with open(config_path, 'r') as file:
        return json.load(file)

config = load_config()
DUCKDB_FILE_PATH = config.get('duckdb_file_path')
API_BASE_URL = config.get('api_base_url')
TARGET_STATUSES = config.get('target_statuses')

def filter_studies_by_status(studies_data, target_statuses):
    filtered_studies = [study for study in studies_data if study.get("overallStatus") in target_statuses]
    return filtered_studies

def main():
    logger = setup_logger(__name__)
    api_client = APIClient(API_BASE_URL)
    openai_api_key = os.getenv("OPENAI_API_KEY")
    extractor = EntityExtractor(use_gpt=False, openai_api_key=openai_api_key)
    data_pipeline = DataPipeline("clinical_trial_pipeline", DUCKDB_FILE_PATH, DUCKDB_FILE_PATH)

    params = {
        'pageSize': 1000,
        'format': 'json',
    }
    
    page = 1
    studies = []

    overall_start_time = time.time()
    logger.info('Started to Extract Data from ClinicalTrial.Gov API')

    
    while page <= 5: # For testing faster, putting max page of api pagination, for demo purpose
    # while True: # For fetching all studies data
        logger.info(f'--- page: {page} ---')
        
        try:
            data = api_client.fetch_data(params)
        except Exception as e:
            logger.error(str(e))
            break

        if not data.get('studies', []):
            break

        studies.extend(data['studies'])
        # Check for next page token
        next_page_token = data.get('nextPageToken')
        if not next_page_token:
            break  # No next page, exit the loop

        # Update params for next page
        params['pageToken'] = next_page_token
        page += 1  # Increment page counter

    # Initialize an empty list to store the data
    studies_data = []

    # Start timer
    start_time = time.time()

    # Loop for storing data with progress bar
    for study in tqdm(studies, desc="Processing studies"):
        # Safely access nested keys
        nctId = study['protocolSection']['identificationModule'].get('nctId', 'Unknown')
        overallStatus = study['protocolSection']['statusModule'].get('overallStatus', 'Unknown')
        startDate = study['protocolSection']['statusModule'].get('startDateStruct', {}).get('date', 'Unknown Date')
        conditions = ', '.join(study['protocolSection'].get('conditionsModule', {}).get('conditions', ['No conditions listed']))
        briefTitle = study['protocolSection']['identificationModule'].get('briefTitle', 'Unknown')
        acronym = study['protocolSection']['identificationModule'].get('acronym', 'Unknown')

        # Extract interventions safely
        interventions_list = study['protocolSection'].get('armsInterventionsModule', {}).get('interventions', [])
        interventions = ', '.join([intervention.get('name', 'No intervention name listed') for intervention in interventions_list]) if interventions_list else "No interventions listed"

        # Extract locations safely
        locations_list = study['protocolSection'].get('contactsLocationsModule', {}).get('locations', [])
        locations = ', '.join([f"{location.get('city', 'No City')} - {location.get('country', 'No Country')}" for location in locations_list]) if locations_list else "No locations listed"

        # Extract dates and phases
        primaryCompletionDate = study['protocolSection']['statusModule'].get('primaryCompletionDateStruct', {}).get('date', 'Unknown Date')
        studyFirstPostDate = study['protocolSection']['statusModule'].get('studyFirstPostDateStruct', {}).get('date', 'Unknown Date')
        lastUpdatePostDate = study['protocolSection']['statusModule'].get('lastUpdatePostDateStruct', {}).get('date', 'Unknown Date')
        studyType = study['protocolSection'].get('designModule', {}).get('studyType', 'Unknown')
        phases = ', '.join(study['protocolSection'].get('designModule', {}).get('phases', ['Not Available']))

        # Extract Eligibility
        eligibilityCriteria = study['protocolSection'].get('eligibilityModule', {}).get('eligibilityCriteria', 'Unknown')
        sex = study['protocolSection'].get('eligibilityModule', {}).get('sex', 'Unknown')
        minimumAge = study['protocolSection'].get('eligibilityModule', {}).get('minimumAge', '0 Year')
        maximumAge = study['protocolSection'].get('eligibilityModule', {}).get('maximumAge', '120 Years')
        stdAges = study['protocolSection'].get('eligibilityModule', {}).get('stdAges', 'Unknown')

        # Extend the data to the list as a dictionary
        studies_data.append({
            'nctId': nctId,
            'briefTitle': briefTitle,
            'acronym': acronym,
            'overallStatus': overallStatus,
            'startDate': startDate,
            'conditions': conditions,
            'interventions': interventions,
            'locations': locations,
            'primaryCompletionDate': primaryCompletionDate,
            'studyFirstPostDate': studyFirstPostDate,
            'lastUpdatePostDate': lastUpdatePostDate,
            'studyType': studyType,
            'phases': phases,
            'eligibilityCriteria': eligibilityCriteria,
            'sex': sex,
            'minimumAge': minimumAge,
            'maximumAge': maximumAge,
            'stdAges': stdAges
        })

    # End timer
    end_time = time.time()
    elapsed_time = end_time - start_time
    minutes = int(elapsed_time // 60)
    seconds = elapsed_time % 60

    # Normalize ages before processing entities
    normalize_ages(studies_data)

    logger.info('Successfully stored data as list')  # Log completion message
    logger.info(f'Total elapsed time: {minutes} minutes and {seconds:.2f} seconds')  # Log total elapsed time of Loop

    filtered_studies = filter_studies_by_status(studies_data, TARGET_STATUSES)

    logger.info('Extracting Entity diseases and medications from EligibilityCriteria Module')
    for study in tqdm(filtered_studies, desc="Processing filtered studies"):
        eligibilityCriteria = study['eligibilityCriteria']
        diseases_medications = extractor.extract_specific_entities(eligibilityCriteria)
        diseases = diseases_medications.get('diseases', '')  # Directly assign the highest-scoring entity
        medications = diseases_medications.get('medications', '')  # Directly assign the highest-scoring entity
        study['diseases'] = diseases
        study['medications'] = medications
        

    logger.info('Sample transformed study data:')
    logger.info(filtered_studies[0])  # Log the first item for verification

    logger.info('Finished Extracting Entity diseases and medications.')

    logger.info('Loading studies data to duckdb as table name studies')
    data_pipeline.load_data(studies_data, 'studies')
    logger.info('Successfully loaded studies data')

    logger.info('Loading filtered_studies_data to duckdb as table name filtered_studies')
    data_pipeline.load_data(filtered_studies, 'filtered_studies')
    logger.info('Successfully loaded filtered studies Data')

    overall_end_time = time.time()
    overall_elapsed_time = overall_end_time - overall_start_time
    overall_minutes = int(overall_elapsed_time // 60)
    overall_seconds = overall_elapsed_time % 60
    logger.info(f'Overall Total elapsed time: {overall_minutes} minutes and {overall_seconds:.2f} seconds')
    
    # Ensure the script exits cleanly
    sys.exit(0)

if __name__ == "__main__":
    main()