"""Execute every docstring example in the package."""

import doctest
import importlib
import pkgutil
import sys

import tacular

# Measured 2026-11-08: 76 modules (63 plus the 13 generated data modules), 10 examples
# in tolerance.py (4), obo_lookup.py (3), constants.py (2) and types.py (1).
# Raise these when you add modules or examples; never lower them without saying why in
# the commit message.
MIN_MODULES = 76
MIN_EXAMPLES = 10

# Modules that cannot be imported in the test environment, by name, with the reason.
# Empty on purpose: tacular has no runtime dependencies and no optional extras, so
# every module imports everywhere the tests run.
SKIP_MODULES: frozenset[str] = frozenset()

# Importing this one leaves tacular.__main__ in sys.modules, which makes runpy warn in
# tests/test_update_cli.py::test_main_module_runs_in_process (measured 2026-11-08:
# RuntimeWarning, "found in sys.modules after import of package"). It is walked and
# counted like every other module, and only the sys.modules entry this test added is
# removed afterwards.
_UNIMPORT_AFTER = "tacular.__main__"


def _raise(name: str) -> None:
    """Fail the walk instead of letting pkgutil drop an unimportable package.

    A name in ``SKIP_MODULES`` is excluded on purpose, so its import error is the
    documented outcome rather than a failure.
    """
    if name in SKIP_MODULES:
        return
    raise ImportError(f"could not import package {name} during the module walk")


def _all_modules():
    mods = [tacular]
    for _finder, name, _ispkg in pkgutil.walk_packages(tacular.__path__, prefix=f"{tacular.__name__}.", onerror=_raise):
        if name in SKIP_MODULES:
            continue
        mods.append(importlib.import_module(name))
    return mods


def test_docstring_examples():
    was_imported = _UNIMPORT_AFTER in sys.modules
    try:
        mods = _all_modules()
        assert len(mods) >= MIN_MODULES, f"module walk found only {len(mods)}"
        attempted = failed = 0
        for mod in mods:
            result = doctest.testmod(mod, verbose=False)
            attempted += result.attempted
            failed += result.failed
        assert failed == 0, f"{failed} of {attempted} docstring examples failed"
        assert attempted >= MIN_EXAMPLES, f"only {attempted} examples ran, expected >= {MIN_EXAMPLES}"
    finally:
        if not was_imported:
            sys.modules.pop(_UNIMPORT_AFTER, None)
