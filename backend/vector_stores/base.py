from abc import ABC, abstractmethod
from typing import List, Dict


class VectorStore(ABC):
    """
    Abstract base class for vector store implementations
    """
    @abstractmethod
    def query(self, query: str, top_k: int = 5) -> List[Dict[str, str]]:
        """
        Perform a vector similarity search against the store. 

        Args: 
            query (str): The natural language query or embedding text.
            top_k (int): The number of top results to return.

        Returns:
            A list of matched records, typically including content and optional metadata fields.
        """
        pass


class DocumentLoader(ABC):
    """
    Abstract base class for document loaders that extract text from various file formats
    (ex.JSON, PDF, TXT) for use in vector embedding pipelines.
    """
    @abstractmethod
    def load(self, path: str) -> List[Dict[str, str]]:
        """
        Loads documents from the given path and returns them as a list of {"text": "..."} dicts.

        Args:
            path (str): Path to the file/directory containing documents to load. 

        Returns:
            A list of dictionaries, each with a "text" field containing extracted content.
        """
        pass
