from .aws_opensearch import AWSOpenSearchStore
from .gcp_vertex import GCPVertexStore
from .azure_ai_search import AzureAISearchStore
from .base import DocumentLoader, VectorStore
from .local_faiss import LocalFAISSStore
from .loaders.json_loader import JSONLoader
from .loaders.pdf_loader import PDFLoader


def get_vector_store(provider: str, loader: DocumentLoader, path: str) -> VectorStore:
    if provider == "local":
        return LocalFAISSStore(loader=loader, path=path)
    elif provider == "aws":
        return AWSOpenSearchStore()
    elif provider == "gcp":
        return GCPVertexStore()
    elif provider == "azure":
        return AzureAISearchStore()
    else:
        raise ValueError(f"Unsupported vector store provider: {provider}")
