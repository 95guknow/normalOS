"""FastAPI dashboard for normalOS.

Clean, modern monitoring interface (March 2026 style).
"""

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

import structlog
from datetime import datetime

from ..core.config import settings

from ..llm.router import LLMRouter

from ..optimization.qubo_solver import QUBOSolver

from ..core.models import Task


logger = structlog.get_logger()

app = FastAPI(title="normalOS Dashboard", version="0.1.0")

# Simple in-memory state for demo
_tasks: list[Task] = []
_llm_router = LLMRouter()
_qubo_solver = QUBOSolver()


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard page."""
    return HTMLResponse(content=get_dashboard_html())


def get_dashboard_html() -> str:
    """Return a clean, self-contained dashboard HTML."""
    task_html = ""
    for task in _tasks[-10:]:  # show last 10
        status_color = {
            "pending": "#f59e0b",
            "running": "#3b82f6",
            "completed": "#10b981",
            "failed": "#ef4444",
        }.get(task.status, "#6b7280")

        task_html += f"""
        <div style="border:1px solid #e5e7eb; padding:12px; margin-bottom:8px; border-radius:8px;">
            <div style="display:flex; justify-content:space-between;">
                <strong>{task.description}</strong>
                <span style="color:{status_color}; font-weight:600;">{task.status}</span>
            </div>
            <div style="font-size:0.85rem; color:#6b7280; margin-top:4px;">
                Priority: {task.priority} | Est. {task.estimated_duration_minutes} min
            </div>
        </div>
        """

    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>normalOS Dashboard</title>
    <style>
        body {{ font-family: system-ui, -apple-system, sans-serif; background:#f8fafc; margin:0; padding:40px; }}
        .container {{ max-width: 960px; margin: 0 auto; }}
        h1 {{ color:#0f172a; }}
        .card {{ background:white; border-radius:12px; padding:24px; box-shadow:0 1px 3px rgba(0,0,0,0.1); }}
    </style>
</head>
<body>
    <div class="container">
        <h1>normalOS Dashboard</h1>
        <p style="color:#64748b;">Clean AI orchestration • {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>

        <div class="card" style="margin-top:24px;">
            <h2 style="margin-top:0;">Recent Tasks</h2>
            {task_html if task_html else '<p style="color:#64748b;">No tasks yet. Use the API to create some.</p>'}
        </div>

        <div class="card" style="margin-top:24px;">
            <h2>Quick Actions</h2>
            <button onclick="createDemoTask()" style="padding:10px 20px; background:#0ea5e9; color:white; border:none; border-radius:6px; cursor:pointer;">
                Create Demo Task
            </button>
        </div>
    </div>

    <script>
    async function createDemoTask() {{
        const res = await fetch('/tasks', {{ method: 'POST' }});
        if (res.ok) window.location.reload();
    }}
    </script>
</body>
</html>"""


@app.post("/tasks")
async def create_task(description: str = "Demo task from dashboard"):
    """Create a new task (demo endpoint)."""
    task = Task(description=description, priority=5)
    _tasks.append(task)
    return {"status": "created", "task_id": task.id}


@app.get("/tasks")
async def list_tasks():
    return [t.model_dump() for t in _tasks]


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.dashboard_host, port=settings.dashboard_port)