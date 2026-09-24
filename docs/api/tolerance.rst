Mass Tolerances
===============

Helpers for ppm errors, Da <-> ppm conversion and tolerance windows. Every function is
also importable from ``tacular``. Units are the lowercase strings ``"da"`` and ``"ppm"``;
anything else raises :class:`~tacular.errors.TacularError`. A ppm tolerance is relative to
the absolute value of the reference mass, so windows around negative masses are symmetric.

.. automodule:: tacular.tolerance
   :members:
   :undoc-members:
