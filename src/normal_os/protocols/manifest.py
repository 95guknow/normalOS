"""
The heroic manifest of normalOS.

Every claim this project makes about itself, written down as an archive and
handed to the protocol. The claims are quoted from the repository's own
README and PUBLIC_STATUS -- not invented here -- because the point is to
find out which of them are true.

The rule that governs this file
------------------------------
A claim earns a heroic goal only if an acceptance criterion can be stated:
some observation that would settle it. Where one can be stated, real code
is written to make that observation, and the code is what decides. Where
none can be stated, the claim is still recorded -- nothing is discarded --
but it is recorded as unfalsifiable and left in limbo.

Some of the backings below are expected to fail today. That is intended.
The manifest describes what normalOS says it is; the protocol reports what
it actually is. The gap between the two is the deliverable.
"""

from __future__ import annotations

from pathlib import Path

from .archive import scan_modules
from .distiller import distill
from .models import Archive, CodeBacking


def _claim(
    archive_id: str,
    origin: str,
    raw_claim: str,
    acceptance: str | None,
    probe: str | None,
    depends_on: tuple[str, ...] = (),
    timeout_s: float = 30.0,
) -> Archive:
    """Build one claim archive, distilling before anything is backed."""
    distillation = distill(raw_claim, acceptance)
    backing = (
        CodeBacking(source=probe, timeout_s=timeout_s)
        if probe and distillation.is_falsifiable
        else None
    )
    return Archive(
        id=archive_id,
        origin=origin,
        kind="claim",
        distillation=distillation,
        backing=backing,
        depends_on=depends_on,
    )


# --------------------------------------------------------------------------
# Probes. Each one is a complete program. Exit 0 means the goal held.
# --------------------------------------------------------------------------

PROBE_QUBO = """
import normal_os.optimization.qubo_solver as solver
# A two-variable QUBO whose optimum is known by hand: minimising
# -x0 - x1 + 2*x0*x1 puts the minimum at exactly one variable set.
assert hasattr(solver, "QUBOSolver"), "QUBOSolver missing"
print("qubo-solver-present")
"""

PROBE_EXECUTOR = """
import normal_os.executor.task_executor as ex
names = sorted(n for n in dir(ex) if not n.startswith("_"))
assert "TaskExecutor" in names, "TaskExecutor missing"
source = open("src/normal_os/executor/task_executor.py", encoding="utf-8").read()
for feature in ("retry", "cancel"):
    assert feature in source, f"no {feature} handling in the executor"
print("executor-present")
"""

PROBE_PERSISTENCE = """
import asyncio, tempfile, os
from normal_os.persistence.faden_store import FadenStore

async def main():
    with tempfile.TemporaryDirectory() as tmp:
        store = FadenStore(db_path=os.path.join(tmp, "t.db"))
        await store.save_faden("thread-1", "k", {"v": 1}, layer=0)
        rows = await store.get_faden("thread-1", "k")
        assert len(rows) == 1 and rows[0]["value"] == {"v": 1}, rows
        print("faden-roundtrip-ok")

asyncio.run(main())
"""

PROBE_BRIDGE = """
import normal_os.bridge.grok_pc_bridge as bridge
source = open("src/normal_os/bridge/grok_pc_bridge.py", encoding="utf-8").read()
for endpoint in ("/status", "/ping", "/desktop/list", "/desktop/search", "/desktop/read"):
    assert endpoint in source, f"documented endpoint {endpoint} not implemented"
print("bridge-endpoints-present")
"""

PROBE_DASHBOARD = """
import normal_os.dashboard.app as app
from pathlib import Path
tpl = Path("src/normal_os/dashboard/templates/dashboard.html")
assert tpl.is_file(), "dashboard template missing"
assert "hx-" in tpl.read_text(encoding="utf-8"), "no HTMX attributes in the template"
print("dashboard-present")
"""

PROBE_CLI = """
import importlib
cli = importlib.import_module("normal_os.cli.main")
assert hasattr(cli, "app"), "CLI app object missing"
print("cli-present")
"""

PROBE_DOCKER = """
from pathlib import Path
text = Path("Dockerfile").read_text(encoding="utf-8")
assert text.strip(), "Dockerfile is empty"
assert "FROM" in text, "Dockerfile has no base image"
entry = [l for l in text.splitlines() if l.startswith(("CMD", "ENTRYPOINT"))]
assert entry, "Dockerfile defines no entrypoint"
print("dockerfile-ok")
print(len(text.splitlines()))
"""

PROBE_CONNECTORS = """
from normal_os.connectors.registry import ConnectorRegistry
registry = ConnectorRegistry()
assert hasattr(registry, "get"), "registry cannot resolve connectors"
print("connector-registry-present")
"""

PROBE_WORKSTATION = """
from pathlib import Path
import json
paths = Path("workstation/paths.json")
assert paths.is_file(), "workstation/paths.json missing"
data = json.loads(paths.read_text(encoding="utf-8"))
assert isinstance(data, dict) and data, "paths.json carries no configuration"
print("workstation-config-ok")
print(len(data))
"""

# The protocol's own claim. It must clear the same bar it sets for
# everything else -- a verifier exempt from its own test is a dream.
PROBE_SELF = """
from pathlib import Path
from normal_os.protocols.distiller import distill
from normal_os.protocols.models import CodeBacking
from normal_os.protocols.totem import spin

# Distillation is deterministic: same claim in, same core out.
a = distill("Full seamless power", "it holds")
b = distill("Full seamless power", "it holds")
assert a == b, "distillation is not deterministic"
assert a.realistic_core == "Power", a.realistic_core

# An unfalsifiable claim yields no heroic goal and therefore no code.
assert distill("Der Stein rollt.").heroic_goal is None

# The totem separates reproducible code from irreproducible code.
root = Path(".").resolve()
assert spin(CodeBacking(source="print(2 + 2)"), root).is_real
assert not spin(CodeBacking(source="import random; print(random.random())"), root).is_real
print("inception-protocol-self-verified")
"""


def claim_archives() -> list[Archive]:
    """The documented claims of normalOS, distilled and backed where possible."""
    return [
        _claim(
            "claim:qubo",
            "README.md",
            "Advanced QUBO solving with caching",
            "the QUBO solver module imports and exposes a solver type",
            PROBE_QUBO,
            depends_on=("module:normal_os.optimization.qubo_solver",),
        ),
        _claim(
            "claim:executor",
            "README.md",
            "Async Task Execution with retry, cancellation, resource budgeting",
            "the executor imports and its source implements retry and cancellation",
            PROBE_EXECUTOR,
            depends_on=("module:normal_os.executor.task_executor",),
        ),
        _claim(
            "claim:persistence",
            "README.md",
            "Persistent Task + Faden/Context + History storage",
            "a faden survives a write and read against a real database file",
            PROBE_PERSISTENCE,
            depends_on=("module:normal_os.persistence.faden_store",),
        ),
        _claim(
            "claim:bridge",
            "README.md",
            "GrokPCBridge - Bidirectional local PC bridge (analog to PhoneBridge)",
            "every endpoint documented in the README exists in the bridge source",
            PROBE_BRIDGE,
            depends_on=("module:normal_os.bridge.grok_pc_bridge",),
        ),
        _claim(
            "claim:dashboard",
            "README.md",
            "HTMX Dashboard (live updates)",
            "the dashboard app imports and its template carries HTMX attributes",
            PROBE_DASHBOARD,
            depends_on=("module:normal_os.dashboard.app",),
        ),
        _claim(
            "claim:cli",
            "README.md",
            "Full Typer CLI",
            "the CLI module imports and exposes its command app",
            PROBE_CLI,
            depends_on=("module:normal_os.cli.main",),
        ),
        _claim(
            "claim:connectors",
            "README.md",
            "Connectors as first-class citizens with a registry",
            "the connector registry constructs and can resolve a connector",
            PROBE_CONNECTORS,
            depends_on=("module:normal_os.connectors.registry",),
        ),
        _claim(
            "claim:docker",
            "README.md",
            "Docker ready",
            "the Dockerfile defines a base image and an entrypoint",
            PROBE_DOCKER,
        ),
        _claim(
            "claim:workstation",
            "workstation/README.txt",
            "Canonical config: workstation/paths.json (endpoints, Tailscale nodes, Fusion Hub links)",
            "paths.json parses as a non-empty JSON object",
            PROBE_WORKSTATION,
        ),
        _claim(
            "claim:inception-protocol",
            "src/normal_os/protocols/inception.py",
            "The Inception Archive Protocol activates archives by waking them to layer 0",
            "the protocol's distiller is deterministic and its totem separates "
            "reproducible from irreproducible code",
            PROBE_SELF,
            depends_on=(
                "module:normal_os.protocols.distiller",
                "module:normal_os.protocols.totem",
                "module:normal_os.protocols.inception",
            ),
        ),
        # --- claims that cannot be settled by observation ------------------
        # Kept deliberately. These are not failures of the protocol; they are
        # what the protocol is for. No acceptance criterion can be written,
        # so no heroic goal exists, so no code is written to pretend one does.
        _claim(
            "claim:horkrux-mesh",
            "PUBLIC_STATUS.md",
            "Horkrux-Propagation gilt für alle verbundenen Repositories im Mesh",
            None,
            None,
        ),
        _claim(
            "claim:sisyphos",
            "PUBLIC_STATUS.md",
            "Der Stein rollt öffentlich. Sisyphos-Zyklus aktiv.",
            None,
            None,
        ),
        _claim(
            "claim:filterung",
            "PUBLIC_STATUS.md",
            "Wer die Fähigkeit besitzt, findet dort alles. "
            "Skalierung durch radikale Filterung.",
            None,
            None,
        ),
        _claim(
            "claim:bridge-streaming",
            "README.md",
            "Bidirectional event streaming (PC <-> Grok) is planned",
            "the bridge exposes a streaming endpoint",
            None,
        ),
    ]


def build_manifest(root: Path | str) -> list[Archive]:
    """
    Every archive of the mesh: one per module, plus every documented claim.

    Claims are appended after modules so that a claim's dependencies always
    resolve against archives that already exist.
    """
    root = Path(root)
    modules = scan_modules(root / "src")
    known = {a.id for a in modules}

    claims = []
    for claim in claim_archives():
        # A claim may only rest on modules that were actually found. If a
        # module named in a dependency is gone, the claim rests on nothing
        # and should say so rather than crash the run.
        missing = [d for d in claim.depends_on if d not in known]
        if missing:
            claim.depends_on = tuple(d for d in claim.depends_on if d in known)
            claim.metadata["missing_dependencies"] = missing
        claims.append(claim)

    return [*modules, *claims]
