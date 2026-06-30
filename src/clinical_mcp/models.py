"""Typed data models shared across the server."""

from __future__ import annotations

from pydantic import BaseModel


class ClinicalRecord(BaseModel):
    """A single synthetic clinical record (full row, internal use only)."""

    pseudo_id: str
    age: int
    sex: str
    diagnosis: str
    therapy: str
    note: str


class PatientSummary(BaseModel):
    """The least-privilege view an agent is allowed to retrieve.

    Deliberately excludes the free-text clinical note: agents get structured
    facts, never a raw document dump.
    """

    pseudo_id: str
    age: int
    sex: str
    diagnosis: str
    therapy: str


class DiagnosisCount(BaseModel):
    """An aggregate count — no row-level data leaves the server."""

    diagnosis: str
    count: int
