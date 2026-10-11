
from functools import lru_cache

import numpy as np
from sentence_transformers import SentenceTransformer

from app.search.models import SearchDocument


MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


@lru_cache(maxsize=1)
def load_model() -> SentenceTransformer:
    """
    Load the embedding model once and reuse it.
    The first load may download model files.
    """
    return SentenceTransformer(MODEL_NAME)


class SemanticSearchEngine:
    """
    Search documents by meaning using text embeddings
    and cosine similarity.
    """

    def __init__(
        self,
        documents: list[SearchDocument],
        model: SentenceTransformer | None = None,
    ):
        self.documents = documents
        self.model = model or load_model()

        self.document_embeddings = None

        if documents:
            texts = [
                f"{document.title}\n{document.content}"
                for document in documents
            ]

            self.document_embeddings = self.model.encode(
                texts,
                convert_to_numpy=True,
                normalize_embeddings=True,
                show_progress_bar=False,
            )

    def search(self, query: str) -> list[dict]:
        """
        Return documents ranked by semantic similarity.
        Scores are cosine similarities because embeddings
        are normalized.
        """
        if not query or not query.strip() or not self.documents:
            return []

        query_embedding = self.model.encode(
            [query.strip()],
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )[0]

        similarities = np.dot(
            self.document_embeddings,
            query_embedding,
        )

        ranked_indices = np.argsort(similarities)[::-1]

        results = []

        for index in ranked_indices:
            score = float(similarities[index])

            results.append(
                {
                    "document": self.documents[int(index)],
                    "score": round(score, 4),
                }
            )

        return results
