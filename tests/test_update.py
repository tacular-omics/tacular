"""Verify each shipped OBO builder reproduces the committed bundled JSON exactly,
and that the offline update path writes a loadable cache.
"""

import importlib
import json
from pathlib import Path

import pytest

from tacular import _cache

REPO = Path(__file__).resolve().parent.parent
OBO_DIR = REPO / "data_gen" / "data"
JSON_DIR = REPO / "jsons"

# (ontology, builder module, OBO filename, json filename, data key). GNOme excluded from
# the default run: its .obo is ~129 MB and parsing it is far too slow for the unit suite.
CASES = [
    ("unimod", "tacular._datagen.unimod", "UNIMOD.obo", "unimodifications.json", "unimodifications"),
    ("xlmod", "tacular._datagen.xlmod", "XLMod.obo", "xlmodifications.json", "xlmodifications"),
    ("psimod", "tacular._datagen.psimod", "PSI-MOD.obo", "psimodifications.json", "psimodifications"),
    ("resid", "tacular._datagen.resid", "PSI-MOD.obo", "resid_modifications.json", "resid_modifications"),
]


@pytest.mark.parametrize("name,module,obo,jsonf,key", CASES)
def test_builder_reproduces_bundled_json(name, module, obo, jsonf, key):
    obo_path = OBO_DIR / obo
    json_path = JSON_DIR / jsonf
    if not obo_path.is_file():
        pytest.skip(f"{obo_path} not present (developer OBO sources not available)")

    builder = importlib.import_module(module)
    _version, infos = builder.build(obo_path)
    built = {i.id: i.to_dict() for i in infos}
    ref = {m["id"]: m for m in json.loads(json_path.read_text())[key]}

    assert set(built) == set(ref), f"{name}: id set mismatch ({len(built)} built vs {len(ref)} ref)"
    diffs = [k for k in ref if built[k] != ref[k]]
    assert not diffs, f"{name}: {len(diffs)} entries differ, e.g. {diffs[:3]}"


def test_offline_update_writes_loadable_cache(tmp_path, monkeypatch):
    obo_path = OBO_DIR / "UNIMOD.obo"
    if not obo_path.is_file():
        pytest.skip("developer OBO sources not available")

    monkeypatch.setenv(_cache.ENV_DATA_DIR, str(tmp_path))
    monkeypatch.delenv(_cache.ENV_DISABLE, raising=False)

    from tacular import update as update_mod
    from tacular.unimod.dclass import UnimodInfo

    refreshed = update_mod.update(["unimod"], offline=OBO_DIR)
    assert refreshed == ["unimod"]

    loaded = _cache.load_cached("unimodifications.json", UnimodInfo)
    assert loaded is not None
    data, _version = loaded
    assert len(data) > 1000
    # the isotope fix must survive the OBO -> cache JSON -> load round-trip
    assert data["536"].dict_composition.get("13C") == 1
