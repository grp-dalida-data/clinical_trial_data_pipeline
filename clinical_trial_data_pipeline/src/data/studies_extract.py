import os
import sys
import dlt
from dlt import pipeline as dlt_pipeline
import logging
import sys
import time
from tqdm import tqdm
import time
import pickle
from dlt.sources.helpers import requests
import re
from transformers import pipeline as hf_pipeline
import torch
import duckdb



# Ensure the 'models' directory is in the Python path
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), '..', 'models')))

"""
Using Hugging Face Model Clinical-AI-Apollo/Medical-NER instead of GPT-3.5
due to the cost I will incur if use OpenAI, as I pull all the studies from
clinicaltrials.gov
"""
from entity_extractor import EntityExtractor 

# Data Pipeline

params = {
    'pageSize': 1000,
    'format': 'json', 
    #'pageToken': None  # first page doesn't need it
}

dlt_pipeline = dlt_pipeline(pipeline_name="clinical_trial_pipeline", destination="duckdb", dataset_name="clinical_trial_data")

overall_start_time = time.time()

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Create a stream handler to output to stdout
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setLevel(logging.INFO)

# Create a formatter and set it for the handler
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
stream_handler.setFormatter(formatter)

# Add the handler to the logger
if not logger.hasHandlers():
    logger.addHandler(stream_handler)

base_url = "https://clinicaltrials.gov/api/v2/studies"
page = 1 # initialize page count
studies = [] # initialize all_page_data


# Start timer
start_time = time.time()

logger.info(f'Started to Extract Data from ClinicalTrial.Gov API')

while True:
  logger.info(f'--- page: {page} ---')  # Log page information
  
  response = requests.get(base_url, params=params)
  
  if not response.ok:
      logger.error('Request failed:', response.text)  # Log error with details
      break
  
  data = response.json()
  data_responses = data['studies']
  studies.extend(data_responses)
  
  
  # Check for next page token
  next_page_token = data.get('nextPageToken')
  if not next_page_token:
      break  # No next page, exit the loop

  # Update params for next page
  params['pageToken'] = next_page_token
  page += 1  # Increment page counter

# End timer
end_time = time.time()
elapsed_time = end_time - start_time
minutes = int(elapsed_time // 60)
seconds = elapsed_time % 60


logger.info('Successfully retrieved all pages.')  # Log completion message
logger.info(f'Total elapsed time: {minutes} minutes and {seconds:.2f} seconds')  # Log total elapsed time for Extracting from API

# Start timer
start_time = time.time()

# Initialize an empty list to store the data
studies_data = []

# Loop for storing data with progress bar
for study in tqdm(studies, desc="Processing studies"):
    # Safely access nested keys
    nctId = study['protocolSection']['identificationModule'].get('nctId', 'Unknown')
    overallStatus = study['protocolSection']['statusModule'].get('overallStatus', 'Unknown')
    startDate = study['protocolSection']['statusModule'].get('startDateStruct', {}).get('date', 'Unknown Date')
    conditions = ', '.join(study['protocolSection'].get('conditionsModule',{}).get('conditions', ['No conditions listed']))
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
    studyType = study['protocolSection'].get('designModule',{}).get('studyType', 'Unknown')
    phases = ', '.join(study['protocolSection'].get('designModule',{}).get('phases', ['Not Available']))

    # Extract Eligibility
    eligibilityCriteria = study['protocolSection'].get('eligibilityModule',{}).get('eligibilityCriteria','Unknown')
    sex = study['protocolSection'].get('eligibilityModule',{}).get('sex','Unknown')
    minimumAge = study['protocolSection'].get('eligibilityModule',{}).get('minimumAge','0 Year')
    maximumAge = study['protocolSection'].get('eligibilityModule',{}).get('maximumAge','120 Years')
    stdAges = study['protocolSection'].get('eligibilityModule',{}).get('stdAges','Uknown')

    # Extend the data to the list as a dictionary
    studies_data.append({
        'nctId' : nctId,
        'briefTitle' : briefTitle,
        'acronym' : acronym,
        'overallStatus' : overallStatus,
        'startDate' : startDate,
        'conditions' : conditions,
        'interventions' : interventions,
        'locations' : locations,
        'primaryCompletionDate' : primaryCompletionDate,
        'studyFirstPostDate' : studyFirstPostDate,
        'lastUpdatePostDate' : lastUpdatePostDate,
        'studyType' : studyType,
        'phases' : phases,
        'eligibilityCriteria' : eligibilityCriteria,
        'sex' : sex,
        'minimumAge' : minimumAge,
        'maximumAge' : maximumAge,
        'stdAges' : stdAges
    })

# End timer
end_time = time.time()
elapsed_time = end_time - start_time
minutes = int(elapsed_time // 60)
seconds = elapsed_time % 60


logger.info('Successfully stored data studies as list ')  # Log completion message
logger.info(f'Total elapsed time: {minutes} minutes and {seconds:.2f} seconds')  # Log total elapsed time of Loop

def convert_age_to_years(age_str):
    # Define conversion factors
    conversion_factors = {
        'year': 1,
        'years': 1,
        'month': 1/12,
        'months': 1/12,
        'week': 1/52,
        'weeks': 1/52,
        'day': 1/365,
        'days': 1/365,
        'hour': 1/8760,
        'hours': 1/8760,
        'minute': 1/525600,
        'minutes': 1/525600
    }

    # Regular expression to extract age and unit
    match = re.match(r'(\d+)\s*(year|years|month|months|week|weeks|day|days|hour|hours|minute|minutes)', age_str.lower())
    
    if match:
        value, unit = match.groups()
        return float(value) * conversion_factors[unit]
    else:
        raise ValueError(f"Unknown age format: {age_str}")
    
def normalize_ages(studies_data):
    for study in studies_data:
        min_age_str = study.get('minimumAge', '0')
        max_age_str = study.get('maximumAge', '120')
        
        try:
            min_age = convert_age_to_years(min_age_str)
        except ValueError as e:
            min_age = float('inf')  # Handle unknown format as no limit
            print(e)
        
        try:
            max_age = convert_age_to_years(max_age_str)
        except ValueError as e:
            max_age = float('inf')  # Handle unknown format as no limit
            print(e)
        
        study['normalized_minimumAge'] = min_age
        study['normalized_maximumAge'] = max_age

normalize_ages(studies_data)

class EntityExtractor:
    def __init__(self, model_name="Clinical-AI-Apollo/Medical-NER", aggregation_strategy='simple'):
        """
        Initialize the EntityExtractor with a specific model.

        Args:
            model_name (str): The name of the model to use for the pipeline.
            aggregation_strategy (str): The strategy to use for aggregation.
        """
        self.pipe = hf_pipeline("token-classification", model=model_name, aggregation_strategy=aggregation_strategy)

    def extract_specific_entities(self, text, target_entities=['DISEASE_DISORDER', 'MEDICATION']):
        """
        Extract specific entities from the given text using the initialized pipeline.

        Args:
            text (str): The input text from which to extract entities.
            target_entities (list): List of entity types to extract (default is ['DISEASE_DISORDER', 'MEDICATION']).

        Returns:
            dict: A dictionary with lists of extracted entities for each target type.
        """
        results = self.pipe(text)
        extracted_entities = {'diseases': [], 'medications': []}
        entity_mapping = {
            'DISEASE_DISORDER': 'diseases',
            'MEDICATION': 'medications'
        }
        
        for entity in results:
            entity_type = entity['entity_group']
            if entity_type in target_entities:
                key = entity_mapping[entity_type]
                extracted_entities[key].append(entity['word'])
        
        return extracted_entities

def get_all_eligibility_criteria(studies_data):
    eligibility_criteria_list = [study["eligibilityCriteria"] for study in studies_data]
    return eligibility_criteria_list

# All eligibility_criteria_list
eligibility_criteria_list = get_all_eligibility_criteria(studies_data)

def get_all_overall_status(studies_data):
    overall_status_list = [study["overallStatus"] for study in studies_data]
    return overall_status_list

# All eligibility_criteria_list
overall_status_list = get_all_overall_status(studies_data)

"""
# This when I check count of studies for every unique overall_status
from collections import Counter

def count_overall_status(overall_status_list):
    status_counts = Counter(overall_status_list)
    return status_counts

# Count each unique overall status
status_counts = count_overall_status(overall_status_list)
"""

def filter_studies_by_status(studies_data, target_statuses):
    filtered_studies = [study for study in studies_data if study.get("overallStatus") in target_statuses]
    return filtered_studies

"""
Define target statuses, this is to reduce the count of the studies
that I'll be extracting it's entity as I would take more than 2 days running 
on my local machine if full data

This is just for a purpose of demonstration of NER (Named Entity Recognition)
using Clinical-AI-Apollo/Medical-NER from hugging face instead of GPT-3.5
"""
target_statuses = ['APPROVED_FOR_MARKETING','AVAILABLE','ENROLLING_BY_INVITATION']

# Filter studies by target statuses
filtered_studies = filter_studies_by_status(studies_data, target_statuses)

# Entity Extractor for Diseases and Medications
extractor = EntityExtractor()

# Start timer
start_time = time.time()

# Loop for storing the entity of diseases and medication with progress bar
"""
This is the one that has been used in place of GPT-3.5
Using Hugging Face Model Clinical-AI-Apollo/Medical-NER
"""
for study in tqdm(filtered_studies, desc="Processing studies"):
    eligibilityCriteria = study['eligibilityCriteria']
    diseases_medications = extractor.extract_specific_entities(eligibilityCriteria)
    study['diseases'] = diseases_medications.get('diseases', '[]')
    study['medications'] = diseases_medications.get('medications', '[]')


# End timer
end_time = time.time()
elapsed_time = end_time - start_time
minutes = int(elapsed_time // 60)
seconds = elapsed_time % 60

logger.info('Successfully stored diseases and medications data as list ')  # Log completion message
logger.info(f'Total elapsed time: {minutes} minutes and {seconds:.2f} seconds')  # Log total elapsed time of Loop

# Normalize and load the data onto the locally created duckdb database 'clinical_trial_pipeline.duckdb'

logger.info('Loading studies data to duckdb as table name studies ')  # Log completion message
dlt_pipeline.run(studies_data, table_name='studies')
logger.info('Successfully loaded studies data')  # Log completion message

logger.info('Loading filtered_studies_data to duckdb as table name filtered_studies')  # Log completion message
dlt_pipeline.run(filtered_studies, table_name='filtered_studies')
logger.info('Successfully loadedfiltered studies Data')  # Log completion message

end_time = time.time()
elapsed_time = end_time - overall_start_time
minutes = int(elapsed_time // 60)
seconds = elapsed_time % 60

logger.info(f'Overall Total elapsed time: {minutes} minutes and {seconds:.2f} seconds')  # Log total elapsed time of Loop