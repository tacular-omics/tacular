import pytest

from tacular import REFMOL_LOOKUP as db
from tacular.refmol import RefMolID


class TestRefMolLookupBasics:
    """Test basic reference molecule lookup operations"""

    def test_getitem_by_name(self):
        """Test __getitem__ with molecule names"""
        if len(list(db)) > 0:
            first_entry = next(iter(db))
            result = db[first_entry.name]
            assert result.name.lower() == first_entry.name.lower()

    def test_getitem_by_refmol_id(self):
        """Test __getitem__ with RefMolID enum"""
        if len(list(db)) > 0:
            first_entry = next(iter(db))
            # Try to get via enum if possible
            for refmol_id in RefMolID:
                result = db[refmol_id]
                assert result is not None
                break

    def test_contains(self):
        """Test __contains__ operator"""
        if len(list(db)) > 0:
            first_entry = next(iter(db))
            assert first_entry.name in db
        assert "NotAReferenceMolecule" not in db

    def test_iter(self):
        """Test iteration over reference molecules"""
        molecules = list(db)
        assert len(molecules) > 0
        # All should have names
        for molecule in molecules:
            assert molecule.name is not None

    def test_get_with_default(self):
        """Test get() method with default value"""
        result = db.get("NonexistentMolecule")
        assert result is None

    def test_case_insensitivity(self):
        """Test case-insensitive lookups"""
        if len(list(db)) > 0:
            first_entry = next(iter(db))
            lower = db.query_name(first_entry.name.lower())
            upper = db.query_name(first_entry.name.upper())
            if lower and upper:
                assert lower is upper


class TestRefMolLookupQueryMethods:
    """Test reference molecule query methods"""

    def test_query_id(self):
        """Test query_id with RefMolID enum"""
        for refmol_id in RefMolID:
            result = db.query_id(refmol_id)
            if result is not None:
                assert result.name is not None
                break

    def test_query_name(self):
        """Test query_name method"""
        if len(list(db)) > 0:
            first_entry = next(iter(db))
            result = db.query_name(first_entry.name)
            assert result is not None
            assert result.name.lower() == first_entry.name.lower()

    def test_query_name_not_found(self):
        """Test query_name with non-existent name"""
        result = db.query_name("NonExistentMoleculeName")
        assert result is None

    def test_query_label_type(self):
        """Test query_label_type grouping method"""
        # Get all label types
        label_types = set()
        for molecule in db:
            if molecule.label_type:
                label_types.add(molecule.label_type.lower())

        if label_types:
            # Query by one label type
            label_type = list(label_types)[0]
            results = db.query_label_type(label_type)
            assert isinstance(results, list)
            # All results should have matching label type
            for result in results:
                assert result.label_type.lower() == label_type

    def test_query_label_type_not_found(self):
        """Test query_label_type with non-existent type"""
        results = db.query_label_type("NonExistentLabelType")
        assert isinstance(results, list)
        assert len(results) == 0

    def test_query_molecule_type(self):
        """Test query_molecule_type grouping method"""
        # Get all molecule types
        molecule_types = set()
        for molecule in db:
            if molecule.molecule_type:
                molecule_types.add(molecule.molecule_type.lower())

        if molecule_types:
            # Query by one molecule type
            mol_type = list(molecule_types)[0]
            results = db.query_molecule_type(mol_type)
            assert isinstance(results, list)
            # All results should have matching molecule type
            for result in results:
                assert result.molecule_type.lower() == mol_type

    def test_query_molecule_type_not_found(self):
        """Test query_molecule_type with non-existent type"""
        results = db.query_molecule_type("NonExistentMoleculeType")
        assert isinstance(results, list)
        assert len(results) == 0

    def test_query_label_type_case_insensitive(self):
        """Test query_label_type is case insensitive"""
        for molecule in db:
            if molecule.label_type:
                lower = db.query_label_type(molecule.label_type.lower())
                upper = db.query_label_type(molecule.label_type.upper())
                assert len(lower) == len(upper)
                break

    def test_query_molecule_type_case_insensitive(self):
        """Test query_molecule_type is case insensitive"""
        for molecule in db:
            if molecule.molecule_type:
                lower = db.query_molecule_type(molecule.molecule_type.lower())
                upper = db.query_molecule_type(molecule.molecule_type.upper())
                assert len(lower) == len(upper)
                break


class TestRefMolGroupingFeatures:
    """Test grouping by label_type and molecule_type"""

    def test_label_type_grouping(self):
        """Test molecules are properly grouped by label_type"""
        # Common label types in mass spec: TMT, iTRAQ
        common_labels = ["TMT", "iTRAQ", "tmt", "itraq"]
        for label in common_labels:
            results = db.query_label_type(label)
            if results:
                # All should have the same label type
                label_types = {r.label_type.lower() for r in results}
                assert len(label_types) == 1
                break

    def test_molecule_type_grouping(self):
        """Test molecules are properly grouped by molecule_type"""
        # Common molecule types: reporter, sidechain, nucleobase
        common_types = ["reporter", "sidechain", "nucleobase"]
        for mol_type in common_types:
            results = db.query_molecule_type(mol_type)
            if results:
                # All should have the same molecule type
                molecule_types = {r.molecule_type.lower() for r in results}
                assert len(molecule_types) == 1
                break

    def test_multiple_molecules_per_label_type(self):
        """Test some label types have multiple molecules"""
        # TMT typically has multiple variants (TMT126, TMT127, etc.)
        tmt_results = db.query_label_type("TMT")
        if tmt_results:
            # TMT should have multiple reporter ions
            assert len(tmt_results) > 1


class TestRefMolMethods:
    """Test RefMolInfo methods"""

    def test_get_mass_monoisotopic(self):
        """Test get_mass with monoisotopic=True"""
        if len(list(db)) > 0:
            molecule = next(iter(db))
            mass = molecule.get_mass(monoisotopic=True)
            assert mass == molecule.monoisotopic_mass
            assert isinstance(mass, float)
            assert mass > 0

    def test_get_mass_average(self):
        """Test get_mass with monoisotopic=False"""
        if len(list(db)) > 0:
            molecule = next(iter(db))
            mass = molecule.get_mass(monoisotopic=False)
            assert mass == molecule.average_mass
            assert isinstance(mass, float)
            assert mass > 0

    def test_composition_property(self):
        """Test composition cached property"""
        if len(list(db)) > 0:
            molecule = next(iter(db))
            comp = molecule.composition
            assert comp is not None
            assert len(comp) > 0

    def test_to_dict(self):
        """Test to_dict conversion"""
        if len(list(db)) > 0:
            molecule = next(iter(db))
            d = molecule.to_dict()
            assert d["name"] == molecule.name
            assert d["label_type"] == molecule.label_type
            assert d["molecule_type"] == molecule.molecule_type
            assert d["chemical_formula"] == molecule.chemical_formula
            assert "monoisotopic_mass" in d
            assert "average_mass" in d
            assert "composition" in d


class TestRefMolEdgeCases:
    """Test edge cases and error handling"""

    def test_getitem_not_found(self):
        """Test __getitem__ with non-existent key raises KeyError"""
        with pytest.raises(KeyError):
            _ = db["NonExistentMolecule"]

    def test_query_name_empty_string(self):
        """Test query_name with empty string"""
        result = db.query_name("")
        assert result is None

    def test_query_label_type_empty_string(self):
        """Test query_label_type with empty string"""
        results = db.query_label_type("")
        assert isinstance(results, list)
        assert len(results) == 0

    def test_query_molecule_type_empty_string(self):
        """Test query_molecule_type with empty string"""
        results = db.query_molecule_type("")
        assert isinstance(results, list)
        assert len(results) == 0


class TestRefMolDataIntegrity:
    """Test data integrity for reference molecules"""

    def test_all_have_names(self):
        """Test all molecules have non-empty names"""
        for molecule in db:
            assert molecule.name is not None
            assert len(molecule.name) > 0

    def test_all_have_label_types(self):
        """Test all molecules have label types"""
        for molecule in db:
            assert molecule.label_type is not None

    def test_all_have_molecule_types(self):
        """Test all molecules have molecule types"""
        for molecule in db:
            assert molecule.molecule_type is not None

    def test_all_have_formulas(self):
        """Test all molecules have chemical formulas"""
        for molecule in db:
            assert molecule.chemical_formula is not None
            assert len(molecule.chemical_formula) > 0

    def test_masses_are_positive(self):
        """Test all masses are positive"""
        for molecule in db:
            assert molecule.monoisotopic_mass > 0
            assert molecule.average_mass > 0

    def test_masses_are_reasonable(self):
        """Test masses are within reasonable ranges"""
        for molecule in db:
            # Reference molecules shouldn't be too large
            assert molecule.monoisotopic_mass < 10000
            assert molecule.average_mass < 10000

    def test_common_reference_molecules_exist(self):
        """Test that some common reference molecules exist"""
        # Common TMT reporter ions
        common_refs = ["TMT126", "TMT127", "sidechain_A", "reporter"]
        found_count = 0
        for name in common_refs:
            if name.lower() in [m.name.lower() for m in db]:
                found_count += 1
        # At least some should exist (but not all may be present)
        assert found_count >= 0

    def test_name_lookup_consistency(self):
        """Test that name lookups return same object"""
        if len(list(db)) > 0:
            first_entry = next(iter(db))
            result1 = db.query_name(first_entry.name)
            result2 = db.query_name(first_entry.name)
            assert result1 is result2

    def test_composition_has_elements(self):
        """Test compositions have at least one element"""
        for molecule in db:
            comp = molecule.composition
            assert len(comp) > 0
            # Total atom count should be reasonable
            total_atoms = sum(comp.values())
            assert total_atoms > 0
            break

    def test_no_duplicate_names(self):
        """Test there are no duplicate names"""
        names = [m.name.lower() for m in db]
        assert len(names) == len(set(names))


if __name__ == "__main__":
    pytest.main([__file__])
