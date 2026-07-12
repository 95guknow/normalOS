from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import uvicorn

from normal_os.core.config import settings
from normal_os.executor.task_executor import TaskExecutor
from normal_os.optimization.qubo_solver import QUBOSolver
from normal_os.core.models import QUBOProblem

app = FastAPI(title="NormalOS Dashboard")

templates = Jinja2Templates(directory="src/normal_os/dashboard/templates")
executor = TaskExecutor()
qubo_solver = QUBOSolver()


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    tasks = await executor.store.list_by_status("pending")  # simplified
    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {"tasks": tasks, "app_name": settings.app_name}
    )


@app.post("/tasks")
async def create_task(task_type: str, payload: dict):
    task_id = await executor.submit(task_type, payload)
    return {"task_id": task_id}


@app.get("/tasks/{task_id}")
async def get_task(task_id: str):
    task = await executor.get_status(task_id)
    return task.model_dump() if task else {"error": "not found"}


@app.post("/qubo/solve")
async def solve_qubo(Q: dict, bias: dict):
    problem = QUBOProblem(Q=Q, bias=bias)
    solution = qubo_solver.solve(problem)
    return solution.model_dump()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)