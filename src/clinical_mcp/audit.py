"""Append-only audit trail.

Every tool invocation is written as one JSON line: who/when/what/how-much.
In a regulated environment, knowing exactly what an agent touched is not
optional — so the audit log is a first-class output, not an afterthought.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from clinical_mcp.config import settings


def record(
    tool: str,
    params: dict[str, Any],
    row_count: int,
    *,
    path: str | None = None,
) -> dict[str, Any]:
    """Append one audit entry and return it (handy for tests/inspection)."""
    entry: dict[str, Any] = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "tool": tool,
        "params": params,
        "row_count": row_count,
    }
    log_path = Path(path or settings.audit_log_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return entry
