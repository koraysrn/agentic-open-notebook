"""Tests for agent run persistence (Road_Map Step 6)."""

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from open_notebook.domain.agent_run import AgentRun


class TestAgentRunModel:
    def test_defaults_and_table_name(self):
        run = AgentRun()
        assert run.table_name == "agent_run"
        assert run.id is None
        assert run.agent is None
        assert run.status is None
        assert run.goal is None
        assert run.state_json is None
        assert run.final_answer is None
        assert run.notebook is None

    @pytest.mark.asyncio
    async def test_save_creates_record_and_updates_id(self):
        run = AgentRun(agent="research", goal="g", status="running")
        created_row = {
            "id": "agent_run:1",
            "agent": "research",
            "goal": "g",
            "status": "running",
            "created": "2026-08-29 10:00:00",
            "updated": "2026-08-29 10:00:00",
        }
        with patch(
            "open_notebook.domain.base.repo_create",
            new=AsyncMock(return_value=[created_row]),
        ):
            await run.save()

        assert run.id == "agent_run:1"
        assert run.status == "running"


class TestMigration24Registration:
    MIGRATIONS_DIR = Path("open_notebook/database/migrations")

    def test_migration_files_exist(self):
        assert (self.MIGRATIONS_DIR / "24.surrealql").is_file()
        assert (self.MIGRATIONS_DIR / "24_down.surrealql").is_file()

    def test_manager_registers_migration_24(self):
        from open_notebook.database.async_migrate import AsyncMigrationManager

        manager = AsyncMigrationManager()
        assert len(manager.up_migrations) >= 24
        assert len(manager.up_migrations) == len(manager.down_migrations)
        assert "agent_run" in manager.up_migrations[23].sql
