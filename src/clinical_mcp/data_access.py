"""Read-only access to the local clinical data view.

The structured tools (patient summary, diagnosis aggregation) read from a
local JSON snapshot. Access is read-only by construction: there is no write,
update, or delete path anywhere in this module.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from clinical_mcp.models import ClinicalRecord, DiagnosisCount, PatientSummary


class ClinicalDataStore:
    def __init__(self, records: list[ClinicalRecord]) -> None:
        self._by_id: dict[str, ClinicalRecord] = {r.pseudo_id: r for r in records}

    @classmethod
    def from_file(cls, path: str) -> "ClinicalDataStore":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        records = [ClinicalRecord(**row) for row in data]
        return cls(records)

    def get_summary(self, pseudo_id: str) -> PatientSummary | None:
        record = self._by_id.get(pseudo_id)
        if record is None:
            return None
        # Note the deliberate omission of `note`: least privilege.
        return PatientSummary(
            pseudo_id=record.pseudo_id,
            age=record.age,
            sex=record.sex,
            diagnosis=record.diagnosis,
            therapy=record.therapy,
        )

    def aggregate_diagnoses(self, top_n: int) -> list[DiagnosisCount]:
        counts = Counter(r.diagnosis for r in self._by_id.values())
        return [
            DiagnosisCount(diagnosis=name, count=n)
            for name, n in counts.most_common(top_n)
        ]

    def __len__(self) -> int:
        return len(self._by_id)
