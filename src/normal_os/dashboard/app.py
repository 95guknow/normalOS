"""FastAPI dashboard with HTMX for better interactivity.

Clean modern dashboard (March 2026 style).
"""

from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

import structlog
from datetime import datetime

from ..core.config import settings
from ..persistence.task_store import TaskStore
from ..core.models import Task

from ..orchestrator import Orchestrator  # type: ignore

logger = structlog.get_logger()

app = FastAPI(title="normalOS Dashboard", version="0.2.0")

templates = Jinja2Templates(directory="src/normal_os/dashboard/templates")

# Global instances
task_store = TaskStore()
orchestrator = Orchestrator()


@app.on_event("startup")
async def startup():
    await task_store.init_db()


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    tasks = await task_store.list_tasks(limit=20)
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "tasks": tasks,
            "now": datetime.now().strftime("%Y-%m-%d %H:%M"),
        },
    )


@app.post("/tasks", response_class=HTMLResponse)
async def create_task(description: str = Form(...), priority: int = Form(5)):
    task = Task(description=description, priority=priority)
    await task_store.add_task(task)
    # Re-render task list
    tasks = await task_store.list_tasks(limit=20)
    return templates.TemplateResponse(
        "partials/task_list.html",
        {"request": {}, "tasks": tasks},
    )


@app.get("/tasks", response_class=HTMLResponse)
async def list_tasks_partial():
    tasks = await task_store.list_tasks(limit=20)
    return templates.TemplateResponse(
        "partials/task_list.html",
        {"request": {}, "tasks": tasks},
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.dashboard_host, port=settings.dashboard_port)