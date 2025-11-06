import os
from typing import List
from pathlib import Path
from dotenv import load_dotenv
from classifier import TextClassifier
from models import DocumentType
from document_types_loader import load_document_types_from_json

load_dotenv()

DATA_PATH = Path(__file__).with_name("data.json")
DOCUMENT_TYPES: List[DocumentType] = load_document_types_from_json(DATA_PATH)

subscription_key = os.getenv("AZURE_OPENAI_API_KEY")
model_name = os.getenv("AZURE_OPENAI_MODEL_NAME")
endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")

# Example usage of the loaded objects (optional quick check)
if __name__ == "__main__":
    # Print the names of document types loaded from data.json
    document_types = [dt.name for dt in DOCUMENT_TYPES]
    document_type_descriptions = {dt.name: dt.description for dt in DOCUMENT_TYPES}
    classifier = TextClassifier(
        api_key=subscription_key,
        endpoint=endpoint,
        model_name=model_name,
    )
    print(
        classifier.classify(
            "This is not an EPC doc",
            document_types,
            label_descriptions=document_type_descriptions,
        )
    )
    