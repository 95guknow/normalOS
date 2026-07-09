# normalOS

**Practical AI Agent Orchestration Framework** (v0.2.0)

Clean, production-oriented implementation written like a senior developer would have done it in March 2026.

## Features

- Multi-LLM router (Grok, OpenAI, Anthropic, Ollama)
- QUBO-based task optimization
- Async SQLite persistence
- Simple but extensible Agent system
- FastAPI + HTMX dashboard (no heavy frontend framework)
- Docker support

## Quick Start (with Docker)

```bash
git clone https://github.com/95guknow/normalOS.git
cd normalOS
docker compose up --build
```

Then open http://localhost:8000

## Local Development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[test]"

python -m normal_os.dashboard.app
```

## Architecture

```
src/normal_os/
├── core/            # Config + models
├── llm/             # Multi-provider router
├── optimization/    # QUBO solver
├── agents/          # BaseAgent + registry + examples
├── persistence/     # Async SQLite task store
├── dashboard/       # FastAPI + HTMX templates
└── orchestrator.py
```

## Next Steps (typical for this kind of project)

- Add real background task execution
- Integrate vector store (Qdrant / Chroma)
- Add evaluation / tracing
- Proper auth for dashboard

MIT License