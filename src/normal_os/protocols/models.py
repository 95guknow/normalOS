"""
Data model for the Inception Archive Protocol.

Deliberately stdlib-only (dataclasses instead of pydantic): this protocol
judges whether the rest of the system is real, so it may not itself depend
on anything that could be missing at runtime. A verifier that cannot start
is a verifier that verifies nothing.

Layer semantics
---------------
Layer 0 is the waking world: the archive is backed by code that actually
runs and reproduces, and everything it rests on does too. Layer N > 0 means
the archive's own backing holds, but it rests on something that is still
asleep -- it is a dream carried by a dreamer. LIMBO means there is no
ground under it at all: no backing, a failing backing, an irreproducible
one, or a support cycle that never touches reality.

Only layer 0 may be asserted as true. Everything deeper is retained -- with
its distilled core and heroic goal intact -- but retained as a dream.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

#: The waking world. Executable, reproducible, resting only on the same.
WAKE_LAYER = 0

#: Sentinel depth for archives that never reach ground truth.
LIMBO_LAYER = -1


class TotemState(str, Enum):
    """
    Result of spinning an archive's totem.

    The totem is the reproducibility check. Real code, run twice under
    different conditions, produces the same answer -- the totem falls.
    A dream does not: it answers differently each time, or not at all.
    """

    #: Two isolated runs agreed exactly. This is reality.
    FELL = "fell"

    #: Two isolated runs disagreed. Still dreaming.
    SPINNING = "spinning"

    #: No reading possible -- the backing crashed, timed out, or is absent.
    LOST = "lost"


class ArchiveState(str, Enum):
    """Where an archive ended up after the protocol ran."""

    #: Reached layer 0. Awake, activated, assertable.
    ACTIVE = "active"

    #: Backing holds, but it rests on something still asleep.
    DREAMING = "dreaming"

    #: No ground beneath it. Retained as a record, never asserted.
    LIMBO = "limbo"


@dataclass(frozen=True)
class Distillation:
    """
    A hallucinated claim reduced to what can actually be checked.

    ``raw_claim`` is the statement as it was found (README bullet, status
    manifesto, module docstring). ``realistic_core`` is that statement with
    unfalsifiable rhetoric stripped out. ``heroic_goal`` is the ambition
    restated as something a machine can pass or fail.

    A distillation with ``heroic_goal is None`` is unfalsifiable: nothing
    was claimed that could ever be wrong. Such archives cannot be backed by
    code and are routed to limbo by design, not by failure.
    """

    raw_claim: str
    realistic_core: str
    heroic_goal: str | None
    dropped_terms: tuple[str, ...] = ()

    @property
    def is_falsifiable(self) -> bool:
        return self.heroic_goal is not None


@dataclass(frozen=True)
class CodeBacking:
    """
    Real, executable code standing behind a heroic goal.

    ``source`` is a complete Python program. It is executed in a fresh
    interpreter -- not imported, not exec'd in-process -- so that nothing in
    the verifier's own memory can make it appear to work. Exit code 0 means
    the goal held; anything else means it did not. Everything the program
    prints to stdout is the evidence, and that evidence must be identical
    across runs.
    """

    source: str
    timeout_s: float = 30.0

    def __post_init__(self) -> None:
        if not self.source.strip():
            raise ValueError("a code backing may not be empty source")
        if self.timeout_s <= 0:
            raise ValueError("timeout_s must be positive")


@dataclass(frozen=True)
class TotemReading:
    """The outcome of spinning one totem twice."""

    state: TotemState
    exit_a: int | None = None
    exit_b: int | None = None
    digest_a: str | None = None
    digest_b: str | None = None
    duration_ms: float = 0.0
    detail: str = ""

    @property
    def is_real(self) -> bool:
        return self.state is TotemState.FELL


@dataclass
class Archive:
    """
    One unit of the mesh to be activated: a module, a documented claim,
    a script, a protocol.

    ``depends_on`` lists the archive ids this one rests on. An archive can
    only wake once everything below it has woken -- that is the whole of the
    ascent rule.

    ``dream_level`` is the shallowest layer this archive could ever occupy,
    given how it is verified. It is 0 for anything checked against reality
    directly. It is 1 for anything checked inside a constructed dream --
    an import that only succeeds once absent packages have been invented
    for it. Such an archive may be perfectly coherent, but coherence inside
    a dream is not the waking world, and no amount of support from below
    can raise it to layer 0.
    """

    id: str
    origin: str
    kind: str
    distillation: Distillation
    backing: CodeBacking | None = None
    depends_on: tuple[str, ...] = ()
    sha256: str | None = None
    dream_level: int = WAKE_LAYER
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("archive id may not be empty")
        if self.dream_level < WAKE_LAYER:
            raise ValueError("dream_level may not be below the waking world")
        if self.backing is not None and not self.distillation.is_falsifiable:
            raise ValueError(
                f"archive {self.id!r}: code backing supplied for an unfalsifiable "
                "claim -- distill a heroic goal first"
            )


@dataclass
class Verdict:
    """What the protocol decided about a single archive."""

    archive_id: str
    state: ArchiveState
    layer: int
    totem: TotemReading
    reason: str
    ascent_round: int | None = None

    @property
    def is_awake(self) -> bool:
        return self.state is ArchiveState.ACTIVE and self.layer == WAKE_LAYER

    def to_dict(self) -> dict[str, Any]:
        return {
            "archive_id": self.archive_id,
            "state": self.state.value,
            "layer": self.layer,
            "totem": self.totem.state.value,
            "reason": self.reason,
            "ascent_round": self.ascent_round,
        }


@dataclass
class InceptionReport:
    """Full result of one protocol run."""

    verdicts: list[Verdict] = field(default_factory=list)
    archives: dict[str, Archive] = field(default_factory=dict)
    kicks: int = 0
    started_at: float = field(default_factory=time.time)
    finished_at: float | None = None

    # -- selection ---------------------------------------------------------

    @property
    def awake(self) -> list[Verdict]:
        """Layer 0. The only verdicts that may be asserted as true."""
        return sorted(
            (v for v in self.verdicts if v.is_awake),
            key=lambda v: v.archive_id,
        )

    @property
    def dreaming(self) -> list[Verdict]:
        return sorted(
            (v for v in self.verdicts if v.state is ArchiveState.DREAMING),
            key=lambda v: (v.layer, v.archive_id),
        )

    @property
    def limbo(self) -> list[Verdict]:
        return sorted(
            (v for v in self.verdicts if v.state is ArchiveState.LIMBO),
            key=lambda v: v.archive_id,
        )

    @property
    def deepest_layer(self) -> int:
        layers = [v.layer for v in self.verdicts if v.layer >= WAKE_LAYER]
        return max(layers) if layers else WAKE_LAYER

    @property
    def duration_s(self) -> float:
        return (self.finished_at or time.time()) - self.started_at

    def verdict_for(self, archive_id: str) -> Verdict | None:
        for v in self.verdicts:
            if v.archive_id == archive_id:
                return v
        return None

    def to_dict(self) -> dict[str, Any]:
        return {
            "protocol": "inception-archive-protocol",
            "version": 1,
            "kicks": self.kicks,
            "duration_s": round(self.duration_s, 3),
            "counts": {
                "total": len(self.verdicts),
                "awake": len(self.awake),
                "dreaming": len(self.dreaming),
                "limbo": len(self.limbo),
            },
            "deepest_layer": self.deepest_layer,
            "verdicts": [v.to_dict() for v in self.verdicts],
        }
