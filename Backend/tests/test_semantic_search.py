
import numpy as np

from app.search.models import SearchDocument
from app.search.semantic_engine import SemanticSearchEngine


class FakeEmbeddingModel:
    """
    Lightweight deterministic model for unit tests.
    These tests do not download or load a real AI model.
    """

    def __init__(self):
        self.embeddings = {
            "Cybersecurity\nProtect computers from hackers and unauthorized access.": [
                1.0, 0.0
            ],
            "Cooking\nLearn to prepare delicious meals at home.": [
                0.0, 1.0
            ],
        }

    def encode(
        self,
        texts,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=False,
    ):
        vectors = []

        for text in texts:
            if text == "How do I keep my computer safe from attacks?":
                vector = [0.9, 0.1]
            else:
                vector = self.embeddings[text]

            vectors.append(vector)

        vectors = np.array(vectors, dtype=float)

        if normalize_embeddings:
            norms = np.linalg.norm(vectors, axis=1, keepdims=True)
            vectors = vectors / norms

        return vectors


def make_documents():
    return [
        SearchDocument(
            id="1",
            title="Cybersecurity",
            content=(
                "Protect computers from hackers and "
                "unauthorized access."
            ),
            source="test://security",
        ),
        SearchDocument(
            id="2",
            title="Cooking",
            content="Learn to prepare delicious meals at home.",
            source="test://cooking",
        ),
    ]


def test_semantic_search_ranks_relevant_document_first():
    engine = SemanticSearchEngine(
        make_documents(),
        model=FakeEmbeddingModel(),
    )

    results = engine.search(
        "How do I keep my computer safe from attacks?"
    )

    assert len(results) == 2
    assert results[0]["document"].title == "Cybersecurity"
    assert results[0]["score"] > results[1]["score"]


def test_empty_query_returns_no_results():
    engine = SemanticSearchEngine(
        make_documents(),
        model=FakeEmbeddingModel(),
    )

    assert engine.search("") == []
    assert engine.search("   ") == []


def test_empty_document_collection_returns_no_results():
    engine = SemanticSearchEngine(
        [],
        model=FakeEmbeddingModel(),
    )

    assert engine.search("cybersecurity") == []


def test_similarity_scores_are_finite():
    engine = SemanticSearchEngine(
        make_documents(),
        model=FakeEmbeddingModel(),
    )

    results = engine.search("How do I keep my computer safe from attacks?")

    assert results
    assert all(np.isfinite(result["score"]) for result in results)
