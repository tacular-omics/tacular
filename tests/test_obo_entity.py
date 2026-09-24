from types import MappingProxyType

import pytest

from tacular.obo_entity import OboEntity, filter_infos


class DummyElement:
    pass


def test_obo_entity_str_and_repr():
    entity = OboEntity(
        id="E1",
        name="TestEntity",
        formula="H2O",
        monoisotopic_mass=18.0106,
        average_mass=18.015,
        dict_composition=MappingProxyType({"H": 2, "O": 1}),
    )
    assert str(entity) == "TestEntity (H2O)"
    assert "OboEntity" in repr(entity)
    assert entity.mass() == 18.0106
    assert entity.mass(monoisotopic=False) == 18.015
    d = entity.to_dict()
    assert d["id"] == "E1"
    assert d["name"] == "TestEntity"
    assert d["formula"] == "H2O"
    assert d["monoisotopic_mass"] == pytest.approx(18.0106, abs=1e-6)
    assert d["average_mass"] == pytest.approx(18.015, abs=1e-6)
    assert d["composition"] == {"H": 2, "O": 1}


def test_obo_entity_update():
    entity = OboEntity(
        id="E1",
        name="TestEntity",
        formula="H2O",
        monoisotopic_mass=18.0106,
        average_mass=18.015,
        dict_composition=MappingProxyType({"H": 2, "O": 1}),
    )
    updated = entity.update(name="UpdatedEntity", monoisotopic_mass=20.0)
    assert updated.name == "UpdatedEntity"
    assert updated.monoisotopic_mass == 20.0
    assert updated.id == "E1"
    assert updated.formula == "H2O"


def test_modentity_inherits_cv():
    OboEntity(
        id="M1",
        name="ModEntity",
        formula=None,
        monoisotopic_mass=None,
        average_mass=None,
        dict_composition=None,
    )


def test_filter_infos():
    e1 = OboEntity(
        id="1",
        name="A",
        formula="H2O",
        monoisotopic_mass=1.0,
        average_mass=2.0,
        dict_composition=MappingProxyType({"H": 2, "O": 1}),
    )
    e2 = OboEntity(
        id="2",
        name="B",
        formula=None,
        monoisotopic_mass=None,
        average_mass=None,
        dict_composition=None,
    )
    infos = [e1, e2]
    assert filter_infos(infos, has_monoisotopic_mass=True) == [e1]
    assert filter_infos(infos, has_monoisotopic_mass=False) == [e2]
    assert filter_infos(infos, has_composition=True) == [e1]
    assert filter_infos(infos, has_composition=False) == [e2]
    assert filter_infos(infos, id="1") == [e1]
    assert filter_infos(infos, name="B") == [e2]


if __name__ == "__main__":
    pytest.main([__file__])


def test_to_dict_composition_is_a_copy():
    """Mutating to_dict()["composition"] must not change the entry itself."""
    import tacular as t

    phospho = t.UNIMOD_LOOKUP["Phospho"]
    before = dict(phospho.dict_composition)
    d = phospho.to_dict()
    d["composition"]["P"] = 99
    d["composition"]["Xx"] = 1
    assert dict(t.UNIMOD_LOOKUP["Phospho"].dict_composition) == before
    assert d["composition"] is not phospho.dict_composition
    assert isinstance(d["composition"], dict)


def test_to_dict_composition_none_stays_none():
    entity = OboEntity("E", "e", None, None, None, None)
    assert entity.to_dict()["composition"] is None


@pytest.mark.parametrize("attr", ["AA_LOOKUP", "FRAGMENT_ION_LOOKUP", "REFMOL_LOOKUP", "MONOSACCHARIDE_LOOKUP"])
def test_other_infos_to_dict_composition_is_a_copy(attr):
    import tacular as t

    info = next(i for i in getattr(t, attr) if i.dict_composition)
    before = dict(info.dict_composition)
    d = info.to_dict()
    d["composition"]["Xx"] = 1
    assert dict(info.dict_composition) == before


def test_get_mass_matches_mass():
    import tacular as t

    for info in (t.UNIMOD_LOOKUP["Phospho"], t.MONOSACCHARIDE_LOOKUP["Hex"]):
        assert info.get_mass() == info.mass() == info.monoisotopic_mass
        assert info.get_mass(monoisotopic=False) == info.mass(False) == info.average_mass
        assert info.get_mass(False) == info.average_mass
