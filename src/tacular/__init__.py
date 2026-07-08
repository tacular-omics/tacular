"""tacular: lookups for amino acids, elements, and mass spectrometry ontologies.

Each ontology (UNIMOD, PSI-MOD, RESID, XLMOD, GNOme, UniProt-PTM) and data type
(amino acids, elements, fragment ion types, monosaccharides, neutral losses,
proteases, mzPAF reference molecules) exposes a module-level ``*_LOOKUP``
singleton -- e.g. ``UNIMOD_LOOKUP``, ``ELEMENT_LOOKUP`` -- built on the shared
:class:`OboLookup` and :class:`OboEntity` base classes in ``obo_lookup.py`` /
``obo_entity.py``. Query by id, name, or (for ontologies) approximate mass; see
each lookup class's docstring for its specific query methods.

Data for the 6 refreshable ontologies (5 OBO-sourced, plus UniProt-PTM from its
own flat-file format) ships baked into the package as of the version above, but
can be refreshed to the latest upstream release without reinstalling via the
``tacular update`` CLI (see :mod:`tacular.update`); each lookup transparently
prefers a refreshed cache over the bundled copy if one exists (see
:mod:`tacular._cache`).
"""

from .amino_acids import AA_LOOKUP, AMINO_ACID_INFOS, ORDERED_AMINO_ACIDS, AALookup, AminoAcid, AminoAcidInfo
from .elements import ELEMENT_LOOKUP, Element, ElementInfo, ElementLookup, parse_composition
from .gno import GNO_LOOKUP, GnoInfo, GnoLookup
from .ion_types import FRAGMENT_ION_LOOKUP, FragmentIonInfo, FragmentIonLookup, IonType, IonTypeLiteral, IonTypeProperty
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
from .proteases import PROTEASE_LITERALS, PROTEASE_LOOKUP, PROTEASES_DICT, ProteaseInfo, Proteases
from .psimod import PSIMOD_LOOKUP, PsimodInfo, PsimodLookup
from .refmol import REFMOL_LOOKUP, RefMolID, RefMolInfo, RefMolLiteral, RefMolLookup
from .resid import RESID_LOOKUP, ResidInfo, ResidLookup
from .unimod import UNIMOD_LOOKUP, UnimodInfo, UnimodLookup
from .uniprot_ptm import UNIPROT_PTM_LOOKUP, UniprotPtmInfo, UniprotPtmLookup
from .xlmod import XLMOD_LOOKUP, XlModInfo, XlModLookup

__version__ = "1.1.0"

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
    "PROTEASE_LITERALS",
    "PROTEASE_LOOKUP",
    "PROTEASES_DICT",
    "ProteaseInfo",
    "Proteases",
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
    "XLMOD_LOOKUP",
    "XlModInfo",
    "XlModLookup",
]
