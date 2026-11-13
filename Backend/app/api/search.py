
import hashlib
import re
import threading

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.document import Document
from app.search.hybrid_engine import HybridSearchEngine
from app.search.models import SearchDocument


router = APIRouter(
    prefix="/search",
    tags=["Search"],
)


# Reuse the hybrid engine while the indexed documents remain unchanged.
_cached_engine: HybridSearchEngine | None = None
_cached_fingerprint: str | None = None
_engine_lock = threading.Lock()


def _fingerprint_documents(
    documents: list[SearchDocument],
) -> str:
    """
    Generate a fingerprint that changes when indexed
    document IDs, titles, content, or sources change.
    """

    digest = hashlib.sha256()

    for document in documents:
        for value in (
            document.id,
            document.title,
            document.content,
            document.source,
        ):
            encoded = value.encode("utf-8")

            # Include the length to keep field boundaries unambiguous.
            digest.update(len(encoded).to_bytes(8, "big"))
            digest.update(encoded)

    return digest.hexdigest()


def _get_hybrid_engine(
    documents: list[SearchDocument],
) -> HybridSearchEngine:
    """
    Reuse the engine for unchanged documents.
    Rebuild it when the indexed document collection changes.
    """

    global _cached_engine, _cached_fingerprint

    fingerprint = _fingerprint_documents(documents)

    with _engine_lock:
        if (
            _cached_engine is None
            or _cached_fingerprint != fingerprint
        ):
            _cached_engine = HybridSearchEngine(documents)
            _cached_fingerprint = fingerprint

        return _cached_engine


def _build_snippet(
    content: str,
    query: str,
    max_length: int = 240,
) -> str:
    """
    Extract a short excerpt near a matching query phrase or term.
    If no literal match exists, return the beginning of the content.
    """

    if not content:
        return ""

    match_position = -1

    # First, look for the complete query phrase.
    phrase = query.strip()

    if phrase:
        phrase_match = re.search(
            re.escape(phrase),
            content,
            flags=re.IGNORECASE,
        )

        if phrase_match:
            match_position = phrase_match.start()

    # If the complete phrase is absent, find the earliest query term.
    if match_position == -1:
        terms = re.findall(r"\w+", query, flags=re.UNICODE)

        positions = []

        for term in terms:
            if len(term) < 2:
                continue

            term_match = re.search(
                re.escape(term),
                content,
                flags=re.IGNORECASE,
            )

            if term_match:
                positions.append(term_match.start())

        if positions:
            match_position = min(positions)

    if match_position == -1:
        match_position = 0

    start = max(0, match_position - max_length // 3)
    end = min(len(content), start + max_length)

    # Avoid cutting words at the beginning of the excerpt.
    if start > 0:
        next_space = content.find(" ", start)
        if next_space != -1 and next_space < end:
            start = next_space + 1

    # Extend the end slightly to finish the last word.
    if end < len(content):
        next_space = content.find(" ", end)
        if next_space != -1:
            end = next_space

    snippet = content[start:end].strip()

    if start > 0:
        snippet = "..." + snippet

    if end < len(content):
        snippet += "..."

    return snippet


@router.get("")
def search(
    q: str = Query(
        ...,
        min_length=1,
        description="Search query",
    ),
    db: Session = Depends(get_db),
):
    """
    Search indexed documents using hybrid keyword
    and semantic relevance ranking.
    """

    database_documents = db.query(Document).all()

    documents = [
        SearchDocument(
            id=str(document.id),
            title=document.title,
            content=document.content,
            source=document.source,
        )
        for document in database_documents
    ]

    # Avoid loading the embedding model when there is
    # nothing to search.
    if not documents:
        return {
            "query": q,
            "count": 0,
            "results": [],
        }

    search_engine = _get_hybrid_engine(documents)
    results = search_engine.search(q)

    return {
        "query": q,
        "count": len(results),
        "results": [
            {
                "id": result["document"].id,
                "title": result["document"].title,
                "source": result["document"].source,
                "snippet": _build_snippet(
                    result["document"].content,
                    q,
                ),
                "score": result["score"],
                "keyword_rank": result["keyword_rank"],
                "semantic_rank": result["semantic_rank"],
            }
            for result in results
        ],
    }
