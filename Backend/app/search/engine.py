from collections import Counter

from app.search.models import SearchDocument


class SearchEngine:
    def __init__(self, documents: list[SearchDocument]):
        self.documents = documents

    def search(self, query: str) -> list[dict]:
        query_words = query.lower().split()
        results = []

        for document in self.documents:
            text = f"{document.title} {document.content}".lower()
            word_counts = Counter(text.split())

            score = sum(word_counts[word] for word in query_words)

            if score > 0:
                results.append(
                    {
                        "document": document,
                        "score": score,
                    }
                )

        results.sort(
            key=lambda result: result["score"],
            reverse=True,
        )

        return results