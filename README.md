# normalOS v1.0

**Clean, explicit, production-oriented orchestration and optimization platform.**

All high-value practical functions from the Fusion Hero OS Horkrux have been extracted, normalized, and made explicit.

## Included Core Capabilities (v1.0)

- Async Task Execution with retry, cancellation, resource budgeting
- Persistent Task + Faden/Context + History storage
- Advanced QUBO solving with caching
- Coevolution routing foundation
- Multi-LLM routing + Structured Output enforcement
- Agent Registry + BaseAgent pattern
- Worker Pool
- HTMX Dashboard (live updates)
- Full Typer CLI
- **GrokPCBridge** – Bidirectional local PC bridge (analog to PhoneBridge)
- Docker ready

## GrokPCBridge (New in v1.0)

The GrokPCBridge gives Grok / normalOS controlled, explicit access to your local Windows PC — especially the Desktop.

This solves requests like "check what Claude left on my desktop" in a clean and secure way.

### How to use

1. On your local PC, start the bridge:

```bash
python -m src.normal_os.bridge.grok_pc_bridge
```

2. The bridge will print a **token** on startup.

3. From Grok/normalOS you can now connect using:
   - Base URL: `http://localhost:8765` (or your PC's IP if remote)
   - Authorization: `Bearer <token>`

### Available Endpoints (v1)

- `GET /status` – Bridge health
- `GET /ping` – Latency measurement
- `GET /desktop/list?subpath=` – List Desktop contents
- `GET /desktop/search?query=claude` – Search files on Desktop
- `GET /desktop/read?path=...` – Read a text file from allowed paths
- `GET /system/info` – Basic system information

### Security Model

- Token-based authentication (required)
- Read-only in v1
- Path allow-list: Desktop, Documents, Downloads (configurable)
- Max file read size: 2 MB
- All operations are logged on the PC side

### Future Extensions (planned)

- Bidirectional event streaming (PC ↔ Grok)
- Controlled write operations (with explicit user approval)
- Resource monitoring + process listing
- Integration into normalOS Orchestrator as native BridgeAgent

## Workstation (Windows PC)

Local ops live under `workstation/` — start scripts, path registry, Tailscale checks, VR load, desktop restore.

```powershell
# Env + Status
.\workstation\load-env.ps1
.\workstation\status.ps1

# Start Fusion + Bridge + Docs
.\workstation\start-normalos.ps1

# VR layer (audit / generate assets)
.\workstation\load-vr.ps1
.\workstation\load-vr.ps1 -Generate

# Link mesh + integration hub
.\workstation\link-all.ps1
```

Canonical config: `workstation/paths.json` (endpoints, Tailscale nodes, Fusion Hub links).

Copy `workstation/.env.example` → `workstation/.env` for API keys (never commit `.env`).

## Status

**v1.0 COMPLETE** — All major practical patterns from the Horkrux are now explicit, clean, and usable.

The GrokPCBridge is the first step toward deep, trusted local PC integration while keeping everything explicit and auditable.