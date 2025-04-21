from .json_loader import JSONLoader
from .pdf_loader import PDFLoader
from vector_stores.base import DocumentLoader


def get_document_loader(format: str) -> DocumentLoader:
    """
    Factory method for creating a document loader based on the file format. 

    Args:
        format (str): The file format - ex. 'json', 'pdf'

    Returns: 
        An instance of a class that implements DocumentLoader.
    """
    format = format.lower()
    if format == "json":
        return JSONLoader()
    elif format == "pdf":
        return PDFLoader()
    else:
        raise ValueError(f"Unsupported document format: {format}")
