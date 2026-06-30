# Design Decisions

This document records *why* the server is built the way it is. The code shows
what; this shows the reasoning a reviewer actually wants to see.

## 1. Capabilities, not queries

**Decision:** expose three narrow, named tools instead of a generic
`run_query` / `execute_sql` tool.

**Why:** the moment an agent can issue arbitrary queries, the security model
collapses — you are one prompt injection away from a full data dump. Modelling
each allowed operation as a deliberate, typed capability makes the attack
surface finite and reviewable. An agent cannot ask for something that does not
exist.

## 2. Policy layer separate from tool logic

**Decision:** all validation lives in `policy.py`, isolated from the tool
functions and from data access.

**Why:** governance you can read in one file is governance you can audit and
test. The policy is enforced *before* any data is touched, and the unit tests
target it directly — so a regression in a guardrail fails CI immediately.

## 3. Least-privilege summaries

**Decision:** `get_patient_summary` returns structured fields only and omits
the free-text clinical note entirely — the `PatientSummary` model has no `note`
field.

**Why:** the safest data is data the tool cannot return. Dropping the note at
the *type* level (not just filtering it at runtime) means it can never leak,
even by accident.

## 4. Pseudonymous identifiers only

**Decision:** patient lookups must match `PT-\d{4}`; names and fiscal codes are
rejected.

**Why:** it bakes a privacy boundary into the interface. The server never
accepts a real-world identifier, so an agent cannot be tricked into correlating
records to real people.

## 5. Audit as a first-class output

**Decision:** every call appends one JSON line to an append-only log.

**Why:** in healthcare and finance, "who accessed what, when" is a compliance
requirement, not a nice-to-have. Making the audit trail a core feature — not a
bolt-on — is the difference between a demo and something deployable.

## 6. Delegate semantic search over HTTP

**Decision:** the MCP server does not reimplement retrieval; it calls the
Clinical RAG Engine over its HTTP API.

**Why:** separation of concerns. The MCP server owns *governance*; the RAG
engine owns *retrieval*. Either can evolve or be replaced independently, and the
boundary is an explicit contract rather than a tangle of shared code.

## 7. Stable SDK over bleeding edge

**Decision:** target the stable `mcp` v1 SDK (`mcp.server.fastmcp.FastMCP`)
rather than the v2 pre-release.

**Why:** a portfolio project should clone and run for a reviewer today. Building
on an alpha SDK that is explicitly "not for production" would trade reliability
for novelty — the wrong trade for something meant to demonstrate judgment.
