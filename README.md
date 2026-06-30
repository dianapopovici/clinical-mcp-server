<div align="center">

# Clinical MCP Server

**A governed, audited Model Context Protocol server that gives any AI agent secure, read-only access to a clinical knowledge base.**
Least-privilege tools · policy validation · append-only audit trail.

[![Python](https://img.shields.io/badge/Python-3.11+-1f2937?logo=python&logoColor=white)](https://www.python.org/)
[![MCP](https://img.shields.io/badge/Protocol-MCP-7c3aed)](https://modelcontextprotocol.io/)
[![FastMCP](https://img.shields.io/badge/SDK-FastMCP-111827)](https://github.com/modelcontextprotocol/python-sdk)
[![License](https://img.shields.io/badge/License-MIT-6b7280)](LICENSE)

**English · [Italiano](README.it.md)**

</div>

---

> **Why this exists.** Connecting an AI agent to enterprise data is easy. Connecting it *safely* is the hard part — and the part regulated organizations actually pay for. The risk is not the model; it is an agent with an open `execute_query(sql)` hatch over patient data. This server is the opposite: a small set of **named, typed, least-privilege tools**, every call **validated against a policy** and written to an **append-only audit log**. The agent can only do what the server deliberately exposes — nothing more.

> This is the **agent-facing front door** to the [Clinical RAG Engine](https://github.com/dianapopovici/clinical-rag-engine). Where the RAG engine *answers* natural-language questions, this MCP server lets an autonomous agent decide *when* and *how* to query it — under strict, auditable constraints.

> **Data disclaimer.** All clinical records are **100% synthetic**, generated with `scripts/generate_synthetic_data.py`. No real patient data is present, referenced, or required.

---

## What an agent can (and cannot) do

The agent never sends raw SQL or free text identifiers. It calls **capabilities**, not queries.

| Tool | Validated input | Returns | Guardrail |
|---|---|---|---|
| `search_clinical_notes` | `query: str`, `limit: int ≤ 10` | grounded answer + cited snippets | delegates to the RAG engine; citations capped |
| `get_patient_summary` | `patient_pseudo_id` matching `PT-\d{4}` | age, sex, diagnosis, therapy | pseudo-IDs only; **never** returns the free-text note |
| `aggregate_diagnoses` | `top_n: int ≤ 20` | counts per diagnosis | aggregation only, no row-level export |

Every call passes through the policy layer **before** execution and is appended to the audit log (`ts / tool / params / row_count`).

---

## Architecture

```
   ┌──────────────┐      MCP (stdio / HTTP)      ┌──────────────────────────────┐
   │   AI Agent    │  ───────────────────────▶   │      Clinical MCP Server       │
   │ (Claude       │                              │                                │
   │  Desktop,     │  ◀───── tool results ─────   │  ┌──────────────────────────┐ │
   │  Cursor, ...) │                              │  │  TOOL REGISTRY (allow-list)│ │
   └──────────────┘                               │  │  • search_clinical_notes  │ │
                                                   │  │  • get_patient_summary    │ │
                                                   │  │  • aggregate_diagnoses    │ │
                                                   │  └────────────┬─────────────┘ │
                                                   │               ▼                │
                                                   │  ┌──────────────────────────┐ │
                                                   │  │  POLICY + AUDIT LAYER      │ │
                                                   │  │  • typed param validation  │ │
                                                   │  │  • pseudo-ID enforcement    │ │
                                                   │  │  • append-only audit log    │ │
                                                   │  └────────────┬─────────────┘ │
                                                   └───────────────┼────────────────┘
                                                                   ▼
                                       ┌──────────────────────────────────────────┐
                                       │  READ-ONLY data access                     │
                                       │  • semantic search → Clinical RAG Engine    │
                                       │  • structured view → local JSON snapshot    │
                                       └──────────────────────────────────────────┘
```

**Key principle:** least privilege by construction. Three narrow tools beat one powerful one. There is no generic query escape hatch anywhere in the codebase.

---

## Tech Stack

| Layer | Technology | Notes |
|---|---|---|
| Language | **Python 3.11+** | Type-hinted, `ruff`-clean. |
| Protocol | **Model Context Protocol** | Official `mcp` Python SDK (FastMCP). |
| Transport | **stdio + streamable HTTP** | stdio for local agents, HTTP for remote. |
| Semantic search | **Clinical RAG Engine** | Reached over HTTP — services stay decoupled. |
| Structured data | **local JSON view** | Read-only; no write/update/delete path. |
| Validation | **Pydantic** | Typed tool schemas and models. |
| Governance | **policy + audit modules** | Allow-listed tools, capped limits, audit trail. |

---

## Quickstart

> Prerequisite: Python 3.11+. The semantic-search tool also needs the companion
> [Clinical RAG Engine](https://github.com/dianapopovici/clinical-rag-engine) running;
> the structured tools work standalone.

```bash
# 1. Clone and enter
git clone https://github.com/dianapopovici/clinical-mcp-server.git
cd clinical-mcp-server

# 2. Environment
python -m venv .venv && source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install -e .    # install the clinical_mcp package itself (src/ layout)

# 3. Generate the synthetic read-only data view
python scripts/generate_synthetic_data.py --records 200

# 4a. Run over stdio (for local agents like Claude Desktop)
python -m clinical_mcp --transport stdio

# 4b. Or run over HTTP (for remote agents)
python -m clinical_mcp --transport http
```

> **Windows note:** there is no `make` here — run the commands above directly.

---

## Connect it to Claude Desktop

Add this to your Claude Desktop `claude_desktop_config.json` (an example lives in
[`examples/claude_desktop_config.json`](examples/claude_desktop_config.json)):

```json
{
  "mcpServers": {
    "clinical": {
      "command": "python",
      "args": ["-m", "clinical_mcp", "--transport", "stdio"],
      "cwd": "/absolute/path/to/clinical-mcp-server"
    }
  }
}
```

Restart Claude Desktop and the three clinical tools become available to the agent.

---

## Governance, concretely

- **Least privilege.** An agent literally cannot request a capability the server does not expose. No `execute_query`, no raw note dumps, no real identifiers.
- **Policy before execution.** Limits are capped (`≤ 10`, `≤ 20`); patient lookups must match `PT-\d{4}`; violations are rejected with a clear message and **nothing is touched**.
- **Auditability.** Every call appends one JSON line to `audit.log` — `ts / tool / params / row_count`. In a regulated setting, that trail is a feature, not an afterthought.
- **Decoupling.** Semantic search is delegated to the RAG engine over HTTP. Swap either side freely; the contract is the protocol, not a vendor.

---

## Project Structure

```
clinical-mcp-server/
├── src/clinical_mcp/
│   ├── __main__.py        # CLI: python -m clinical_mcp --transport {stdio,http}
│   ├── server.py          # FastMCP server + the 3 governed tools
│   ├── policy.py          # validation guardrails (the governance core)
│   ├── audit.py           # append-only audit trail
│   ├── data_access.py     # read-only local data view
│   ├── rag_client.py      # HTTP client for the Clinical RAG Engine
│   ├── config.py          # 12-factor settings
│   └── models.py          # Pydantic models
├── scripts/
│   └── generate_synthetic_data.py
├── tests/                 # deterministic units for policy / audit / data
├── examples/
│   └── claude_desktop_config.json
├── DECISIONS.md           # why it is built this way
└── requirements.txt
```

See **[DECISIONS.md](DECISIONS.md)** for the engineering rationale behind every major choice.

---

## Roadmap

- [ ] OAuth-scoped HTTP transport for multi-tenant deployments.
- [ ] Per-tool rate limiting + token-budget enforcement.
- [ ] Tamper-evident (signed) audit log.

---

<div align="center">

**Built by [Diana Popovici](https://www.linkedin.com/in/diana-popovici)** — AI systems that actually work in production.

</div>
