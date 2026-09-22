from fastapi import APIRouter, Query

from app.search.engine import SearchEngine
from app.search.models import SearchDocument


router = APIRouter(prefix="/search", tags=["Search"])


documents = [
    SearchDocument(
        id="doc-1",
        title="Python Programming",
        content="Python is useful for web development, automation, and artificial intelligence.",
        source="demo://python",
    ),
    SearchDocument(
        id="doc-2",
        title="Java Programming",
        content="Java is widely used for enterprise applications and backend development.",
        source="demo://java",
    ),
    SearchDocument(
        id="doc-3",
        title="Python Automation",
        content="Python Python automation can simplify repetitive tasks and workflows.",
        source="demo://automation",
    ),
]


search_engine = SearchEngine(documents)


@router.get("")
def search(
    q: str = Query(
        ...,
        min_length=1,
        description="Search query",
    )
):
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