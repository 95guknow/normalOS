"""
Entry point for the Inception Archive Protocol.

    python -m normal_os.protocols.inception [--root PATH] [--json OUT] [--markdown OUT]

Prints what is awake, what is dreaming and why, and what is in limbo. The
exit code answers one question only: did the first layer wake? It is 0 when
at least one archive reached layer 0 and the protocol itself is among them,
and 1 otherwise -- because a protocol that cannot verify itself has no
standing to report on anything else.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .inception import InceptionProtocol, write_json_report
from .manifest import build_manifest
from .models import ArchiveState, InceptionReport, TotemState

SELF_ARCHIVE = "claim:inception-protocol"

_STATE_MARK = {
    ArchiveState.ACTIVE: "WACH ",
    ArchiveState.DREAMING: "TRAUM",
    ArchiveState.LIMBO: "LIMBO",
}

_TOTEM_MARK = {
    TotemState.FELL: "totem fiel",
    TotemState.SPINNING: "totem dreht",
    TotemState.LOST: "totem verloren",
}


def genuine_defects(report: InceptionReport) -> list[tuple[str, str]]:
    """
    The defects that belong to normalOS itself, not to the machine.

    A module archive in limbo says only that the module did not import
    here. Cross-referencing it with its dream archive says why: if the
    module holds once absent packages are stubbed, the environment was at
    fault and installing them fixes it. If it fails even inside the dream,
    the code is broken on every machine there has ever been, and no install
    will help. Those are the ones worth a developer's attention, so they
    are reported apart from the noise.

    Returns ``(module, failure)`` pairs, sorted.
    """
    defects: list[tuple[str, str]] = []
    for verdict in report.limbo:
        if not verdict.archive_id.startswith("dream:"):
            continue
        archive = report.archives[verdict.archive_id]
        module = archive.metadata.get("module", verdict.archive_id)
        detail = verdict.totem.detail
        defects.append((str(module), detail.replace("backing failed: ", "")))
    return sorted(defects)


def render_text(report: InceptionReport) -> str:
    """Human-readable summary for the terminal."""
    out: list[str] = []
    add = out.append

    awake, dreaming, limbo = report.awake, report.dreaming, report.limbo
    total = len(report.verdicts)

    add("=" * 78)
    add("INCEPTION ARCHIVE PROTOCOL")
    add("=" * 78)
    add(
        f"{total} Archive | {len(awake)} wach | {len(dreaming)} träumend | "
        f"{len(limbo)} Limbo | {report.kicks} Kicks | {report.duration_s:.1f}s"
    )
    add("")

    add(f"-- LAYER 0 — DIE WACHE WELT ({len(awake)}) " + "-" * 30)
    add("Nur diese Archive dürfen behauptet werden.")
    add("")
    for verdict in awake:
        archive = report.archives[verdict.archive_id]
        add(f"  [{_STATE_MARK[verdict.state]}] {verdict.archive_id}")
        if archive.kind == "claim":
            add(f"          Ziel: {archive.distillation.heroic_goal}")
    add("")

    if dreaming:
        add(f"-- TIEFERE LAYER — GETRAGEN VON TRÄUMERN ({len(dreaming)}) " + "-" * 14)
        for verdict in dreaming:
            add(f"  [{_STATE_MARK[verdict.state]}] L{verdict.layer}  {verdict.archive_id}")
            add(f"          {verdict.reason}")
        add("")

    if limbo:
        add(f"-- LIMBO — KEIN BODEN DARUNTER ({len(limbo)}) " + "-" * 25)
        add("Nichts hiervon wird gelöscht. Es wird nur nicht mehr für Realität gehalten.")
        add("")
        unfalsifiable = [
            v
            for v in limbo
            if not report.archives[v.archive_id].distillation.is_falsifiable
        ]
        failed = [v for v in limbo if v not in unfalsifiable]

        for verdict in failed:
            archive = report.archives[verdict.archive_id]
            add(f"  [{_STATE_MARK[verdict.state]}] {verdict.archive_id}")
            add(f"          {_TOTEM_MARK[verdict.totem.state]}: {verdict.reason}")
            if archive.distillation.heroic_goal:
                add(f"          Heroisches Ziel bleibt: {archive.distillation.heroic_goal}")
        if unfalsifiable:
            add("")
            add("  Unfalsifizierbar — kein Prüfkriterium formulierbar, daher kein Code:")
            for verdict in unfalsifiable:
                archive = report.archives[verdict.archive_id]
                add(f"    - {verdict.archive_id}: „{archive.distillation.realistic_core}“")
        add("")

    defects = genuine_defects(report)
    if defects:
        add(f"-- ECHTE DEFEKTE ({len(defects)}) " + "-" * 45)
        add("Scheitert auch im injizierten Traum: der Fehler liegt im Code selbst,")
        add("nicht an fehlenden Paketen. Kein pip install repariert das hier.")
        add("")
        for module, failure in defects:
            add(f"  {module}")
            add(f"      {failure}")
        add("")

    self_verdict = report.verdict_for(SELF_ARCHIVE)
    add("=" * 78)
    if self_verdict and self_verdict.is_awake:
        add("Das Protokoll hat sich selbst verifiziert. Der erste Träumer ist wach.")
    else:
        add("Das Protokoll konnte sich selbst NICHT verifizieren.")
        if self_verdict:
            add(f"  {self_verdict.reason}")
    add("=" * 78)
    return "\n".join(out)


def render_markdown(report: InceptionReport) -> str:
    """Report suitable for committing next to the code."""
    out: list[str] = []
    add = out.append

    add("# Inception Archive Protocol — Report")
    add("")
    add(
        f"**{len(report.awake)} wach · {len(report.dreaming)} träumend · "
        f"{len(report.limbo)} Limbo** — {report.kicks} Kicks, "
        f"{report.duration_s:.1f}s, tiefstes Layer {report.deepest_layer}."
    )
    add("")
    add(
        "Ein Archiv erreicht Layer 0, wenn sein eigener Code reproduzierbar läuft "
        "*und* alles, worauf es ruht, ebenfalls wach ist. Nur Layer 0 darf "
        "behauptet werden."
    )
    add("")

    add("## Layer 0 — die wache Welt")
    add("")
    add("| Archiv | Art | Heroisches Ziel |")
    add("| --- | --- | --- |")
    for verdict in report.awake:
        archive = report.archives[verdict.archive_id]
        goal = archive.distillation.heroic_goal or "—"
        add(f"| `{verdict.archive_id}` | {archive.kind} | {goal} |")
    add("")

    if report.dreaming:
        add("## Tiefere Layer — noch von Träumern getragen")
        add("")
        add("| Archiv | Layer | Grund |")
        add("| --- | --- | --- |")
        for verdict in report.dreaming:
            add(f"| `{verdict.archive_id}` | {verdict.layer} | {verdict.reason} |")
        add("")

    defects = genuine_defects(report)
    if defects:
        add("## Echte Defekte")
        add("")
        add(
            "Diese Module scheitern auch dann, wenn alle fehlenden Pakete als Stub "
            "injiziert werden. Der Fehler liegt im Code selbst und ist auf jeder "
            "Maschine derselbe — kein `pip install` behebt ihn."
        )
        add("")
        add("| Modul | Fehler |")
        add("| --- | --- |")
        for module, failure in defects:
            add(f"| `{module}` | {failure} |")
        add("")

    if report.limbo:
        add("## Limbo — kein Boden darunter")
        add("")
        add(
            "Behalten, nicht gelöscht. Jedes Ziel bleibt formuliert und kann "
            "jederzeit mit echtem Code unterfüttert werden."
        )
        add("")
        add("| Archiv | Totem | Grund |")
        add("| --- | --- | --- |")
        for verdict in report.limbo:
            add(
                f"| `{verdict.archive_id}` | {_TOTEM_MARK[verdict.totem.state]} "
                f"| {verdict.reason} |"
            )
        add("")

    return "\n".join(out) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="inception",
        description="Activate the normalOS archives by waking them to layer 0.",
    )
    parser.add_argument(
        "--root",
        default=None,
        help="repository root (default: inferred from this file's location)",
    )
    parser.add_argument("--json", dest="json_out", default=None, help="write JSON report here")
    parser.add_argument(
        "--markdown", dest="md_out", default=None, help="write Markdown report here"
    )
    parser.add_argument(
        "--workers", type=int, default=4, help="how many totems to spin at once"
    )
    parser.add_argument(
        "--quiet", action="store_true", help="suppress the terminal report"
    )
    args = parser.parse_args(argv)

    # src/normal_os/protocols/runner.py -> repository root is four levels up.
    root = Path(args.root).resolve() if args.root else Path(__file__).resolve().parents[3]

    archives = build_manifest(root)
    protocol = InceptionProtocol(root, archives, max_workers=args.workers)
    report = protocol.run()

    if not args.quiet:
        print(render_text(report))

    if args.json_out:
        written = write_json_report(report, args.json_out)
        print(f"\nJSON report: {written}")

    if args.md_out:
        md_path = Path(args.md_out)
        md_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.write_text(render_markdown(report), encoding="utf-8")
        print(f"Markdown report: {md_path}")

    self_verdict = report.verdict_for(SELF_ARCHIVE)
    woke = bool(report.awake) and self_verdict is not None and self_verdict.is_awake
    return 0 if woke else 1


if __name__ == "__main__":  # pragma: no cover - entry point
    sys.exit(main())
