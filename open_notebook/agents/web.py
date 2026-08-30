"""Web research tools for the Agent Engine (Road_Map Step 11).

Both tools go through ``prepare_pinned_http_target()`` so outbound requests
to user-supplied hostnames are DNS-pinned and never resolve to blocked
addresses (cloud metadata endpoints, link-local, etc.).
"""

import os
from typing import Any

import httpx

from open_notebook.exceptions import ConfigurationError, NetworkError
from open_notebook.utils.url_validation import prepare_pinned_http_target

_PROVIDER = "web_research"


async def fetch_web_page(url: str) -> dict[str, Any]:
    """Fetch a web page's status and leading text, SSRF-pinned."""
    target = await prepare_pinned_http_target(url, _PROVIDER)
    try:
        async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
            response = await client.get(
                target.url,
                headers=target.headers,
                extensions=target.extensions,
            )
            response.raise_for_status()
    except httpx.HTTPError as e:
        raise NetworkError(f"Failed to fetch {url}: {e}") from e

    return {
        "url": url,
        "status_code": response.status_code,
        "content": response.text[:2000],
    }


async def web_search(query: str, limit: int = 5) -> list[dict[str, Any]]:
    """Search the web through a configured search endpoint.

    The endpoint is configured via ``OPEN_NOTEBOOK_SEARCH_API_URL`` and must
    accept POSTed JSON ``{"query": ..., "limit": ...}`` and return a body with
    a ``results`` list. Keeping the contract provider-agnostic means any
    search backend (self-hosted or commercial) can be swapped in.
    """
    endpoint = os.getenv("OPEN_NOTEBOOK_SEARCH_API_URL", "").strip()
    if not endpoint:
        raise ConfigurationError(
            "Web search is not configured. Set OPEN_NOTEBOOK_SEARCH_API_URL."
        )

    target = await prepare_pinned_http_target(endpoint, _PROVIDER)
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(
                target.url,
                headers=target.headers,
                extensions=target.extensions,
                json={"query": query, "limit": limit},
            )
            response.raise_for_status()
            data = response.json()
    except httpx.HTTPError as e:
        raise NetworkError(f"Web search failed: {e}") from e

    results = data.get("results", []) if isinstance(data, dict) else []
    return list(results)[:limit]
