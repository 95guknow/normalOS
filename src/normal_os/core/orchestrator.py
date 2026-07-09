"""
Main orchestrator coordinating LLM, optimization, agents and now connectors.

Expanded autonomously to integrate all external connectors
and the GrokPCBridge as first-class citizens.
"""

from typing import Any, Dict, Optional

import structlog

from ..llm.router import LLMRouter
from ..optimization.qubo_solver import QUBOSolver
from ..agents.registry import AgentRegistry
from ..connectors.registry import ConnectorRegistry
from ..core.models import Task, OptimizationResult

logger = structlog.get_logger()


class Orchestrator:
    """High-level coordinator for normalOS (expanded)."""

    def __init__(self):
        self.llm = LLMRouter()
        self.qubo = QUBOSolver()
        self.agents = AgentRegistry()
        self.connectors = ConnectorRegistry()
        self.tasks: list[Task] = []

    async def initialize_connectors(self):
        """Connect all enabled external connectors at startup."""
        results = await self.connectors.connect_all()
        logger.info("connectors_initialized", results=results)
        return results

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

    async def use_connector(self, connector_name: str, action: str, params: dict) -> dict:
        """Execute an action on any registered connector."""
        connector = self.connectors.get(connector_name)
        if not connector:
            raise ValueError(f"Connector '{connector_name}' not found")
        result = await connector.execute(action, params)
        return result.model_dump()

    async def close(self):
        await self.llm.close()
