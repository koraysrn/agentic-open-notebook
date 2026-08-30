# Roadmap

This is the English summary of the phased plan recorded in
[`Road_Map.md`](../../Road_Map.md) (originally derived from
[`PROJE MİMARİSİ.md`](../../PROJE MİMARİSİ.md)).

## Phase 1 — Foundation · ✅ done

Environment bootstrap, decision record (ADR-008), MIT license confirmation.

## Phase 2 — Agent Engine · ✅ done

Agent abstraction, registry, tool registry, supervisor graph, `agent_run`
persistence, agents API + UI.

## Phase 3 — Control Layer · ✅ done

Claim/verification models, contradiction + hallucination checks, 3 graphs.

## Phase 4 — Research + Live Sync · ✅ done

Research graph (gather → synthesize → fact-check), web tools, sync connections
and Google Drive connector.

## Phase 5 — Education + Persona · ✅ done

Education material graph, persona engine, adaptive learning, migrations 26/27.

## Phase 6 — Action + Workflow · ✅ done

Email/Jira connectors, approvals, workflow engine + scheduler, migrations
28/29/31.

## Phase 7 — Unified Product · ✅ in progress

Multi-user foundation (migration 30 + users API) is in place. The UI redesign
is complete.

## Next steps

1. **External web research** — set `OPEN_NOTEBOOK_SEARCH_API_URL` (e.g.
   SearXNG) to enable the `web_search` tool end-to-end.
2. **Sync/action credentials** — configure Google Drive token, SMTP, and Jira
   credentials to exercise live connectors.
3. **Permissions** — layer user ownership/roles on top of the `user` table.
4. **Stronger orchestration** — larger local or cloud LLMs improve multi-step
   tool-chaining quality (the pipeline is model-agnostic).

## Working rules (kept throughout)

1. Vertical slices — each step is independently runnable and tested.
2. Test-first — backend `uv run pytest tests/`, frontend `npm run test`.
3. Migration discipline — every new table ships with `N.surrealql`,
   `N_down.surrealql`, and a manual registration in
   [`async_migrate.py`](../../open_notebook/database/async_migrate.py).
4. Decision records — structural decisions become an ADR/PDR.
5. Async-first — long work is a `surreal-commands` job, never inline.
6. Provider-agnostic — every LLM call via
   [`provision_langchain_model()`](../../open_notebook/ai/provision.py).
