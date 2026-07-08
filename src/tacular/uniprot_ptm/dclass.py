from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from typing import TYPE_CHECKING, Any, Self

from ..amino_acids import AminoAcid
from ..obo_entity import OboEntity

if TYPE_CHECKING:
    from ..psimod.dclass import PsimodInfo
    from ..unimod.dclass import UnimodInfo


class ModLocation(StrEnum):
    """Enum for the polypeptide-position values ("PP" field) used by UniProt PTM entries."""

    ANYWHERE = "Anywhere."
    NTERM = "N-terminal."
    CTERM = "C-terminal."
    PROTEIN_CORE = "Protein core."


@dataclass(frozen=True, slots=True)
class UniprotPtmInfo(OboEntity):
    """A UniProt PTM entry (one ``ptmlist.txt`` record).

    Adds UniProt-specific fields on top of :class:`~tacular.OboEntity`'s id/name/
    formula/mass/composition; see :attr:`location` and :attr:`residue` for derived
    single-value views of :attr:`position_polypeptide` and :attr:`target`.
    """

    feature_key: str | None = field(default=None)
    """UniProt feature key (``FT``), e.g. ``"MOD_RES"``, ``"CARBOHYD"``, ``"LIPID"``."""
    target: str | None = field(default=None)
    """Target amino acid name (``TG``), e.g. ``"Serine."``. See :attr:`residue`."""
    position_aa: str | None = field(default=None)
    """Position of the modification on the amino acid (``PA``), e.g. ``"Amino acid side chain."``."""
    position_polypeptide: str | None = field(default=None)
    """Position of the modification in the polypeptide (``PP``). See :attr:`location`."""
    cellular_location: str | None = field(default=None)
    """Cellular location (``LC``), if given."""
    taxonomic_range: tuple[str, ...] = field(default=())
    """Taxonomic range entries (``TR``), one per occurrence."""
    keywords: tuple[str, ...] = field(default=())
    """Keyword entries (``KW``), one per occurrence."""
    cross_references: tuple[str, ...] = field(default=())
    """Cross-reference entries (``DR``), e.g. ``"PSI-MOD; MOD:01624."``. See :attr:`has_psimod`/:meth:`get_psimod`."""

    @property
    def id_tag(self) -> str:
        """`id` with leading zeros stripped, e.g. ``"0450"`` -> ``"450"``."""
        return self.id.lstrip("0")

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> Self:
        """Reconstruct a UniprotPtmInfo from its ``to_dict`` representation.

        Extends the base id/name/formula/mass/composition fields (see
        :meth:`OboEntity.from_dict`) with this ontology's extra fields, so a
        value round-tripped through :mod:`tacular._cache` keeps them.
        """
        return cls(
            id=data["id"],
            name=data["name"],
            formula=data.get("formula"),
            monoisotopic_mass=data.get("monoisotopic_mass"),
            average_mass=data.get("average_mass"),
            dict_composition=data.get("composition"),
            feature_key=data.get("feature_key"),
            target=data.get("target"),
            position_aa=data.get("position_aa"),
            position_polypeptide=data.get("position_polypeptide"),
            cellular_location=data.get("cellular_location"),
            taxonomic_range=tuple(data.get("taxonomic_range") or ()),
            keywords=tuple(data.get("keywords") or ()),
            cross_references=tuple(data.get("cross_references") or ()),
        )

    def to_dict(self, float_precision: int | None = 6) -> dict[str, object]:
        """Convert to a dictionary, extending :meth:`OboEntity.to_dict` with this
        ontology's extra fields (see :meth:`from_dict` for the inverse).

        Note:
            Calls ``OboEntity.to_dict(self, ...)`` explicitly rather than zero-arg
            ``super()``: ``@dataclass(slots=True)`` rebuilds the class object,
            which leaves zero-arg ``super()`` referencing a stale ``__class__``
            cell and raises ``TypeError: super(type, obj): obj must be an
            instance or subtype of type``.
        """
        data = OboEntity.to_dict(self, float_precision)
        data.update(
            feature_key=self.feature_key,
            target=self.target,
            position_aa=self.position_aa,
            position_polypeptide=self.position_polypeptide,
            cellular_location=self.cellular_location,
            # Lists, not tuples: to_dict's output must be plain-JSON-serializable, and match
            # what a JSON round-trip (json.dump then json.load) produces byte-for-byte.
            taxonomic_range=list(self.taxonomic_range),
            keywords=list(self.keywords),
            cross_references=list(self.cross_references),
        )
        return data

    def update(self, **kwargs: Any) -> Self:
        """Return a new instance with updated fields."""
        return self.__class__(
            id=kwargs.get("id", self.id),
            name=kwargs.get("name", self.name),
            formula=kwargs.get("formula", self.formula),
            monoisotopic_mass=kwargs.get("monoisotopic_mass", self.monoisotopic_mass),
            average_mass=kwargs.get("average_mass", self.average_mass),
            dict_composition=kwargs.get("dict_composition", self.dict_composition),
            feature_key=kwargs.get("feature_key", self.feature_key),
            target=kwargs.get("target", self.target),
            position_aa=kwargs.get("position_aa", self.position_aa),
            position_polypeptide=kwargs.get("position_polypeptide", self.position_polypeptide),
            cellular_location=kwargs.get("cellular_location", self.cellular_location),
            taxonomic_range=kwargs.get("taxonomic_range", self.taxonomic_range),
            keywords=kwargs.get("keywords", self.keywords),
            cross_references=kwargs.get("cross_references", self.cross_references),
        )

    # ------------------------------------------------------------------
    # Cross-reference helpers
    # ------------------------------------------------------------------

    def _psimod_id(self) -> str | None:
        """The referenced PSI-MOD id (e.g. ``"01624"``), or ``None`` if not cross-referenced."""
        for ref in self.cross_references:
            if ref.startswith("PSI-MOD; MOD:"):
                return ref[len("PSI-MOD; MOD:") :].rstrip(".")
        return None

    def _unimod_id(self) -> str | None:
        """The referenced UNIMOD id (e.g. ``"1"``), or ``None`` if not cross-referenced."""
        for ref in self.cross_references:
            if ref.startswith("Unimod; "):
                return ref[len("Unimod; ") :].rstrip(".")
        return None

    @property
    def has_psimod(self) -> bool:
        """Whether this entry cross-references a PSI-MOD id."""
        return self._psimod_id() is not None

    @property
    def has_unimod(self) -> bool:
        """Whether this entry cross-references a UNIMOD id."""
        return self._unimod_id() is not None

    def get_psimod(self) -> PsimodInfo | None:
        """The cross-referenced :class:`~tacular.PsimodInfo`, or ``None`` if not
        cross-referenced (or the referenced id no longer resolves)."""
        from ..psimod import PSIMOD_LOOKUP

        mod_id = self._psimod_id()
        if mod_id is None:
            return None
        return PSIMOD_LOOKUP.query_id(mod_id)

    def get_unimod(self) -> UnimodInfo | None:
        """The cross-referenced :class:`~tacular.UnimodInfo`, or ``None`` if not
        cross-referenced (or the referenced id no longer resolves)."""
        from ..unimod import UNIMOD_LOOKUP

        mod_id = self._unimod_id()
        if mod_id is None:
            return None
        return UNIMOD_LOOKUP.query_id(mod_id)

    @property
    def location(self) -> ModLocation | None:
        """:attr:`position_polypeptide` as a :class:`ModLocation`, or ``None`` if
        unset or not a single recognized value (e.g. a crosslink's compound
        ``"Anywhere-Protein core."``)."""
        try:
            return ModLocation(self.position_polypeptide)
        except ValueError:
            return None

    @property
    def residue(self) -> AminoAcid | None:
        """:attr:`target` as a single :class:`~tacular.AminoAcid`, or ``None`` if
        unset or not one of the 20 standard residues (e.g. an ambiguous
        ``"Asparagine or Aspartate."`` or a crosslink's compound target)."""
        match self.target:
            case "Alanine.":
                return AminoAcid.A
            case "Arginine.":
                return AminoAcid.R
            case "Asparagine.":
                return AminoAcid.N
            case "Aspartate.":
                return AminoAcid.D
            case "Cysteine.":
                return AminoAcid.C
            case "Glutamate.":
                return AminoAcid.E
            case "Glutamine.":
                return AminoAcid.Q
            case "Glycine.":
                return AminoAcid.G
            case "Histidine.":
                return AminoAcid.H
            case "Isoleucine.":
                return AminoAcid.I
            case "Leucine.":
                return AminoAcid.L
            case "Lysine.":
                return AminoAcid.K
            case "Methionine.":
                return AminoAcid.M
            case "Phenylalanine.":
                return AminoAcid.F
            case "Proline.":
                return AminoAcid.P
            case "Serine.":
                return AminoAcid.S
            case "Threonine.":
                return AminoAcid.T
            case "Tryptophan.":
                return AminoAcid.W
            case "Tyrosine.":
                return AminoAcid.Y
            case "Valine.":
                return AminoAcid.V
            case _:
                return None
