"""Tool registry: the only way agents touch the knowledge base (ADR-008).

Every tool is a thin async wrapper around a domain/repository function. Tools
return JSON-serializable dicts/lists and never issue raw SurrealQL themselves,
so the supervisor can pass results to any provider without provider-specific
glue. Typed domain exceptions (``NotFoundError``, ``InvalidInputError``) are
allowed to propagate to the caller.
"""

from collections.abc import Awaitable, Callable
from datetime import datetime
from typing import Any, Literal

from open_notebook.agents.web import fetch_web_page, web_search
from open_notebook.domain.notebook import Note, Notebook, Source, text_search

Tool = Callable[..., Awaitable[Any]]


def _normalize_record_id(prefix: str, value: str) -> str:
    """Ensure an id carries its table prefix (``table:id``)."""
    value = value.strip()
    return value if value.startswith(f"{prefix}:") else f"{prefix}:{value}"


async def get_current_timestamp() -> str:
    """Return the current timestamp as ``YYYYMMDDHHmmss``."""
    return datetime.now().strftime("%Y%m%d%H%M%S")


async def list_notebooks() -> list[dict[str, Any]]:
    """List notebooks with their id, name, description, and archived flag."""
    notebooks = await Notebook.get_all(order_by="created desc")
    return [
        {
            "id": notebook.id,
            "name": notebook.name,
            "description": notebook.description,
            "archived": bool(notebook.archived),
        }
        for notebook in notebooks
    ]


async def search_sources(query: str, limit: int = 10) -> list[dict[str, Any]]:
    """Search sources and notes by keyword using full-text search."""
    raw = await text_search(query, limit, source=True, note=True)
    results: list[dict[str, Any]] = []
    for item in raw or []:
        if not isinstance(item, dict):
            continue
        results.append(
            {
                "id": item.get("id"),
                "title": item.get("title"),
                "content": (item.get("full_text") or item.get("content") or "")[:500],
                "score": item.get("score"),
            }
        )
    return results


async def get_source_content(source_id: str) -> dict[str, Any]:
    """Fetch a source's id, title, and full text."""
    source = await Source.get(_normalize_record_id("source", source_id))
    return await source.get_context(context_size="long")


async def list_notes(notebook_id: str | None = None) -> list[dict[str, Any]]:
    """List notes, optionally scoped to a notebook."""
    if notebook_id:
        notebook = await Notebook.get(_normalize_record_id("notebook", notebook_id))
        notes = await notebook.get_notes(include_content=True)
    else:
        notes = await Note.get_all(order_by="updated desc")

    return [
        {
            "id": note.id,
            "title": note.title,
            "note_type": note.note_type,
            "content": (note.content or "")[:500],
        }
        for note in notes
    ]


async def create_note(
    notebook_id: str,
    content: str,
    title: str | None = None,
    note_type: Literal["human", "ai"] = "ai",
) -> dict[str, Any]:
    """Create a note and link it to a notebook."""
    note = Note(title=title, content=content, note_type=note_type)
    await note.save()
    await note.add_to_notebook(_normalize_record_id("notebook", notebook_id))
    return {"id": note.id, "title": note.title, "note_type": note.note_type}


class ToolRegistry:
    """A name-keyed collection of callable agent tools."""

    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, name: str, tool: Tool) -> None:
        if name in self._tools:
            raise ValueError(f"Tool already registered: {name}")
        self._tools[name] = tool

    def unregister(self, name: str) -> None:
        self._tools.pop(name, None)

    def get(self, name: str) -> Tool | None:
        return self._tools.get(name)

    def list_tools(self) -> list[str]:
        return list(self._tools.keys())

    def clear(self) -> None:
        self._tools.clear()

    def __len__(self) -> int:
        return len(self._tools)

    def __contains__(self, name: object) -> bool:
        return name in self._tools


DEFAULT_TOOLS: dict[str, Tool] = {
    "get_current_timestamp": get_current_timestamp,
    "list_notebooks": list_notebooks,
    "search_sources": search_sources,
    "get_source_content": get_source_content,
    "list_notes": list_notes,
    "create_note": create_note,
    "web_search": web_search,
    "fetch_web_page": fetch_web_page,
}


def build_default_tool_registry() -> ToolRegistry:
    """Build a registry pre-populated with the default tool set."""
    registry = ToolRegistry()
    for name, tool in DEFAULT_TOOLS.items():
        registry.register(name, tool)
    return registry


# The process-wide registry used by the orchestration layer.
tool_registry = build_default_tool_registry()
