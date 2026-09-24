Shared Types
============

Vocabulary types shared by the tacular-omics packages, so the same parameter accepts the
same strings everywhere. Both are also importable from ``tacular``.

- ``ToleranceUnit = Literal["da", "ppm"]``: the unit of a mass tolerance (the
  ``tolerance_unit=`` keyword). Same object as :data:`tacular.tolerance.ToleranceUnit`.
- ``Polarity = Literal["positive", "negative"]``: scan or ionization polarity.

.. code-block:: python

   from tacular.types import Polarity, ToleranceUnit
