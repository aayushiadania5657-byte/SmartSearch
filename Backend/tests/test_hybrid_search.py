
from app.search.hybrid_engine import HybridSearchEngine
from app.search.models import SearchDocument


class FakeSearchEngine:
    def __init__(self, results):
        self.results = results

    def search(self, query):
        return self.results


def make_documents():
    return [
        SearchDocument(
            id="1",
            title="Python Guide",
            content="Learn Python programming.",
            source="test://python",
        ),
        SearchDocument(
            id="2",
            title="Automation Guide",
            content="Automate repetitive computer tasks.",
            source="test://automation",
        ),
        SearchDocument(
            id="3",
            title="Cooking Guide",
            content="Learn to prepare meals.",
            source="test://cooking",
        ),
    ]


def test_hybrid_search_combines_both_rankings():
    documents = make_documents()

    keyword_engine = FakeSearchEngine([
        {"document": documents[0], "score": 8.0},
        {"document": documents[1], "score": 5.0},
    ])

    semantic_engine = FakeSearchEngine([
        {"document": documents[1], "score": 0.91},
        {"document": documents[0], "score": 0.82},
    ])

    engine = HybridSearchEngine(
        documents,
        keyword_engine=keyword_engine,
        semantic_engine=semantic_engine,
    )

    results = engine.search("Python automation")

    assert len(results) == 2
    assert results[0]["document"].id == "1"
    assert results[1]["document"].id == "2"


def test_document_ranked_first_by_both_engines_wins():
    documents = make_documents()

    keyword_engine = FakeSearchEngine([
        {"document": documents[0], "score": 10.0},
        {"document": documents[1], "score": 4.0},
    ])

    semantic_engine = FakeSearchEngine([
        {"document": documents[0], "score": 0.95},
        {"document": documents[1], "score": 0.80},
    ])

    engine = HybridSearchEngine(
        documents,
        keyword_engine=keyword_engine,
        semantic_engine=semantic_engine,
    )

    results = engine.search("Python programming")

    assert results[0]["document"].id == "1"
    assert results[0]["score"] > results[1]["score"]


def test_empty_query_returns_no_results():
    documents = make_documents()

    engine = HybridSearchEngine(
        documents,
        keyword_engine=FakeSearchEngine([]),
        semantic_engine=FakeSearchEngine([]),
    )

    assert engine.search("") == []
    assert engine.search("   ") == []


def test_documents_are_not_duplicated():
    documents = make_documents()

    keyword_engine = FakeSearchEngine([
        {"document": documents[0], "score": 5.0},
    ])

    semantic_engine = FakeSearchEngine([
        {"document": documents[0], "score": 0.90},
        {"document": documents[1], "score": 0.70},
    ])

    engine = HybridSearchEngine(
        documents,
        keyword_engine=keyword_engine,
        semantic_engine=semantic_engine,
    )

    results = engine.search("Python")
    result_ids = [result["document"].id for result in results]

    assert len(result_ids) == len(set(result_ids))
    assert set(result_ids) == {"1", "2"}


def test_negative_weights_are_rejected():
    documents = make_documents()

    try:
        HybridSearchEngine(
            documents,
            keyword_engine=FakeSearchEngine([]),
            semantic_engine=FakeSearchEngine([]),
            keyword_weight=-1.0,
        )
    except ValueError:
        pass
    else:
        raise AssertionError("Negative weights should be rejected.")


def test_both_zero_weights_are_rejected():
    documents = make_documents()

    try:
        HybridSearchEngine(
            documents,
            keyword_engine=FakeSearchEngine([]),
            semantic_engine=FakeSearchEngine([]),
            keyword_weight=0.0,
            semantic_weight=0.0,
        )
    except ValueError:
        pass
    else:
        raise AssertionError("Both zero weights should be rejected.")


def test_identical_documents_are_deduplicated():
    first = SearchDocument(
        id="10",
        title="Cybersecurity Best Practices",
        content="Keep software updated and enable a firewall.",
        source="demo://cybersecurity",
    )

    duplicate = SearchDocument(
        id="11",
        title="Cybersecurity Best Practices",
        content="Keep software updated and enable a firewall.",
        source="upload://cybersecurity.pdf",
    )

    keyword_engine = FakeSearchEngine([
        {"document": first, "score": 5.0},
        {"document": duplicate, "score": 4.0},
    ])

    semantic_engine = FakeSearchEngine([
        {"document": duplicate, "score": 0.95},
        {"document": first, "score": 0.90},
    ])

    engine = HybridSearchEngine(
        [first, duplicate],
        keyword_engine=keyword_engine,
        semantic_engine=semantic_engine,
    )

    results = engine.search("cybersecurity")

    assert len(results) == 1
    assert results[0]["document"].id in {"10", "11"}
