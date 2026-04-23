from __future__ import annotations

import json
import math
import re
import sqlite3
from dataclasses import asdict

from core.config import Settings
from core.models import MemoryHit, ResearchRunResult

STOPWORDS = {
    "about",
    "after",
    "against",
    "from",
    "into",
    "that",
    "this",
    "with",
    "what",
    "when",
    "where",
    "would",
    "their",
    "there",
    "which",
    "latest",
    "the",
    "and",
    "for",
    "are",
    "our",
    "how",
    "should",
    "use",
    "can",
    "will",
}

_METADATA_CHAR_LIMIT = 32_000


class MemoryStore:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.settings.ensure_directories()
        self._initialize()

    def find_related_runs(self, question: str, limit: int = 3) -> list[MemoryHit]:
        with self._connect() as connection:
            connection.row_factory = sqlite3.Row
            rows = connection.execute(
                """
                SELECT run_id, created_at, user_question, summary, confidence
                FROM runs
                ORDER BY created_at DESC
                LIMIT 50
                """
            ).fetchall()

        if not rows:
            return []

        query_tokens = self._tokenize(question)
        corpus = [
            self._tokenize(f"{row['user_question']} {row['summary']}")
            for row in rows
        ]
        idf = self._build_idf(corpus)

        matches: list[MemoryHit] = []
        for row, doc_tokens in zip(rows, corpus):
            score = self._weighted_jaccard(query_tokens, doc_tokens, idf)
            if score <= 0:
                continue
            matches.append(
                MemoryHit(
                    run_id=row["run_id"],
                    created_at=row["created_at"],
                    user_question=row["user_question"],
                    summary=row["summary"],
                    confidence=int(row["confidence"]),
                    score=round(score, 4),
                )
            )

        matches.sort(key=lambda item: (item.score, item.created_at), reverse=True)
        return matches[:limit]

    def save_run(self, result: ResearchRunResult) -> None:
        summary = result.final_brief.executive_summary.strip()
        metadata_raw = json.dumps(asdict(result), ensure_ascii=False)
        if len(metadata_raw) > _METADATA_CHAR_LIMIT:
            metadata_raw = metadata_raw[:_METADATA_CHAR_LIMIT]
        with self._connect() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO runs (
                    run_id,
                    created_at,
                    user_question,
                    use_case,
                    summary,
                    final_markdown,
                    confidence,
                    trace_path,
                    metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    result.run_id,
                    result.trace[0].timestamp if result.trace else "",
                    result.user_question,
                    result.use_case,
                    summary,
                    result.final_markdown,
                    result.evaluation.confidence,
                    result.trace_path,
                    metadata_raw,
                ),
            )

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS runs (
                    run_id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    user_question TEXT NOT NULL,
                    use_case TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    final_markdown TEXT NOT NULL,
                    confidence INTEGER NOT NULL,
                    trace_path TEXT NOT NULL,
                    metadata_json TEXT NOT NULL
                )
                """
            )

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(
            self.settings.memory_db_path,
            check_same_thread=False,
        )

    @staticmethod
    def _tokenize(text: str) -> set[str]:
        return {
            token
            for token in re.findall(r"[a-z0-9]{3,}", text.lower())
            if token not in STOPWORDS
        }

    @staticmethod
    def _build_idf(corpus: list[set[str]]) -> dict[str, float]:
        if not corpus:
            return {}

        doc_freq: dict[str, int] = {}
        for document in corpus:
            for token in document:
                doc_freq[token] = doc_freq.get(token, 0) + 1

        total_docs = len(corpus)
        return {
            term: math.log((total_docs + 1) / (freq + 1)) + 1.0
            for term, freq in doc_freq.items()
        }

    @staticmethod
    def _weighted_jaccard(
        left: set[str],
        right: set[str],
        idf: dict[str, float],
    ) -> float:
        if not left or not right:
            return 0.0

        intersection = left & right
        union = left | right
        intersection_weight = sum(idf.get(token, 1.0) for token in intersection)
        union_weight = sum(idf.get(token, 1.0) for token in union)
        if union_weight == 0:
            return 0.0
        return intersection_weight / union_weight
