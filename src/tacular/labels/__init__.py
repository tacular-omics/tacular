"""Quantitative labels: isobaric tags (``ISOBARIC_TAG_LOOKUP``: TMT, TMTpro, iTRAQ) with
their reporter ions, and SILAC labels (``SILAC_LOOKUP``) with the light/medium/heavy sets.
"""

from .dclass import IsobaricTagInfo, ReporterIon, SilacLabelInfo
from .lookup import ISOBARIC_TAG_LOOKUP, SILAC_LOOKUP, IsobaricTagLookup, SilacLabelLookup

__all__ = [
    "ISOBARIC_TAG_LOOKUP",
    "IsobaricTagInfo",
    "IsobaricTagLookup",
    "ReporterIon",
    "SILAC_LOOKUP",
    "SilacLabelInfo",
    "SilacLabelLookup",
]
