"""Example concrete agents for normalOS."""

from .base import BaseAgent, registry
from ..core.models import Task
from ..llm.router import LLMRouter

import structlog

logger = structlog.get_logger()


class LLMAgent(BaseAgent):
    """Agent that uses an LLM to complete tasks."""

    name = "llm_agent"
    description = "Uses LLM to process and complete tasks"

    def __init__(self, llm_router: LLMRouter | None = None):
        self.llm = llm_router or LLMRouter()

    async def run(self, task: Task, context: dict | None = None) -> dict:
        prompt = f"Complete the following task: {task.description}\n\nContext: {context or {}}"
        response = await self.llm.generate(prompt)
        logger.info("llm_agent_completed_task", task_id=task.id)
        return {
            "result": response.content,
            "provider": response.provider,
            "model": response.model,
        }


# Auto-register
registry.register(LLMAgent())