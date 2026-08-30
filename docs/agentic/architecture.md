# Architecture

Agentic Open Notebook keeps the three-tier foundation of Open Notebook and adds
an **engine layer** on top of it. The rule from day one: *additive, not
destructive* — the core (notebooks, sources, notes, chat, podcast, search)
keeps working, and every new engine plugs into the existing domain and
background-job machinery.

## The three tiers (inherited)

| Tier | Tech | Port | Role |
|---|---|---|---|
| Frontend | Next.js 16 / React 19 | 3000 | UI, i18n (14 locales), design-token system |
| API | FastAPI | 5055 | REST surface, router per feature |
| Database | SurrealDB | 8000 (Docker) | Record store, vector search, migrations |
| Worker | surreal-commands | — | Async jobs: podcast, embedding, source processing, agents, workflows |

Every layer is **async-first**. Long-running work is never run inline in the API
request — it is submitted as a `surreal-commands` job and picked up by the worker.

## The engine layer (what we added)

```mermaid
flowchart TB
  UI[Next.js frontend] --> API[FastAPI /api]

  API --> AG[/agents/run]
  API --> RS[/research]
  API --> ED[/education/material]
  API --> WF[/workflows]
  API --> AP[/approvals]
  API --> IN[/integrations]

  AG -->|submit_command| Q[(surreal-commands queue)]
  WF -->|submit_command| Q
  Q --> W[Background worker]

  subgraph Engines
    SUP[Supervisor graph<br/>plan → execute → decide → finalize]
    CTL[Control layer<br/>claim verification + hallucination check]
    RES[Research graph<br/>gather → synthesize → fact-check]
    EDU[Education engine<br/>plan + quiz + flashcards]
    PER[Persona engine]
    ACT[Action connectors<br/>email / jira]
    SYNC[Live-sync connectors<br/>google drive]
  end

  SUP --> TR[Tool registry]
  RES --> CTL
  W --> SUP
  W --> WF
  TR --> D[(SurrealDB)]

  D --> |migrations 24-31| NEW[(agent_run, approval,<br/>workflow, user,<br/>sync_connection,<br/>persona, learning_progress)]
```

### Agent Engine

- [`open_notebook/agents/`](../../open_notebook/agents) — `Agent` model,
  `AgentRegistry`, and a `ToolRegistry` of thin, domain-safe tools.
- [`open_notebook/graphs/agent.py`](../../open_notebook/graphs/agent.py) — the
  **supervisor graph**. It is a bounded loop
  (`plan → execute → decide → finalize`, `MAX_ITERATIONS = 5`), so an unbounded
  tool loop is structurally impossible. A known tool that fails at runtime is
  recorded as an error entry rather than aborting the run.

### Control layer

[`open_notebook/graphs/control.py`](../../open_notebook/graphs/control.py) emits
structured verification: each claim is labelled `verified`, `external`,
`inferred` or `unverified`, with contradiction and hallucination checks.

### Research

[`open_notebook/graphs/research.py`](../../open_notebook/graphs/research.py)
chains **gather evidence → synthesize draft → fact-check** and is exposed
synchronously through `POST /api/research`.

### Education, Persona, Action, Live-sync, Workflow

- Education ([`open_notebook/graphs/education.py`](../../open_notebook/graphs/education.py))
  produces a study plan, explanation, quiz and flashcards.
- Persona ([`open_notebook/engine/persona.py`](../../open_notebook/engine/persona.py))
  builds an expert-lens prompt for re-interpreting material.
- Action ([`open_notebook/connectors/action.py`](../../open_notebook/connectors/action.py))
  gates every external action behind an **approved** record.
- Live-sync ([`open_notebook/connectors/sync.py`](../../open_notebook/connectors/sync.py))
  diffs remote state and dedupes by content hash.
- Workflow ([`open_notebook/engine/workflow.py`](../../open_notebook/engine/workflow.py),
  [`open_notebook/engine/scheduler.py`](../../open_notebook/engine/scheduler.py))
  validates and runs tool-step definitions on a schedule.

## Data model additions

Migrations 24–31 in
[`open_notebook/database/async_migrate.py`](../../open_notebook/database/async_migrate.py):

| # | Table | Purpose |
|---|---|---|
| 24 | `agent_run` | Supervisor run history |
| 25 | `sync_connection` | Live-sync connection state |
| 26 | `persona` | Saved personas |
| 27 | `learning_progress` | Adaptive-learning state |
| 28 | `approval` | Human approval gate for actions |
| 29 | `workflow` | Workflow definitions |
| 30 | `user` | Multi-user foundation |
| 31 | `workflow.last_run_at` | Scheduler bookkeeping |

## Cross-cutting decisions

- **Provider-agnostic AI** — every LLM call goes through
  [`provision_langchain_model()`](../../open_notebook/ai/provision.py), never a
  hard-coded provider.
- **Tool safety** — tools never touch the DB directly; they wrap the domain
  layer, and workflows can only run registered tool names.
- **Web safety** — outbound web tools use DNS-pinned, SSRF-blocked HTTP targets
  ([`open_notebook/utils/url_validation.py`](../../open_notebook/utils/url_validation.py)).
