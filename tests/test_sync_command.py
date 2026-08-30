"""Tests for the sync background command (Road_Map Step 14)."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from commands.sync_commands import RunSyncInput, run_sync_command


class TestRunSyncCommand:
    @pytest.mark.asyncio
    async def test_unknown_provider_raises_value_error(self):
        fake_connection = SimpleNamespace(provider="unknown")
        with patch(
            "commands.sync_commands.SyncConnection.get",
            new=AsyncMock(return_value=fake_connection),
        ):
            with pytest.raises(ValueError, match="Unknown sync provider"):
                await run_sync_command(RunSyncInput(connection_id="c:1"))
