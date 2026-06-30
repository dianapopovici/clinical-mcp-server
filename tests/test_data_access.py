"""Tests for the read-only data store and least-privilege summaries."""

from clinical_mcp.data_access import ClinicalDataStore
from clinical_mcp.models import ClinicalRecord

RECORDS = [
    ClinicalRecord(pseudo_id="PT-0001", age=63, sex="F",
                   diagnosis="Ipertensione arteriosa essenziale",
                   therapy="Ramipril 5mg", note="ANAMNESI: ... sensitive free text ..."),
    ClinicalRecord(pseudo_id="PT-0002", age=71, sex="M",
                   diagnosis="Diabete mellito tipo 2",
                   therapy="Metformina 850mg", note="ANAMNESI: ..."),
    ClinicalRecord(pseudo_id="PT-0003", age=55, sex="M",
                   diagnosis="Ipertensione arteriosa essenziale",
                   therapy="Ramipril 5mg", note="ANAMNESI: ..."),
]


def _store():
    return ClinicalDataStore(RECORDS)


def test_summary_excludes_free_text_note():
    summary = _store().get_summary("PT-0001")
    assert summary is not None
    # least privilege: the PatientSummary model has no `note` field at all
    assert not hasattr(summary, "note")
    assert summary.diagnosis == "Ipertensione arteriosa essenziale"


def test_summary_missing_id_returns_none():
    assert _store().get_summary("PT-9999") is None


def test_aggregate_counts_and_caps_top_n():
    counts = _store().aggregate_diagnoses(top_n=1)
    assert len(counts) == 1
    # most common diagnosis is hypertension (2 of 3 records)
    assert counts[0].diagnosis == "Ipertensione arteriosa essenziale"
    assert counts[0].count == 2
