from __future__ import annotations

import math
from copy import deepcopy
from typing import Any, Callable

from .chunking import _dot
from .embeddings import _mock_embed
from .models import Document


def _normalize(vector: list[float]) -> list[float]:
    values = [float(value) for value in vector]

    if not all(math.isfinite(value) for value in values):
        raise ValueError("Embedding values must be finite")

    norm = math.hypot(*values)

    return [value / norm for value in values] if norm else values


class EmbeddingStore:
    """In-memory vector store; documents must be chunked before ingestion."""

    def __init__(
        self,
        collection_name: str = "documents",
        embedding_fn: Callable[[str], list[float]] | None = None,
    ) -> None:
        self._embedding_fn = (
            embedding_fn if embedding_fn is not None else _mock_embed
        )
        self._collection_name = collection_name

        # Keep starter attributes, but use only the in-memory implementation.
        self._use_chroma = False
        self._store: list[dict[str, Any]] = []
        self._collection = None
        self._next_index = 0

    def _make_record(self, doc: Document) -> dict[str, Any]:
        metadata = deepcopy(doc.metadata)
        metadata.setdefault("doc_id", doc.id)

        return {
            "id": doc.id,
            "content": doc.content,
            "metadata": metadata,
            "embedding": _normalize(self._embedding_fn(doc.content)),
        }

    def _search_records(self, query: str, records: list[dict[str, Any]], top_k: int) -> list[dict[str, Any]]:
        if top_k <= 0 or not records or not query.strip():
            return []

        query_vector = _normalize(self._embedding_fn(query))
        results: list[dict[str, Any]] = []

        for record in records:
            if len(query_vector) != len(record["embedding"]):
                raise ValueError(
                    "Query and document embeddings must have the same dimension"
                )

            results.append(
                {
                    "id": record["id"],
                    "content": record["content"],
                    "metadata": deepcopy(record["metadata"]),
                    "score": _dot(query_vector, record["embedding"]),
                }
            )

        results.sort(key=lambda result: result["score"], reverse=True)

        return results[:top_k]

    def add_documents(self, docs: list[Document]) -> None:
        """Append one record per Document; do not chunk or overwrite by ID."""
        for doc in docs:
            record = self._make_record(doc)

            if (
                self._store
                and len(record["embedding"])
                != len(self._store[0]["embedding"])
            ):
                raise ValueError(
                    "All document embeddings must have the same dimension"
                )

            self._store.append(record)
            self._next_index += 1

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        return self._search_records(query, self._store, top_k)

    def get_collection_size(self) -> int:
        return len(self._store)

    def search_with_filter(self, query: str, top_k: int = 3, metadata_filter: dict = None) -> list[dict]:
        if not metadata_filter:
            return self.search(query, top_k)

        candidates = [
            record
            for record in self._store
            if all(
                key in record["metadata"]
                and record["metadata"][key] == value
                for key, value in metadata_filter.items()
            )
        ]

        return self._search_records(query, candidates, top_k)

    def delete_document(self, doc_id: str) -> bool:
        previous_size = len(self._store)

        self._store = [
            record
            for record in self._store
            if record["metadata"]["doc_id"] != doc_id
        ]

        return len(self._store) < previous_size
