"""Tests for migrations 25-29 (Live Sync, Persona, Learning, Approval, Workflow)."""

from pathlib import Path

from open_notebook.database.async_migrate import AsyncMigrationManager


class TestMigrations25To29:
    MIGRATIONS_DIR = Path("open_notebook/database/migrations")

    def test_migration_files_exist(self):
        for number in (25, 26, 27, 28, 29):
            assert (self.MIGRATIONS_DIR / f"{number}.surrealql").is_file()
            assert (self.MIGRATIONS_DIR / f"{number}_down.surrealql").is_file()

    def test_manager_registers_all_migrations(self):
        manager = AsyncMigrationManager()
        assert len(manager.up_migrations) >= 29
        assert len(manager.up_migrations) == len(manager.down_migrations)

    def test_latest_tables_registered(self):
        manager = AsyncMigrationManager()
        sql_25 = manager.up_migrations[24].sql
        sql_26 = manager.up_migrations[25].sql
        sql_27 = manager.up_migrations[26].sql
        sql_28 = manager.up_migrations[27].sql
        sql_29 = manager.up_migrations[28].sql
        assert "sync_connection" in sql_25
        assert "persona" in sql_26
        assert "learning_progress" in sql_27
        assert "approval" in sql_28
        assert "workflow" in sql_29
