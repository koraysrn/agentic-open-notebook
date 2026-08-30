# Agentic Open Notebook — Project Documentation

This folder holds the documentation for the work built **on top of** the
[Open Notebook](https://github.com/lfnovo/open-notebook) research assistant.

Open Notebook remains the foundation (3-tier architecture, multi-provider AI,
SurrealDB, podcast engine). Agentic Open Notebook adds a **multi-agent
orchestration layer** and a set of engines that turn the assistant into a
personal knowledge operating system.

## Documents

| Document | Purpose |
|---|---|
| [architecture.md](architecture.md) | System architecture, the engine layer, and the data model additions |
| [what-we-built.md](what-we-built.md) | The complete delta from upstream Open Notebook |
| [features.md](features.md) | Feature catalogue: what each engine does and where it lives |
| [roadmap.md](roadmap.md) | The phased plan, its status, and next steps |

## Upstream credit

This project is a derivative of **Open Notebook** by
[Luis Novo](https://github.com/lfnovo), licensed under the MIT License
([`LICENSE`](../../LICENSE)). The original project:

- Repository: <https://github.com/lfnovo/open-notebook>
- Website: <https://www.open-notebook.ai>

We keep the upstream code, tests, documentation and CI and add our engines as
an additive layer — the original MIT notice is preserved in full.
