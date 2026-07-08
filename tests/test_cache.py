"""Tests for the runtime data cache (tacular._cache) and OboEntity round-trip."""

import json
import logging
import warnings

import pytest

from tacular import _cache
from tacular.unimod.dclass import UnimodInfo

BAKED = {"1": UnimodInfo("1", "Baked", "C2H2O", 42.010565, 42.0367, {"C": 2, "H": 2, "O": 1})}
BAKED_VERSION = "baked-v1"


@pytest.fixture
def cache_env(tmp_path, monkeypatch):
    """Point the cache at a temp dir and ensure it is enabled."""
    monkeypatch.setenv(_cache.ENV_DATA_DIR, str(tmp_path))
    monkeypatch.delenv(_cache.ENV_DISABLE, raising=False)
    return tmp_path


def _write_cache(tmp_path, entries, version="cached-v1"):
    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    payload = {"metadata": {"data_version": version}, "unimodifications": entries}
    (data_dir / "unimodifications.json").write_text(json.dumps(payload))


def test_from_dict_roundtrips_composition_key():
    info = BAKED["1"]
    restored = UnimodInfo.from_dict(info.to_dict())
    assert restored == info
    # to_dict serialises dict_composition under the "composition" key
    assert info.to_dict()["composition"] == info.dict_composition


def test_resolve_falls_back_to_baked_when_no_cache(cache_env):
    data, version = _cache.resolve("unimodifications.json", UnimodInfo, BAKED, BAKED_VERSION)
    assert data is BAKED
    assert version == BAKED_VERSION


def test_resolve_prefers_cache(cache_env):
    _write_cache(
        cache_env,
        [
            {
                "id": "1",
                "name": "Cached",
                "formula": "C2H2O",
                "monoisotopic_mass": 99.9,
                "average_mass": 42.0,
                "composition": {"C": 2, "H": 2, "O": 1},
            }
        ],
        version="cached-v9",
    )
    data, version = _cache.resolve("unimodifications.json", UnimodInfo, BAKED, BAKED_VERSION)
    assert version == "cached-v9"
    assert data["1"].name == "Cached"
    assert data["1"].monoisotopic_mass == 99.9


def test_disable_flag_forces_baked(cache_env, monkeypatch):
    _write_cache(
        cache_env,
        [
            {
                "id": "1",
                "name": "Cached",
                "formula": None,
                "monoisotopic_mass": None,
                "average_mass": None,
                "composition": None,
            }
        ],
    )
    monkeypatch.setenv(_cache.ENV_DISABLE, "1")
    data, version = _cache.resolve("unimodifications.json", UnimodInfo, BAKED, BAKED_VERSION)
    assert data is BAKED
    assert version == BAKED_VERSION


def test_corrupt_cache_logs_and_falls_back(cache_env, caplog):
    data_dir = cache_env / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / "unimodifications.json").write_text("{ not valid json")
    with caplog.at_level(logging.WARNING):
        data, version = _cache.resolve("unimodifications.json", UnimodInfo, BAKED, BAKED_VERSION)
    assert data is BAKED
    assert "ignoring unreadable cached data" in caplog.text


def test_corrupt_cache_does_not_raise_under_warnings_as_errors(cache_env):
    # A corrupt cache must never break `import tacular` under `-W error`.
    data_dir = cache_env / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / "unimodifications.json").write_text("{ truncated")
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        data, _ = _cache.resolve("unimodifications.json", UnimodInfo, BAKED, BAKED_VERSION)
    assert data is BAKED


def test_empty_cache_file_falls_back(cache_env):
    _write_cache(cache_env, [])  # no entries
    data, _ = _cache.resolve("unimodifications.json", UnimodInfo, BAKED, BAKED_VERSION)
    assert data is BAKED


def test_duplicate_id_in_cache_falls_back(cache_env):
    _write_cache(
        cache_env,
        [
            {
                "id": "1",
                "name": "A",
                "formula": None,
                "monoisotopic_mass": None,
                "average_mass": None,
                "composition": None,
            },
            {
                "id": "1",
                "name": "B",
                "formula": None,
                "monoisotopic_mass": None,
                "average_mass": None,
                "composition": None,
            },
        ],
    )
    data, _ = _cache.resolve("unimodifications.json", UnimodInfo, BAKED, BAKED_VERSION)
    assert data is BAKED


def test_duplicate_case_insensitive_name_in_cache_falls_back(cache_env):
    def entry(id_, name):
        return {
            "id": id_,
            "name": name,
            "formula": None,
            "monoisotopic_mass": None,
            "average_mass": None,
            "composition": None,
        }

    _write_cache(cache_env, [entry("1", "Same"), entry("2", "same")])
    data, _ = _cache.resolve("unimodifications.json", UnimodInfo, BAKED, BAKED_VERSION)
    assert data is BAKED


def test_cache_preserves_full_float_precision(cache_env):
    hi = UnimodInfo("1", "Precise", "C", 123.45678901234567, 98.76543210987654, {"C": 1})
    _cache.save("unimodifications.json", "unimodifications", [hi], "v")
    loaded = _cache.load_cached("unimodifications.json", UnimodInfo)
    assert loaded is not None
    data, _ = loaded
    # full precision, not rounded to 6 decimals
    assert data["1"].monoisotopic_mass == 123.45678901234567
    assert data["1"].average_mass == 98.76543210987654


def test_save_then_load_roundtrip(cache_env):
    infos = list(BAKED.values())
    path = _cache.save("unimodifications.json", "unimodifications", infos, "saved-v2")
    assert path.is_file()
    loaded = _cache.load_cached("unimodifications.json", UnimodInfo)
    assert loaded is not None
    data, version = loaded
    assert version == "saved-v2"
    assert data["1"] == BAKED["1"]


def test_obo_dir_is_under_cache_dir(cache_env):
    assert _cache.obo_dir() == _cache.cache_dir() / "obo"


def test_cache_file_with_only_metadata_key_falls_back(cache_env):
    data_dir = cache_env / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / "unimodifications.json").write_text(json.dumps({"metadata": {"data_version": "v1"}}))
    data, version = _cache.resolve("unimodifications.json", UnimodInfo, BAKED, BAKED_VERSION)
    assert data is BAKED
    assert version == BAKED_VERSION


def test_no_data_file_returns_none_from_load_cached(cache_env):
    assert _cache.load_cached("unimodifications.json", UnimodInfo) is None
