import aiosqlite
import json
from typing import Any, Dict, List, Optional


class ContextStore:
    """Explicit persistent context / thread memory store."""

    def __init__(self, db_path: str = "./data/normalos.db"):
        self.db_path = db_path

    async def set(self, task_id: str, key: str, value: Any):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR REPLACE INTO task_context (task_id, key, value)
                VALUES (?, ?, ?)
            """, (task_id, key, json.dumps(value)))
            await db.commit()

    async def get(self, task_id: str, key: str) -> Optional[Any]:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT value FROM task_context WHERE task_id = ? AND key = ?",
                (task_id, key),
            )
            row = await cursor.fetchone()
            return json.loads(row[0]) if row else None

    async def get_all(self, task_id: str) -> Dict[str, Any]:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT key, value FROM task_context WHERE task_id = ?",
                (task_id,),
            )
            rows = await cursor.fetchall()
            return {row[0]: json.loads(row[1]) for row in rows}