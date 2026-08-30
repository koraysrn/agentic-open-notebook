"""Submit one agent run and poll it to completion (post-fix verification)."""

import asyncio
import json
import sys
import time

import httpx

BASE = "http://localhost:5055/api"


async def main() -> int:
    timeout = httpx.Timeout(60.0, connect=20.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        submit = await client.post(
            f"{BASE}/agents/run",
            json={"goal": "List my notebooks and summarize what they contain"},
        )
        submit.raise_for_status()
        command_id = submit.json()["command_id"]
        print(f"Submitted agent run: {command_id}")

        deadline = time.time() + 420
        while time.time() < deadline:
            response = await client.get(f"{BASE}/commands/jobs/{command_id}")
            response.raise_for_status()
            body = response.json()
            status = body.get("status")
            print(f"  status={status}")
            if status in ("completed", "failed"):
                print(json.dumps(body, indent=2, default=str))
                return 0 if status == "completed" else 1
            await asyncio.sleep(5)
        print("Timed out waiting for agent run.")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
