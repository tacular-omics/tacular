import pytest

from tacular import FRAGMENT_ION_LOOKUP as db
from tacular.ion_types import IonType
from tacular.ion_types.dclass import IonTypeProperty


class TestFragmentIonLookupBasics:
    """Test basic fragment ion lookup operations"""

    def test_getitem_by_id(self):
        """Test __getitem__ with ion IDs"""
        # Common ion types: a, b, c, x, y, z
        if "b" in db:
            b_ion = db["b"]
            assert b_ion.id == "b"
            assert b_ion.name is not None

    def test_getitem_by_ion_type_enum(self):
        """Test __getitem__ with IonType enum"""
        # Access via enum
        if hasattr(IonType, "b"):
            b_ion = db[IonType.b]
            assert b_ion.id == "b"

    def test_getitem_by_name(self):
        """Test __getitem__ with ion names"""
        # Try to get by name if we know one exists
        for ion in db:
            result = db[ion.name]
            assert result.name == ion.name
            break

    def test_contains(self):
        """Test __contains__ operator"""
        # Test with known ion types
        if "b" in db:
            assert "b" in db
            assert "B" in db  # case insensitive
        assert "notanion" not in db

    def test_iter(self):
        """Test iteration over fragment ions"""
        ions = list(db)
        assert len(ions) > 0
        # All should have IDs and names
        for ion in ions:
            assert ion.id is not None
            assert ion.name is not None

    def test_get_with_default(self):
        """Test get() method with default value"""
        result = db.get("nonexistent", None)
        assert result is None

    def test_case_insensitivity(self):
        """Test case-insensitive lookups"""
        if "b" in db:
            b_lower = db.query_id("b")
            b_upper = db.query_id("B")
            assert b_lower is b_upper


class TestFragmentIonLookupQueryMethods:
    """Test fragment ion query methods"""

    def test_query_id(self):
        """Test query_id method"""
        if "y" in db:
            y_ion = db.query_id("y")
            assert y_ion is not None
            assert y_ion.id == "y"
            # Case insensitive
            assert db.query_id("Y") is y_ion

    def test_query_id_not_found(self):
        """Test query_id with non-existent ID"""
        result = db.query_id("notanion")
        assert result is None

    def test_query_name(self):
        """Test query_name method"""
        for ion in db:
            result = db.query_name(ion.name)
            assert result is not None
            assert result.name.lower() == ion.name.lower()
            break

    def test_query_name_not_found(self):
        """Test query_name with non-existent name"""
        result = db.query_name("NonExistentIonName")
        assert result is None

    def test_query_ion_type(self):
        """Test query_ion_type with IonType enum"""
        if hasattr(IonType, "b"):
            result = db.query_ion_type(IonType.b)
            assert result is not None
            assert result.id == "b"


class TestFragmentIonProperties:
    """Test IonTypeProperty flags and helper methods"""

    def test_is_forward(self):
        """Test is_forward property for a, b, c ions"""
        # a, b, c are forward ions
        for ion_id in ["a", "b", "c"]:
            if ion_id in db:
                ion = db[ion_id]
                assert ion.is_forward
                assert not ion.is_backward

    def test_is_backward(self):
        """Test is_backward property for x, y, z ions"""
        # x, y, z are backward ions
        for ion_id in ["x", "y", "z"]:
            if ion_id in db:
                ion = db[ion_id]
                assert ion.is_backward
                assert not ion.is_forward

    def test_is_internal(self):
        """Test is_internal property"""
        # Check if any internal ions exist
        for ion in db:
            if ion.is_internal:
                assert not ion.is_forward
                assert not ion.is_backward
                break

    def test_is_intact(self):
        """Test is_intact property for precursor ions"""
        # Check if precursor or neutral ions exist
        for ion in db:
            if ion.is_intact:
                # Intact ions should not be forward or backward
                assert not ion.is_forward
                assert not ion.is_backward
                break

    def test_property_flags(self):
        """Test IonTypeProperty flags are set correctly"""
        for ion in db:
            # Properties should be an IonTypeProperty flag
            assert isinstance(ion.properties, IonTypeProperty)
            # Check at least one property method works
            _ = ion.is_forward
            _ = ion.is_backward


class TestFragmentIonMethods:
    """Test FragmentIonInfo methods"""

    def test_get_mass_monoisotopic(self):
        """Test get_mass with monoisotopic=True"""
        for ion in db:
            if ion.monoisotopic_mass is not None:
                mass = ion.get_mass(monoisotopic=True)
                assert mass == ion.monoisotopic_mass
                assert isinstance(mass, float)
                break

    def test_get_mass_average(self):
        """Test get_mass with monoisotopic=False"""
        for ion in db:
            if ion.average_mass is not None:
                mass = ion.get_mass(monoisotopic=False)
                assert mass == ion.average_mass
                assert isinstance(mass, float)
                break

    def test_get_mass_not_available(self):
        """Test get_mass raises error when mass not available"""
        # Create a scenario or find an ion without mass
        for ion in db:
            if ion.monoisotopic_mass is None:
                with pytest.raises(ValueError):
                    ion.get_mass(monoisotopic=True)
                break

    def test_composition_property(self):
        """Test composition cached property"""
        for ion in db:
            if ion.dict_composition is not None:
                comp = ion.composition
                assert comp is not None
                assert len(comp) > 0
                break

    def test_composition_not_available(self):
        """Test composition raises error when not available"""
        for ion in db:
            if ion.dict_composition is None:
                with pytest.raises(ValueError):
                    _ = ion.composition
                break

    def test_to_dict(self):
        """Test to_dict conversion"""
        for ion in db:
            d = ion.to_dict()
            assert d["id"] == ion.id
            assert d["name"] == ion.name
            assert "formula" in d
            assert "monoisotopic_mass" in d
            assert "average_mass" in d
            assert "composition" in d
            break


class TestFragmentIonEdgeCases:
    """Test edge cases and error handling"""

    def test_getitem_not_found(self):
        """Test __getitem__ with non-existent key raises KeyError"""
        with pytest.raises(KeyError):
            _ = db["nonexistention"]

    def test_query_id_empty_string(self):
        """Test query_id with empty string"""
        result = db.query_id("")
        assert result is None

    def test_query_name_empty_string(self):
        """Test query_name with empty string"""
        result = db.query_name("")
        assert result is None


class TestFragmentIonDataIntegrity:
    """Test data integrity for fragment ions"""

    def test_all_ions_have_ids(self):
        """Test all ions have non-empty IDs"""
        for ion in db:
            assert ion.id is not None
            assert len(ion.id) > 0

    def test_all_ions_have_names(self):
        """Test all ions have non-empty names"""
        for ion in db:
            assert ion.name is not None
            assert len(ion.name) > 0

    def test_common_ions_exist(self):
        """Test that common fragment ions exist"""
        common_ions = ["a", "b", "c", "x", "y", "z"]
        found_count = 0
        for ion_id in common_ions:
            if ion_id in db:
                found_count += 1
        # At least some common ions should exist
        assert found_count > 0

    def test_masses_are_reasonable(self):
        """Test masses are within reasonable ranges"""
        for ion in db:
            if ion.monoisotopic_mass is not None:
                # Fragment ion masses can be negative or positive
                # but should be reasonable
                assert abs(ion.monoisotopic_mass) < 1000
            if ion.average_mass is not None:
                assert abs(ion.average_mass) < 1000

    def test_id_name_lookup_consistency(self):
        """Test that ID and name lookups return same object"""
        for ion in db:
            by_id = db.query_id(ion.id)
            by_name = db.query_name(ion.name)
            assert by_id is by_name
            break

    def test_ion_type_property(self):
        """Test ion_type property returns correct IonType"""
        for ion in db:
            ion_type = ion.ion_type
            assert isinstance(ion_type, IonType)
            assert ion_type.value == ion.id
            break


if __name__ == "__main__":
    pytest.main([__file__])
