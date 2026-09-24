"""tacular: lookups for amino acids, elements, and mass spectrometry ontologies.

Each ontology (UNIMOD, PSI-MOD, RESID, XLMOD, GNOme, UniProt-PTM) and data type
(amino acids, elements, fragment ion types, monosaccharides, neutral losses,
proteases, mzPAF reference molecules) exposes a module-level ``*_LOOKUP``
singleton -- e.g. ``UNIMOD_LOOKUP``, ``ELEMENT_LOOKUP``. The 6 ontology lookups
share the :class:`~tacular.obo_lookup.OntologyLookup` and :class:`OboEntity` base
classes in ``obo_lookup.py`` / ``obo_entity.py``; the other data types have their
own lookup classes. Every lookup supports ``lookup[key]``, ``get``, ``in``,
``len``, iteration, ``keys``, ``values`` and ``items``; a miss raises
:class:`TacularKeyError`. Query by id, name, or (for ontologies) approximate mass;
see each lookup class's docstring for its specific query methods. Physical
constants (proton, electron, neutron masses) are in :mod:`tacular.constants`.

Data for the 6 refreshable ontologies (5 OBO-sourced, plus UniProt-PTM from its
own flat-file format) ships baked into the package as of the version above, but
can be refreshed to the latest upstream release without reinstalling via the
``tacular update`` CLI (see :mod:`tacular.update`); each lookup transparently
prefers a refreshed cache over the bundled copy if one exists (see
:mod:`tacular._cache`).
"""

from importlib import import_module
from typing import TYPE_CHECKING

from . import constants as constants
from .amino_acids import AA_LOOKUP, AMINO_ACID_INFOS, ORDERED_AMINO_ACIDS, AALookup, AminoAcid, AminoAcidInfo
from .elements import ELEMENT_LOOKUP, Element, ElementInfo, ElementKey, ElementLookup, parse_composition
from .errors import TacularError, TacularKeyError
from .ion_types import FRAGMENT_ION_LOOKUP, FragmentIonInfo, FragmentIonLookup, IonType, IonTypeLiteral, IonTypeProperty
from .labels import (
    ISOBARIC_TAG_LOOKUP,
    SILAC_LOOKUP,
    IsobaricTagInfo,
    IsobaricTagLookup,
    ReporterIonInfo,
    SilacLabelInfo,
    SilacLabelLookup,
)
from .monosaccharides import MONOSACCHARIDE_LOOKUP, Monosaccharide, MonosaccharideInfo, MonosaccharideLookup
from .neutral_deltas import (
    NEUTRAL_DELTA_DICT,
    NEUTRAL_DELTA_LOOKUP,
    NeutralDelta,
    NeutralDeltaInfo,
    NeutralDeltaLiteral,
    NeutralDeltaLookup,
)
from .obo_entity import OboEntity
from .obo_lookup import OntologyLookup
from .proteases import PROTEASE_DICT, PROTEASE_LOOKUP, Protease, ProteaseInfo, ProteaseLiteral, ProteaseLookup
from .refmol import REFMOL_LOOKUP, RefMolID, RefMolInfo, RefMolLiteral, RefMolLookup
from .tolerance import ToleranceUnit, da_to_ppm, ppm_error, ppm_to_da, tolerance_window, within_tolerance
from .types import Polarity

__version__ = "1.2.0"

# The six ontologies (about 2 MB of bundled data) load on first attribute access, not at
# ``import tacular``: ``tacular.GNO_LOOKUP`` and ``from tacular import GNO_LOOKUP`` both
# go through ``__getattr__`` below. Importing ``tacular.gno`` etc. directly also works.
_LAZY_SUBMODULES: dict[str, tuple[str, ...]] = {
    "gno": ("GNO_LOOKUP", "GnoInfo", "GnoLookup"),
    "psimod": ("PSIMOD_LOOKUP", "PsimodInfo", "PsimodLookup"),
    "resid": ("RESID_LOOKUP", "ResidInfo", "ResidLookup"),
    "unimod": ("UNIMOD_LOOKUP", "UnimodInfo", "UnimodLookup"),
    "uniprot_ptm": ("UNIPROT_PTM_LOOKUP", "ModLocation", "UniprotPtmInfo", "UniprotPtmLookup"),
    "xlmod": ("XLMOD_LOOKUP", "XlmodInfo", "XlmodLookup"),
}
_LAZY_ATTRS: dict[str, str] = {name: module for module, names in _LAZY_SUBMODULES.items() for name in names}

if TYPE_CHECKING:
    from .gno import GNO_LOOKUP, GnoInfo, GnoLookup
    from .psimod import PSIMOD_LOOKUP, PsimodInfo, PsimodLookup
    from .resid import RESID_LOOKUP, ResidInfo, ResidLookup
    from .unimod import UNIMOD_LOOKUP, UnimodInfo, UnimodLookup
    from .uniprot_ptm import UNIPROT_PTM_LOOKUP, ModLocation, UniprotPtmInfo, UniprotPtmLookup
    from .xlmod import XLMOD_LOOKUP, XlmodInfo, XlmodLookup


def __getattr__(name: str) -> object:
    """Import an ontology subpackage on first access to it (``tacular.unimod``) or to one
    of its names (``tacular.UNIMOD_LOOKUP``) (PEP 562)."""
    if name in _LAZY_SUBMODULES:
        return import_module(f".{name}", __name__)  # the import binds it on the package too
    module = _LAZY_ATTRS.get(name)
    if module is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    submodule = import_module(f".{module}", __name__)
    for attr in _LAZY_SUBMODULES[module]:
        globals()[attr] = getattr(submodule, attr)
    return globals()[name]


def __dir__() -> list[str]:
    """Module attributes, including the not-yet-loaded ontology subpackages and names."""
    return sorted(set(globals()) | set(_LAZY_ATTRS) | set(_LAZY_SUBMODULES))


__all__ = [
    "AA_LOOKUP",
    "AminoAcid",
    "AminoAcidInfo",
    "AALookup",
    "AMINO_ACID_INFOS",
    "ORDERED_AMINO_ACIDS",
    "ELEMENT_LOOKUP",
    "Element",
    "ElementInfo",
    "ElementKey",
    "ElementLookup",
    "parse_composition",
    "GNO_LOOKUP",
    "GnoInfo",
    "GnoLookup",
    "FRAGMENT_ION_LOOKUP",
    "FragmentIonInfo",
    "FragmentIonLookup",
    "IonType",
    "IonTypeLiteral",
    "IonTypeProperty",
    "MONOSACCHARIDE_LOOKUP",
    "Monosaccharide",
    "MonosaccharideInfo",
    "MonosaccharideLookup",
    "NEUTRAL_DELTA_DICT",
    "NEUTRAL_DELTA_LOOKUP",
    "NeutralDelta",
    "NeutralDeltaInfo",
    "NeutralDeltaLiteral",
    "NeutralDeltaLookup",
    "OboEntity",
    "OntologyLookup",
    "PROTEASE_DICT",
    "PROTEASE_LOOKUP",
    "Protease",
    "ProteaseInfo",
    "ProteaseLiteral",
    "ProteaseLookup",
    "PSIMOD_LOOKUP",
    "PsimodInfo",
    "PsimodLookup",
    "REFMOL_LOOKUP",
    "RefMolID",
    "RefMolInfo",
    "RefMolLiteral",
    "RefMolLookup",
    "RESID_LOOKUP",
    "ResidInfo",
    "ResidLookup",
    "UNIMOD_LOOKUP",
    "UnimodInfo",
    "UnimodLookup",
    "UNIPROT_PTM_LOOKUP",
    "UniprotPtmInfo",
    "UniprotPtmLookup",
    "ModLocation",
    "XLMOD_LOOKUP",
    "XlmodInfo",
    "XlmodLookup",
    "TacularError",
    "TacularKeyError",
    "ISOBARIC_TAG_LOOKUP",
    "IsobaricTagInfo",
    "IsobaricTagLookup",
    "ReporterIonInfo",
    "SILAC_LOOKUP",
    "SilacLabelInfo",
    "SilacLabelLookup",
    "Polarity",
    "ToleranceUnit",
    "da_to_ppm",
    "ppm_error",
    "ppm_to_da",
    "tolerance_window",
    "within_tolerance",
]
