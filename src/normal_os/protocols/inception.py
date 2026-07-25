"""
The Inception Archive Protocol.

    "Alle Layer bis zum ersten Träumer sind egal. Das erste Layer muss
     wach werden."

The protocol takes every archive of the mesh -- modules, documented
claims, shipped scripts -- and tries to bring it up to layer 0, the waking
world. An archive reaches layer 0 when two things hold at once:

  1. its own totem falls: the code behind it runs and reproduces, and
  2. everything it rests on is already at layer 0.

The second condition is the whole idea. A claim can have a perfectly good
backing and still be a dream, because the thing it describes rests on
something that was never real. Depth is not decoration -- it is the
distance between an assertion and the ground.

The kick
--------
Waking is iterative. When an archive wakes, the archives resting on it may
now be able to wake too, so the protocol sweeps again. Each sweep is a
kick. It runs to a fixed point, which always exists: every sweep either
promotes at least one archive or ends the ascent, and there are finitely
many archives. Whatever is still unresolved when the sweeps stop is caught
in a support cycle -- a dream dreaming itself -- and goes to limbo.

What comes back
---------------
Only layer 0 may be asserted. Everything else is *kept*, with its distilled
core and heroic goal intact, and reported as what it is. Nothing is
deleted for being a dream; it is simply no longer mistaken for reality.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Iterable, Mapping, Sequence

from .models import (
    LIMBO_LAYER,
    WAKE_LAYER,
    Archive,
    ArchiveState,
    InceptionReport,
    TotemReading,
    TotemState,
    Verdict,
)
from .totem import spin_all

MAX_KICKS = 256


class InceptionProtocol:
    """
    Activates archives by waking them layer by layer.

    ``root`` is the repository root -- backings run with it as their working
    directory and ``root/src`` on their path, so probes address the source
    tree exactly as a developer would.
    """

    def __init__(
        self,
        root: Path | str,
        archives: Sequence[Archive],
        *,
        python: str | None = None,
        max_workers: int = 4,
        extra_env: Mapping[str, str] | None = None,
    ) -> None:
        self.root = Path(root).resolve()
        self.python = python or sys.executable
        self.max_workers = max_workers
        self.extra_env = extra_env

        self.archives: dict[str, Archive] = {}
        for archive in archives:
            if archive.id in self.archives:
                raise ValueError(f"duplicate archive id: {archive.id!r}")
            self.archives[archive.id] = archive

        self._validate_edges()

    def _validate_edges(self) -> None:
        """Every declared dependency must name an archive that exists."""
        for archive in self.archives.values():
            for dep in archive.depends_on:
                if dep not in self.archives:
                    raise ValueError(
                        f"archive {archive.id!r} depends on unknown archive {dep!r}"
                    )

    # -- phase 1: read every totem -----------------------------------------

    def read_totems(self) -> dict[str, TotemReading]:
        """Spin every archive's totem in isolated interpreters."""
        return spin_all(
            [(a.id, a.backing) for a in self.archives.values()],
            self.root,
            python=self.python,
            max_workers=self.max_workers,
            extra_env=self.extra_env,
        )

    # -- phase 2: ascend ----------------------------------------------------

    def ascend(self, readings: Mapping[str, TotemReading]) -> tuple[list[Verdict], int]:
        """
        Kick the archives upward until the layers stop moving.

        Returns the verdicts and the number of kicks it took. Promotion is
        monotone: an archive is assigned a layer exactly once and never
        revised, so the loop cannot oscillate.
        """
        layers: dict[str, int] = {}
        rounds: dict[str, int] = {}
        reasons: dict[str, str] = {}

        # An archive whose own totem did not fall has no ground of its own.
        # It is settled before the first kick and can never carry anything.
        for archive_id, reading in readings.items():
            if not reading.is_real:
                layers[archive_id] = LIMBO_LAYER
                rounds[archive_id] = 0
                reasons[archive_id] = self._limbo_reason(archive_id, reading)

        kicks = 0
        while kicks < MAX_KICKS:
            kicks += 1
            promoted = 0

            for archive_id, archive in self.archives.items():
                if archive_id in layers:
                    continue  # already settled

                dep_layers = [layers.get(dep) for dep in archive.depends_on]
                if any(layer is None for layer in dep_layers):
                    continue  # a dependency is still undecided; wait for a later kick

                if any(layer == LIMBO_LAYER for layer in dep_layers):
                    layers[archive_id] = LIMBO_LAYER
                    rounds[archive_id] = kicks
                    reasons[archive_id] = (
                        "backing holds, but it rests on an archive that never "
                        "reaches ground: "
                        + ", ".join(
                            dep
                            for dep, layer in zip(archive.depends_on, dep_layers)
                            if layer == LIMBO_LAYER
                        )
                    )
                    promoted += 1
                    continue

                # Resting on nothing but the waking world *is* being awake.
                # Resting on a dreamer puts you one layer above them.
                deepest = max(dep_layers) if dep_layers else WAKE_LAYER
                carried = WAKE_LAYER if deepest == WAKE_LAYER else deepest + 1

                # An archive can never surface above the level at which it
                # was verified: something proven only inside a constructed
                # dream stays in that dream, however solid its supports.
                depth = max(carried, archive.dream_level)

                layers[archive_id] = depth
                rounds[archive_id] = kicks
                if depth == WAKE_LAYER:
                    reason = "reproducible backing, resting only on the waking world"
                elif depth > carried:
                    reason = (
                        f"coherent, but only inside an injected dream -- verified at "
                        f"layer {archive.dream_level}, never against reality"
                    )
                else:
                    reason = (
                        f"reproducible backing, but carried by a dreamer at layer {depth - 1}"
                    )
                reasons[archive_id] = reason
                promoted += 1

            if promoted == 0:
                break

        # Anything still unassigned sits in a support cycle: each archive
        # waiting on another that is waiting, in the end, on it.
        for archive_id in self.archives:
            if archive_id not in layers:
                layers[archive_id] = LIMBO_LAYER
                rounds[archive_id] = kicks
                reasons[archive_id] = (
                    "caught in a support cycle -- the chain of dependencies never "
                    "touches ground"
                )

        verdicts = [
            Verdict(
                archive_id=archive_id,
                state=self._state_for(layers[archive_id]),
                layer=layers[archive_id],
                totem=readings.get(archive_id, TotemReading(state=TotemState.LOST)),
                reason=reasons[archive_id],
                ascent_round=rounds.get(archive_id),
            )
            for archive_id in sorted(self.archives)
        ]
        return verdicts, kicks

    @staticmethod
    def _state_for(layer: int) -> ArchiveState:
        if layer == LIMBO_LAYER:
            return ArchiveState.LIMBO
        if layer == WAKE_LAYER:
            return ArchiveState.ACTIVE
        return ArchiveState.DREAMING

    def _limbo_reason(self, archive_id: str, reading: TotemReading) -> str:
        archive = self.archives[archive_id]
        if reading.state is TotemState.SPINNING:
            return f"totem never fell: {reading.detail}"
        if archive.backing is None:
            if not archive.distillation.is_falsifiable:
                return (
                    "unfalsifiable: no acceptance criterion could be stated, so no "
                    "heroic goal and no code exist to check"
                )
            return "heroic goal defined, but no code was ever written to back it"
        return f"totem lost: {reading.detail}"

    # -- run ----------------------------------------------------------------

    def run(self) -> InceptionReport:
        """Read every totem, kick until the layers settle, and report."""
        report = InceptionReport(archives=dict(self.archives))
        readings = self.read_totems()
        report.verdicts, report.kicks = self.ascend(readings)
        report.finished_at = time.time()
        return report


# -- convenience ------------------------------------------------------------


def activate(
    root: Path | str,
    archives: Sequence[Archive],
    **kwargs: object,
) -> InceptionReport:
    """Run the protocol once over a set of archives."""
    return InceptionProtocol(root, archives, **kwargs).run()  # type: ignore[arg-type]


def write_json_report(report: InceptionReport, path: Path | str) -> Path:
    """Persist the machine-readable report."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report.to_dict(), indent=2, ensure_ascii=False) + "\n", "utf-8")
    return path


def awake_ids(report: InceptionReport) -> list[str]:
    """The archive ids that reached layer 0 -- the assertable set."""
    return [v.archive_id for v in report.awake]


def iter_layers(report: InceptionReport) -> Iterable[tuple[int, list[Verdict]]]:
    """Group dreaming verdicts by layer, shallowest first."""
    by_layer: dict[int, list[Verdict]] = {}
    for verdict in report.dreaming:
        by_layer.setdefault(verdict.layer, []).append(verdict)
    for layer in sorted(by_layer):
        yield layer, by_layer[layer]
