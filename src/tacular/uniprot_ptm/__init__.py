"""
UniProt PTM module. Provides lookup for UniProt controlled vocabulary of
posttranslational modifications (ptmlist.txt).
"""

from .data import UniprotPtmInfo
from .lookup import UNIPROT_PTM_LOOKUP, UniprotPtmLookup

__all__ = [
    "UniprotPtmLookup",
    "UNIPROT_PTM_LOOKUP",
    "UniprotPtmInfo",
]
