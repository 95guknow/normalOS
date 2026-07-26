"""
Tests for the Inception Archive Protocol.

Written against ``unittest`` rather than pytest on purpose: the protocol
refuses to depend on anything that might be missing, and its tests hold to
the same rule. Run them with

    PYTHONPATH=src python -m unittest discover -s tests -v

The tests that matter most here are the negative ones. A verifier that only
ever confirms things is indistinguishable from one that always says yes, so
each check below also proves the protocol rejects what it should: dreams
that do not reproduce, goals with no code, and support that never reaches
ground.
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from normal_os.protocols.archive import (  # noqa: E402
    _close_over_imports,
    import_roots,
    module_name_for,
    parse_dependencies,
    scan_modules,
)
from normal_os.protocols.distiller import distill, strip_intensifiers  # noqa: E402
from normal_os.protocols.inception import InceptionProtocol  # noqa: E402
from normal_os.protocols.injection import external_imports  # noqa: E402
from normal_os.protocols.models import (  # noqa: E402
    LIMBO_LAYER,
    WAKE_LAYER,
    Archive,
    ArchiveState,
    CodeBacking,
    Distillation,
    TotemState,
)
from normal_os.protocols.runner import genuine_defects  # noqa: E402
from normal_os.protocols.totem import spin  # noqa: E402


def archive(
    archive_id: str,
    source: str | None = "print('ok')",
    *,
    depends_on: tuple[str, ...] = (),
    dream_level: int = WAKE_LAYER,
    acceptance: str | None = "it runs",
) -> Archive:
    """A minimal archive for exercising the engine."""
    distillation = distill(f"Archive {archive_id} works.", acceptance)
    return Archive(
        id=archive_id,
        origin="test",
        kind="test",
        distillation=distillation,
        backing=CodeBacking(source=source) if source and distillation.is_falsifiable else None,
        depends_on=depends_on,
        dream_level=dream_level,
    )


class TestDistiller(unittest.TestCase):
    def test_strips_unverifiable_intensifiers(self):
        core, dropped = strip_intensifiers("Advanced seamless QUBO solving")
        self.assertEqual(core, "QUBO solving")
        self.assertEqual(dropped, ("Advanced", "seamless"))

    def test_keeps_the_checkable_remainder_verbatim(self):
        core, _ = strip_intensifiers("Full Typer CLI")
        self.assertEqual(core, "Typer CLI")

    def test_is_deterministic(self):
        claim = "Comprehensive powerful orchestration"
        self.assertEqual(distill(claim, "x"), distill(claim, "x"))

    def test_acceptance_criterion_produces_a_heroic_goal(self):
        result = distill("Docker ready", "the Dockerfile defines an entrypoint")
        self.assertTrue(result.is_falsifiable)
        self.assertIn("nachweisbar durch", result.heroic_goal or "")

    def test_claim_without_acceptance_criterion_stays_unfalsifiable(self):
        result = distill("Der Stein rollt öffentlich.")
        self.assertIsNone(result.heroic_goal)
        self.assertFalse(result.is_falsifiable)
        # The claim itself is kept -- reduced, never discarded.
        self.assertEqual(result.realistic_core, "Der Stein rollt öffentlich.")

    def test_promised_future_is_not_a_present_fact(self):
        result = distill("Event streaming (planned)", "the endpoint answers")
        self.assertIsNone(result.heroic_goal)

    def test_pure_rhetoric_leaves_no_core(self):
        result = distill("Revolutionary. Groundbreaking. Unprecedented.", "x")
        self.assertEqual(result.realistic_core, "")
        self.assertIsNone(result.heroic_goal)

    def test_empty_claim_is_rejected(self):
        with self.assertRaises(ValueError):
            distill("   ")


class TestTotem(unittest.TestCase):
    def test_reproducible_code_makes_the_totem_fall(self):
        reading = spin(CodeBacking(source="print(sum(range(50)))"), REPO_ROOT)
        self.assertIs(reading.state, TotemState.FELL)
        self.assertTrue(reading.is_real)

    def test_randomness_keeps_the_totem_spinning(self):
        reading = spin(
            CodeBacking(source="import random; print(random.random())"), REPO_ROOT
        )
        self.assertIs(reading.state, TotemState.SPINNING)
        self.assertFalse(reading.is_real)

    def test_hash_order_dependence_keeps_the_totem_spinning(self):
        # Two runs use different PYTHONHASHSEED values, so an answer that
        # depends on set iteration order cannot pass for a fact.
        reading = spin(
            CodeBacking(source="print({'alpha', 'beta', 'gamma', 'delta'})"), REPO_ROOT
        )
        self.assertIs(reading.state, TotemState.SPINNING)

    def test_failing_code_loses_the_totem(self):
        reading = spin(CodeBacking(source="raise SystemExit(3)"), REPO_ROOT)
        self.assertIs(reading.state, TotemState.LOST)

    def test_absent_backing_loses_the_totem(self):
        reading = spin(None, REPO_ROOT)
        self.assertIs(reading.state, TotemState.LOST)
        self.assertIn("no code backing", reading.detail)

    def test_timeout_loses_the_totem(self):
        reading = spin(
            CodeBacking(source="import time; time.sleep(30)", timeout_s=0.5), REPO_ROOT
        )
        self.assertIs(reading.state, TotemState.LOST)
        self.assertIn("did not terminate", reading.detail)

    def test_backing_runs_in_a_fresh_interpreter(self):
        # A name defined only in this process must not be visible to the
        # child; otherwise the check is measuring our memory, not reality.
        globals()["_smuggled_marker"] = 1
        reading = spin(CodeBacking(source="print(_smuggled_marker)"), REPO_ROOT)
        self.assertIs(reading.state, TotemState.LOST)

    def test_empty_backing_is_rejected_at_construction(self):
        with self.assertRaises(ValueError):
            CodeBacking(source="   ")


class TestAscent(unittest.TestCase):
    def test_grounded_archive_wakes_at_layer_zero(self):
        report = InceptionProtocol(REPO_ROOT, [archive("a")]).run()
        verdict = report.verdict_for("a")
        self.assertEqual(verdict.layer, WAKE_LAYER)
        self.assertIs(verdict.state, ArchiveState.ACTIVE)
        self.assertTrue(verdict.is_awake)

    def test_chain_of_grounded_archives_all_wakes(self):
        archives = [
            archive("base"),
            archive("mid", depends_on=("base",)),
            archive("top", depends_on=("mid",)),
        ]
        report = InceptionProtocol(REPO_ROOT, archives).run()
        self.assertEqual(len(report.awake), 3)
        self.assertEqual(report.deepest_layer, WAKE_LAYER)

    def test_archive_resting_on_limbo_falls_to_limbo(self):
        archives = [
            archive("broken", source="raise SystemExit(1)"),
            archive("dependent", depends_on=("broken",)),
        ]
        report = InceptionProtocol(REPO_ROOT, archives).run()
        # Its own backing is fine; what it rests on is not.
        self.assertIs(report.verdict_for("dependent").state, ArchiveState.LIMBO)
        self.assertIn("never reaches ground", report.verdict_for("dependent").reason)

    def test_dream_level_holds_an_archive_above_the_waking_world(self):
        report = InceptionProtocol(REPO_ROOT, [archive("dreamt", dream_level=1)]).run()
        verdict = report.verdict_for("dreamt")
        self.assertEqual(verdict.layer, 1)
        self.assertIs(verdict.state, ArchiveState.DREAMING)
        self.assertFalse(verdict.is_awake)

    def test_resting_on_a_dreamer_puts_you_deeper_still(self):
        archives = [
            archive("dreamer", dream_level=1),
            archive("carried", depends_on=("dreamer",)),
        ]
        report = InceptionProtocol(REPO_ROOT, archives).run()
        self.assertEqual(report.verdict_for("dreamer").layer, 1)
        self.assertEqual(report.verdict_for("carried").layer, 2)
        self.assertEqual(report.deepest_layer, 2)

    def test_support_cycle_never_touches_ground(self):
        archives = [
            archive("x", depends_on=("y",)),
            archive("y", depends_on=("x",)),
        ]
        report = InceptionProtocol(REPO_ROOT, archives).run()
        for archive_id in ("x", "y"):
            verdict = report.verdict_for(archive_id)
            self.assertEqual(verdict.layer, LIMBO_LAYER)
            self.assertIn("support cycle", verdict.reason)

    def test_goal_without_code_stays_in_limbo(self):
        report = InceptionProtocol(REPO_ROOT, [archive("unbacked", source=None)]).run()
        verdict = report.verdict_for("unbacked")
        self.assertIs(verdict.state, ArchiveState.LIMBO)
        self.assertIn("no code", verdict.reason)

    def test_unfalsifiable_claim_is_kept_but_never_asserted(self):
        unfalsifiable = archive("manifesto", source=None, acceptance=None)
        report = InceptionProtocol(REPO_ROOT, [unfalsifiable]).run()
        verdict = report.verdict_for("manifesto")
        self.assertIs(verdict.state, ArchiveState.LIMBO)
        self.assertIn("unfalsifiable", verdict.reason)
        # Kept in the record rather than deleted.
        self.assertIn("manifesto", report.archives)

    def test_ascent_terminates_and_counts_its_kicks(self):
        chain = [archive("n0")]
        chain += [archive(f"n{i}", depends_on=(f"n{i - 1}",)) for i in range(1, 6)]
        report = InceptionProtocol(REPO_ROOT, chain).run()
        self.assertEqual(len(report.awake), 6)
        self.assertGreaterEqual(report.kicks, 1)

    def test_duplicate_archive_ids_are_rejected(self):
        with self.assertRaises(ValueError):
            InceptionProtocol(REPO_ROOT, [archive("dup"), archive("dup")])

    def test_dependency_on_unknown_archive_is_rejected(self):
        with self.assertRaises(ValueError):
            InceptionProtocol(REPO_ROOT, [archive("a", depends_on=("ghost",))])

    def test_backing_for_unfalsifiable_claim_is_rejected(self):
        with self.assertRaises(ValueError):
            Archive(
                id="bad",
                origin="test",
                kind="test",
                distillation=Distillation(
                    raw_claim="x", realistic_core="x", heroic_goal=None
                ),
                backing=CodeBacking(source="print(1)"),
            )


class TestDependencyParsing(unittest.TestCase):
    def _write(self, tmp: Path, relative: str, body: str) -> Path:
        path = tmp / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
        return path

    def test_relative_import_resolves_against_the_parent_package(self):
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            path = self._write(tmp, "pkg/agents/base.py", "from ..core.models import Task\n")
            deps = parse_dependencies(path, "pkg.agents.base", "pkg")
            self.assertEqual(deps, ("pkg.core.models",))

    def test_relative_import_in_package_init_anchors_on_the_package(self):
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            path = self._write(tmp, "pkg/connectors/__init__.py", "from .base import C\n")
            deps = parse_dependencies(
                path, "pkg.connectors", "pkg", is_package=True
            )
            self.assertEqual(deps, ("pkg.connectors.base",))

    def test_import_inside_a_function_is_not_an_import_time_dependency(self):
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            path = self._write(
                tmp, "pkg/lazy.py", "def go():\n    from pkg.heavy import thing\n"
            )
            self.assertEqual(parse_dependencies(path, "pkg.lazy", "pkg"), ())

    def test_main_guard_import_is_not_an_import_time_dependency(self):
        # This is the false cycle the protocol caught in its own source.
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            path = self._write(
                tmp,
                "pkg/tool.py",
                'if __name__ == "__main__":\n    from pkg.runner import main\n',
            )
            self.assertEqual(parse_dependencies(path, "pkg.tool", "pkg"), ())

    def test_unparseable_file_reports_no_dependencies(self):
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            path = self._write(tmp, "pkg/bad.py", "def (:\n")
            self.assertEqual(parse_dependencies(path, "pkg.bad", "pkg"), ())

    def test_module_name_drops_the_init_suffix(self):
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            self._write(tmp, "pkg/sub/__init__.py", "")
            self.assertEqual(
                module_name_for(tmp / "pkg/sub/__init__.py", tmp), "pkg.sub"
            )

    def test_import_roots_reports_top_level_names(self):
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            path = self._write(
                tmp, "pkg/m.py", "import os\nfrom pydantic import BaseModel\n"
            )
            self.assertEqual(import_roots(path), {"os", "pydantic"})


class TestInjection(unittest.TestCase):
    def test_stdlib_and_in_tree_are_never_stubbed(self):
        found = external_imports({"os", "sys", "json", "normal_os", "pydantic", "httpx"})
        self.assertEqual(found, ("httpx", "pydantic"))

    def test_third_party_imports_propagate_along_the_in_tree_graph(self):
        # 'leaf' imports nothing external itself, but importing it imports
        # 'core', which needs pydantic. Its dream must include pydantic or
        # the injection collapses for exactly the reason it exists.
        closure = _close_over_imports(
            in_tree_deps={"leaf": ("core",), "core": ()},
            direct_external={"leaf": (), "core": ("pydantic",)},
        )
        self.assertEqual(closure["leaf"], ("pydantic",))

    def test_closure_survives_an_import_cycle(self):
        closure = _close_over_imports(
            in_tree_deps={"a": ("b",), "b": ("a",)},
            direct_external={"a": ("httpx",), "b": ("structlog",)},
        )
        self.assertEqual(closure["a"], ("httpx", "structlog"))

    def test_injected_dream_reveals_a_defect_a_missing_package_would_hide(self):
        # The module below is broken on every machine that has ever run
        # Python -- but a missing 'pydantic' would report only the missing
        # package and the real defect would never surface.
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            src = tmp / "src" / "brokenpkg"
            src.mkdir(parents=True)
            (src / "__init__.py").write_text("", encoding="utf-8")
            (src / "models.py").write_text(
                "from typing import Literal\n"
                "from pydantic import BaseModel\n"
                "class Status(str, Literal):\n"
                "    OK = 'ok'\n",
                encoding="utf-8",
            )
            archives = scan_modules(tmp / "src", package="brokenpkg")
            dream = next(a for a in archives if a.id == "dream:brokenpkg.models")
            reading = spin(dream.backing, tmp)
            self.assertIs(reading.state, TotemState.LOST)
            self.assertIn("Literal", reading.detail)

    def test_module_that_only_lacks_a_package_holds_inside_the_dream(self):
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            src = tmp / "src" / "okpkg"
            src.mkdir(parents=True)
            (src / "__init__.py").write_text("", encoding="utf-8")
            (src / "svc.py").write_text(
                "from pydantic import BaseModel\n"
                "class Thing(BaseModel):\n"
                "    pass\n"
                "def go():\n"
                "    return 1\n",
                encoding="utf-8",
            )
            archives = scan_modules(tmp / "src", package="okpkg")
            dream = next(a for a in archives if a.id == "dream:okpkg.svc")
            self.assertIs(spin(dream.backing, tmp).state, TotemState.FELL)
            # And the real import genuinely fails, which is the contrast
            # that makes the dream result meaningful.
            real = next(a for a in archives if a.id == "module:okpkg.svc")
            self.assertIs(spin(real.backing, tmp).state, TotemState.LOST)


class TestScanner(unittest.TestCase):
    def test_scan_produces_source_and_module_tiers(self):
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            src = tmp / "src" / "tinypkg"
            src.mkdir(parents=True)
            (src / "__init__.py").write_text("", encoding="utf-8")
            (src / "pure.py").write_text("VALUE = 1\n", encoding="utf-8")

            archives = {a.id: a for a in scan_modules(tmp / "src", package="tinypkg")}
            self.assertIn("source:tinypkg.pure", archives)
            self.assertIn("module:tinypkg.pure", archives)
            # No third-party imports, so there is no dream to inject.
            self.assertNotIn("dream:tinypkg.pure", archives)
            # The real import rests on the file being real Python.
            self.assertIn(
                "source:tinypkg.pure", archives["module:tinypkg.pure"].depends_on
            )

    def test_dependency_free_module_wakes_end_to_end(self):
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            src = tmp / "src" / "tinypkg"
            src.mkdir(parents=True)
            (src / "__init__.py").write_text("", encoding="utf-8")
            (src / "pure.py").write_text("VALUE = 1\n", encoding="utf-8")

            report = InceptionProtocol(tmp, scan_modules(tmp / "src", package="tinypkg")).run()
            self.assertTrue(report.verdict_for("module:tinypkg.pure").is_awake)
            self.assertEqual(report.limbo, [])

    def test_malformed_source_cannot_reach_the_waking_world(self):
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            src = tmp / "src" / "tinypkg"
            src.mkdir(parents=True)
            (src / "__init__.py").write_text("", encoding="utf-8")
            (src / "bad.py").write_text("def (:\n", encoding="utf-8")

            report = InceptionProtocol(tmp, scan_modules(tmp / "src", package="tinypkg")).run()
            self.assertIs(
                report.verdict_for("source:tinypkg.bad").state, ArchiveState.LIMBO
            )
            # And nothing built on it may wake either.
            self.assertIs(
                report.verdict_for("module:tinypkg.bad").state, ArchiveState.LIMBO
            )


class TestReporting(unittest.TestCase):
    def test_genuine_defects_are_separated_from_environment_failures(self):
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            src = tmp / "src" / "mixedpkg"
            src.mkdir(parents=True)
            (src / "__init__.py").write_text("", encoding="utf-8")
            # Only needs a package it does not have -> environment.
            (src / "fine.py").write_text(
                "from pydantic import BaseModel\nVALUE = 1\n", encoding="utf-8"
            )
            # Broken regardless of any package -> genuine defect.
            (src / "broken.py").write_text(
                "from typing import Literal\n"
                "from pydantic import BaseModel\n"
                "class S(str, Literal):\n    A = 'a'\n",
                encoding="utf-8",
            )

            report = InceptionProtocol(tmp, scan_modules(tmp / "src", package="mixedpkg")).run()
            defects = dict(genuine_defects(report))
            self.assertIn("mixedpkg.broken", defects)
            self.assertNotIn("mixedpkg.fine", defects)

    def test_report_serialises_to_json_safe_primitives(self):
        import json

        report = InceptionProtocol(REPO_ROOT, [archive("a")]).run()
        json.dumps(report.to_dict())  # must not raise
        self.assertEqual(report.to_dict()["counts"]["awake"], 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
