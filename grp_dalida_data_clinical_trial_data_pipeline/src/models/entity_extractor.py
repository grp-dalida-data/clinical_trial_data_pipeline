from transformers import pipeline as hf_pipeline

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