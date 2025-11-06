from dataclasses import dataclass
from typing import List


@dataclass
class Parameter:
    name: str
    description: str


@dataclass
class DocumentType:
    name: str
    description: str
    parameters: List[Parameter]


