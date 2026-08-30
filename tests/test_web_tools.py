"""Tests for the web research tools (Road_Map Step 11)."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from open_notebook.agents.web import fetch_web_page, web_search
from open_notebook.exceptions import ConfigurationError


class _FakeResponse:
    status_code = 200
    text = "hello world"

    def raise_for_status(self):
        pass


class _FakeClient:
    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    async def get(self, *args, **kwargs):
        return _FakeResponse()


class TestWebSearch:
    @pytest.mark.asyncio
    async def test_raises_when_not_configured(self, monkeypatch):
        monkeypatch.delenv("OPEN_NOTEBOOK_SEARCH_API_URL", raising=False)
        with pytest.raises(ConfigurationError):
            await web_search("query")


class TestFetchWebPage:
    @pytest.mark.asyncio
    async def test_fetches_with_pinned_target(self):
        target = SimpleNamespace(
            url="https://93.184.216.34/", headers={}, extensions={}
        )
        with (
            patch(
                "open_notebook.agents.web.prepare_pinned_http_target",
                new=AsyncMock(return_value=target),
            ),
            patch(
                "open_notebook.agents.web.httpx.AsyncClient",
                return_value=_FakeClient(),
            ),
        ):
            result = await fetch_web_page("https://example.com")

        assert result["status_code"] == 200
        assert result["content"] == "hello world"

    @pytest.mark.asyncio
    async def test_propagates_ssrf_guard_error(self):
        with patch(
            "open_notebook.agents.web.prepare_pinned_http_target",
            new=AsyncMock(side_effect=ValueError("blocked address")),
        ):
            with pytest.raises(ValueError, match="blocked address"):
                await fetch_web_page("http://169.254.169.254/")
