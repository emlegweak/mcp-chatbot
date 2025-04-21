import fitz  # PyMuPDF https://github.com/pymupdf/PyMuPDF
from vector_stores.base import DocumentLoader


class PDFLoader(DocumentLoader):
    def load(self, path: str):
        documents = []
        with fitz.open(path) as pdf:
            for i, page in enumerate(pdf):
                text = page.get_text()
                documents.append({"text": text, "page": str(i)})
        return documents
