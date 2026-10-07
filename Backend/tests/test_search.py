from app.search.engine import SearchEngine
from app.search.models import SearchDocument


def test_search_returns_matching_documents():
    documents = [
        SearchDocument(
            id="doc-1",
            title="Python Programming",
            content=(
                "Python is useful for web development "
                "and automation."
            ),
            source="test://python",
        ),
        SearchDocument(
            id="doc-2",
            title="Java Programming",
            content=(
                "Java is widely used for enterprise "
                "applications."
            ),
            source="test://java",
        ),
    ]

    engine = SearchEngine(documents)

    results = engine.search("python")

    assert len(results) == 1
    assert results[0]["document"].id == "doc-1"


def test_bm25_ranks_more_relevant_document_higher():
    documents = [
        SearchDocument(
            id="doc-1",
            title="Python",
            content=(
                "Python is a programming language."
            ),
            source="test://python",
        ),
        SearchDocument(
            id="doc-2",
            title="Python Automation",
            content=(
                "Python Python Python automation "
                "is useful for repetitive tasks."
            ),
            source="test://automation",
        ),
    ]

    engine = SearchEngine(documents)

    results = engine.search("python automation")

    assert len(results) == 2
    assert results[0]["document"].id == "doc-2"


def test_title_match_gets_additional_relevance():
    documents = [
        SearchDocument(
            id="doc-1",
            title="Programming Guide",
            content=(
                "Python is discussed in this document."
            ),
            source="test://guide",
        ),
        SearchDocument(
            id="doc-2",
            title="Python Programming",
            content=(
                "This document discusses programming."
            ),
            source="test://python",
        ),
    ]

    engine = SearchEngine(documents)

    results = engine.search("python")

    assert len(results) == 2
    assert results[0]["document"].id == "doc-2"


def test_exact_phrase_gets_additional_relevance():
    documents = [
        SearchDocument(
            id="doc-1",
            title="Machine Learning",
            content=(
                "Machine learning is a field of "
                "artificial intelligence."
            ),
            source="test://ml",
        ),
        SearchDocument(
            id="doc-2",
            title="Artificial Intelligence",
            content=(
                "Machine and learning are discussed "
                "as separate concepts."
            ),
            source="test://ai",
        ),
    ]

    engine = SearchEngine(documents)

    results = engine.search("machine learning")

    assert len(results) == 2
    assert results[0]["document"].id == "doc-1"


def test_empty_query_returns_no_results():
    documents = [
        SearchDocument(
            id="doc-1",
            title="Python",
            content="Python programming.",
            source="test://python",
        )
    ]

    engine = SearchEngine(documents)

    results = engine.search("   ")

    assert results == []