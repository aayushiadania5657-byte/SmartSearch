from app.search.engine import SearchEngine
from app.search.models import SearchDocument


def test_search_ranks_matching_documents():
    documents = [
        SearchDocument(
            id="doc-1",
            title="Python Programming",
            content="Python is useful for web development and automation.",
            source="test://python",
        ),
        SearchDocument(
            id="doc-2",
            title="Java Programming",
            content="Java is widely used for enterprise applications.",
            source="test://java",
        ),
        SearchDocument(
            id="doc-3",
            title="Python Automation",
            content="Python Python automation can simplify repetitive tasks.",
            source="test://automation",
        ),
    ]

    engine = SearchEngine(documents)

    results = engine.search("python")

    assert len(results) == 2
    assert results[0]["document"].id == "doc-3"
    assert results[0]["score"] > results[1]["score"]