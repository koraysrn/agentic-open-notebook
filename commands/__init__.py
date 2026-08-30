"""Surreal-commands integration for Open Notebook"""

# The worker starts via `surreal-commands-worker --import-modules commands`,
# so this package is imported before the worker connects to SurrealDB. Inject
# the internal DB hosts into no_proxy first so the DB websocket is never
# tunnelled through a configured HTTP proxy (issue #1160).
from open_notebook.utils.proxy import ensure_internal_no_proxy

ensure_internal_no_proxy()

# Import every command module so the @command decorators register their
# handlers with the worker registry. The agent/workflow/sync/action commands
# were previously missing from this list, so the worker failed with
# "Command not found" even though the API accepted submissions.
from . import (  # noqa: F401
    action_commands,
    agent_commands,
    sync_commands,
    workflow_commands,
)
from .embedding_commands import (
    embed_insight_command,
    embed_note_command,
    embed_source_command,
    rebuild_embeddings_command,
)
from .podcast_commands import generate_podcast_command
from .source_commands import process_source_command

__all__ = [
    # Command modules (imported for side-effect registration)
    "action_commands",
    "agent_commands",
    "sync_commands",
    "workflow_commands",
    # Embedding commands
    "embed_note_command",
    "embed_insight_command",
    "embed_source_command",
    "rebuild_embeddings_command",
    # Other commands
    "generate_podcast_command",
    "process_source_command",
]
