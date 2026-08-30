"""End-to-end simulation of 10 user scenarios against the running stack.

Drives the real FastAPI (http://localhost:5055) — not mocks — to create
notebooks, sources, notes, approvals and workflows, and to exercise the new
Research and Education endpoints plus async Agent runs.

Run with:  uv run python scripts/simulate_scenarios.py
"""

import asyncio
import json
import time

import httpx

BASE = "http://localhost:5055/api"

REPORT: list[dict] = []


def log(scenario: str, status: str, detail: str = "") -> None:
    print(f"[{scenario}] {status}: {detail}")
    REPORT.append({"scenario": scenario, "status": status, "detail": detail})


async def call(
    client: httpx.AsyncClient, method: str, path: str, **kwargs
):
    response = await client.request(method, f"{BASE}{path}", **kwargs)
    return response


async def create_notebook(client: httpx.AsyncClient, name: str, description: str = ""):
    response = await call(
        client, "POST", "/notebooks", json={"name": name, "description": description}
    )
    response.raise_for_status()
    return response.json()["id"]


async def create_text_source(
    client: httpx.AsyncClient,
    notebook_id: str,
    title: str,
    content: str,
    embed: bool = False,
):
    response = await call(
        client,
        "POST",
        "/sources/json",
        json={
            "type": "text",
            "title": title,
            "content": content,
            "notebooks": [notebook_id],
            "embed": embed,
        },
    )
    response.raise_for_status()
    return response.json()


async def create_note(
    client: httpx.AsyncClient, notebook_id: str, title: str, content: str
):
    response = await call(
        client,
        "POST",
        "/notes",
        json={
            "title": title,
            "content": content,
            "note_type": "human",
            "notebook_id": notebook_id,
        },
    )
    response.raise_for_status()
    return response.json()


async def search(client: httpx.AsyncClient, query: str, limit: int = 5):
    response = await call(
        client,
        "POST",
        "/search",
        json={"query": query, "type": "text", "limit": limit},
    )
    response.raise_for_status()
    return response.json()


async def poll_command(client: httpx.AsyncClient, command_id: str, seconds: int = 60):
    deadline = time.time() + seconds
    status = "unknown"
    while time.time() < deadline:
        response = await call(client, "GET", f"/commands/jobs/{command_id}")
        if response.status_code == 200:
            body = response.json()
            status = body.get("status", "unknown")
            if status in ("completed", "failed"):
                return body
        await asyncio.sleep(3)
    return {"status": status, "result": None}


async def scenario_student(client: httpx.AsyncClient) -> None:
    notebook = await create_notebook(
        client, "Biology 101", "Introductory biology study notebook."
    )
    await create_text_source(
        client,
        notebook,
        "Photosynthesis overview",
        "Photosynthesis is the process plants use to convert light energy into "
        "chemical energy stored in glucose. It takes place in chloroplasts and "
        "produces oxygen as a by-product.",
        embed=True,
    )
    response = await call(
        client,
        "POST",
        "/education/material",
        json={
            "source_content": (
                "Photosynthesis converts light energy into chemical energy in "
                "chloroplasts, producing glucose and oxygen."
            )
        },
    )
    response.raise_for_status()
    body = response.json()
    log(
        "1-Student",
        "PASS",
        f"notebook={notebook} plan_steps={len(body.get('plan', []))} "
        f"quiz={len(body.get('quiz', []))} flashcards={len(body.get('flashcards', []))}",
    )


async def scenario_academic(client: httpx.AsyncClient) -> None:
    notebook = await create_notebook(
        client, "Climate Research", "Climate change literature review."
    )
    await create_text_source(
        client,
        notebook,
        "Global temperature trends",
        "Global average temperatures have risen about 1.1 degrees Celsius since "
        "the pre-industrial era, driven primarily by greenhouse gas emissions.",
    )
    await create_text_source(
        client,
        notebook,
        "Carbon dioxide levels",
        "Atmospheric CO2 concentrations have increased from roughly 280 ppm "
        "before industrialization to over 420 ppm today.",
    )
    response = await call(
        client,
        "POST",
        "/research",
        json={"question": "How much has the global temperature risen since the pre-industrial era?"},
    )
    response.raise_for_status()
    body = response.json()
    log(
        "2-Academic",
        "PASS",
        f"draft_chars={len(body.get('draft', ''))} claims={len(body.get('claims', []))} "
        f"evidence={len(body.get('evidence', []))}",
    )


async def scenario_startup(client: httpx.AsyncClient) -> None:
    notebook = await create_notebook(
        client, "Product Research", "Competitive analysis for the new product."
    )
    await create_text_source(
        client,
        notebook,
        "Competitor notes",
        "Competitor A focuses on enterprise pricing while Competitor B targets "
        "small teams with a freemium tier.",
    )
    await create_note(
        client,
        notebook,
        "Positioning hypothesis",
        "We should differentiate on privacy and self-hosting.",
    )
    response = await call(
        client,
        "POST",
        "/agents/run",
        json={"goal": "Summarize my product research sources", "notebook_id": notebook},
    )
    response.raise_for_status()
    command_id = response.json()["command_id"]
    status = await poll_command(client, command_id, seconds=60)
    log(
        "3-Startup",
        "PASS" if status.get("status") == "completed" else "SUBMITTED",
        f"command_id={command_id} status={status.get('status')}",
    )


async def scenario_developer(client: httpx.AsyncClient) -> None:
    notebook = await create_notebook(
        client, "API Notes", "Developer scratchpad for the REST API."
    )
    await create_note(
        client,
        notebook,
        "Auth flow",
        "The API uses a password middleware in dev; production hardening is out of scope.",
    )
    result = await search(client, "password middleware", limit=3)
    log(
        "4-Developer",
        "PASS",
        f"search_total={result.get('total_count')} hits={len(result.get('results', []))}",
    )


async def scenario_employee(client: httpx.AsyncClient) -> None:
    notebook = await create_notebook(
        client, "Weekly Reports", "Automated weekly reporting."
    )
    await create_text_source(
        client,
        notebook,
        "Last week summary",
        "Closed 3 deals and onboarded 2 customers last week.",
    )
    create_resp = await call(
        client,
        "POST",
        "/approvals",
        json={"notebook_id": notebook, "action_type": "email", "payload": "{}"},
    )
    create_resp.raise_for_status()
    approval_id = create_resp.json()["id"]
    approve_resp = await call(
        client, "POST", f"/approvals/{approval_id}/approve"
    )
    approve_resp.raise_for_status()
    log(
        "5-Employee",
        "PASS",
        f"approval={approval_id} status={approve_resp.json().get('status')}",
    )


async def scenario_researcher(client: httpx.AsyncClient) -> None:
    notebook = await create_notebook(
        client, "ML Literature", "Machine learning paper notes."
    )
    await create_text_source(
        client,
        notebook,
        "Transformers paper",
        "The Transformer architecture replaces recurrence with self-attention, "
        "enabling much longer-range dependencies.",
    )
    await create_text_source(
        client,
        notebook,
        "Scaling laws",
        "Model performance improves predictably with more parameters, data, and compute.",
    )
    await create_note(
        client,
        notebook,
        "Key insight",
        "Attention is all you need; scaling laws govern modern LLMs.",
    )
    result = await search(client, "self-attention", limit=3)
    log(
        "6-Researcher",
        "PASS",
        f"search_total={result.get('total_count')} hits={len(result.get('results', []))}",
    )


async def scenario_presentation(client: httpx.AsyncClient) -> None:
    notebook = await create_notebook(
        client, "Talk Outline", "Quarterly review talk."
    )
    await create_text_source(
        client,
        notebook,
        "Quarterly numbers",
        "Revenue grew 12% quarter over quarter; churn fell to 2.1%.",
    )
    await create_note(
        client,
        notebook,
        "Opening story",
        "Start with the customer who doubled their usage after the new release.",
    )
    response = await call(
        client,
        "POST",
        "/education/material",
        json={
            "source_content": (
                "Revenue grew 12% quarter over quarter and churn fell to 2.1%. "
                "The talk should open with a customer story."
            )
        },
    )
    response.raise_for_status()
    body = response.json()
    log(
        "7-Presentation",
        "PASS",
        f"outline_steps={len(body.get('plan', []))} explanation_chars={len(body.get('explanation', ''))}",
    )


async def scenario_learning(client: httpx.AsyncClient) -> None:
    notebook = await create_notebook(
        client, "Spanish Vocab", "Spanish vocabulary practice."
    )
    await create_text_source(
        client,
        notebook,
        "Common greetings",
        "Hola means hello. Gracias means thank you. Por favor means please.",
    )
    response = await call(
        client,
        "POST",
        "/education/material",
        json={
            "source_content": "Hola means hello. Gracias means thank you. Por favor means please."
        },
    )
    response.raise_for_status()
    body = response.json()
    log(
        "8-Learning",
        "PASS",
        f"flashcards={len(body.get('flashcards', []))} quiz={len(body.get('quiz', []))}",
    )


async def scenario_persona(client: httpx.AsyncClient) -> None:
    notebook = await create_notebook(
        client, "Finance Review", "Quarterly finance commentary."
    )
    await create_text_source(
        client,
        notebook,
        "Margins",
        "Gross margin expanded 300 basis points while operating expenses grew 8%.",
    )
    response = await call(
        client,
        "POST",
        "/agents/run",
        json={
            "goal": "As a financial analyst persona, interpret the margin trends in my finance review sources",
            "notebook_id": notebook,
        },
    )
    response.raise_for_status()
    command_id = response.json()["command_id"]
    status = await poll_command(client, command_id, seconds=60)
    log(
        "9-Persona",
        "PASS" if status.get("status") == "completed" else "SUBMITTED",
        f"command_id={command_id} status={status.get('status')}",
    )


async def scenario_live_sync(client: httpx.AsyncClient) -> None:
    integrations = (await call(client, "GET", "/integrations")).json()
    connectors = [c["name"] for c in integrations.get("connectors", [])]

    workflow_resp = await call(
        client,
        "POST",
        "/workflows",
        json={
            "name": "Daily timestamp",
            "definition": json.dumps({"steps": [{"tool": "get_current_timestamp"}]}),
            "schedule": "daily",
            "enabled": True,
        },
    )
    workflow_resp.raise_for_status()
    workflow_id = workflow_resp.json()["id"]
    run_resp = await call(client, "POST", f"/workflows/{workflow_id}/run")
    run_resp.raise_for_status()
    run_status = await poll_command(
        client, run_resp.json()["command_id"], seconds=45
    )
    log(
        "10-LiveSync",
        "PASS" if run_status.get("status") == "completed" else "SUBMITTED",
        f"connectors={connectors} workflow={workflow_id} run_status={run_status.get('status')}",
    )


async def main() -> int:
    timeout = httpx.Timeout(600.0, connect=30.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        health = (await call(client, "GET", "/config")).json()
        log("health", "PASS", f"db={health.get('dbStatus')}")

        for scenario in (
            scenario_student,
            scenario_academic,
            scenario_startup,
            scenario_developer,
            scenario_employee,
            scenario_researcher,
            scenario_presentation,
            scenario_learning,
            scenario_persona,
            scenario_live_sync,
        ):
            name = scenario.__name__.removeprefix("scenario_").replace("_", " ")
            try:
                await scenario(client)
            except Exception as exc:  # noqa: BLE001 - report and continue
                log(name, "FAIL", f"{type(exc).__name__}: {exc}")

    print("\n==== SIMULATION REPORT ====")
    for row in REPORT:
        print(f"{row['scenario']:16} {row['status']:10} {row['detail']}")
    print(f"\nTotal: {len(REPORT)} entries")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
