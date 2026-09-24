"""Physical constants shared by the tacular-omics packages, in unified atomic mass units (Da).

Sources:

- :data:`PROTON_MASS`, :data:`ELECTRON_MASS`, :data:`NEUTRON_MASS`: CODATA 2018
  recommended values (Tiesinga et al., Rev. Mod. Phys. 93, 025010 (2021);
  https://physics.nist.gov/cuu/Constants/).
- :data:`HYDROGEN_MASS` and :data:`C13_C12_MASS_DIFF`: the atomic masses of
  1H and 13C in tacular's bundled isotope table (NIST "Atomic Weights and
  Isotopic Compositions", which takes its masses from the 2016 Atomic Mass Evaluation,
  Wang et al., Chinese Phys. C 41, 030003 (2017)), so they agree exactly with
  ``ELEMENT_LOOKUP["1H"].mass`` and ``ELEMENT_LOOKUP["13C"].mass - 12``.

>>> from tacular.constants import PROTON_MASS, C13_C12_MASS_DIFF
>>> round(PROTON_MASS, 6), round(C13_C12_MASS_DIFF, 6)
(1.007276, 1.003355)
"""

from typing import Final

__all__ = [
    "C13_C12_MASS_DIFF",
    "ELECTRON_MASS",
    "HYDROGEN_MASS",
    "NEUTRON_MASS",
    "PROTON_MASS",
]

PROTON_MASS: Final[float] = 1.007276466621
"""Proton rest mass (CODATA 2018): the mass added per positive charge by protonation."""

ELECTRON_MASS: Final[float] = 0.000548579909065
"""Electron rest mass (CODATA 2018)."""

NEUTRON_MASS: Final[float] = 1.00866491595
"""Free neutron rest mass (CODATA 2018). For isotope-peak spacing use :data:`C13_C12_MASS_DIFF`."""

HYDROGEN_MASS: Final[float] = 1.00782503223
"""Atomic mass of 1H (proton + electron - binding energy; AME2016 via NIST)."""

C13_C12_MASS_DIFF: Final[float] = 1.00335483507
"""Mass difference 13C - 12C (AME2016 via NIST): the spacing of isotope peaks
for carbon-dominated molecules, in Da per charge."""
