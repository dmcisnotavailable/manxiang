from __future__ import annotations

import re
from dataclasses import dataclass

from manxiang.schema import SourceChunk


@dataclass(frozen=True)
class RetrievalResult:
    chunk: SourceChunk
    score: float
    matched_terms: tuple[str, ...]


class KeywordRetriever:
    def retrieve(self, query: str, chunks: list[SourceChunk], limit: int = 5) -> list[RetrievalResult]:
        if limit <= 0:
            return []
        terms = self._terms(query)
        if not terms:
            return []
        results = [self._score_chunk(terms, chunk) for chunk in chunks]
        non_zero = [result for result in results if result.score > 0]
        return sorted(non_zero, key=lambda result: result.score, reverse=True)[:limit]

    def _score_chunk(self, terms: list[str], chunk: SourceChunk) -> RetrievalResult:
        normalized = chunk.text.lower()
        matched = tuple(term for term in terms if term.lower() in normalized)
        coverage = len(matched) / len(terms)
        density = len(matched) / max(1, len(chunk.text))
        return RetrievalResult(
            chunk=chunk,
            score=round(coverage * 100 + density, 6),
            matched_terms=matched,
        )

    def _terms(self, query: str) -> list[str]:
        raw_terms = re.split(r"[\s,，.。、!！?？;；:：]+", query.strip())
        terms: list[str] = []
        for term in raw_terms:
            clean = term.strip().lower()
            if clean and clean not in terms:
                terms.append(clean)
        return terms
