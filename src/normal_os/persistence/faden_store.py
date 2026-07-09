import aiosqlite
import json
from typing import Any, Dict, List, Optional


class FadenStore:
    """Explicit persistent thread/faden memory store (extracted + normalized from Horkrux faden_store)."""

    def __init__(self, db_path: str = "./data/normalos.db"):
        self.db_path = db_path

    async def _ensure_table(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS faden (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    thread_id TEXT,
                    key TEXT,
                    value TEXT,
                    layer INTEGER DEFAULT 0,
                    ts TEXT
                )
            """)
            await db.commit()

    async def save_faden(self, thread_id: str, key: str, value: Any, layer: int = 0):
        await self._ensure_table()
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO faden (thread_id, key, value, layer, ts)
                VALUES (?, ?, ?, ?, datetime('now'))
            """, (thread_id, key, json.dumps(value), layer))
            await db.commit()

    async def get_faden(self, thread_id: str, key: str | None = None) -> List[Dict]:
        await self._ensure_table()
        async with aiosqlite.connect(self.db_path) as db:
            if key:
                cursor = await db.execute(
                    "SELECT * FROM faden WHERE thread_id = ? AND key = ? ORDER BY ts DESC",
                    (thread_id, key),
                )
            else:
                cursor = await db.execute(
                    "SELECT * FROM faden WHERE thread_id = ? ORDER BY ts DESC",
                    (thread_id,),
                )
            rows = await cursor.fetchall()
            return [
                {
                    "id": r[0],
                    "thread_id": r[1],
                    "key": r[2],
                    "value": json.loads(r[3]),
                    "layer": r[4],
                    "ts": r[5],
                }
                for r in rows
            ]