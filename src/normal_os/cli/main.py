import typer
from typing import Optional
from normal_os.core.config import settings
from normal_os.executor.task_executor import TaskExecutor
from normal_os.optimization.qubo_solver import QUBOSolver
from normal_os.core.models import QUBOProblem

app = typer.Typer(help="NormalOS v1 CLI - Clean orchestration platform")
executor = TaskExecutor()
qubo = QUBOSolver()


@app.command()
def version():
    typer.echo("normalOS v1.0")


@app.command()
def submit(
    task_type: str,
    payload: str = "{}",
    priority: int = 5,
):
    """Submit a new task."""
    import asyncio
    import json
    task_id = asyncio.run(
        executor.submit(task_type, json.loads(payload), priority=priority)
    )
    typer.echo(f"Task submitted: {task_id}")


@app.command()
def status(task_id: str):
    """Check task status."""
    import asyncio
    task = asyncio.run(executor.get_status(task_id))
    if task:
        typer.echo(f"Status: {task.status} | Result: {task.result}")
    else:
        typer.echo("Task not found")


@app.command()
def solve_qubo(Q: str, bias: str):
    """Solve a QUBO problem."""
    import json
    problem = QUBOProblem(Q=json.loads(Q), bias=json.loads(bias))
    solution = qubo.solve(problem)
    typer.echo(solution.model_dump_json(indent=2))


if __name__ == "__main__":
    app()