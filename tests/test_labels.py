"""Tests for tacular.labels: isobaric tags, reporter ions and SILAC labels."""

import dataclasses
import json
import pickle

import pytest

import tacular as t
from tacular import ISOBARIC_TAG_LOOKUP, SILAC_LOOKUP, TacularKeyError
from tacular.constants import ELECTRON_MASS, PROTON_MASS

# TMT / TMTpro reporter ion m/z (1+), transcribed exactly from Thermo Fisher Scientific,
# "TMTpro Mass Tag Labeling Reagents and Kits" user guide MAN0018773, Table 2. The TMT
# (non-pro) reporters 126-131C have the same compositions, so the same values apply.
THERMO_TMTPRO_MZ: dict[str, float] = {
    "126": 126.127726,
    "127N": 127.124761,
    "127C": 127.131081,
    "128N": 128.128116,
    "128C": 128.134436,
    "129N": 129.131471,
    "129C": 129.137791,
    "130N": 130.134826,
    "130C": 130.141146,
    "131N": 131.138181,
    "131C": 131.144501,
    "132N": 132.141536,
    "132C": 132.147856,
    "133N": 133.144891,
    "133C": 133.151211,
    "134N": 134.148246,
    "134C": 134.154566,
    "135N": 135.151601,
}
# Legacy 4-decimal iTRAQ reporter m/z, as in SCIEX's iTRAQ documentation and MSnbase's
# iTRAQ4/iTRAQ8 tables. These are ~0.0005 above tacular's computed values, i.e. they
# look like the ion mass without the electron subtracted; tacular does subtract it.
LEGACY_ITRAQ_MZ: dict[str, float] = {
    "113": 113.1079,
    "114": 114.1112,
    "115": 115.1083,
    "116": 116.1116,
    "117": 117.1150,
    "118": 118.1120,
    "119": 119.1153,
    "121": 121.1220,
}

EXPECTED_CHANNELS = {
    "TMT0": "126",
    "TMT2": "126 127C",
    "TMT6": "126 127N 128C 129N 130C 131N",
    "TMT10": "126 127N 127C 128N 128C 129N 129C 130N 130C 131N",
    "TMT11": "126 127N 127C 128N 128C 129N 129C 130N 130C 131N 131C",
    "TMTpro0": "126",
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


TMT_TAGS = [tag for tag in ALL_TAGS if tag.name.startswith("TMT")]
ITRAQ_TAGS = [tag for tag in ALL_TAGS if tag.name.startswith("iTRAQ")]


@pytest.mark.parametrize("tag", TMT_TAGS, ids=lambda tag: tag.name)
def test_tmt_reporter_mz_matches_thermo_table(tag):
    for ion in tag.reporter_ions:
        assert ion.mz == pytest.approx(THERMO_TMTPRO_MZ[ion.channel], abs=2e-6), ion.channel
    assert list(tag.reporter_mzs) == sorted(tag.reporter_mzs)


@pytest.mark.parametrize("tag", ITRAQ_TAGS, ids=lambda tag: tag.name)
def test_itraq_reporter_mz_is_computed_and_legacy_tables_skip_the_electron(tag):
    for ion in tag.reporter_ions:
        composition_mass = sum(t.ELEMENT_LOOKUP.get_mass(symbol) * n for symbol, n in ion.dict_composition.items())
        assert ion.mz == composition_mass - ELECTRON_MASS
        # legacy tables are higher by about one electron mass (4-decimal rounding: 1e-4)
        offset = LEGACY_ITRAQ_MZ[ion.channel] - ion.mz
        assert offset == pytest.approx(ELECTRON_MASS, abs=1e-4), ion.channel
        assert 0.0004 < offset < 0.0007
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
    # average masses use the bundled element table; UNIMOD's atomic weights differ slightly
    assert info.average_mass == pytest.approx(unimod.average_mass, abs=6e-4)
    assert info.get_mass() == info.monoisotopic_mass
    assert info.get_mass(monoisotopic=False) == info.average_mass


@pytest.mark.parametrize("info", ALL_TAGS + ALL_SILAC, ids=lambda info: info.name)
def test_mass_is_derived_from_the_element_table(info):
    expected = sum(t.ELEMENT_LOOKUP.get_mass(symbol) * n for symbol, n in info.dict_composition.items())
    assert info.monoisotopic_mass == expected
    assert sum(info.composition.values()) == sum(info.dict_composition.values())


EXPECTED_CHANNEL_TAGS = {
    "iTRAQ4": {"114": 532, "115": 533, "116": 214, "117": 214},
    "iTRAQ8": {"113": 730, "114": 730, "115": 731, "116": 730, "117": 730, "118": 731, "119": 731, "121": 731},
}


@pytest.mark.parametrize("tag", ALL_TAGS, ids=lambda tag: tag.name)
def test_per_channel_tags_match_bundled_unimod(tag):
    expected = EXPECTED_CHANNEL_TAGS.get(tag.name, dict.fromkeys(tag.channels, tag.unimod_id))
    assert {ion.channel: ion.tag_unimod_id for ion in tag.reporter_ions} == expected
    for ion in tag.reporter_ions:
        unimod = t.UNIMOD_LOOKUP.query_id(str(ion.tag_unimod_id))
        assert unimod is not None
        assert ion.tag_unimod_name == unimod.name
        assert dict(ion.tag_dict_composition) == dict(unimod.dict_composition)
        assert ion.tag_monoisotopic_mass == pytest.approx(unimod.monoisotopic_mass, abs=2e-6)


def test_itraq_channel_tag_masses():
    itraq4 = ISOBARIC_TAG_LOOKUP["iTRAQ4"]
    # UNIMOD 532 / 533 monoisotopic masses (UNIMOD rounds to 6 places from its own table)
    assert itraq4.query_reporter("114").tag_monoisotopic_mass == pytest.approx(144.105918, abs=2e-6)  # type: ignore[union-attr]
    assert itraq4.query_reporter("115").tag_monoisotopic_mass == pytest.approx(144.099599, abs=2e-6)  # type: ignore[union-attr]
    assert itraq4.query_reporter("116").tag_monoisotopic_mass == itraq4.monoisotopic_mass  # type: ignore[union-attr]
    itraq8 = ISOBARIC_TAG_LOOKUP["iTRAQ8"]
    assert itraq8.query_reporter("121").tag_monoisotopic_mass == pytest.approx(304.199040, abs=2e-6)  # type: ignore[union-attr]
    assert itraq8.query_reporter("113").tag_monoisotopic_mass == itraq8.monoisotopic_mass  # type: ignore[union-attr]


def test_name_aliases_and_case():
    assert ISOBARIC_TAG_LOOKUP["tmt10plex"] is ISOBARIC_TAG_LOOKUP["TMT10"]
    assert ISOBARIC_TAG_LOOKUP["TMTpro18"] is ISOBARIC_TAG_LOOKUP["TMT18"]
    assert ISOBARIC_TAG_LOOKUP["TMTzero"] is ISOBARIC_TAG_LOOKUP["TMT0"]
    assert ISOBARIC_TAG_LOOKUP["tmtpro_zero"] is ISOBARIC_TAG_LOOKUP["TMTproZero"] is ISOBARIC_TAG_LOOKUP["TMTpro0"]
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
    for bad in (None, True, "x", "UNIMOD:", 1.5, "\u0667\u0663\u0667"):  # last: Arabic-Indic "737"
        assert ISOBARIC_TAG_LOOKUP.query_unimod_id(bad) == []  # type: ignore[arg-type]


def test_query_reporter():
    tag = ISOBARIC_TAG_LOOKUP["TMT18"]
    assert tag.query_reporter("134c") is tag.reporter_ions[16]
    assert tag.query_reporter("999") is None
    assert tag.query_reporter(" 127n ") is tag.reporter_ions[1]
    assert tag.query_reporter(None) is None  # type: ignore[arg-type]
    assert ISOBARIC_TAG_LOOKUP["TMT6"].query_reporter("127C") is None
    assert not hasattr(tag, "reporter")
    ion = tag.query_reporter("126")
    assert ion is not None
    assert {element.symbol: n for element, n in ion.composition.items()} == {"C": 8, "H": 16, "N": 1}


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
    if isinstance(info, t.ReporterIonInfo):
        with pytest.raises(TypeError):
            info.tag_dict_composition["C"] = 1  # type: ignore[index]
    assert pickle.loads(pickle.dumps(info)) == info
    assert dataclasses.replace(info) == info
    json.dumps(info.to_dict())
    assert json.loads(json.dumps(info.to_dict(float_precision=None))) == info.to_dict(float_precision=None)


def test_to_dict_keys():
    tag = ISOBARIC_TAG_LOOKUP["iTRAQ4"].to_dict()
    assert tag["unimod_id"] == 214 and len(tag["reporter_ions"]) == 4  # type: ignore[arg-type]
    ion = ISOBARIC_TAG_LOOKUP["iTRAQ4"].reporter_ions[0].to_dict()
    assert ion["mz"] == 114.11068
    assert ion["tag_unimod_id"] == 532 and ion["tag_unimod_name"] == "iTRAQ4plex114"
    assert ion["tag_monoisotopic_mass"] == pytest.approx(144.105918, abs=2e-6)
    assert SILAC_LOOKUP["Arg10"].to_dict()["residue"] == "R"


def test_reprs():
    assert repr(ISOBARIC_TAG_LOOKUP) == "<IsobaricTagLookup: 10 entries>"
    assert repr(SILAC_LOOKUP) == "<SilacLabelLookup: 5 entries>"
