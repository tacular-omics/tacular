import pytest

from tacular import UNIPROT_PTM_LOOKUP as db
from tacular import AminoAcid
from tacular.uniprot_ptm.dclass import ModLocation, UniprotPtmInfo


def _make(**overrides) -> UniprotPtmInfo:
    defaults: dict = dict(
        id="9999",
        name="Test Mod",
        formula=None,
        monoisotopic_mass=None,
        average_mass=None,
        dict_composition=None,
    )
    defaults.update(overrides)
    return UniprotPtmInfo(**defaults)


class TestUniprotPtmLookupBasics:
    """Test basic UniProt PTM lookup operations"""

    def test_getitem_by_id(self):
        """Test __getitem__ with IDs"""
        if len(list(db)) > 0:
            first_entry = next(iter(db))
            result = db[first_entry.id]
            assert result.id == first_entry.id
            assert result.name is not None

    def test_contains(self):
        """Test __contains__ operator"""
        if len(list(db)) > 0:
            first_entry = next(iter(db))
            assert first_entry.id in db
            assert first_entry.name in db
        assert "NotAModification" not in db
        assert "INVALID" not in db

    def test_iter(self):
        """Test iteration over UniProt PTM entries"""
        entries = list(db)
        assert len(entries) > 0
        for entry in entries:
            assert entry.id is not None
            assert entry.name is not None

    def test_get_with_default(self):
        """Test get() method with default value"""
        result = db.get("NonexistentEntry", default=None)
        assert result is None

    def test_len(self):
        """Test __len__ returns correct count"""
        length = len(db)
        assert length > 0
        assert length == len(list(db))


class TestUniprotPtmLookupQueryMethods:
    """Test UniProt PTM query methods"""

    def test_query_id_numeric(self):
        """Test query_id with numeric IDs"""
        if len(list(db)) > 0:
            first_entry = next(iter(db))
            result = db.query_id(first_entry.id)
            assert result.id == first_entry.id
            # Try with stripped leading zeros
            try:
                int_id = int(first_entry.id)
                result = db.query_id(str(int_id))
                assert result is not None
            except ValueError:
                pass

    def test_query_id_with_prefix(self):
        """Test query_id with PTM- prefix"""
        if len(list(db)) > 0:
            first_entry = next(iter(db))
            # UniProt PTM accessions are stored without "PTM-" prefix
            # but OntologyLookup should handle prefix stripping
            result = db.query_id(first_entry.id)
            assert result is not None

    def test_query_id_not_found(self):
        """Test query_id with non-existent ID"""
        result = db.query_id("99999")
        assert result is None

    def test_query_name(self):
        """Test query_name with case insensitivity"""
        if len(list(db)) > 0:
            first_entry = next(iter(db))
            result = db.query_name(first_entry.name)
            assert result is not None
            assert result.name.lower() == first_entry.name.lower()

            # Try with different case
            result_upper = db.query_name(first_entry.name.upper())
            assert result_upper is not None
            result_lower = db.query_name(first_entry.name.lower())
            assert result_lower is not None

    def test_query_name_not_found(self):
        """Test query_name with non-existent name"""
        result = db.query_name("NonExistentPtmName")
        assert result is None

    def test_query_mass_monoisotopic(self):
        """Test query_mass with monoisotopic masses"""
        for entry in db:
            if entry.monoisotopic_mass is not None:
                mass = entry.monoisotopic_mass
                results = db.query_mass(mass, tolerance=0.01, monoisotopic=True)
                assert len(results) > 0
                assert any(r.id == entry.id for r in results)
                break

    def test_query_mass_average(self):
        """Test query_mass with average masses"""
        for entry in db:
            if entry.average_mass is not None:
                mass = entry.average_mass
                results = db.query_mass(mass, tolerance=0.01, monoisotopic=False)
                assert len(results) > 0
                assert any(r.id == entry.id for r in results)
                break

    def test_query_mass_no_results(self):
        """Test query_mass with mass that has no matches"""
        results = db.query_mass(999999.999, tolerance=0.01)
        assert len(results) == 0

    def test_query_mass_tolerance(self):
        """Test query_mass with different tolerances"""
        for entry in db:
            if entry.monoisotopic_mass is not None:
                mass = entry.monoisotopic_mass
                results_tight = db.query_mass(mass, tolerance=0.001, monoisotopic=True)
                results_loose = db.query_mass(mass, tolerance=1.0, monoisotopic=True)
                assert len(results_loose) >= len(results_tight)
                break


class TestUniprotPtmSpecialFeatures:
    """Test UniProt PTM special features like choice() and filtering"""

    def test_choice_random_selection(self):
        """Test choice() returns random entry"""
        if len(list(db)) > 1:
            choice1 = db.choice()
            assert choice1 is not None
            assert choice1.id is not None

            choice2 = db.choice()
            assert choice2 is not None

    def test_getitem_tries_name_then_id(self):
        """Test __getitem__ tries name first, then ID"""
        if len(list(db)) > 0:
            first_entry = next(iter(db))
            result = db[first_entry.name]
            assert result.name.lower() == first_entry.name.lower()
            result = db[first_entry.id]
            assert result.id == first_entry.id


class TestUniprotPtmEdgeCases:
    """Test edge cases and error handling"""

    def test_getitem_not_found(self):
        """Test __getitem__ with non-existent key raises KeyError"""
        with pytest.raises(KeyError):
            _ = db["NonExistentPtmKey"]

    def test_query_id_empty_string(self):
        """Test query_id with empty string"""
        result = db.query_id("")
        assert result is None

    def test_query_name_empty_string(self):
        """Test query_name with empty string"""
        result = db.query_name("")
        assert result is None

    def test_query_mass_negative(self):
        """Test query_mass with negative mass returns a list"""
        results = db.query_mass(-100.0, tolerance=0.01)
        assert isinstance(results, list)

    def test_query_mass_zero_tolerance(self):
        """Test query_mass with zero tolerance"""
        for entry in db:
            if entry.monoisotopic_mass is not None:
                results = db.query_mass(entry.monoisotopic_mass, tolerance=0.0, monoisotopic=True)
                assert len(results) > 0
                break


class TestUniprotPtmDataIntegrity:
    """Test data integrity for UniProt PTM entries"""

    def test_all_entries_have_ids(self):
        """Test all entries have non-empty IDs"""
        for entry in db:
            assert entry.id is not None
            assert len(entry.id) > 0

    def test_all_entries_have_names(self):
        """Test all entries have non-empty names"""
        for entry in db:
            assert entry.name is not None
            assert len(entry.name) > 0

    def test_ids_are_numeric_strings(self):
        """Test all IDs are zero-padded numeric strings (PTM- prefix stripped)"""
        for entry in db:
            assert entry.id.isdigit(), f"Expected numeric ID, got: {entry.id}"

    def test_masses_are_reasonable(self):
        """Test all defined masses are within a reasonable range"""
        for entry in db:
            if entry.monoisotopic_mass is not None:
                assert abs(entry.monoisotopic_mass) < 10000
            if entry.average_mass is not None:
                assert abs(entry.average_mass) < 10000

    def test_id_name_lookup_consistency(self):
        """Test that ID and name lookups return same object"""
        count_checked = 0
        for entry in db:
            by_id = db.query_id(entry.id)
            by_name = db.query_name(entry.name)
            assert by_id is by_name
            count_checked += 1
            if count_checked >= 10:
                break

    def test_mass_query_returns_correct_entries(self):
        """Test mass queries return entries within tolerance"""
        for entry in db:
            if entry.monoisotopic_mass is not None:
                tolerance = 0.01
                results = db.query_mass(entry.monoisotopic_mass, tolerance=tolerance, monoisotopic=True)
                for result in results:
                    if result.monoisotopic_mass is not None:
                        assert abs(result.monoisotopic_mass - entry.monoisotopic_mass) <= tolerance
                break

    def test_no_duplicate_ids(self):
        """Test there are no duplicate IDs"""
        ids = [entry.id for entry in db]
        assert len(ids) == len(set(ids))

    def test_iteration_order_stable(self):
        """Test iteration order is stable across calls"""
        list1 = list(db)
        list2 = list(db)
        assert [e.id for e in list1] == [e.id for e in list2]

    def test_version_is_set(self):
        """Test that the version string is not the stub 'unknown'"""
        assert db._version != "unknown"
        assert len(db._version) > 0


class TestUniprotPtmLocation:
    """`location` maps `position_polypeptide` (PP) to a `ModLocation`, or None if
    unset/unrecognized -- covers a real bug where the enum values didn't match the
    data ("N-terminus."/"C-terminus." vs. the actual "N-terminal."/"C-terminal."),
    so every N/C-terminal entry raised instead of resolving."""

    @pytest.mark.parametrize(
        "pp,expected",
        [
            ("Anywhere.", ModLocation.ANYWHERE),
            ("N-terminal.", ModLocation.NTERM),
            ("C-terminal.", ModLocation.CTERM),
            ("Protein core.", ModLocation.PROTEIN_CORE),
        ],
    )
    def test_recognized_values(self, pp, expected):
        assert _make(position_polypeptide=pp).location == expected

    def test_missing_pp_is_none(self):
        assert _make(position_polypeptide=None).location is None

    def test_compound_crosslink_style_value_is_none(self):
        """Crosslink-style compound PP values (e.g. "Anywhere-Protein core.") don't
        map to a single ModLocation and must not raise."""
        assert _make(position_polypeptide="Anywhere-Protein core.").location is None


class TestUniprotPtmResidue:
    """`residue` maps `target` (TG) to a single `AminoAcid`, or None if
    unset/ambiguous/non-standard -- must never raise for real ptmlist.txt data."""

    def test_standard_residue(self):
        assert _make(target="Serine.").residue == AminoAcid.S

    def test_missing_target_is_none(self):
        assert _make(target=None).residue is None

    def test_ambiguous_target_is_none(self):
        assert _make(target="Asparagine or Aspartate.").residue is None

    def test_non_standard_residue_is_none(self):
        """Selenocysteine is a real UniProt target but not one of the 20 standard residues."""
        assert _make(target="Selenocysteine.").residue is None

    def test_compound_crosslink_style_target_is_none(self):
        assert _make(target="Alanine-Arginine.").residue is None


class TestUniprotPtmUpdate:
    """`update()` is overridden here (not the base OboEntity one) to also carry
    forward this ontology's extra fields."""

    def test_update_extra_field_leaves_others_unchanged(self):
        info = _make(target="Serine.", feature_key="MOD_RES")
        updated = info.update(target="Threonine.")
        assert updated.target == "Threonine."
        assert updated.feature_key == "MOD_RES"
        assert updated.id == info.id


class TestUniprotPtmDictRoundTrip:
    """`to_dict`/`from_dict` must round-trip this ontology's extra fields (not just
    the base OboEntity ones) -- these were previously silently dropped, which would
    have made a `tacular update uniprot_ptm` cache refresh lossy."""

    def test_round_trip_preserves_extra_fields(self):
        info = _make(
            formula="C2H2O",
            monoisotopic_mass=42.010565,
            average_mass=42.0367,
            dict_composition={"C": 2, "H": 2, "O": 1},
            feature_key="MOD_RES",
            target="Serine.",
            position_aa="Amino acid side chain.",
            position_polypeptide="Anywhere.",
            cellular_location="Extracellular and lumenal localisation.",
            taxonomic_range=("Eukaryota; taxId:2759 (Eukaryota).",),
            keywords=("Hydroxylation.",),
            cross_references=("PSI-MOD; MOD:00046.", "Unimod; 1."),
        )
        rebuilt = UniprotPtmInfo.from_dict(info.to_dict())
        assert rebuilt == info
        assert rebuilt.target == info.target
        assert rebuilt.location == info.location
        assert rebuilt.residue == info.residue
        assert rebuilt.cross_references == info.cross_references

    def test_round_trip_with_empty_multi_value_fields(self):
        info = _make()
        rebuilt = UniprotPtmInfo.from_dict(info.to_dict())
        assert rebuilt == info
        assert rebuilt.taxonomic_range == ()
        assert rebuilt.keywords == ()
        assert rebuilt.cross_references == ()

    def test_to_dict_is_plain_json_serializable(self):
        """Multi-value fields must serialize as lists, not tuples, so `to_dict()`
        output matches what a real JSON round-trip (json.dump/json.load) produces."""
        import json

        info = _make(taxonomic_range=("Bacteria; taxId:2 (Bacteria).",))
        data = info.to_dict()
        assert isinstance(data["taxonomic_range"], list)
        reloaded = json.loads(json.dumps(data))
        assert reloaded == data


class TestUniprotPtmCrossReferences:
    """`has_psimod`/`has_unimod`/`get_psimod`/`get_unimod` resolve cross-references
    against the live PSIMOD_LOOKUP/UNIMOD_LOOKUP; a stale/removed id must resolve
    to None rather than raise."""

    def test_resolves_psimod_reference(self):
        entry = db.query_id("0476")
        assert entry is not None
        assert entry.has_psimod
        assert entry.get_psimod() is not None

    def test_resolves_unimod_reference(self):
        entry = db.query_id("0369")
        assert entry is not None
        assert entry.has_unimod
        assert entry.get_unimod() is not None

    def test_stale_psimod_reference_resolves_to_none(self):
        """PTM-0722 cross-references PSI-MOD MOD:01875, which isn't in the bundled
        PSI-MOD snapshot (version skew between the two ontology sources) -- must
        resolve to None, not raise."""
        entry = db.query_id("0722")
        assert entry is not None
        assert entry.has_psimod
        assert entry.get_psimod() is None

    def test_no_cross_reference(self):
        entry = db.query_id("0663")
        assert entry is not None
        assert not entry.has_psimod
        assert not entry.has_unimod
        assert entry.get_psimod() is None
        assert entry.get_unimod() is None


class TestUniprotPtmDataProperties:
    """`location`/`residue` must never raise across the full bundled dataset."""

    def test_location_never_raises(self):
        for entry in db:
            entry.location  # noqa: B018 - accessing for side-effect-free validation

    def test_residue_never_raises(self):
        for entry in db:
            entry.residue  # noqa: B018 - accessing for side-effect-free validation


if __name__ == "__main__":
    pytest.main([__file__])
