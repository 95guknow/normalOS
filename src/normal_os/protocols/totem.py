"""
The totem: the reality check of the Inception Archive Protocol.

Cobb's totem tells him which world he is in. Ours does the same job with
the only test that actually distinguishes code from prose: run it twice, in
two separate interpreters, under deliberately different conditions, and see
whether reality comes out the same both times.

Why two *processes* and not two calls
-------------------------------------
An in-process check can be fooled by everything the verifier already has in
memory: modules imported by someone else, caches warmed by an earlier test,
monkeypatched globals. Those are exactly the conditions under which a dream
feels solid. A fresh interpreter has none of them, so a backing that only
works "in context" is caught here rather than believed.

Why different hash seeds
------------------------
The two runs use different PYTHONHASHSEED values. Code that iterates a set
or a dict keyed by strings and prints the result will disagree between the
runs, and disagreement is the signal we want -- an answer that depends on
where in memory something happened to land is not a fact about the world.
Genuinely deterministic code is unaffected.
"""

from __future__ import annotations

import hashlib
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Iterable, Mapping, Sequence

from .models import CodeBacking, TotemReading, TotemState

#: Distinct hash seeds for the two runs. Any deterministic program is
#: indifferent to these; anything relying on hash order is not.
_SEED_A = "0"
_SEED_B = "1"

_STDERR_EXCERPT = 400


def _digest(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()[:16]


def _child_env(root: Path, seed: str, extra: Mapping[str, str] | None) -> dict[str, str]:
    env = dict(os.environ)
    env["PYTHONHASHSEED"] = seed
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    # The protocol verifies a source tree, not an installed distribution:
    # point the child at src/ so archives resolve without a build step.
    src = root / "src"
    pythonpath = str(src if src.is_dir() else root)
    if env.get("PYTHONPATH"):
        pythonpath = os.pathsep.join([pythonpath, env["PYTHONPATH"]])
    env["PYTHONPATH"] = pythonpath
    env.pop("PYTHONSTARTUP", None)
    if extra:
        env.update(extra)
    return env


class _Run:
    """One execution of a backing in an isolated interpreter."""

    __slots__ = ("exit_code", "digest", "stderr", "timed_out")

    def __init__(self, exit_code: int | None, digest: str | None, stderr: str, timed_out: bool):
        self.exit_code = exit_code
        self.digest = digest
        self.stderr = stderr
        self.timed_out = timed_out


def _run_once(
    backing: CodeBacking,
    root: Path,
    seed: str,
    python: str,
    extra_env: Mapping[str, str] | None,
) -> _Run:
    try:
        # -s drops the per-user site directory so a backing cannot lean on
        # something only this machine happens to have. Full -I is wrong here:
        # it also discards PYTHONPATH, which is how the child finds src/.
        proc = subprocess.run(
            [python, "-s", "-c", backing.source],
            cwd=str(root),
            env=_child_env(root, seed, extra_env),
            capture_output=True,
            timeout=backing.timeout_s,
        )
    except subprocess.TimeoutExpired:
        return _Run(None, None, f"timed out after {backing.timeout_s}s", True)
    except OSError as exc:  # interpreter missing, exec failed
        return _Run(None, None, f"could not launch interpreter: {exc}", False)

    stderr = proc.stderr.decode("utf-8", "replace").strip()
    return _Run(proc.returncode, _digest(proc.stdout), stderr[-_STDERR_EXCERPT:], False)


def spin(
    backing: CodeBacking | None,
    root: Path | str,
    *,
    python: str | None = None,
    extra_env: Mapping[str, str] | None = None,
) -> TotemReading:
    """
    Spin one totem.

    Returns :class:`TotemState.FELL` only when both isolated runs exited 0
    *and* produced byte-identical stdout. Anything else is a dream:
    ``SPINNING`` when the two runs disagreed, ``LOST`` when there was no
    reading to take at all.
    """
    if backing is None:
        return TotemReading(
            state=TotemState.LOST,
            detail="no code backing -- nothing was ever built to check",
        )

    root = Path(root)
    python = python or sys.executable
    started = time.perf_counter()

    # The two runs are independent, so overlap them. They are subprocesses,
    # so threads are the right tool -- the GIL is released across the wait.
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [
            pool.submit(_run_once, backing, root, seed, python, extra_env)
            for seed in (_SEED_A, _SEED_B)
        ]
        run_a, run_b = (f.result() for f in futures)

    elapsed_ms = (time.perf_counter() - started) * 1000.0

    if run_a.timed_out or run_b.timed_out:
        return TotemReading(
            state=TotemState.LOST,
            exit_a=run_a.exit_code,
            exit_b=run_b.exit_code,
            duration_ms=elapsed_ms,
            detail=f"backing did not terminate within {backing.timeout_s}s",
        )

    if run_a.exit_code != 0 or run_b.exit_code != 0:
        failing = run_a if run_a.exit_code != 0 else run_b
        detail = failing.stderr.splitlines()[-1] if failing.stderr else "no diagnostic output"
        return TotemReading(
            state=TotemState.LOST,
            exit_a=run_a.exit_code,
            exit_b=run_b.exit_code,
            digest_a=run_a.digest,
            digest_b=run_b.digest,
            duration_ms=elapsed_ms,
            detail=f"backing failed: {detail}",
        )

    if run_a.digest != run_b.digest:
        return TotemReading(
            state=TotemState.SPINNING,
            exit_a=0,
            exit_b=0,
            digest_a=run_a.digest,
            digest_b=run_b.digest,
            duration_ms=elapsed_ms,
            detail="two isolated runs disagreed -- the result is not reproducible",
        )

    return TotemReading(
        state=TotemState.FELL,
        exit_a=0,
        exit_b=0,
        digest_a=run_a.digest,
        digest_b=run_b.digest,
        duration_ms=elapsed_ms,
        detail="reproducible across isolated runs",
    )


def spin_all(
    backings: Sequence[tuple[str, CodeBacking | None]],
    root: Path | str,
    *,
    python: str | None = None,
    max_workers: int = 4,
    extra_env: Mapping[str, str] | None = None,
) -> dict[str, TotemReading]:
    """Spin many totems concurrently, keyed by archive id."""
    if not backings:
        return {}

    readings: dict[str, TotemReading] = {}
    workers = max(1, min(max_workers, len(backings)))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {
            archive_id: pool.submit(spin, backing, root, python=python, extra_env=extra_env)
            for archive_id, backing in backings
        }
        for archive_id, future in futures.items():
            readings[archive_id] = future.result()
    return readings


def iter_states(readings: Iterable[TotemReading]) -> dict[TotemState, int]:
    """Tally totem states -- used for the report header."""
    tally = {state: 0 for state in TotemState}
    for reading in readings:
        tally[reading.state] += 1
    return tally
