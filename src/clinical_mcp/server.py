"""The Clinical MCP Server.

Exposes three narrow, governed tools to any MCP-compatible agent. The agent
never sends raw SQL or free text identifiers: it calls named capabilities with
typed parameters, every call is policy-checked, and every call is audited.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from mcp.server.fastmcp import FastMCP

from clinical_mcp import audit, policy
from clinical_mcp.config import settings
from clinical_mcp.data_access import ClinicalDataStore
from clinical_mcp.rag_client import RAGClient

mcp = FastMCP("clinical-mcp-server", host=settings.mcp_host, port=settings.mcp_port)


@lru_cache(maxsize=1)
def _store() -> ClinicalDataStore:
    return ClinicalDataStore.from_file(settings.data_path)


@lru_cache(maxsize=1)
def _rag() -> RAGClient:
    return RAGClient()


@mcp.tool()
def search_clinical_notes(query: str, limit: int = 5) -> dict[str, Any]:
    """Search the clinical knowledge base in natural language.

    Returns a grounded answer plus the cited source snippets. Delegates the
    actual retrieval to the Clinical RAG Engine. `limit` caps the number of
    citations returned (1-10).
    """
    policy.enforce_search_limit(limit)
    result = _rag().search(query, limit)
    audit.record(
        "search_clinical_notes",
        {"query": query, "limit": limit},
        row_count=len(result.get("sources", [])),
    )
    return result


@mcp.tool()
def get_patient_summary(patient_pseudo_id: str) -> dict[str, Any]:
    """Return a structured summary for one pseudonymous patient ID (e.g. 'PT-0042').

    Returns age, sex, diagnosis and therapy only — never the free-text note.
    Free-text or real-world identifiers are rejected.
    """
    pid = policy.enforce_pseudo_id(patient_pseudo_id)
    summary = _store().get_summary(pid)
    audit.record(
        "get_patient_summary",
        {"patient_pseudo_id": pid},
        row_count=0 if summary is None else 1,
    )
    if summary is None:
        return {"error": f"no record found for {pid}"}
    return summary.model_dump()


@mcp.tool()
def aggregate_diagnoses(top_n: int = 10) -> list[dict[str, Any]]:
    """Return the most frequent diagnoses as counts (aggregation only, 1-20).

    No row-level data is exported — only diagnosis names and their counts.
    """
    policy.enforce_top_n(top_n)
    counts = _store().aggregate_diagnoses(top_n)
    audit.record(
        "aggregate_diagnoses",
        {"top_n": top_n},
        row_count=len(counts),
    )
    return [c.model_dump() for c in counts]


def run(transport: str = "stdio") -> None:
    if transport == "http":
        mcp.run(transport="streamable-http")
    else:
        mcp.run(transport="stdio")
