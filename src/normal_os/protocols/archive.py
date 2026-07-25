"""
Archive discovery.

An *archive* is one unit of the mesh that the protocol can wake: a Python
module, a documented claim, a shipped script. This module finds the module
archives automatically -- every ``.py`` file under the source tree becomes
an archive whose heroic goal is the plainest one available:

    this module can be imported, and its public surface is stable.

That goal is backed by code that imports the module in a fresh interpreter
and prints its sorted public names. A module that only imports because
something else already imported it, or whose surface shifts between runs,
fails that check. It is a low bar deliberately -- a module that cannot
clear it cannot support anything built on top of it.

Dependency edges come from the import statements themselves, parsed with
``ast`` rather than executed. Reading a module's imports must not run it:
half the point of the protocol is to judge modules that are unsafe to run.
"""

from __future__ import annotations

import ast
import hashlib
from pathlib import Path
from typing import Iterator

from .distiller import distill
from .injection import build_injected_probe, external_imports
from .models import Archive, CodeBacking

#: Directories that are never archives of the system itself.
SKIP_DIRS = frozenset(
    {".git", "__pycache__", ".venv", "venv", "node_modules", ".mypy_cache",
     ".ruff_cache", ".pytest_cache", "build", "dist", ".eggs"}
)

MODULE_IMPORT_TIMEOUT_S = 30.0


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def iter_python_files(src_root: Path) -> Iterator[Path]:
    """Yield every Python file under ``src_root``, skipping build noise."""
    for path in sorted(src_root.rglob("*.py")):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        yield path


def module_name_for(path: Path, src_root: Path) -> str:
    """Dotted module name for a file inside the source root."""
    relative = path.relative_to(src_root).with_suffix("")
    parts = list(relative.parts)
    if parts and parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def parse_dependencies(
    path: Path, module: str, known_prefix: str, *, is_package: bool = False
) -> tuple[str, ...]:
    """
    Extract the in-tree modules this module imports, without executing it.

    Relative imports resolve against the module's anchor package, so
    ``from ..core.models import Task`` inside ``normal_os.agents.base``
    yields ``normal_os.core.models``. For a package's ``__init__``, the
    anchor is the package itself rather than its parent -- ``from .base
    import Connector`` in ``normal_os/connectors/__init__.py`` yields
    ``normal_os.connectors.base``, not ``normal_os.base``.
    """
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"), filename=str(path))
    except SyntaxError:
        # A module that does not even parse has no dependencies worth
        # tracking -- its own totem will report the failure.
        return ()

    parts = module.split(".")
    anchor = parts if is_package else parts[:-1]
    found: set[str] = set()

    for node in _import_time_nodes(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith(known_prefix):
                    found.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                keep = len(anchor) - node.level + 1
                if keep < 0:
                    # Reaches above the tree root; not resolvable in-tree.
                    continue
                base = anchor[:keep]
                target = ".".join([*base, node.module]) if node.module else ".".join(base)
            else:
                target = node.module or ""
            if target.startswith(known_prefix):
                found.add(target)

    found.discard(module)
    return tuple(sorted(found))


def _is_main_guard(node: ast.stmt) -> bool:
    """True for ``if __name__ == "__main__":`` -- not executed on import."""
    if not isinstance(node, ast.If):
        return False
    test = node.test
    return (
        isinstance(test, ast.Compare)
        and isinstance(test.left, ast.Name)
        and test.left.id == "__name__"
        and len(test.comparators) == 1
        and isinstance(test.comparators[0], ast.Constant)
        and test.comparators[0].value == "__main__"
    )


def _import_time_nodes(tree: ast.Module) -> Iterator[ast.stmt]:
    """
    Yield the statements that actually run when the module is imported.

    Imports nested inside a function or class body do not run at import
    time, and imports under ``if __name__ == "__main__"`` never run on
    import at all. Counting either as a dependency invents edges that the
    interpreter would never follow -- which is how a perfectly fine module
    ends up accused of sitting in a support cycle.
    """
    stack: list[ast.stmt] = list(tree.body)
    while stack:
        node = stack.pop()
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        if _is_main_guard(node):
            continue
        yield node
        for field_name in ("body", "orelse", "finalbody"):
            stack.extend(getattr(node, field_name, []) or [])
        for handler in getattr(node, "handlers", []) or []:
            stack.extend(handler.body)


def import_roots(path: Path) -> set[str]:
    """Top-level package names this module imports at import time."""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"), filename=str(path))
    except SyntaxError:
        return set()

    roots: set[str] = set()
    for node in _import_time_nodes(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                roots.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and not node.level and node.module:
            roots.add(node.module.split(".")[0])
    return roots


def _import_probe(module: str) -> str:
    """
    Source of the backing that proves a module is real.

    It imports the module and prints its sorted public surface. Sorting
    matters: an unsorted ``dir()`` would vary with hash seed and every
    module would look like a dream.
    """
    return (
        "import importlib\n"
        f"module = importlib.import_module({module!r})\n"
        "surface = sorted(n for n in dir(module) if not n.startswith('_'))\n"
        f"print({module!r})\n"
        "print(len(surface))\n"
        "for name in surface:\n"
        "    print(name)\n"
    )


def _parse_probe(relative: str) -> str:
    """
    Source of the backing that proves a file is at least real Python.

    This needs nothing installed, so it is the one check that separates a
    genuinely malformed file from a machine that is merely missing a
    package. It prints a structural fingerprint -- statement count and the
    sorted names the module defines -- so a silent rewrite cannot pass.
    """
    return (
        "import ast\n"
        f"source = open({relative!r}, encoding='utf-8').read()\n"
        f"tree = ast.parse(source, filename={relative!r})\n"
        "names = sorted({node.name for node in ast.walk(tree)\n"
        "                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef,\n"
        "                                     ast.ClassDef))})\n"
        f"print({relative!r})\n"
        "print(len(tree.body), len(names))\n"
        "for name in names:\n"
        "    print(name)\n"
    )


def _close_over_imports(
    in_tree_deps: dict[str, tuple[str, ...]],
    direct_external: dict[str, tuple[str, ...]],
) -> dict[str, tuple[str, ...]]:
    """
    Propagate third-party imports along the in-tree import graph.

    Importing a module imports everything it imports, so a module with no
    third-party imports of its own still fails on ``pydantic`` if one of
    its in-tree dependencies needs it. A dream built only from a module's
    direct imports collapses the moment that happens, which makes the whole
    injection useless. So each module is stubbed against the closure of
    everything reachable from it.

    Import cycles are traversed once via the visited set, so a cycle in the
    tree cannot spin this forever.
    """
    closure: dict[str, tuple[str, ...]] = {}
    for module in in_tree_deps:
        seen: set[str] = set()
        stack = [module]
        roots: set[str] = set()
        while stack:
            current = stack.pop()
            if current in seen:
                continue
            seen.add(current)
            roots.update(direct_external.get(current, ()))
            stack.extend(in_tree_deps.get(current, ()))
        closure[module] = tuple(sorted(roots))
    return closure


def scan_modules(
    src_root: Path | str,
    *,
    package: str = "normal_os",
    id_prefix: str = "module:",
    source_prefix: str = "source:",
    dream_prefix: str = "dream:",
) -> list[Archive]:
    """
    Build the archives for every Python module under ``src_root``.

    Each module yields up to three archives, and the split is what makes
    the layer report say something useful instead of "nothing works":

    ``source:<module>``
        The file parses as Python. Needs nothing installed, so it can reach
        layer 0 on any machine. A failure here is a defect, full stop.

    ``module:<module>``
        The module imports for real, against the actual environment, and
        exposes a stable public surface. This is the only module archive
        that can reach the waking world.

    ``dream:<module>``
        Built only for modules that import third-party packages. It imports
        the module with the absent ones stubbed out. Verified inside a
        constructed dream, so it carries ``dream_level=1`` and can never
        pass for reality -- but when it holds while ``module:`` fails, the
        cause was the environment; when it fails too, the defect is in the
        code itself and always was.
    """
    src_root = Path(src_root)
    if not src_root.is_dir():
        raise FileNotFoundError(f"source root does not exist: {src_root}")

    files = list(iter_python_files(src_root))
    names = {module_name_for(path, src_root): path for path in files}
    names.pop("", None)

    # First pass: resolve the in-tree import graph and each module's own
    # third-party imports, without executing anything.
    in_tree_deps: dict[str, tuple[str, ...]] = {}
    direct_external: dict[str, tuple[str, ...]] = {}
    for module, path in names.items():
        deps = parse_dependencies(
            path, module, package, is_package=(path.name == "__init__.py")
        )
        in_tree_deps[module] = tuple(d for d in deps if d in names)
        direct_external[module] = external_imports(
            import_roots(path), in_tree_prefix=package
        )

    transitive_external = _close_over_imports(in_tree_deps, direct_external)

    archives: list[Archive] = []
    for module, path in sorted(names.items()):
        # Only depend on modules that are themselves archives here; an
        # import of something outside the tree is the module's own problem
        # and shows up when its totem is spun.
        in_tree = tuple(f"{id_prefix}{d}" for d in in_tree_deps[module])

        relative = path.relative_to(src_root)
        # Probes run with the repository root as their working directory,
        # so file paths must be addressed from there, not from src/.
        from_root = Path(src_root.name) / relative if src_root.name else relative
        source_id = f"{source_prefix}{module}"
        digest = sha256_file(path)
        line_count = len(path.read_bytes().splitlines())

        archives.append(
            Archive(
                id=source_id,
                origin=str(relative),
                kind="source",
                distillation=distill(
                    f"The file {relative} is well-formed Python.",
                    "parse the file with ast in a fresh interpreter and read a "
                    "stable set of defined names",
                ),
                backing=CodeBacking(
                    source=_parse_probe(str(from_root)), timeout_s=MODULE_IMPORT_TIMEOUT_S
                ),
                sha256=digest,
                metadata={"module": module, "lines": line_count},
            )
        )

        archives.append(
            Archive(
                id=f"{id_prefix}{module}",
                origin=str(relative),
                kind="module",
                distillation=distill(
                    f"Module {module} is a working part of normalOS.",
                    f"import {module} in a fresh interpreter and read a stable "
                    "public surface",
                ),
                backing=CodeBacking(
                    source=_import_probe(module), timeout_s=MODULE_IMPORT_TIMEOUT_S
                ),
                depends_on=(source_id, *in_tree),
                sha256=digest,
                metadata={"module": module, "lines": line_count},
            )
        )

        third_party = transitive_external[module]
        if third_party:
            archives.append(
                Archive(
                    id=f"{dream_prefix}{module}",
                    origin=str(relative),
                    kind="dream",
                    distillation=distill(
                        f"Module {module} holds together once {', '.join(third_party)} "
                        "is dreamt up for it.",
                        f"import {module} with absent packages stubbed and read a "
                        "stable public surface",
                    ),
                    backing=CodeBacking(
                        source=build_injected_probe(module, third_party),
                        timeout_s=MODULE_IMPORT_TIMEOUT_S,
                    ),
                    depends_on=(source_id,),
                    sha256=digest,
                    dream_level=1,
                    metadata={"module": module, "stubbed": list(third_party)},
                )
            )

    return archives
