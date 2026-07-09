import asyncio
from typing import Any, Callable, Dict, List

import structlog

from normal_os.core.models import Task
from normal_os.executor.task_executor import TaskExecutor

logger = structlog.get_logger(__name__)


class WorkerPool:
    """Explicit worker pool for concurrent task execution with resource control."""

    def __init__(self, max_workers: int = 8):
        self.max_workers = max_workers
        self.executor = TaskExecutor(max_concurrent=max_workers)
        self._workers: List[asyncio.Task] = []

    async def start(self):
        logger.info("worker_pool_started", max_workers=self.max_workers)

    async def submit_and_run(
        self,
        task_type: str,
        payload: dict[str, Any],
        handler: Callable,
        priority: int = 5,
    ) -> str:
        task_id = await self.executor.submit(task_type, payload, priority=priority)
        task = await self.executor.store.get(task_id)
        if task:
            asyncio.create_task(self.executor.run_task(task, handler))
        return task_id

    async def shutdown(self):
        logger.info("worker_pool_shutdown")