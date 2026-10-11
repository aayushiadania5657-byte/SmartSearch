
from app.search.engine import SearchEngine
from app.search.models import SearchDocument
from app.search.semantic_engine import SemanticSearchEngine


class HybridSearchEngine:
    """
    Combine keyword and semantic rankings using
    Reciprocal Rank Fusion (RRF).

    RRF combines ranking positions rather than raw
    scores, which have different scales.
    """

    RRF_K = 60

    def __init__(
        self,
        documents: list[SearchDocument],
        keyword_engine=None,
        semantic_engine=None,
        keyword_weight: float = 1.0,
        semantic_weight: float = 1.0,
    ):
        if keyword_weight < 0 or semantic_weight < 0:
            raise ValueError("Ranking weights cannot be negative.")

        if keyword_weight == 0 and semantic_weight == 0:
            raise ValueError("At least one ranking weight must be positive.")

        self.documents = documents
        self.keyword_weight = keyword_weight
        self.semantic_weight = semantic_weight

        # Dependency injection makes testing easier and lets us
        # reuse existing engines without modifying them.
        self.keyword_engine = keyword_engine or SearchEngine(documents)
        self.semantic_engine = semantic_engine or SemanticSearchEngine(
            documents
        )

    def search(self, query: str) -> list[dict]:
        """
        Return documents ranked by combined keyword and
        semantic relevance.
        """

        if not query or not query.strip():
            return []

        keyword_results = self.keyword_engine.search(query)
        semantic_results = self.semantic_engine.search(query)

        # Store each document once, even if both engines find it.
        documents_by_id = {
            document.id: document
            for document in self.documents
        }

        fused_scores = {
            document_id: 0.0
            for document_id in documents_by_id
        }

        keyword_ranks = {}
        semantic_ranks = {}

        def add_ranked_results(results, weight, rank_map):
            for rank, result in enumerate(results, start=1):
                document = result["document"]
                document_id = document.id

                if document_id not in documents_by_id:
                    continue

                rank_map[document_id] = rank

                fused_scores[document_id] += (
                    weight / (self.RRF_K + rank)
                )

        add_ranked_results(
            keyword_results,
            self.keyword_weight,
            keyword_ranks,
        )

        add_ranked_results(
            semantic_results,
            self.semantic_weight,
            semantic_ranks,
        )

        ranked_documents = []

        for document_id, document in documents_by_id.items():
            # Exclude documents not retrieved by either engine.
            if (
                document_id not in keyword_ranks
                and document_id not in semantic_ranks
            ):
                continue

            ranked_documents.append(
                {
                    "document": document,
                    "score": round(fused_scores[document_id], 6),
                    "keyword_rank": keyword_ranks.get(document_id),
                    "semantic_rank": semantic_ranks.get(document_id),
                }
            )

        ranked_documents.sort(
            key=lambda result: (
                -result["score"],
                result["document"].id,
            )
        )

        return ranked_documents
