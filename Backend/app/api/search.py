from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.document import Document
from app.search.engine import SearchEngine
from app.search.models import SearchDocument


router = APIRouter(
    prefix="/search",
    tags=["Search"],
)


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
    Search all indexed documents and return
    results ranked by relevance.
    """

    database_documents = (
        db.query(Document).all()
    )

    documents = [
        SearchDocument(
            id=str(document.id),
            title=document.title,
            content=document.content,
            source=document.source,
        )
        for document in database_documents
    ]

    search_engine = SearchEngine(
        documents
    )

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
            }
            for result in results
        ],
    }