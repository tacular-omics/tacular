"""XLMOD lookups (``XLMOD_LOOKUP``): query cross-linker modification entries by id or name."""

from .dclass import XlmodInfo
from .lookup import XLMOD_LOOKUP, XlmodLookup

__all__ = ["XlmodInfo", "XLMOD_LOOKUP", "XlmodLookup"]
