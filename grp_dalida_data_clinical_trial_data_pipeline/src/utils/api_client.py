# src/utils/api_client.py
from dlt.sources.helpers import requests

class APIClient:
    def __init__(self, base_url):
        self.base_url = base_url

    def fetch_data(self, params):
        response = requests.get(self.base_url, params=params)
        if not response.ok:
            raise Exception(f'Request failed: {response.text}')
        return response.json()
