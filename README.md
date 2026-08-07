# normalOS v2.0

**Clean, explicit, production-oriented orchestration and optimization platform.**

All high-value practical functions from the Fusion Hero OS Horkrux have been extracted, normalized, and made explicit.

## Versionslinie (ab v2.0 eigenständig)

`VERSION` im Root ist ab v2.0 die einzige Quelle der Wahrheit für normalOS. Alle Manifeste folgen ihr: `pyproject.toml` und `src/normal_os/__init__.py`.

**Was v2.0 benennt:** eine Zählung statt drei. Bis v2.0 führte dieses Repository drei widersprüchliche Versionsmarker — README `v1.0`, `pyproject.toml` `0.5.0`, `__init__.py` `0.1.0`. Der Ära-Inhalt von v2.0 ist genau deren Vereinheitlichung; der Sprung ist damit gedeckt, nicht bloß gesetzt.

**Entkopplung:** normalOS zählt **getrennt** von der Fusion-Hero-OS-Plattformversion. `normalOS v2.0` ist nicht `Plattform v20` — die Zahlen stehen zufällig nebeneinander, nicht in Beziehung. Wo dieses Repository die Fusion-Hero-OS-Version nennt (etwa `PUBLIC_STATUS.md`), ist das ein Verweis auf ein anderes Produkt, keine eigene Zählung.

Signatur-Trigger: `=====NormalOS` (registriert in `ops_vocabulary.yaml` → `signatures.normalos` im Fusion-Hero-OS-Repo, implementiert in `fusion_hero_os/core/persona_signature.py`).

## Included Core Capabilities (seit v1.0, unverändert in v2.0)

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

## Inception Archive Protocol

Aktiviert alle Archive des Mesh, indem es sie auf **Layer 0** hebt — die wache
Welt. Ohne Abhängigkeiten, läuft mit nacktem Python 3.11.

```bash
PYTHONPATH=src python -m normal_os.protocols --root .
```

Jede Behauptung dieses Repos wird auf ihren realistischen Kern reduziert, gegen
ein Abnahmekriterium zu einem heroischen Ziel geschärft und dann mit echtem
Code unterfüttert. Was ohne Abnahmekriterium bleibt, bekommt keinen Code, der
so tut, als gäbe es eins — es wird behalten, aber nicht behauptet.

Ein Archiv wacht auf, wenn sein Code in zwei getrennten Interpretern
reproduzierbar läuft **und** alles, worauf es ruht, ebenfalls wach ist.

Aktueller Stand: [`INCEPTION_REPORT.md`](INCEPTION_REPORT.md) ·
Details: [`docs/INCEPTION_PROTOCOL.md`](docs/INCEPTION_PROTOCOL.md)

> Der erste Lauf hat gemeldet, dass die unten dokumentierten Kernmodule nicht
> importierbar sind — unabhängig von installierten Paketen. Die Liste steht im
> Report. Die Behauptungen bleiben bestehen, sie gelten nur nicht als belegt,
> bis der Code sie trägt.

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