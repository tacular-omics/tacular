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

from . import constants as constants
from .amino_acids import AA_LOOKUP, AMINO_ACID_INFOS, ORDERED_AMINO_ACIDS, AALookup, AminoAcid, AminoAcidInfo
from .elements import ELEMENT_LOOKUP, Element, ElementInfo, ElementKey, ElementLookup, parse_composition
from .errors import TacularError, TacularKeyError
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
from .obo_lookup import OntologyLookup
from .proteases import PROTEASE_DICT, PROTEASE_LOOKUP, Protease, ProteaseInfo, ProteaseLiteral, ProteaseLookup
from .psimod import PSIMOD_LOOKUP, PsimodInfo, PsimodLookup
from .refmol import REFMOL_LOOKUP, RefMolID, RefMolInfo, RefMolLiteral, RefMolLookup
from .resid import RESID_LOOKUP, ResidInfo, ResidLookup
from .unimod import UNIMOD_LOOKUP, UnimodInfo, UnimodLookup
from .uniprot_ptm import UNIPROT_PTM_LOOKUP, ModLocation, UniprotPtmInfo, UniprotPtmLookup
from .xlmod import XLMOD_LOOKUP, XlmodInfo, XlmodLookup

__version__ = "1.2.0"

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
]
