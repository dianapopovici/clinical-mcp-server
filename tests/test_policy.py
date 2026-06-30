"""Tests for the policy layer — the governance guardrails."""

import pytest

from clinical_mcp import policy


def test_search_limit_accepts_valid():
    assert policy.enforce_search_limit(5) == 5
    assert policy.enforce_search_limit(policy.MAX_SEARCH_LIMIT) == policy.MAX_SEARCH_LIMIT


@pytest.mark.parametrize("bad", [0, -1, policy.MAX_SEARCH_LIMIT + 1, 999])
def test_search_limit_rejects_out_of_range(bad):
    with pytest.raises(policy.PolicyViolation):
        policy.enforce_search_limit(bad)


def test_top_n_accepts_valid():
    assert policy.enforce_top_n(10) == 10
    assert policy.enforce_top_n(policy.MAX_AGGREGATE_TOP_N) == policy.MAX_AGGREGATE_TOP_N


@pytest.mark.parametrize("bad", [0, -5, policy.MAX_AGGREGATE_TOP_N + 1])
def test_top_n_rejects_out_of_range(bad):
    with pytest.raises(policy.PolicyViolation):
        policy.enforce_top_n(bad)


def test_pseudo_id_normalizes_and_accepts():
    assert policy.enforce_pseudo_id("pt-0042") == "PT-0042"
    assert policy.enforce_pseudo_id("  PT-0001 ") == "PT-0001"


@pytest.mark.parametrize(
    "bad",
    ["Mario Rossi", "RSSMRA80A01H501U", "PT-42", "patient-0042", "", "DROP TABLE"],
)
def test_pseudo_id_rejects_free_text(bad):
    with pytest.raises(policy.PolicyViolation):
        policy.enforce_pseudo_id(bad)
