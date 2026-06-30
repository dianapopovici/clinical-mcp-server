"""Thin HTTP client for the Clinical RAG Engine.

Semantic search is *not* reimplemented here — it is delegated to the companion
Clinical RAG Engine over its HTTP API. This keeps the two services decoupled:
the MCP server owns governance, the RAG engine owns retrieval.
"""

from __future__ import annotations

from typing import Any

import httpx

from clinical_mcp.config import settings


class RAGClient:
    def __init__(self, base_url: str | None = None, timeout: float = 30.0) -> None:
        self.base_url = (base_url or settings.rag_api_url).rstrip("/")
        self.timeout = timeout

    def search(self, query: str, limit: int) -> dict[str, Any]:
        """Query the RAG engine and return its answer plus capped citations.

        On any connectivity error a structured error dict is returned, so the
        calling agent receives a clean message instead of a stack trace.
        """
        try:
            response = httpx.post(
                f"{self.base_url}/query",
                json={"question": query},
                timeout=self.timeout,
            )
            response.raise_for_status()
            payload = response.json()
        except httpx.HTTPError as exc:
            return {
                "error": "clinical-rag-engine unreachable",
                "detail": str(exc),
                "hint": f"is the RAG engine running at {self.base_url}?",
            }

        sources = payload.get("sources", []) or []
        return {
            "answer": payload.get("answer", ""),
            "sources": sources[:limit],
        }
