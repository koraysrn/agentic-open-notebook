# Extension Points

How each subsystem of the target architecture plugs into the existing Open Notebook codebase. This is the inventory produced by Road_Map Step 1; it is a living map, updated as subsystems land.

## Legend

- **Hook**: where the new code attaches.
- **Mechanism**: the interface used (module, graph, router, migration, command, prompt).
- **Touches core**: whether existing core files are modified.

## Agent Engine (Phase 2)

| Subsystem | Hook | Mechanism | Touches core |
|---|---|---|---|
| Agent abstraction + registry | `open_notebook/agents/` (new) | Python package, Pydantic models | No |
| Tool registry | `open_notebook/agents/tools.py` (new) | LangChain `@tool` wrappers over domain/repo | No |
| Orchestrator (supervisor) | `open_notebook/graphs/agent.py` (new) | LangGraph `StateGraph` | No |
| Agent state | `open_notebook/database/migrations/N.surrealql` | `agent_run` table + SQLite checkpoints | Migration only |
| Agent API | `api/routers/agents.py` + `api/main.py` | FastAPI router | `api/main.py` registration |
| Long-running agent work | `commands/agent_commands.py` | `surreal-commands` job | No |

## Control Layer (Phase 3)

| Subsystem | Hook | Mechanism | Touches core |
|---|---|---|---|
| Evidence / citation verification | `open_notebook/graphs/control.py` + `prompts/control/` | LangGraph + Jinja2 | No |
| Claim taxonomy (`verified` / `external` / `inferred` / `unverified`) | response models in `api/models.py` | Pydantic | Yes (additive field) |
| Confidence scoring | response models | Pydantic field | Yes (additive) |

## Research + Live Sync (Phase 4)

| Subsystem | Hook | Mechanism | Touches core |
|---|---|---|---|
| Web research tool | `open_notebook/agents/tools.py` + `validate_url()` | Tool + SSRF guard | No |
| Research workflow | `open_notebook/graphs/research.py` | LangGraph | No |
| Sync connection storage | `sync_connection` table | Migration + domain model | Migration only |
| Credential storage for connectors | `open_notebook/utils/encryption.py` | Existing encryption | No |
| Sync jobs | `commands/sync_commands.py` | `surreal-commands` job | No |

## Education + Persona (Phase 5)

| Subsystem | Hook | Mechanism | Touches core |
|---|---|---|---|
| Persona definitions | `persona` table + `prompts/persona/` | Migration + Jinja2 | Migration only |
| Education generation | `open_notebook/graphs/education.py` + `prompts/education/` | LangGraph + Pydantic output | No |
| Learning progress | `learning_progress` table | Migration + domain model | Migration only |

## Action + Workflow (Phase 6)

| Subsystem | Hook | Mechanism | Touches core |
|---|---|---|---|
| Approval queue | `approval` table + `api/routers/approvals.py` | Migration + router | Migration only |
| Action execution | `commands/action_commands.py` | `surreal-commands` job, gated on approval | No |
| Workflow definitions | `workflow` table | Migration + domain model | Migration only |
| Workflow execution | `open_notebook/graphs/workflow.py` | LangGraph over registered agents/tools | No |

## UI (all phases)

| Subsystem | Hook | Mechanism | Touches core |
|---|---|---|---|
| New pages | `frontend/src/app/(dashboard)/<section>/` | Next.js App Router routes | No |
| Types | `frontend/src/lib/types/api.ts` | TypeScript interfaces | Yes (additive) |
| API clients | `frontend/src/lib/api/<section>.ts` | axios via single `apiClient` | No |
| Data hooks | `frontend/src/lib/hooks/use-<section>.ts` | TanStack Query | No |
| Translations | `frontend/src/lib/locales/*/` | i18n keys in all locales | Yes (additive) |

## Non-negotiable rules when using these hooks

1. Every DB query, graph call, and AI call is `await`-ed (async-first).
2. Every LLM call goes through `provision_langchain_model()` — never a provider client.
3. Every new table ships as `N.surrealql` + `N_down.surrealql` and is registered in `AsyncMigrationManager`.
4. Long-running work is a `surreal-commands` job, never inline in a request.
5. New UI strings exist in every locale under `frontend/src/lib/locales/`.
