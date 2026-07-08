"""RESID lookups (``RESID_LOOKUP``): query RESID protein modification entries by id or name."""

from .dclass import ResidInfo
from .lookup import RESID_LOOKUP, ResidLookup

__all__ = ["ResidInfo", "RESID_LOOKUP", "ResidLookup"]
