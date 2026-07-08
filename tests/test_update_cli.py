"""Tests for the `tacular` CLI (src/tacular/update.py, __main__.py)."""

import logging
import subprocess
import sys
from pathlib import Path

import pytest

from tacular import _cache
from tacular import update as update_mod

REPO = Path(__file__).resolve().parent.parent
OBO_DIR = REPO / "data_gen" / "data"


@pytest.fixture(autouse=True)
def isolated_cache(tmp_path, monkeypatch):
    """Every test in this file gets its own empty cache dir."""
    monkeypatch.setenv(_cache.ENV_DATA_DIR, str(tmp_path))
    monkeypatch.delenv(_cache.ENV_DISABLE, raising=False)
    return tmp_path


@pytest.fixture(autouse=True)
def restore_root_logger():
    # Every test in this file calls main(), which calls _configure_logging() ->
    # logging.basicConfig(force=True) -- that replaces the root logger's handlers
    # process-wide (including pytest's own caplog handler). Restore afterwards so
    # other test files in this session aren't affected by test ordering.
    root = logging.getLogger()
    handlers, level = list(root.handlers), root.level
    yield
    root.handlers[:] = handlers
    root.setLevel(level)


@pytest.mark.parametrize(
    "verbosity,expected_level",
    [(0, 30), (1, 20), (2, 10), (3, 10)],  # WARNING, INFO, DEBUG, DEBUG (caps at -vv)
)
def test_configure_logging_maps_verbosity_to_level(verbosity, expected_level):
    update_mod._configure_logging(verbosity)
    assert logging.getLogger().getEffectiveLevel() == expected_level


def test_cli_requires_a_subcommand():
    with pytest.raises(SystemExit):
        update_mod.main([])


def test_cli_where_prints_cache_dir(capsys):
    rc = update_mod.main(["where"])
    assert rc == 0
    assert str(_cache.cache_dir()) in capsys.readouterr().out


def test_cli_status_runs_with_no_cache(capsys):
    rc = update_mod.main(["status"])
    assert rc == 0
    out = capsys.readouterr().out
    for name in update_mod.ONTOLOGIES:
        assert name in out
    assert "cache enabled" in out


def test_cli_status_reports_disabled_cache(monkeypatch, capsys):
    monkeypatch.setenv(_cache.ENV_DISABLE, "1")
    rc = update_mod.main(["status"])
    assert rc == 0
    assert "cache DISABLED" in capsys.readouterr().out


def test_cli_status_reports_cached_entries(tmp_path, capsys):
    from tacular.unimod.dclass import UnimodInfo

    info = UnimodInfo("1", "Test", "C", 12.0, 12.01, {"C": 1})
    _cache.save("unimodifications.json", "unimodifications", [info], "v1")
    rc = update_mod.main(["status"])
    assert rc == 0
    out = capsys.readouterr().out
    lines = [line for line in out.splitlines() if line.startswith("unimod")]
    assert lines and lines[0].split()[1] == "yes"


def test_cli_clear_with_nothing_cached(capsys):
    rc = update_mod.main(["clear"])
    assert rc == 0
    assert "no cached data to remove" in capsys.readouterr().out


def test_cli_clear_removes_cache(tmp_path, capsys):
    from tacular.unimod.dclass import UnimodInfo

    info = UnimodInfo("1", "Test", "C", 12.0, 12.01, {"C": 1})
    path = _cache.save("unimodifications.json", "unimodifications", [info], "v1")
    assert path.is_file()

    rc = update_mod.main(["clear"])
    assert rc == 0
    assert "removed cached data" in capsys.readouterr().out
    assert not path.is_file()


def test_cli_update_rejects_unknown_ontology(capsys):
    rc = update_mod.main(["update", "not-a-real-ontology"])
    assert rc == 1
    assert "unknown ontologies" in capsys.readouterr().err


def test_cli_update_offline_missing_obo_errors(tmp_path, capsys):
    rc = update_mod.main(["update", "unimod", "--offline", str(tmp_path)])
    assert rc == 1
    assert "not found" in capsys.readouterr().err


def test_cli_update_offline_success(capsys):
    if not (OBO_DIR / "UNIMOD.obo").is_file():
        pytest.skip("developer OBO sources not available")
    rc = update_mod.main(["update", "unimod", "--offline", str(OBO_DIR)])
    assert rc == 0
    out = capsys.readouterr().out
    assert "done: refreshed ['unimod']" in out


def test_update_function_rejects_unknown_ontology():
    with pytest.raises(ValueError, match="unknown ontologies"):
        update_mod.update(["not-a-real-ontology"])


def test_update_prints_mass_mismatch_note(tmp_path, capsys):
    obo_dir = tmp_path / "obo"
    obo_dir.mkdir()
    (obo_dir / "UNIMOD.obo").write_text(
        'date: test\n\n[Term]\nid: UNIMOD:1\nname: Bad\nxref: delta_composition "C(1)"\nxref: delta_mono_mass "999.0"\n'
    )
    update_mod.update(["unimod"], offline=obo_dir)
    out = capsys.readouterr().out
    assert "internally inconsistent in the source" in out
    assert "Bad" in out


def test_cli_update_all_ontologies_warns_about_large_download(monkeypatch, capsys):
    # Don't actually hit the network/129MB GNOme download in a unit test: stub update()
    # and just verify the CLI's up-front warning and argument wiring.
    calls = []
    monkeypatch.setattr(update_mod, "update", lambda names, offline: calls.append((names, offline)) or [])

    rc = update_mod.main(["update"])
    assert rc == 0
    assert calls == [(None, None)]
    assert "large download" in capsys.readouterr().out


def test_mass_mismatches_flags_disagreement():
    from tacular.unimod.dclass import UnimodInfo

    consistent = UnimodInfo("1", "Acetyl", "C2H2O", 42.010565, 42.0367, {"C": 2, "H": 2, "O": 1})
    inconsistent = UnimodInfo("2", "Bad", "C1", 999.0, 999.0, {"C": 1})
    no_comp = UnimodInfo("3", "NoComp", None, 5.0, 5.0, None)
    no_mass = UnimodInfo("4", "NoMass", "C1", None, None, {"C": 1})

    mismatches = update_mod._mass_mismatches([consistent, inconsistent, no_comp, no_mass])
    ids = [m[0] for m in mismatches]
    assert ids == ["2"]
    _id, name, delta = mismatches[0]
    assert name == "Bad"
    assert delta == pytest.approx(999.0 - 12.0, abs=1e-6)


def test_mass_mismatches_skips_unknown_element_symbol():
    from tacular.unimod.dclass import UnimodInfo

    unknown_elem = UnimodInfo("1", "Bad", "Xx", 5.0, 5.0, {"Xx": 1})
    assert update_mod._mass_mismatches([unknown_elem]) == []


def test_download_writes_file_atomically(tmp_path, monkeypatch):
    import io

    class _FakeResponse(io.BytesIO):
        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

    monkeypatch.setattr(update_mod.urllib.request, "urlopen", lambda req: _FakeResponse(b"fake obo contents"))

    dest = tmp_path / "Fake.obo"
    update_mod._download("https://example.invalid/fake.obo", dest)

    assert dest.is_file()
    assert dest.read_bytes() == b"fake obo contents"
    assert not dest.with_suffix(dest.suffix + ".part").exists()


def test_module_cli_subprocess_smoke(isolated_cache):
    # One real subprocess invocation as an end-to-end smoke test of the console entrypoint wiring.
    result = subprocess.run(
        [sys.executable, "-m", "tacular", "where"],
        capture_output=True,
        text=True,
        cwd=REPO,
        env={**__import__("os").environ, _cache.ENV_DATA_DIR: str(isolated_cache)},
    )
    assert result.returncode == 0
    assert str(isolated_cache) in result.stdout


def test_main_module_runs_in_process(isolated_cache, monkeypatch, capsys):
    # Run __main__.py in-process (via runpy) so coverage attributes it correctly,
    # unlike the subprocess smoke test above.
    import runpy

    monkeypatch.setattr(sys, "argv", ["tacular", "where"])
    with pytest.raises(SystemExit) as exc_info:
        runpy.run_module("tacular.__main__", run_name="__main__")
    assert exc_info.value.code == 0
    assert str(isolated_cache) in capsys.readouterr().out
