"""XLMOD lookups (``XLMOD_LOOKUP``): query cross-linker modification entries by id or name."""

from .dclass import XlModInfo
from .lookup import XLMOD_LOOKUP, XlModLookup

__all__ = ["XlModInfo", "XLMOD_LOOKUP", "XlModLookup"]
