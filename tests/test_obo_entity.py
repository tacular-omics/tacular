from types import MappingProxyType

import pytest

from tacular.obo_entity import OboEntity


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
    assert entity.get_mass() == 18.0106
    assert entity.get_mass(monoisotopic=False) == 18.015
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


def test_get_mass_matches_fields_and_is_keyword_only():
    import tacular as t

    for info in (t.UNIMOD_LOOKUP["Phospho"], t.MONOSACCHARIDE_LOOKUP["Hex"]):
        assert info.get_mass() == info.monoisotopic_mass
        assert info.get_mass(monoisotopic=False) == info.average_mass
        with pytest.raises(TypeError):
            info.get_mass(False)  # type: ignore[misc]
        assert not hasattr(info, "mass")
