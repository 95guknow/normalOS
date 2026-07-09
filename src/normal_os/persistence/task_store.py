"""Simple async SQLite persistence layer using SQLModel + aiosqlite.

Clean and pragmatic for small-to-medium projects.
"""

import aiosqlite
from sqlmodel import SQLModel, Field, select
from typing import Optional, AsyncGenerator
from datetime import datetime

from ..core.models import Task as TaskModel


class TaskRecord(SQLModel, table=True):
    """Database model for tasks."""
    __tablename__ = "tasks"

    id: str = Field(primary_key=True)
    description: str
    priority: int = 5
    estimated_duration_minutes: int = 30
    status: str = "pending"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    metadata_json: str = "{}"


class TaskStore:
    """Async task persistence."""

    def __init__(self, db_path: str = "normalos.db"):
        self.db_path = db_path

    async def init_db(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    description TEXT NOT NULL,
                    priority INTEGER DEFAULT 5,
                    estimated_duration_minutes INTEGER DEFAULT 30,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    metadata_json TEXT DEFAULT '{}'
                )
            """)
            await db.commit()

    async def add_task(self, task: TaskModel) -> TaskModel:
        record = TaskRecord(
            id=task.id,
            description=task.description,
            priority=task.priority,
            estimated_duration_minutes=task.estimated_duration_minutes,
            status=task.status,
            created_at=task.created_at,
            metadata_json=str(task.metadata),
        )
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT INTO tasks (id, description, priority, estimated_duration_minutes, status, created_at, metadata_json) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (record.id, record.description, record.priority, record.estimated_duration_minutes, record.status, record.created_at, record.metadata_json),
            )
            await db.commit()
        return task

    async def list_tasks(self, status: Optional[str] = None, limit: int = 50) -> list[TaskModel]:
        query = "SELECT * FROM tasks ORDER BY created_at DESC LIMIT ?"
        params = [limit]
        if status:
            query = "SELECT * FROM tasks WHERE status = ? ORDER BY created_at DESC LIMIT ?"
            params = [status, limit]

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(query, params) as cursor:
                rows = await cursor.fetchall()

        tasks = []
        for row in rows:
            tasks.append(TaskModel(
                id=row["id"],
                description=row["description"],
                priority=row["priority"],
                estimated_duration_minutes=row["estimated_duration_minutes"],
                status=row["status"],
                created_at=row["created_at"],
                metadata=eval(row["metadata_json"]) if row["metadata_json"] else {},
            ))
        return tasks

    async def update_status(self, task_id: str, status: str):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE tasks SET status = ?, completed_at = ? WHERE id = ?",
                (status, datetime.utcnow() if status in ("completed", "failed") else None, task_id),
            )
            await db.commit()