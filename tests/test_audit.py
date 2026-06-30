"""Tests for the append-only audit trail."""

import json

from clinical_mcp import audit


def test_record_writes_one_json_line(tmp_path):
    log = tmp_path / "audit.log"
    entry = audit.record(
        "search_clinical_notes",
        {"query": "ipertensione", "limit": 5},
        row_count=5,
        path=str(log),
    )

    assert entry["tool"] == "search_clinical_notes"
    assert entry["row_count"] == 5
    assert "ts" in entry

    lines = log.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    assert json.loads(lines[0]) == entry


def test_record_appends_not_overwrites(tmp_path):
    log = tmp_path / "audit.log"
    audit.record("aggregate_diagnoses", {"top_n": 3}, row_count=3, path=str(log))
    audit.record("get_patient_summary", {"patient_pseudo_id": "PT-0001"}, row_count=1, path=str(log))

    lines = log.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2
