# ADR-008: Agent Engine lives inside the Open Notebook core

- **Status**: Accepted
- **Date**: 2026-08
- **Related**: PROJE MİMARİSİ.md, Road_Map.md, [ADR-004](ADR-004-background-workers.md)

## Context

The project is evolving Open Notebook into a Personal Knowledge Operating System. The first new subsystem is the Agent Engine (Road_Map Phase 2). Before any agent code lands, four structural questions need an answer: where the agent layer lives relative to the existing core, how agents coordinate, how agent tools access the knowledge base, and how long-running agent state persists.

## Decision

1. **Embedded and additive.** The agent layer lives in a new `open_notebook/agents/` package inside the existing backend. It is additive: it consumes the existing domain models, graphs, and API, and never rewrites them.
2. **Supervisor orchestration.** A single Orchestrator graph decomposes a user goal into agent/tool calls. It extends the existing plan → execute → answer pattern in `open_notebook/graphs/ask.py` instead of introducing a new orchestration framework.
3. **Tool registry.** Agents act only through registered tools that wrap domain/repository functions. Tools never touch the database directly, and they stay provider-agnostic via JSON + Pydantic output parsing.
4. **State persistence.** Multi-step agent runs persist through LangGraph checkpoints (the same SQLite mechanism chat uses) plus an `agent_run` table for observable status and resumability.

## Alternatives considered

- **Separate microservice driving Open Notebook over REST/MCP.** Cleaner isolation, but it adds deployment complexity and duplicates auth/state; rejected for the first vertical slice.
- **LangGraph prebuilt supervisor/agents.** Attractive, but the prebuilt API churns across versions and hides the loop limits we need; rejected in favor of an explicit, small supervisor graph.
- **In-memory agent state only.** Rejected: API restarts would lose in-flight research and violate the async-first principle.

## Consequences

- **Easier:** a new agent is just a new module registered in a registry; existing RAG, search, and notes remain untouched.
- **Harder:** the supervisor loop must be bounded (max iterations + token budget) and tested, because unbounded tool loops are a real failure mode.
- **Watch:** LangGraph version upgrades (pinned `<2`) and the sync-node / `asyncio.new_event_loop()` pattern documented in `open_notebook/AGENTS.md`.
