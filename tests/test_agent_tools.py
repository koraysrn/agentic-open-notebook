"""Tests for the agent tool registry and its tools (Road_Map Step 4).

Tools are tested against mocked domain functions — they must stay thin
wrappers, so the tests assert the boundary (what the tool calls and what it
returns), not the database.
"""

import re
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from open_notebook.agents.tools import (
    DEFAULT_TOOLS,
    ToolRegistry,
    create_note,
    get_current_timestamp,
    get_source_content,
    list_notebooks,
    list_notes,
    search_sources,
    tool_registry,
)


class TestToolRegistry:
    def test_fresh_registry_is_empty(self):
        assert len(ToolRegistry()) == 0

    def test_register_and_get(self):
        registry = ToolRegistry()
        async def dummy():
            return 1

        registry.register("dummy", dummy)
        assert registry.get("dummy") is dummy
        assert "dummy" in registry

    def test_duplicate_registration_raises(self):
        registry = ToolRegistry()
        async def dummy():
            return 1

        registry.register("dummy", dummy)
        with pytest.raises(ValueError, match="already registered"):
            registry.register("dummy", dummy)

    def test_unregister_removes_tool(self):
        registry = ToolRegistry()
        async def dummy():
            return 1

        registry.register("dummy", dummy)
        registry.unregister("dummy")
        assert registry.get("dummy") is None

    def test_list_tools(self):
        registry = ToolRegistry()
        async def dummy():
            return 1

        registry.register("dummy", dummy)
        assert registry.list_tools() == ["dummy"]

    def test_clear_empties_registry(self):
        registry = ToolRegistry()
        async def dummy():
            return 1

        registry.register("dummy", dummy)
        registry.clear()
        assert len(registry) == 0


class TestDefaultToolRegistry:
    def test_contains_expected_tools(self):
        expected = {
            "get_current_timestamp",
            "list_notebooks",
            "search_sources",
            "get_source_content",
            "list_notes",
            "create_note",
            "web_search",
            "fetch_web_page",
        }
        assert set(tool_registry.list_tools()) == expected

    def test_default_tools_mapping_matches_registry(self):
        assert set(DEFAULT_TOOLS.keys()) == set(tool_registry.list_tools())


class TestTimestampTool:
    @pytest.mark.asyncio
    async def test_returns_14_digit_timestamp(self):
        value = await get_current_timestamp()
        assert re.fullmatch(r"\d{14}", value)


class TestKnowledgeTools:
    @pytest.mark.asyncio
    async def test_list_notebooks(self):
        fake = SimpleNamespace(
            id="notebook:1", name="Proje", description="d", archived=False
        )
        with patch(
            "open_notebook.agents.tools.Notebook.get_all",
            new=AsyncMock(return_value=[fake]),
        ):
            result = await list_notebooks()
        assert result == [
            {
                "id": "notebook:1",
                "name": "Proje",
                "description": "d",
                "archived": False,
            }
        ]

    @pytest.mark.asyncio
    async def test_search_sources_normalizes_results(self):
        raw = [
            {"id": "source:1", "title": "A", "full_text": "body"},
            {"id": "note:2", "title": "B", "content": "note body"},
        ]
        with patch(
            "open_notebook.agents.tools.text_search",
            new=AsyncMock(return_value=raw),
        ):
            result = await search_sources("query", limit=5)
        assert result[0] == {
            "id": "source:1",
            "title": "A",
            "content": "body",
            "score": None,
        }
        assert result[1]["content"] == "note body"

    @pytest.mark.asyncio
    async def test_get_source_content_normalizes_id(self):
        fake_source = SimpleNamespace(
            get_context=AsyncMock(
                return_value={"id": "source:1", "title": "A", "full_text": "x"}
            )
        )
        with patch(
            "open_notebook.agents.tools.Source.get",
            new=AsyncMock(return_value=fake_source),
        ) as mock_get:
            result = await get_source_content("1")
        mock_get.assert_awaited_once_with("source:1")
        assert result["full_text"] == "x"

    @pytest.mark.asyncio
    async def test_list_notes_scoped_to_notebook(self):
        fake_note = SimpleNamespace(
            id="note:1", title="n", note_type="ai", content="content"
        )
        fake_notebook = SimpleNamespace(
            get_notes=AsyncMock(return_value=[fake_note])
        )
        with patch(
            "open_notebook.agents.tools.Notebook.get",
            new=AsyncMock(return_value=fake_notebook),
        ):
            result = await list_notes(notebook_id="1")
        assert result[0]["id"] == "note:1"
        assert result[0]["content"] == "content"

    @pytest.mark.asyncio
    async def test_list_notes_unscoped(self):
        fake_note = SimpleNamespace(
            id="note:1", title="n", note_type="human", content=None
        )
        with patch(
            "open_notebook.agents.tools.Note.get_all",
            new=AsyncMock(return_value=[fake_note]),
        ):
            result = await list_notes()
        assert result[0]["content"] == ""

    @pytest.mark.asyncio
    async def test_create_note_links_to_notebook(self):
        with (
            patch(
                "open_notebook.agents.tools.Note.save",
                new=AsyncMock(return_value=None),
            ),
            patch(
                "open_notebook.agents.tools.Note.add_to_notebook",
                new=AsyncMock(return_value=None),
            ) as mock_link,
        ):
            result = await create_note(
                notebook_id="1", title="t", content="body", note_type="ai"
            )
        mock_link.assert_awaited_once_with("notebook:1")
        assert result["title"] == "t"
        assert result["note_type"] == "ai"
