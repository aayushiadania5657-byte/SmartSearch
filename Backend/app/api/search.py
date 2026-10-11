
import hashlib
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
                "score": result["score"],
                "keyword_rank": result["keyword_rank"],
                "semantic_rank": result["semantic_rank"],
            }
            for result in results
        ],
    }
