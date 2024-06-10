from transformers import pipeline as hf_pipeline
from openai import OpenAI
client = OpenAI()
import os
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

# Set your OpenAI API key
client.api_key = os.getenv("OPENAI_API_KEY")

class EntityExtractor:
    def __init__(self, model_name="Clinical-AI-Apollo/Medical-NER", aggregation_strategy='simple', use_gpt=False, openai_api_key=None):
        """
        Initialize the EntityExtractor with a specific model.

        Args:
            model_name (str): The name of the model to use for the pipeline.
            aggregation_strategy (str): The strategy to use for aggregation.
            use_gpt (bool): Whether to use GPT-3.5 for entity extraction.
            openai_api_key (str): The OpenAI API key to use for GPT-3.5.
        """
        self.use_gpt = use_gpt
        if use_gpt:
            if not openai_api_key:
                raise ValueError("OpenAI API key must be provided if using GPT-3.5")
            client.api_key = openai_api_key
        else:
            self.pipe = hf_pipeline("token-classification", model=model_name, aggregation_strategy=aggregation_strategy)

    def extract_specific_entities(self, text, target_entities=['DISEASE_DISORDER', 'MEDICATION']):
        """
        Extract specific entities from the given text using the initialized pipeline or GPT-3.5.

        Args:
            text (str): The input text from which to extract entities.
            target_entities (list): List of entity types to extract (default is ['DISEASE_DISORDER', 'MEDICATION']).

        Returns:
            dict: A dictionary with the highest-scoring extracted entity for each target type or an empty string if none.
        """
        if self.use_gpt:
            return self.extract_with_gpt(text, target_entities)
        else:
            return self.extract_with_model(text, target_entities)

    def extract_with_model(self, text, target_entities):
        results = self.pipe(text)
        extracted_entities = {'diseases': '', 'medications': ''}
        entity_mapping = {
            'DISEASE_DISORDER': 'diseases',
            'MEDICATION': 'medications'
        }
        highest_score_entities = {key: {'score': 0, 'entity': ''} for key in entity_mapping.values()}
        
        for entity in results:
            entity_type = entity['entity_group']
            if entity_type in target_entities:
                key = entity_mapping[entity_type]
                if entity['score'] > highest_score_entities[key]['score']:
                    highest_score_entities[key] = {'score': entity['score'], 'entity': entity['word']}
        
        for key, value in highest_score_entities.items():
            extracted_entities[key] = value['entity']
        
        return extracted_entities

    def extract_with_gpt(self, text, target_entities):
        messages = [
            {"role": "user", "content": f"Extract the following entities from the text: {', '.join(target_entities)} and output only the highest scoring entity for each in the format {{'diseases': '', 'medications': ''}}. Text: {text}"}
        ]
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo-16k",
            messages=messages,
            temperature=1,
            max_tokens=512,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )
        
        extracted_entities = {'diseases': '', 'medications': ''}
        
        try:
            # Ensure correct parsing of the response content
            response_content = response.choices[0].message.content.strip()
            # Assuming the response is directly a dictionary in string form
            extracted_entities = eval(response_content.split('\n')[0])
        except Exception as e:
            print(f"Error parsing GPT response: {e}")
        
        return extracted_entities