from dataclasses import dataclass


@dataclass
class SearchDocument:
    """
    Internal representation of a searchable document.
    """

    id: str
    title: str
    content: str
    source: str