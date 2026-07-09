"""Main orchestrator coordinating LLM, optimization and agents.

Clean, pragmatic implementation.
"""

from typing import Any

import structlog

from ..llm.router import LLMRouter
from ..optimization.qubo_solver import QUBOSolver
from ..core.models import Task, OptimizationResult

logger = structlog.get_logger()


class Orchestrator:
    """High-level coordinator for normalOS."""

    def __init__(self):
        self.llm = LLMRouter()
        self.qubo = QUBOSolver()
        self.tasks: list[Task] = []

    async def add_task(self, description: str, priority: int = 5, **kwargs) -> Task:
        task = Task(description=description, priority=priority, **kwargs)
        self.tasks.append(task)
        logger.info("task_added", task_id=task.id, description=description)
        return task

    def optimize_schedule(self) -> OptimizationResult:
        if not self.tasks:
            return OptimizationResult(task_order=[], energy=0.0, solver_time_ms=0.0)
        result = self.qubo.optimize_task_order(self.tasks)
        logger.info("schedule_optimized", num_tasks=len(self.tasks), energy=result.energy)
        return result

    async def run_task_with_llm(self, task: Task, prompt: str) -> dict[str, Any]:
        """Execute a task by calling an LLM."""
        task.status = "running"
        try:
            response = await self.llm.generate(prompt)
            task.status = "completed"
            return {
                "task_id": task.id,
                "status": "completed",
                "llm_response": response.content,
                "provider": response.provider,
            }
        except Exception as e:
            task.status = "failed"
            logger.error("task_failed", task_id=task.id, error=str(e))
            raise

    async def close(self):
        await self.llm.close()