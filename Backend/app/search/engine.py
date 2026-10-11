
import math
import re
from collections import Counter

from app.search.models import SearchDocument


class SearchEngine:
    """
    BM25-based search engine for SmartSearch.

    BM25 considers:
    - Term frequency
    - Inverse document frequency
    - Document length
    - Average document length

    Additional relevance signals:
    - Title matches
    - Exact phrase matches
    - Stop-word filtering
    """

    K1 = 1.5
    B = 0.75

    TITLE_BOOST = 2.0
    PHRASE_BOOST = 1.5

    STOP_WORDS = {
        "a", "an", "and", "are", "as", "at",
        "be", "but", "by",
        "do", "does", "for", "from",
        "had", "has", "have", "how",
        "i", "if", "in", "into", "is", "it",
        "me", "my",
        "of", "on", "or", "our",
        "the", "their", "this", "to",
        "was", "we", "were", "what", "when",
        "where", "which", "who", "why", "with",
        "you", "your",
    }

    def __init__(self, documents: list[SearchDocument]):
        self.documents = documents

        self.document_tokens = {}
        self.document_frequencies = Counter()

        total_length = 0

        for document in documents:
            tokens = self._tokenize(document.content)

            self.document_tokens[document.id] = tokens
            total_length += len(tokens)

            for token in set(tokens):
                self.document_frequencies[token] += 1

        self.document_count = len(documents)

        if self.document_count:
            self.average_document_length = (
                total_length / self.document_count
            )
        else:
            self.average_document_length = 0.0

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        """
        Normalize text into lowercase tokens and
        remove common English stop words.
        """

        tokens = re.findall(
            r"\b[a-zA-Z0-9]+\b",
            text.lower(),
        )

        return [
            token
            for token in tokens
            if token not in SearchEngine.STOP_WORDS
        ]

    @staticmethod
    def _normalize_text(text: str) -> str:
        """Normalize text for phrase matching."""

        return " ".join(SearchEngine._tokenize(text))

    def _calculate_idf(self, term: str) -> float:
        """
        Calculate inverse document frequency (IDF).
        Rare terms receive greater importance.
        """

        document_frequency = self.document_frequencies.get(
            term, 0
        )

        if self.document_count == 0:
            return 0.0

        return math.log(
            1
            + (
                self.document_count
                - document_frequency
                + 0.5
            )
            / (
                document_frequency + 0.5
            )
        )

    def _calculate_bm25(
        self,
        term: str,
        term_frequency: int,
        document_length: int,
    ) -> float:
        """Calculate one term's contribution to BM25."""

        if term_frequency == 0:
            return 0.0

        if self.average_document_length == 0:
            return 0.0

        idf = self._calculate_idf(term)

        length_normalization = (
            1
            - self.B
            + self.B
            * (
                document_length
                / self.average_document_length
            )
        )

        numerator = term_frequency * (self.K1 + 1)

        denominator = (
            term_frequency
            + self.K1 * length_normalization
        )

        return idf * (numerator / denominator)

    def _calculate_score(
        self,
        document: SearchDocument,
        query: str,
    ) -> float:
        """Calculate the complete relevance score."""

        query_tokens = self._tokenize(query)

        if not query_tokens:
            return 0.0

        document_tokens = self.document_tokens.get(
            document.id, []
        )

        if not document_tokens:
            return 0.0

        term_frequencies = Counter(document_tokens)
        document_length = len(document_tokens)

        score = 0.0

        # BM25 content score
        for term in set(query_tokens):
            term_frequency = term_frequencies.get(term, 0)

            score += self._calculate_bm25(
                term=term,
                term_frequency=term_frequency,
                document_length=document_length,
            )

        # Title relevance boost
        normalized_title = self._normalize_text(
            document.title
        )
        title_frequencies = Counter(
            self._tokenize(document.title)
        )

        for term in set(query_tokens):
            if title_frequencies.get(term, 0) > 0:
                score += self.TITLE_BOOST

        # Exact phrase relevance boost
        normalized_query = self._normalize_text(query)
        normalized_content = self._normalize_text(
            document.content
        )

        if (
            normalized_query
            and normalized_query in normalized_content
        ):
            score += self.PHRASE_BOOST

        if (
            normalized_query
            and normalized_query in normalized_title
        ):
            score += self.PHRASE_BOOST

        return round(score, 4)

    def search(self, query: str) -> list[dict]:
        """
        Search documents and return positive-scoring
        results ordered by BM25 relevance.
        """

        normalized_query = self._normalize_text(query)

        if not normalized_query:
            return []

        results = []

        for document in self.documents:
            score = self._calculate_score(
                document,
                normalized_query,
            )

            if score > 0:
                results.append({
                    "document": document,
                    "score": score,
                })

        results.sort(
            key=lambda result: result["score"],
            reverse=True,
        )

        return results
