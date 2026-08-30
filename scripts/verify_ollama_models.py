"""Verify the configured Ollama chat + embedding models actually respond."""

import asyncio
import sys

from dotenv import load_dotenv

load_dotenv()

from open_notebook.ai.models import model_manager
from open_notebook.ai.provision import provision_langchain_model


async def main() -> int:
    embed = await model_manager.get_embedding_model()
    if embed is None:
        print("FAIL: no embedding model configured")
        return 1
    print(f"Embedding model: {getattr(embed, 'model_name', embed)}")
    vectors = await embed.aembed(["Open Notebook embedding test"])
    print(f"Embedding dim: {len(vectors[0])}")

    chat = await model_manager.get_default_model("chat")
    if chat is None:
        print("FAIL: no chat model configured")
        return 1
    print(f"Chat model: {getattr(chat, 'model_name', chat)}")

    langchain_model = await provision_langchain_model(
        "Reply with exactly: OK", None, "chat", max_tokens=100
    )
    reply = await langchain_model.ainvoke("Reply with exactly: OK")
    print(f"Chat reply content: {getattr(reply, 'content', reply)}")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
