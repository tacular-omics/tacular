"""``AALookup`` (singleton ``AA_LOOKUP``): query amino acids by one-letter code, three-letter code, or name."""

from collections import Counter
from collections.abc import Mapping
from functools import cached_property

from .._lookup import _BaseLookup
from ..elements import ElementInfo
from ..errors import TacularError
from .data import AMINO_ACID_INFOS, AminoAcid
from .dclass import AminoAcidInfo

__all__ = ["AA_LOOKUP", "ORDERED_AMINO_ACIDS", "AALookup"]


class AALookup(_BaseLookup[str, str, AminoAcidInfo]):
    """Amino acid lookup (singleton ``AA_LOOKUP``), keyed by one-letter code,
    three-letter code, or name (all case-insensitive).

    ``lookup[key]`` tries the one-letter code, then the three-letter code, then the
    name, and raises :class:`~tacular.TacularKeyError` if nothing matches (including
    keys that are not strings); ``get`` / ``in`` / ``query_*`` never raise.
    Iteration, :meth:`keys`, :meth:`values` and :meth:`items` follow one-letter-code
    order A-Z.
    """

    _kind = "Amino acid"

    def __init__(self, data: Mapping[AminoAcid, AminoAcidInfo]) -> None:
        """Build one-letter, three-letter, and name indexes from ``data``."""
        ordered = sorted(data.values(), key=lambda info: str(info.id))
        self._by_one_letter: dict[str, AminoAcidInfo] = {str(info.id): info for info in ordered}
        self._by_three_letter = {info.three_letter_code.lower(): info for info in ordered}
        self._by_name = {info.name.lower(): info for info in ordered}

    def _entries(self) -> Mapping[str, AminoAcidInfo]:
        return self._by_one_letter

    def _resolve(self, key: object) -> AminoAcidInfo | None:
        if not isinstance(key, str):
            return None
        return (
            self._by_one_letter.get(key.upper())
            or self._by_three_letter.get(key.lower())
            or self._by_name.get(key.lower())
        )

    def _miss_message(self, key: object) -> str:
        return f"Amino acid {key!r} not found by one-letter code, three-letter code, or name."

    def query_one_letter(self, code: str) -> AminoAcidInfo | None:
        """By one-letter code (case-insensitive); ``None`` if nothing matches."""
        return self._by_one_letter.get(code.upper()) if isinstance(code, str) else None

    def query_three_letter(self, code: str) -> AminoAcidInfo | None:
        """By three-letter code (case-insensitive); ``None`` if nothing matches."""
        return self._by_three_letter.get(code.lower()) if isinstance(code, str) else None

    def query_name(self, name: str) -> AminoAcidInfo | None:
        """By full name (case-insensitive); ``None`` if nothing matches."""
        return self._by_name.get(name.lower()) if isinstance(name, str) else None

    @cached_property
    def ordered_amino_acids(self) -> tuple[AminoAcidInfo, ...]:
        """All amino acids in one-letter-code order A-Z."""
        return tuple(self._by_one_letter.values())

    @cached_property
    def ambiguous_amino_acids(self) -> tuple[AminoAcidInfo, ...]:
        """Ambiguity codes (B, J, X, Z)."""
        return tuple(aa for aa in self.ordered_amino_acids if aa.is_ambiguous)

    @cached_property
    def mass_amino_acids(self) -> tuple[AminoAcidInfo, ...]:
        """Amino acids with both a monoisotopic and an average mass."""
        return tuple(
            aa for aa in self.ordered_amino_acids if aa.monoisotopic_mass is not None and aa.average_mass is not None
        )

    @cached_property
    def unambiguous_amino_acids(self) -> tuple[AminoAcidInfo, ...]:
        """Every amino acid except the ambiguity codes (B, J, X, Z)."""
        return tuple(aa for aa in self.ordered_amino_acids if not aa.is_ambiguous)

    @cached_property
    def mass_unambiguous_amino_acids(self) -> tuple[AminoAcidInfo, ...]:
        """Unambiguous amino acids with both masses defined."""
        return tuple(
            aa
            for aa in self.unambiguous_amino_acids
            if aa.monoisotopic_mass is not None and aa.average_mass is not None
        )

    def is_ambiguous(self, key: str) -> bool:
        """Whether ``key`` is an ambiguity code.

        Raises:
            TacularKeyError: if ``key`` matches no amino acid.
        """
        return self[key].is_ambiguous

    def is_mass_ambiguous(self, key: str) -> bool:
        """Whether ``key`` stands for residues of different masses.

        Raises:
            TacularKeyError: if ``key`` matches no amino acid.
        """
        return self[key].is_mass_ambiguous

    def is_unambiguous(self, key: str) -> bool:
        """``not is_ambiguous(key)``."""
        return not self[key].is_ambiguous

    def is_mass_unambiguous(self, key: str) -> bool:
        """``not is_mass_ambiguous(key)``."""
        return not self[key].is_mass_ambiguous

    def get_mass(self, key: str, *, monoisotopic: bool = True) -> float:
        """Monoisotopic (default) or average residue mass of ``key`` in Da.

        Raises:
            TacularKeyError: if ``key`` matches no amino acid.
            TacularError: if the amino acid has no such mass (e.g. ``B``).
        """
        mass = self[key].get_mass(monoisotopic=monoisotopic)
        if mass is None:
            kind = "monoisotopic" if monoisotopic else "average"
            raise TacularError(f"Amino acid {key!r} does not have a defined {kind} mass.")
        return mass

    def composition(self, key: str) -> Counter[ElementInfo]:
        """Elemental composition of ``key`` (a fresh copy).

        Raises:
            TacularKeyError: if ``key`` matches no amino acid.
            TacularError: if the amino acid has no defined composition (e.g. ``B``).
        """
        comp = self[key].composition
        if comp is None:
            raise TacularError(f"Amino acid {key!r} does not have a defined elemental composition.")
        return comp


AA_LOOKUP = AALookup(AMINO_ACID_INFOS)

ORDERED_AMINO_ACIDS: list[str] = [str(aa.id) for aa in AA_LOOKUP.ordered_amino_acids]
"""One-letter codes A-Z."""
