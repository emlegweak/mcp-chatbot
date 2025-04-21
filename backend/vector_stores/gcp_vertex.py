from .base import VectorStore
from google.cloud import aiplatform
import os


class GCPVertexStore(VectorStore):
    def __init__(self):
        aiplatform.init(project=os.getenv("GCP_PROJECT_ID"),
                        location=os.getenv("GCP_REGION"))
        self.index = aiplatform.MatchingEngineIndex(
            endpoint=os.getenv("GCP_VECTOR_INDEX"))

    def query(self, query: str, top_k: int = 5):
        return [{"text": "Example result from GCP Vertex Vector Search"}]
