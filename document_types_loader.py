import json
from pathlib import Path
from typing import List

from models import DocumentType, Parameter


def load_document_types_from_json(json_path: Path) -> List[DocumentType]:
    with json_path.open(encoding="utf-8") as f:
        raw = json.load(f)
    document_types: List[DocumentType] = []
    for dt in raw.get("document_types", []):
        params = [Parameter(**p) for p in dt.get("parameters", [])]
        document_types.append(
            DocumentType(
                name=dt.get("name", ""),
                description=dt.get("description", ""),
                parameters=params,
            )
        )
    return document_types


