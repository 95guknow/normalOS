"""
Dream injection.

A module that fails to import because ``pydantic`` is not installed has told
us nothing about itself -- only about the machine it ran on. To find out
whether its own logic holds, we build it a dream: every absent third-party
package is replaced by a permissive stub, and the module is imported inside
that constructed reality.

What the two outcomes mean
--------------------------
Imports for real            -> the module is awake. Layer 0.
Imports only under stubs    -> the module is coherent, but only inside a
                               dream someone built for it. Layer 1.
Fails even under stubs      -> the defect is in the module's own code. No
                               environment will fix it. Limbo.

That last case is the valuable one, and it is why this exists. It finds
defects that a missing-dependency error would otherwise hide forever --
code that has never once run, in any environment, and never could.

Only packages that are genuinely absent are stubbed. Anything really
installed is imported for real, so injection can never mask a defect in
code that had a working dependency available to it.
"""

from __future__ import annotations

import sys

#: Import-time machinery for the injected dream. This is emitted verbatim
#: into the probe program, so it must stand alone with no imports beyond
#: the standard library.
INJECTION_PRELUDE = '''
import importlib.util as _ilu
import sys as _sys
import types as _types

_STUB_TARGETS = {targets!r}


def _absent(name):
    """True when a package genuinely cannot be found on this machine."""
    root = name.split(".")[0]
    if root in _sys.modules:
        return False
    try:
        return _ilu.find_spec(root) is None
    except (ImportError, ValueError):
        return True


class _Stub:
    """
    Stands in for any object an absent package would have provided.

    It can be subclassed (so ``class Task(BaseModel)`` works), called (so
    ``Field(default_factory=list)`` works), used as a decorator (so
    ``@app.get("/x")`` works), and subscripted (so ``Optional[str]``
    works). It does exactly enough to let import-time code complete.
    """

    def __init__(self, *args, **kwargs):
        pass

    def __call__(self, *args, **kwargs):
        # Bare decorator use: @something -> hand the function straight back
        # so the name it defines survives.
        if len(args) == 1 and not kwargs and callable(args[0]):
            return args[0]
        return _Stub()

    def __getattr__(self, name):
        if name.startswith("__") and name.endswith("__"):
            raise AttributeError(name)
        return _Stub()

    def __class_getitem__(cls, item):
        return cls

    def __iter__(self):
        return iter(())

    def __bool__(self):
        return True


class _StubModule(_types.ModuleType):
    """A module whose every attribute is a fresh stub class."""

    def __getattr__(self, name):
        if name.startswith("__") and name.endswith("__"):
            raise AttributeError(name)
        made = type(name, (_Stub,), {{"__module__": self.__name__}})
        setattr(self, name, made)
        return made


class _StubFinder:
    """Resolves only the packages we decided are absent."""

    def __init__(self, roots):
        self.roots = set(roots)

    def find_module(self, fullname, path=None):  # legacy API, unused
        return None

    def find_spec(self, fullname, path=None, target=None):
        root = fullname.split(".")[0]
        if root not in self.roots:
            return None
        spec = _ilu.spec_from_loader(fullname, _StubLoader())
        spec.submodule_search_locations = []
        return spec


class _StubLoader:
    def create_module(self, spec):
        module = _StubModule(spec.name)
        module.__path__ = []
        return module

    def exec_module(self, module):
        return None


_STUBBED = sorted(name for name in _STUB_TARGETS if _absent(name))
if _STUBBED:
    _sys.meta_path.insert(0, _StubFinder(_STUBBED))
'''


def stdlib_roots() -> frozenset[str]:
    """Top-level names that ship with Python and must never be stubbed."""
    return frozenset(sys.stdlib_module_names)


def external_imports(
    import_roots: set[str], *, in_tree_prefix: str = "normal_os"
) -> tuple[str, ...]:
    """
    Reduce a module's import roots to the third-party packages among them.

    Standard library and in-tree modules are excluded: neither is a
    candidate for stubbing, because neither can be missing without the
    problem being the code's own.
    """
    stdlib = stdlib_roots()
    return tuple(
        sorted(
            root
            for root in import_roots
            if root
            and root != in_tree_prefix
            and not root.startswith(f"{in_tree_prefix}.")
            and root not in stdlib
        )
    )


def build_injected_probe(module: str, targets: tuple[str, ...]) -> str:
    """
    A probe that imports ``module`` inside an injected dream.

    It prints which packages had to be invented, then the module's public
    surface. Both are sorted, so the output is identical across runs and
    the totem can tell reproducible success from luck.
    """
    prelude = INJECTION_PRELUDE.format(targets=list(targets))
    return (
        prelude
        + "\n"
        + "import importlib\n"
        + f"_module = importlib.import_module({module!r})\n"
        + "print('injected', ' '.join(_STUBBED) or '-')\n"
        + f"print({module!r})\n"
        + "_surface = sorted(n for n in dir(_module) if not n.startswith('_'))\n"
        + "print(len(_surface))\n"
        + "for _name in _surface:\n"
        + "    print(_name)\n"
    )
