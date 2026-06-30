"""The policy layer: every tool argument is validated here before execution.

This is the heart of the governance story. An agent cannot ask for more than
the server is willing to give: limits are capped, identifiers must match a
strict pattern, and anything out of policy is rejected with a clear error
*before* any data is touched.
"""

from __future__ import annotations

import re

MAX_SEARCH_LIMIT = 10
MAX_AGGREGATE_TOP_N = 20

# Patients are addressable only by pseudonymous IDs like "PT-0042".
# Free-text identifiers (names, fiscal codes) are rejected by construction.
PSEUDO_ID_PATTERN = re.compile(r"^PT-\d{4}$")


class PolicyViolation(ValueError):
    """Raised when a tool call violates an access policy."""


def enforce_search_limit(limit: int) -> int:
    if not isinstance(limit, int) or limit < 1:
        raise PolicyViolation("limit must be a positive integer")
    if limit > MAX_SEARCH_LIMIT:
        raise PolicyViolation(f"limit must be <= {MAX_SEARCH_LIMIT}")
    return limit


def enforce_top_n(top_n: int) -> int:
    if not isinstance(top_n, int) or top_n < 1:
        raise PolicyViolation("top_n must be a positive integer")
    if top_n > MAX_AGGREGATE_TOP_N:
        raise PolicyViolation(f"top_n must be <= {MAX_AGGREGATE_TOP_N}")
    return top_n


def enforce_pseudo_id(pseudo_id: str) -> str:
    candidate = (pseudo_id or "").strip().upper()
    if not PSEUDO_ID_PATTERN.match(candidate):
        raise PolicyViolation(
            "patient_pseudo_id must be a pseudonymous ID like 'PT-0042' "
            "(real identifiers are not accepted)"
        )
    return candidate
