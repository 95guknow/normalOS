# normalOS v1.0

**Clean, explicit, production-oriented orchestration and optimization platform.**

Extracted and normalized from the Fusion Hero OS Horkrux. All implicit high-value patterns made explicit, clean, and usable.

## Core Principles

- Explicit over implicit
- Strong typing + clean architecture
- Async-first with proper resource control
- Production-ready structure (March 2026 style)

## Architecture

- `core/` — Config, Models, Orchestrator
- `agents/` — BaseAgent + explicit Registry
- `executor/` — TaskExecutor + WorkerPool
- `persistence/` — TaskStore + ContextStore + History
- `optimization/` — QUBOSolver (dimod + caching)
- `llm/` — Multi-provider Router + Structured Output
- `dashboard/` — FastAPI + HTMX (live updates)
- `cli/` — Full Typer CLI

## Quickstart

```bash
uv sync
normalos --help
uvicorn src.normal_os.dashboard.app:app --reload
```

## Key Features (v1.0)

- Async Task execution with retry, cancellation, resource budgeting
- Persistent Context + Result History
- QUBO optimization with caching
- Multi-LLM routing foundation
- Structured output enforcement
- HTMX live dashboard
- Powerful CLI

## Status

**v1.0 ready** — Core systems stable and explicit.