from .base import VectorStore
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
import os


class AzureAISearchStore(VectorStore):
    def __init__(self):
        endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
        key = os.getenv("AZURE_SEARCH_KEY")
        index_name = os.getenv("AZURE_SEARCH_INDEX")
        self.client = SearchClient(
            endpoint=endpoint, index_name=index_name, credential=AzureKeyCredential(key))

    def query(self, query: str, top_k: int = 5):
        results = self.client.search(query)
        return [{"text": r["content"]} for r in results]
