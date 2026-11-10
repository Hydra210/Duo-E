from __future__ import annotations

from pathlib import Path

import aiosqlite


class Database:
    def __init__(self, path: Path):
        self.path = path

    async def initialize(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        async with aiosqlite.connect(self.path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS backups (
                    backup_id TEXT PRIMARY KEY,
                    guild_id INTEGER NOT NULL,
                    guild_name TEXT NOT NULL,
                    object_key TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    created_by INTEGER NOT NULL,
                    size_bytes INTEGER NOT NULL
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS audit_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER NOT NULL,
                    actor_id INTEGER NOT NULL,
                    action TEXT NOT NULL,
                    details TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS scheduled_tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER NOT NULL,
                    task_type TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    run_at TEXT NOT NULL,
                    enabled INTEGER NOT NULL DEFAULT 1
                )
            """)
            await db.commit()

    async def add_backup(self, row: tuple) -> None:
        async with aiosqlite.connect(self.path) as db:
            await db.execute(
                "INSERT INTO backups VALUES (?, ?, ?, ?, ?, ?, ?)", row
            )
            await db.commit()

    async def list_backups(self, guild_id: int) -> list[tuple]:
        async with aiosqlite.connect(self.path) as db:
            cursor = await db.execute(
                """SELECT backup_id, guild_name, created_at, created_by, size_bytes
                   FROM backups WHERE guild_id = ? ORDER BY created_at DESC""",
                (guild_id,),
            )
            return await cursor.fetchall()

    async def get_backup(self, guild_id: int, backup_id: str) -> tuple | None:
        async with aiosqlite.connect(self.path) as db:
            cursor = await db.execute(
                """SELECT backup_id, object_key, created_at, size_bytes
                   FROM backups WHERE guild_id = ? AND backup_id = ?""",
                (guild_id, backup_id),
            )
            return await cursor.fetchone()

    async def add_audit_event(
        self, guild_id: int, actor_id: int, action: str, details: str, created_at: str
    ) -> None:
        async with aiosqlite.connect(self.path) as db:
            await db.execute(
                """INSERT INTO audit_events
                   (guild_id, actor_id, action, details, created_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (guild_id, actor_id, action, details, created_at),
            )
            await db.commit()
