# Feature catalogue

## Multi-agent orchestration

An LLM-driven supervisor breaks a user goal into concrete tool calls and loops
until it has enough evidence to answer.

- **Location:** [`open_notebook/graphs/agent.py`](../../open_notebook/graphs/agent.py)
- **Agents:** orchestrator, research, education, presentation, report, podcast,
  fact-checker, control, persona, action
  ([`open_notebook/agents/definitions.py`](../../open_notebook/agents/definitions.py))
- **Tools:** list/search sources, read source content, list/create notes,
  timestamp, web search, fetch web page
  ([`open_notebook/agents/tools.py`](../../open_notebook/agents/tools.py))
- **API:** `POST /api/agents/run` → background `run_agent` command

## Verification & hallucination control

Every generated claim can be labelled `verified`, `external`, `inferred` or
`unverified`, with contradiction and hallucination checks on top.

- **Location:** [`open_notebook/graphs/control.py`](../../open_notebook/graphs/control.py)

## Source-cited research reports

Turn a question into evidence gathering (internal knowledge base + best-effort
web search), a synthesized draft, and a fact-checked claim list.

- **Location:** [`open_notebook/graphs/research.py`](../../open_notebook/graphs/research.py)
- **API:** `POST /api/research`

## Study material generation

Paste any source and get a study plan, an explanation, a quiz and flashcards.

- **Location:** [`open_notebook/graphs/education.py`](../../open_notebook/graphs/education.py)
- **API:** `POST /api/education/material`

## Expert personas

Re-interpret material from a chosen expert perspective.

- **Location:** [`open_notebook/engine/persona.py`](../../open_notebook/engine/persona.py)

## Live sync

Connect external sources (Google Drive today) and diff remote state into the
knowledge base, deduped by content hash.

- **Location:** [`open_notebook/connectors/sync.py`](../../open_notebook/connectors/sync.py)
- **API:** `GET /api/integrations`

## Human-approved actions

Every external action (email, Jira) is gated behind an approval record and only
executes when `approved`.

- **Location:** [`open_notebook/connectors/action.py`](../../open_notebook/connectors/action.py)
- **API:** `POST /api/approvals`, `POST /api/approvals/{id}/approve`

## Workflows & scheduler

Define a sequence of registered tool steps, run it on demand or on an
hourly/daily/weekly schedule.

- **Location:** [`open_notebook/engine/workflow.py`](../../open_notebook/engine/workflow.py),
  [`open_notebook/engine/scheduler.py`](../../open_notebook/engine/scheduler.py)
- **API:** `GET/POST /api/workflows`, `POST /api/workflows/{id}/run`

## Activity stream

A merged stream of recent agent runs and approvals.

- **API:** `GET /api/activity`

## Multi-user foundation

A `user` table and users API ready for permission work.

- **API:** [`api/routers/users.py`](../../api/routers/users.py)

## Redesigned UI

Modern, minimalist, premium look with a non-technical navigation and a Home
dashboard.

- **Tokens:** [`frontend/src/app/globals.css`](../../frontend/src/app/globals.css)
- **Navigation:** [`frontend/src/components/layout/AppSidebar.tsx`](../../frontend/src/components/layout/AppSidebar.tsx)
