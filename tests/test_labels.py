"""Tests for tacular.labels: isobaric tags, reporter ions and SILAC labels."""

import dataclasses
import json
import pickle

import pytest

import tacular as t
from tacular import ISOBARIC_TAG_LOOKUP, SILAC_LOOKUP, TacularKeyError
from tacular.constants import PROTON_MASS

# Reporter ion m/z (1+).
# TMT / TMTpro: Thermo Fisher Scientific, TMT10plex/TMT11plex and TMTpro 16plex/18plex
#   Label Reagent Set user guides, reporter ion m/z tables (6 decimals).
# iTRAQ: SCIEX iTRAQ Reagents 4plex/8plex documentation (the 6-decimal values used by
#   search engines; Ross et al. 2004, Mol Cell Proteomics 3:1154; Choe et al. 2007,
#   Proteomics 7:3651).
# Every published value here agrees with the computed one to 1e-5, so none is overridden.
PUBLISHED_REPORTER_MZ: dict[str, float] = {
    "126": 126.127726,
    "127N": 127.124761,
    "127C": 127.131081,
    "128N": 128.128116,
    "128C": 128.134436,
    "129N": 129.131471,
    "129C": 129.137790,
    "130N": 130.134825,
    "130C": 130.141145,
    "131N": 131.138180,
    "131C": 131.144500,
    "132N": 132.141535,
    "132C": 132.147855,
    "133N": 133.144890,
    "133C": 133.151210,
    "134N": 134.148245,
    "134C": 134.154565,
    "135N": 135.151600,
}
PUBLISHED_ITRAQ_MZ: dict[str, float] = {
    "113": 113.107325,
    "114": 114.110680,
    "115": 115.107715,
    "116": 116.111069,
    "117": 117.114424,
    "118": 118.111459,
    "119": 119.114814,
    "121": 121.121524,
}

EXPECTED_CHANNELS = {
    "TMT0": "126",
    "TMT2": "126 127C",
    "TMT6": "126 127N 128C 129N 130C 131N",
    "TMT10": "126 127N 127C 128N 128C 129N 129C 130N 130C 131N",
    "TMT11": "126 127N 127C 128N 128C 129N 129C 130N 130C 131N 131C",
    "TMT16": "126 127N 127C 128N 128C 129N 129C 130N 130C 131N 131C 132N 132C 133N 133C 134N",
    "TMT18": "126 127N 127C 128N 128C 129N 129C 130N 130C 131N 131C 132N 132C 133N 133C 134N 134C 135N",
    "iTRAQ4": "114 115 116 117",
    "iTRAQ8": "113 114 115 116 117 118 119 121",
}

ALL_TAGS = list(ISOBARIC_TAG_LOOKUP)
ALL_SILAC = list(SILAC_LOOKUP)


def test_plexes_and_channels():
    assert ISOBARIC_TAG_LOOKUP.keys() == list(EXPECTED_CHANNELS)
    for name, channels in EXPECTED_CHANNELS.items():
        tag = ISOBARIC_TAG_LOOKUP[name]
        assert tag.channels == tuple(channels.split())
        assert tag.plex == len(channels.split())


@pytest.mark.parametrize("tag", ALL_TAGS, ids=lambda tag: tag.name)
def test_reporter_mz_matches_published(tag):
    published = PUBLISHED_ITRAQ_MZ if tag.name.startswith("iTRAQ") else PUBLISHED_REPORTER_MZ
    for ion in tag.reporter_ions:
        assert ion.mz == pytest.approx(published[ion.channel], abs=1e-5), ion.channel
    assert list(tag.reporter_mzs) == sorted(tag.reporter_mzs)


@pytest.mark.parametrize("tag", ALL_TAGS, ids=lambda tag: tag.name)
def test_reporter_ions_agree_with_mzpaf_reference_molecules(tag):
    # REFMOL stores the neutral reporter (the ion minus a proton), from the mzPAF spec
    prefix = "iTRAQ" if tag.name.startswith("iTRAQ") else "TMT"
    for ion in tag.reporter_ions:
        refmol = t.REFMOL_LOOKUP[f"{prefix}{ion.channel}"]
        # H atom minus electron vs the CODATA proton mass differ by ~1e-8
        assert ion.mz == pytest.approx(refmol.monoisotopic_mass + PROTON_MASS, abs=1e-7)
        hydrogen = dict(refmol.dict_composition)
        hydrogen["H"] += 1
        assert dict(ion.dict_composition) == hydrogen


@pytest.mark.parametrize("info", ALL_TAGS + ALL_SILAC, ids=lambda info: info.name)
def test_matches_bundled_unimod(info):
    unimod = t.UNIMOD_LOOKUP.query_id(str(info.unimod_id))
    assert unimod is not None
    assert unimod.name == info.unimod_name
    assert dict(info.dict_composition) == dict(unimod.dict_composition)
    assert info.monoisotopic_mass == pytest.approx(unimod.monoisotopic_mass, abs=2e-6)
    assert info.get_mass() == info.monoisotopic_mass
    assert info.get_mass(monoisotopic=False) == info.average_mass


@pytest.mark.parametrize("info", ALL_TAGS + ALL_SILAC, ids=lambda info: info.name)
def test_mass_is_derived_from_the_element_table(info):
    expected = sum(t.ELEMENT_LOOKUP.get_mass(symbol) * n for symbol, n in info.dict_composition.items())
    assert info.monoisotopic_mass == expected
    assert sum(info.composition.values()) == sum(info.dict_composition.values())


def test_name_aliases_and_case():
    assert ISOBARIC_TAG_LOOKUP["tmt10plex"] is ISOBARIC_TAG_LOOKUP["TMT10"]
    assert ISOBARIC_TAG_LOOKUP["TMTpro18"] is ISOBARIC_TAG_LOOKUP["TMT18"]
    assert ISOBARIC_TAG_LOOKUP["TMTzero"] is ISOBARIC_TAG_LOOKUP["TMT0"]
    assert ISOBARIC_TAG_LOOKUP.get("TMT7") is None
    assert SILAC_LOOKUP["k+8"] is SILAC_LOOKUP["Lys8"] is SILAC_LOOKUP["K8"]
    assert SILAC_LOOKUP["R10"].residue == "R"
    with pytest.raises(TacularKeyError):
        SILAC_LOOKUP["Lys9"]


def test_query_unimod_id():
    shared = [tag.name for tag in ISOBARIC_TAG_LOOKUP.query_unimod_id(737)]
    assert shared == ["TMT6", "TMT10", "TMT11"]
    assert ISOBARIC_TAG_LOOKUP.query_unimod_id("UNIMOD:2016") == ISOBARIC_TAG_LOOKUP.query_unimod_id("U:2016")
    assert [s.name for s in SILAC_LOOKUP.query_unimod_id("188")] == ["Lys6", "Arg6"]
    for bad in (None, True, "x", "UNIMOD:", 1.5):
        assert ISOBARIC_TAG_LOOKUP.query_unimod_id(bad) == []  # type: ignore[arg-type]


def test_reporter_by_channel():
    tag = ISOBARIC_TAG_LOOKUP["TMT18"]
    assert tag.reporter("134c") is tag.reporter_ions[16]
    assert tag.reporter("999") is None
    assert tag.reporter(None) is None  # type: ignore[arg-type]
    assert ISOBARIC_TAG_LOOKUP["TMT6"].reporter("127C") is None


def test_silac_residues_and_sets():
    assert [s.name for s in SILAC_LOOKUP.query_residue("k")] == ["Lys4", "Lys6", "Lys8"]
    assert [s.name for s in SILAC_LOOKUP.query_residue("R")] == ["Arg6", "Arg10"]
    assert SILAC_LOOKUP.query_residue(None) == []  # type: ignore[arg-type]
    assert SILAC_LOOKUP.set_names == ("light", "medium", "heavy")
    assert SILAC_LOOKUP.get_set("light") == ()
    assert [s.name for s in SILAC_LOOKUP.get_set("Medium")] == ["Lys4", "Arg6"]
    assert [s.name for s in SILAC_LOOKUP.get_set("heavy")] == ["Lys8", "Arg10"]
    assert SILAC_LOOKUP.query_set("super-heavy") is None
    assert SILAC_LOOKUP.query_set(None) is None  # type: ignore[arg-type]
    with pytest.raises(TacularKeyError):
        SILAC_LOOKUP.get_set("super-heavy")


def test_silac_delta_masses():
    expected = {"Lys4": 4.025107, "Lys6": 6.020129, "Lys8": 8.014199, "Arg6": 6.020129, "Arg10": 10.008269}
    assert {s.name: round(s.monoisotopic_mass, 6) for s in SILAC_LOOKUP} == expected


@pytest.mark.parametrize(
    "info", [*ALL_TAGS, *ALL_SILAC, ISOBARIC_TAG_LOOKUP["TMT11"].reporter_ions[-1]], ids=lambda i: type(i).__name__
)
def test_frozen_read_only_and_serializable(info):
    with pytest.raises(dataclasses.FrozenInstanceError):
        info.dict_composition = {}  # type: ignore[misc]
    with pytest.raises(TypeError):
        info.dict_composition["C"] = 1  # type: ignore[index]
    assert pickle.loads(pickle.dumps(info)) == info
    assert dataclasses.replace(info) == info
    json.dumps(info.to_dict())
    assert json.loads(json.dumps(info.to_dict(float_precision=None))) == info.to_dict(float_precision=None)


def test_to_dict_keys():
    tag = ISOBARIC_TAG_LOOKUP["iTRAQ4"].to_dict()
    assert tag["unimod_id"] == 214 and len(tag["reporter_ions"]) == 4  # type: ignore[arg-type]
    assert ISOBARIC_TAG_LOOKUP["iTRAQ4"].reporter_ions[0].to_dict()["mz"] == 114.11068
    assert SILAC_LOOKUP["Arg10"].to_dict()["residue"] == "R"


def test_reprs():
    assert repr(ISOBARIC_TAG_LOOKUP) == "<IsobaricTagLookup: 9 entries>"
    assert repr(SILAC_LOOKUP) == "<SilacLabelLookup: 5 entries>"
