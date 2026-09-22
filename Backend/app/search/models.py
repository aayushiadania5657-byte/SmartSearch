from dataclasses import dataclass


@dataclass
class SearchDocument:
    id: str
    title: str
    content: str
    source: str