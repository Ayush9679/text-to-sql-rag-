import re


class RelevanceScorer:

    STOP_WORDS = {
        "a",
        "an",
        "the",
        "is",
        "are",
        "was",
        "were",
        "of",
        "to",
        "in",
        "on",
        "for",
        "from",
        "by",
        "with",
        "and",
        "or",
        "what",
        "which",
        "how",
        "many",
        "much",
        "did",
        "do",
        "does",
        "show",
        "me",
        "our",
    }

    def tokenize(self, text: str) -> list[str]:
        tokens = re.findall(
            r"[a-zA-Z_][a-zA-Z0-9_]*",
            text.lower(),
        )

        return [
            token
            for token in tokens
            if token not in self.STOP_WORDS
        ]

    def score(
        self,
        query: str,
        content: str,
    ) -> float:

        query_terms = self.tokenize(query)
        content_terms = self.tokenize(content)

        if not query_terms or not content_terms:
            return 0.0

        matched_terms = 0

        for query_term in query_terms:

            for content_term in content_terms:

                if (
                    query_term == content_term
                    or query_term in content_term
                    or content_term in query_term
                ):
                    matched_terms += 1
                    break

        return round(
            matched_terms / len(query_terms),
            4,
        )