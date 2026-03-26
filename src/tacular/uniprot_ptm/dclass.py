from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import TYPE_CHECKING, Any, Self

from tacular import AminoAcid

from ..obo_entity import OboEntity

if TYPE_CHECKING:
    from ..psimod.dclass import PsimodInfo
    from ..unimod.dclass import UnimodInfo


class ModLocation(StrEnum):
    """Enum for PTM location types"""

    ANYWHERE = "Anywhere."
    NTERM = "N-terminus."
    CTERM = "C-terminus."


@dataclass(frozen=True, slots=True)
class UniprotPtmInfo(OboEntity):
    """Class to store information about a UniProt PTM entry"""

    feature_key: str | None = field(default=None)  # FT
    target: str | None = field(default=None)  # TG
    position_aa: str | None = field(default=None)  # PA
    position_polypeptide: str | None = field(default=None)  # PP
    cellular_location: str | None = field(default=None)  # LC
    taxonomic_range: tuple[str, ...] = field(default=())  # TR (multi-value)
    keywords: tuple[str, ...] = field(default=())  # KW (multi-value)
    cross_references: tuple[str, ...] = field(default=())  # DR (multi-value)

    @property
    def id_tag(self) -> str:
        return self.id.lstrip("0")

    def update(self, **kwargs: Any) -> Self:
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
        for ref in self.cross_references:
            if ref.startswith("PSI-MOD; MOD:"):
                return ref[len("PSI-MOD; MOD:") :].rstrip(".")
        return None

    def _unimod_id(self) -> str | None:
        for ref in self.cross_references:
            if ref.startswith("Unimod; "):
                return ref[len("Unimod; ") :].rstrip(".")
        return None

    @property
    def has_psimod(self) -> bool:
        return self._psimod_id() is not None

    @property
    def has_unimod(self) -> bool:
        return self._unimod_id() is not None

    def get_psimod(self) -> PsimodInfo | None:
        from ..psimod import PSIMOD_LOOKUP

        mod_id = self._psimod_id()
        if mod_id is None:
            return None
        return PSIMOD_LOOKUP.query_id(mod_id)

    def get_unimod(self) -> UnimodInfo | None:
        from ..unimod import UNIMOD_LOOKUP

        mod_id = self._unimod_id()
        if mod_id is None:
            return None
        return UNIMOD_LOOKUP.query_id(mod_id)

    @property
    def location(self) -> ModLocation:
        match self.position_polypeptide:
            case ModLocation.NTERM.value:
                return ModLocation.NTERM
            case ModLocation.CTERM.value:
                return ModLocation.CTERM
            case ModLocation.ANYWHERE.value:
                return ModLocation.ANYWHERE
            case _:
                raise ValueError(f"Unknown modification location: {self.position_polypeptide}")

    @property
    def residue(self) -> AminoAcid:
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
                raise ValueError(f"Unknown target amino acid: {self.target}")
