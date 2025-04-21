import os
import json
import faiss  # https://ai.meta.com/tools/faiss/
import numpy as np
from typing import List, Dict, Optional
from sentence_transformers import SentenceTransformer
from vector_stores.base import VectorStore, DocumentLoader


class LocalFAISSStore(VectorStore):
    """
    Implements a local vector store using FAISS and SentenceTransformers. 

    This store uses a 384-dimensional embedding model to convert documents into dense vectors,
    which are indexed in-memory using FAISS for fast similarity search. 
    """

    def __init__(
        self,
        loader: DocumentLoader,
        path: str,
        index_path: Optional[str] = None
    ):
        """
        Initialize the FAISS index and loads documents using the provided loader. 

        Args:
            loader (DocumentLoader): A loader implementation that supports extracting documents from JSON, PDF, TXT.
            data_path (str): Path to the input file or directory containing documents.
            index_path (Optional[str]): Optional path to a prebuilt FAISS index (not used in-memory version).
        """
        # 384-dim transformer-based embedding model
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.index_path = index_path
        self.path = path

        # FAISS index for L2 (Euclidean) similarity search
        self.index = faiss.IndexFlatL2(384)
        # stores raw documents in-memory
        self.documents: List[Dict[str, str]] = []

        if os.path.exists(self.path):
            self.documents = loader.load(path)

        if self.documents:
            vectors = self.model.encode([doc["text"]
                                        for doc in self.documents])
            self.index.add(np.array(vectors).astype("float32"))

    def query(self, query: str, top_k: int = 5):
        """
        Search for the top_k most similar documents based on vector similarity.

        Args:
            query (str): The natural language query string.
            top_k (int): The number of similar results to return.

        Returns: 
            A list of document dictionaries with similarity to the input query.
        """
        # encode query into vector
        query_vector = self.model.encode([query]).astype("float32")

        # return fallback if no documents are indexed
        if self.index.ntotal == 0:
            return [{"text": "No documents indexed yet."}]

        # perform vector similarity search
        distances, indices = self.index.search(query_vector, top_k)

        # retrieve documents by index
        results = []
        for i in indices[0]:
            if i < len(self.documents):
                results.append(self.documents[i])
        return results
