"""Protease lookups (``PROTEASE_LOOKUP``): query digestion enzymes by id or name."""

from .data import PROTEASE_DICT, Protease, ProteaseLiteral
from .dclass import ProteaseInfo
from .lookup import PROTEASE_LOOKUP, ProteaseLookup

__all__ = [
    "Protease",
    "ProteaseLiteral",
    "ProteaseInfo",
    "PROTEASE_DICT",
    "PROTEASE_LOOKUP",
    "ProteaseLookup",
]
