<div align="center">

# Clinical MCP Server

**Un server Model Context Protocol governato e tracciato che dà a qualsiasi agente AI un accesso sicuro e in sola lettura a una knowledge base clinica.**
Strumenti a privilegio minimo · validazione tramite policy · audit trail append-only.

[![Python](https://img.shields.io/badge/Python-3.11+-1f2937?logo=python&logoColor=white)](https://www.python.org/)
[![MCP](https://img.shields.io/badge/Protocol-MCP-7c3aed)](https://modelcontextprotocol.io/)
[![FastMCP](https://img.shields.io/badge/SDK-FastMCP-111827)](https://github.com/modelcontextprotocol/python-sdk)
[![License](https://img.shields.io/badge/License-MIT-6b7280)](LICENSE)

**[English](README.md) · Italiano**

</div>

---

> **Perché esiste.** Collegare un agente AI ai dati aziendali è facile. Collegarlo *in sicurezza* è la parte difficile — ed è la parte per cui le organizzazioni regolamentate pagano davvero. Il rischio non è il modello: è un agente con una botola aperta `execute_query(sql)` sui dati dei pazienti. Questo server è l'opposto: un insieme ristretto di **strumenti nominali, tipizzati, a privilegio minimo**, ogni chiamata **validata da una policy** e scritta in un **log di audit append-only**. L'agente può fare solo ciò che il server espone deliberatamente — niente di più.

> Questa è la **porta d'accesso lato agente** al [Clinical RAG Engine](https://github.com/dianapopovici/clinical-rag-engine). Dove il RAG engine *risponde* a domande in linguaggio naturale, questo server MCP permette a un agente autonomo di decidere *quando* e *come* interrogarlo — sotto vincoli rigidi e tracciabili.

> **Avvertenza sui dati.** Tutte le cartelle cliniche sono **100% sintetiche**, generate con `scripts/generate_synthetic_data.py`. Nessun dato reale di paziente è presente, citato o richiesto.

---

## Cosa può (e non può) fare un agente

L'agente non invia mai SQL grezzo o identificativi in testo libero. Chiama **capacità**, non query.

| Strumento | Input validato | Restituisce | Guardrail |
|---|---|---|---|
| `search_clinical_notes` | `query: str`, `limit: int ≤ 10` | risposta ancorata + citazioni | delega al RAG engine; citazioni limitate |
| `get_patient_summary` | `patient_pseudo_id` che corrisponde a `PT-\d{4}` | età, sesso, diagnosi, terapia | solo pseudo-ID; **mai** la nota testuale |
| `aggregate_diagnoses` | `top_n: int ≤ 20` | conteggi per diagnosi | solo aggregazione, nessun dato a livello di riga |

Ogni chiamata passa per il livello di policy **prima** dell'esecuzione e viene aggiunta al log di audit (`ts / tool / params / row_count`).

---

## Architettura

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
                                                   │  │  • validazione tipizzata    │ │
                                                   │  │  • vincolo pseudo-ID        │ │
                                                   │  │  • audit log append-only    │ │
                                                   │  └────────────┬─────────────┘ │
                                                   └───────────────┼────────────────┘
                                                                   ▼
                                       ┌──────────────────────────────────────────┐
                                       │  Accesso dati in SOLA LETTURA               │
                                       │  • ricerca semantica → Clinical RAG Engine   │
                                       │  • vista strutturata → snapshot JSON locale  │
                                       └──────────────────────────────────────────┘
```

**Principio chiave:** privilegio minimo per costruzione. Tre strumenti ristretti battono uno potente. Non esiste alcuna botola di query generica in tutto il codice.

---

## Stack tecnologico

| Livello | Tecnologia | Note |
|---|---|---|
| Linguaggio | **Python 3.11+** | Type-hinted, pulito con `ruff`. |
| Protocollo | **Model Context Protocol** | SDK Python ufficiale `mcp` (FastMCP). |
| Trasporto | **stdio + HTTP streamable** | stdio per agenti locali, HTTP per remoti. |
| Ricerca semantica | **Clinical RAG Engine** | Raggiunto via HTTP — i servizi restano disaccoppiati. |
| Dati strutturati | **vista JSON locale** | Sola lettura; nessun percorso di scrittura. |
| Validazione | **Pydantic** | Schemi degli strumenti e modelli tipizzati. |
| Governance | **moduli policy + audit** | Strumenti in allow-list, limiti, audit trail. |

---

## Avvio rapido

> Prerequisito: Python 3.11+. Lo strumento di ricerca semantica richiede anche il companion
> [Clinical RAG Engine](https://github.com/dianapopovici/clinical-rag-engine) in esecuzione;
> gli strumenti strutturati funzionano da soli.

```bash
# 1. Clona ed entra nella cartella
git clone https://github.com/dianapopovici/clinical-mcp-server.git
cd clinical-mcp-server

# 2. Ambiente
python -m venv .venv && source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install -e .    # installa il pacchetto clinical_mcp stesso (layout src/)

# 3. Genera la vista dati sintetica in sola lettura
python scripts/generate_synthetic_data.py --records 200

# 4a. Avvio su stdio (per agenti locali come Claude Desktop)
python -m clinical_mcp --transport stdio

# 4b. Oppure su HTTP (per agenti remoti)
python -m clinical_mcp --transport http
```

> **Nota per Windows:** qui non c'è `make` — esegui i comandi sopra direttamente.

---

## Collegarlo a Claude Desktop

Aggiungi questo al file `claude_desktop_config.json` di Claude Desktop (un esempio è in
[`examples/claude_desktop_config.json`](examples/claude_desktop_config.json)):

```json
{
  "mcpServers": {
    "clinical": {
      "command": "python",
      "args": ["-m", "clinical_mcp", "--transport", "stdio"],
      "cwd": "/percorso/assoluto/della/clinical-mcp-server"
    }
  }
}
```

Riavvia Claude Desktop e i tre strumenti clinici diventano disponibili all'agente.

---

## La governance, in concreto

- **Privilegio minimo.** Un agente non può letteralmente richiedere una capacità che il server non espone. Niente `execute_query`, niente dump delle note, niente identificativi reali.
- **Policy prima dell'esecuzione.** I limiti sono massimizzati (`≤ 10`, `≤ 20`); le ricerche paziente devono corrispondere a `PT-\d{4}`; le violazioni sono respinte con un messaggio chiaro e **non viene toccato nulla**.
- **Tracciabilità.** Ogni chiamata aggiunge una riga JSON ad `audit.log` — `ts / tool / params / row_count`. In un contesto regolamentato, quel registro è una funzionalità, non un ripensamento.
- **Disaccoppiamento.** La ricerca semantica è delegata al RAG engine via HTTP. Sostituisci una delle due parti liberamente; il contratto è il protocollo, non un fornitore.

---

## Struttura del progetto

```
clinical-mcp-server/
├── src/clinical_mcp/
│   ├── __main__.py        # CLI: python -m clinical_mcp --transport {stdio,http}
│   ├── server.py          # server FastMCP + i 3 strumenti governati
│   ├── policy.py          # guardrail di validazione (il cuore della governance)
│   ├── audit.py           # audit trail append-only
│   ├── data_access.py     # vista dati locale in sola lettura
│   ├── rag_client.py      # client HTTP per il Clinical RAG Engine
│   ├── config.py          # configurazione 12-factor
│   └── models.py          # modelli Pydantic
├── scripts/
│   └── generate_synthetic_data.py
├── tests/                 # unità deterministiche per policy / audit / dati
├── examples/
│   └── claude_desktop_config.json
├── DECISIONS.md           # perché è costruito così
└── requirements.txt
```

Vedi **[DECISIONS.md](DECISIONS.md)** per la motivazione ingegneristica dietro ogni scelta principale.

---

## Roadmap

- [ ] Trasporto HTTP con scope OAuth per deployment multi-tenant.
- [ ] Rate limiting per strumento + enforcement del budget di token.
- [ ] Audit log a prova di manomissione (firmato).

---

<div align="center">

**Realizzato da [Diana Popovici](https://www.linkedin.com/in/diana-popovici)** — sistemi AI che funzionano davvero in produzione.

</div>
