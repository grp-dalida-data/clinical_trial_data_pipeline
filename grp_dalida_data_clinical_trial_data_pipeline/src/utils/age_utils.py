# src/utils/age_utils.py
import re

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
