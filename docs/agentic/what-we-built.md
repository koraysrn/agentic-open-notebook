# What we built on top of Open Notebook

This document is the complete delta: everything added or changed relative to
upstream [Open Notebook](https://github.com/lfnovo/open-notebook).

## 1. Agent Engine

New package [`open_notebook/agents/`](../../open_notebook/agents):

- `Agent` Pydantic model — `name`, `description`, `capabilities`, `tools`,
  `system_prompt`.
- `AgentRegistry` — registration, lookup, capability-based selection.
- `definitions.py` — 10 default agents: orchestrator, research, education,
  presentation, report, podcast, fact-checker, control, persona, action.
- `tools.py` — `ToolRegistry` + 8 tools: `list_notebooks`, `search_sources`,
  `get_source_content`, `list_notes`, `create_note`, `get_current_timestamp`,
  `web_search`, `fetch_web_page`.
- `web.py` — web tools with SSRF-pinned outbound requests.

Supervisor graph in [`open_notebook/graphs/agent.py`](../../open_notebook/graphs/agent.py):
bounded `plan → execute → decide → finalize` loop with resilient per-tool
execution. Exposed through `POST /api/agents/run` + background command
`run_agent`.

## 2. Control layer

[`open_notebook/graphs/control.py`](../../open_notebook/graphs/control.py):

- `Claim` with verification labels: `verified`, `external`, `inferred`,
  `unverified`.
- `Contradiction` and `HallucinationCheck` models.
- Three graphs: verification, contradiction detection, hallucination check.

## 3. Research

[`open_notebook/graphs/research.py`](../../open_notebook/graphs/research.py):
`gather → synthesize → fact_check`, feeding the draft back through the control
layer. Exposed through `POST /api/research`
([`api/routers/research.py`](../../api/routers/research.py)).

## 4. Education + Persona

- [`open_notebook/graphs/education.py`](../../open_notebook/graphs/education.py)
  generates `EducationMaterial` (study plan, explanation, quiz, flashcards).
  Exposed through `POST /api/education/material`
  ([`api/routers/education.py`](../../api/routers/education.py)).
- [`open_notebook/engine/persona.py`](../../open_notebook/engine/persona.py) —
  expert-lens prompt builder.
- [`open_notebook/engine/adaptive.py`](../../open_notebook/engine/adaptive.py) —
  weak-subject selection for adaptive learning.

## 5. Live sync

- [`open_notebook/connectors/sync.py`](../../open_notebook/connectors/sync.py):
  `diff_remote_state`, `dedupe_by_content_hash`, `GoogleDriveConnector`
  (Google Drive API v3).
- `sync_connection` domain + migration 25, `run_sync` background command, and
  `GET /api/integrations`.

## 6. Action + Approvals

- [`open_notebook/connectors/action.py`](../../open_notebook/connectors/action.py):
  `EmailConnector` (SMTP), `JiraConnector` (REST), `execute_approved_action`
  gated on `status == "approved"`.
- `approval` domain + migration 28 and `POST /api/approvals`.

## 7. Workflow + Scheduler

- [`open_notebook/engine/workflow.py`](../../open_notebook/engine/workflow.py):
  `validate_definition` / `run_definition` (registered tools only).
- [`open_notebook/engine/scheduler.py`](../../open_notebook/engine/scheduler.py):
  `is_due` (hourly/daily/weekly) + `tick_scheduler`.
- `workflow` domain + migrations 29/31 and `/api/workflows`.

## 8. Multi-user foundation

`user` domain + migration 30 and [`api/routers/users.py`](../../api/routers/users.py).

## 9. UI/UX redesign

- New design-token system in
  [`frontend/src/app/globals.css`](../../frontend/src/app/globals.css)
  (indigo `#635BFF`, soft shadows, 10–14 px radii).
- New non-technical navigation: Home / Notebooks / Research / Study / Create /
  Workflows / Integrations / Activity / Settings.
- Home dashboard, plus functional Research, Study and Create pages wired to the
  new endpoints.

## 10. Fixes and hardening

- **Worker command registration** — the agent/workflow/sync/action commands were
  not imported by [`commands/__init__.py`](../../commands/__init__.py), so the
  worker failed with `Command not found`. All command modules are now imported.
- **Agent resilience** — a single failing tool no longer aborts a run.
- **Embedding bootstrap** — local Ollama setup script
  ([`scripts/configure_ollama_models.py`](../../scripts/configure_ollama_models.py)).
- **Windows test fixes** and Vitest pinning (see the upstream test suite notes).

## Test coverage

- Backend: 761 tests (`uv run pytest tests/`).
- Frontend: 140 tests (`npm run test`), `npm run lint`, `npm run build`.
