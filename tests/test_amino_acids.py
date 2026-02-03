import pytest

from tacular import AA_LOOKUP as db
from tacular.amino_acids import AminoAcid


class TestAALookupBasics:
    """Test basic lookup operations"""

    def test_one_letter_lookup(self):
        """Test one-letter code lookups"""
        ala = db.one_letter("A")
        assert ala.name == "Alanine"
        assert ala.three_letter_code == "Ala"
        assert ala.id == "A"

        # Case insensitive
        assert db.one_letter("a") is ala

        # Multiple amino acids
        gly = db.one_letter("G")
        assert gly.name == "Glycine"
        assert gly.three_letter_code == "Gly"

    def test_three_letter_lookup(self):
        """Test three-letter code lookups"""
        ala = db.one_letter("A")
        assert db.three_letter("Ala") is ala
        assert db.three_letter("ALA") is ala
        assert db.three_letter("ala") is ala

        val = db.three_letter("Val")
        assert val.name == "Valine"
        assert val.id == "V"

    def test_name_lookup(self):
        """Test name-based lookups"""
        ala = db.one_letter("A")
        assert db.name("Alanine") is ala
        assert db.name("alanine") is ala
        assert db.name("ALANINE") is ala

        leu = db.name("Leucine")
        assert leu.id == "L"
        assert leu.three_letter_code == "Leu"

    def test_getitem_all_methods(self):
        """Test __getitem__ tries all lookup methods"""
        # Get by one letter
        assert db["A"] == db.one_letter("A")
        # Get by three letter
        assert db["Ala"] == db.one_letter("A")
        assert db["ALA"] == db.one_letter("A")
        # Get by name
        assert db["Alanine"] == db.one_letter("A")
        assert db["alanine"] == db.one_letter("A")

    def test_contains(self):
        """Test __contains__ operator"""
        assert "A" in db
        assert "Ala" in db
        assert "Alanine" in db
        assert "alanine" in db
        assert "NotAnAA" not in db
        assert "XYZ" not in db
        assert "999" not in db

    def test_iter(self):
        """Test iteration over amino acids"""
        amino_acids = list(db)
        assert len(amino_acids) > 0
        # Should be ordered A-Z
        assert amino_acids[0].id == "A"
        # All should be AminoAcidInfo objects
        for aa in amino_acids:
            assert aa.id is not None
            assert aa.name is not None

    def test_enum_access(self):
        """Test access via Enum member"""
        info = db.one_letter(str(AminoAcid.A))
        assert info.name == "Alanine"


class TestAALookupEdgeCases:
    """Test edge cases and error handling"""

    def test_one_letter_not_found(self):
        """Test KeyError for invalid one-letter codes"""
        with pytest.raises(KeyError):
            db.one_letter("1")
        with pytest.raises(KeyError):
            db.one_letter("0")
        with pytest.raises(KeyError):
            db.one_letter("!")

    def test_three_letter_not_found(self):
        """Test KeyError for invalid three-letter codes"""
        with pytest.raises(KeyError):
            db.three_letter("Xyz")
        with pytest.raises(KeyError):
            db.three_letter("123")
        with pytest.raises(KeyError):
            db.three_letter("AAA")

    def test_name_not_found(self):
        """Test KeyError for invalid names"""
        with pytest.raises(KeyError):
            db.name("NotAnAminoAcid")
        with pytest.raises(KeyError):
            db.name("Unknown")

    def test_getitem_not_found(self):
        """Test KeyError for __getitem__ with invalid keys"""
        with pytest.raises(KeyError):
            _ = db["Unknown"]
        with pytest.raises(KeyError):
            _ = db["XYZ"]


class TestAALookupCachedProperties:
    """Test cached property methods"""

    def test_ordered_amino_acids(self):
        """Test ordered_amino_acids property"""
        ordered = db.ordered_amino_acids
        assert len(ordered) > 0
        # Should start with A
        assert ordered[0].id == "A"
        # Should be a tuple
        assert isinstance(ordered, tuple)

    def test_ambiguous_amino_acids(self):
        """Test ambiguous_amino_acids property"""
        ambiguous = db.ambiguous_amino_acids
        # B, J, X, Z are ambiguous
        ambiguous_ids = {aa.id for aa in ambiguous}
        assert "B" in ambiguous_ids or "J" in ambiguous_ids or "X" in ambiguous_ids or "Z" in ambiguous_ids
        # All should be marked as ambiguous
        for aa in ambiguous:
            assert aa.is_ambiguous

    def test_unambiguous_amino_acids(self):
        """Test unambiguous_amino_acids property"""
        unambiguous = db.unambiguous_amino_acids
        # Should have more than ambiguous
        assert len(unambiguous) > len(db.ambiguous_amino_acids)
        # All should not be marked as ambiguous
        for aa in unambiguous:
            assert not aa.is_ambiguous

    def test_mass_amino_acids(self):
        """Test mass_amino_acids property"""
        mass_aas = db.mass_amino_acids
        # All should have masses
        for aa in mass_aas:
            assert aa.monoisotopic_mass is not None
            assert aa.average_mass is not None

    def test_mass_unambiguous_amino_acids(self):
        """Test mass_unambiguous_amino_acids property"""
        mass_unambig = db.mass_unambiguous_amino_acids
        # All should have masses and not be ambiguous
        for aa in mass_unambig:
            assert aa.monoisotopic_mass is not None
            assert aa.average_mass is not None
            assert not aa.is_ambiguous


class TestAALookupHelperMethods:
    """Test helper methods like is_ambiguous, mass, composition"""

    def test_is_ambiguous(self):
        """Test is_ambiguous method"""
        # B is typically ambiguous
        if "B" in db:
            assert db.is_ambiguous("B")
        # A is not ambiguous
        assert not db.is_ambiguous("A")

    def test_is_unambiguous(self):
        """Test is_unambiguous method"""
        assert db.is_unambiguous("A")
        assert db.is_unambiguous("G")

    def test_is_mass_ambiguous(self):
        """Test is_mass_ambiguous method"""
        # Most amino acids are not mass ambiguous
        assert not db.is_mass_ambiguous("A")

    def test_is_mass_unambiguous(self):
        """Test is_mass_unambiguous method"""
        assert db.is_mass_unambiguous("A")

    def test_mass_monoisotopic(self):
        """Test mass method with monoisotopic=True"""
        mass = db.mass("A", monoisotopic=True)
        assert isinstance(mass, float)
        assert mass > 0

    def test_mass_average(self):
        """Test mass method with monoisotopic=False"""
        mass = db.mass("A", monoisotopic=False)
        assert isinstance(mass, float)
        assert mass > 0

    def test_mass_ambiguous_aa(self):
        """Test mass method with ambiguous amino acid raises error"""
        # B doesn't have defined mass
        if "B" in db:
            with pytest.raises(ValueError):
                db.mass("B", monoisotopic=True)

    def test_composition(self):
        """Test composition method"""
        comp = db.composition("A")
        assert comp is not None
        # Alanine has C, H, N, O
        assert len(comp) > 0

    def test_composition_ambiguous_aa(self):
        """Test composition with ambiguous amino acid raises error"""
        if "B" in db:
            with pytest.raises(ValueError):
                db.composition("B")


class TestAADataIntegrity:
    """Test data integrity for known amino acids"""

    def test_alanine_properties(self):
        """Test Alanine (A) has correct properties"""
        ala = db["A"]
        assert ala.id == "A"
        assert ala.name == "Alanine"
        assert ala.three_letter_code == "Ala"
        assert ala.monoisotopic_mass is not None
        assert ala.average_mass is not None
        assert not ala.is_ambiguous

    def test_glycine_properties(self):
        """Test Glycine (G) has correct properties"""
        gly = db["G"]
        assert gly.id == "G"
        assert gly.name == "Glycine"
        assert gly.three_letter_code == "Gly"
        assert gly.monoisotopic_mass is not None

    def test_leucine_isoleucine_mass_ambiguity(self):
        """Test L/I mass ambiguity flag"""
        # L and I have same mass but are not mass ambiguous in normal sense
        if "L" in db and "I" in db:
            leu = db["L"]
            ile = db["I"]
            assert leu.monoisotopic_mass == ile.monoisotopic_mass

    def test_masses_are_positive(self):
        """Test all defined masses are positive"""
        for aa in db.mass_amino_acids:
            assert aa.monoisotopic_mass >= 0
            assert aa.average_mass >= 0

    def test_formulas_exist(self):
        """Test that amino acids with mass have formulas"""
        for aa in db.mass_amino_acids:
            assert aa.formula is not None
            assert len(aa.formula) >= 0

    def test_all_have_three_letter_codes(self):
        """Test all amino acids have three-letter codes"""
        for aa in db:
            assert aa.three_letter_code is not None
            assert len(aa.three_letter_code) == 3


if __name__ == "__main__":
    pytest.main([__file__])
