"""Shared vocabulary types for the tacular-omics packages.

Packages that depend on tacular import these instead of defining their own, so the same
parameter accepts the same strings everywhere. mzmlpy and tdfpy do not depend on tacular
and keep identical local copies.

>>> from tacular.types import Polarity, ToleranceUnit
"""

from typing import Literal

from .tolerance import ToleranceUnit

__all__ = ["Polarity", "ToleranceUnit"]

Polarity = Literal["positive", "negative"]
"""Scan or ionization polarity."""
