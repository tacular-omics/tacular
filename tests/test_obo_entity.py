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
    mod = OboEntity(
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
