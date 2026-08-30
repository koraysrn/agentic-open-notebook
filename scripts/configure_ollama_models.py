"""Configure local Ollama chat + embedding models and set them as defaults.

Idempotent: existing model rows are reused, so this can be run repeatedly.
Run with:  uv run python scripts/configure_ollama_models.py
"""

import asyncio
import sys

from dotenv import load_dotenv

load_dotenv()

from open_notebook.ai.models import Model
from open_notebook.database.repository import repo_query, repo_upsert

CHAT_MODEL = ("qwen2.5", "ollama", "language")
EMBED_MODEL = ("nomic-embed-text", "ollama", "embedding")


async def _existing_model_id(name: str, provider: str, model_type: str) -> str | None:
    result = await repo_query(
        "SELECT * FROM model WHERE name = $name AND provider = $provider "
        "AND type = $type LIMIT 1",
        {"name": name, "provider": provider, "type": model_type},
    )
    if result:
        row = result[0] if isinstance(result, list) else result
        return row.get("id")
    return None


async def ensure_model(name: str, provider: str, model_type: str) -> str:
    model_id = await _existing_model_id(name, provider, model_type)
    if model_id:
        print(f"Reusing existing {model_type} model '{name}': {model_id}")
        return model_id

    model = Model(name=name, provider=provider, type=model_type)
    await model.save()
    print(f"Created {model_type} model '{name}' ({provider}): {model.id}")
    return model.id or ""


async def main() -> int:
    chat_id = await ensure_model(*CHAT_MODEL)
    embed_id = await ensure_model(*EMBED_MODEL)

    await repo_upsert(
        "open_notebook",
        "open_notebook:default_models",
        {
            "default_chat_model": chat_id,
            "default_embedding_model": embed_id,
        },
    )

    print("Default models updated:")
    print(f"  default_chat_model      = {chat_id}")
    print(f"  default_embedding_model = {embed_id}")
    print("  (transformation/tools/large_context fall back to the chat model)")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
