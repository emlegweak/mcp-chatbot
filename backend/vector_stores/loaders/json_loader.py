import json
from vector_stores.base import DocumentLoader


class JSONLoader(DocumentLoader):
    def load(self, path: str):
        with open(path, "r") as file:
            return json.load(file)
