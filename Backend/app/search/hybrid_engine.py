
from app.search.engine import SearchEngine
from app.search.models import SearchDocument
from app.search.semantic_engine import SemanticSearchEngine


class HybridSearchEngine:
    """
    Combine keyword and semantic rankings using
    Reciprocal Rank Fusion (RRF).
    """

    RRF_K = 60
    SEMANTIC_TOP_K = 3

    def __init__(
        self,
        documents: list[SearchDocument],
        keyword_engine=None,
        semantic_engine=None,
        keyword_weight: float = 1.0,
        semantic_weight: float = 1.0,
        semantic_top_k: int = SEMANTIC_TOP_K,
    ):
        if keyword_weight < 0 or semantic_weight < 0:
            raise ValueError("Ranking weights cannot be negative.")

        if keyword_weight == 0 and semantic_weight == 0:
            raise ValueError(
                "At least one ranking weight must be positive."
            )

        if semantic_top_k < 1:
            raise ValueError("semantic_top_k must be at least 1.")

        self.documents = documents
        self.keyword_weight = keyword_weight
        self.semantic_weight = semantic_weight
        self.semantic_top_k = semantic_top_k

        self.keyword_engine = (
            keyword_engine
            if keyword_engine is not None
            else SearchEngine(documents)
        )

        self.semantic_engine = (
            semantic_engine
            if semantic_engine is not None
            else SemanticSearchEngine(documents)
        )

    @staticmethod
    def _deduplication_key(document: SearchDocument) -> tuple[str, str]:
        """
        Identify duplicate documents by normalized title and content.

        Source and ID are intentionally excluded so that copies
        imported from different locations can be grouped.
        """

        normalized_title = " ".join(
            document.title.casefold().split()
        )
        normalized_content = " ".join(
            document.content.casefold().split()
        )

        return normalized_title, normalized_content

    def search(self, query: str) -> list[dict]:
        """Return deduplicated documents ranked by RRF."""

        if not query or not query.strip():
            return []

        keyword_results = self.keyword_engine.search(query)
        semantic_results = self.semantic_engine.search(query)

        semantic_results = semantic_results[:self.semantic_top_k]

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
                fused_scores[document_id] += weight / (
                    self.RRF_K + rank
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

        # Remove identical title/content pairs, keeping the
        # highest-ranked copy. Database records are not deleted.
        deduplicated_results = []
        seen_keys = set()

        for result in ranked_documents:
            key = self._deduplication_key(result["document"])

            if key in seen_keys:
                continue

            seen_keys.add(key)
            deduplicated_results.append(result)

        return deduplicated_results
