import pytest

from tacular import AA_LOOKUP as db
from tacular.amino_acids import AminoAcid


def test_amino_acid_lookup_methods():
    # Test one letter
    ala = db.one_letter("A")
    assert ala.name == "Alanine"
    assert ala.three_letter_code == "Ala"

    # Test three letter
    assert db.three_letter("Ala") is ala
    assert db.three_letter("ALA") is ala
    assert db.three_letter("ala") is ala

    # Test name
    assert db.name("Alanine") is ala
    assert db.name("alanine") is ala

    # Failures
    with pytest.raises(KeyError):
        db.one_letter("1")  # Not an amino acid
    with pytest.raises(KeyError):
        db.three_letter("Xyz")
    with pytest.raises(KeyError):
        db.name("NotAnAminoAcid")


def test_amino_acid_getitem():
    # Get by one letter
    assert db["A"] == db.one_letter("A")
    # Get by three letter
    assert db["Ala"] == db.one_letter("A")
    assert db["ALA"] == db.one_letter("A")
    # Get by name
    assert db["Alanine"] == db.one_letter("A")
    assert db["alanine"] == db.one_letter("A")

    # Missing
    with pytest.raises(KeyError):
        _ = db["Unknown"]


def test_amino_acid_enum_access():
    # If the user can access via Enum member
    info = db.one_letter(str(AminoAcid.A))
    assert info.name == "Alanine"
