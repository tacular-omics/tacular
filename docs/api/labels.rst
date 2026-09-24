Quantitative Labels
===================

Isobaric tags (TMT 0/2/6/10/11, TMTpro 16/18, iTRAQ 4/8) with their reporter ion
channels, and SILAC labels (Lys4, Lys6, Lys8, Arg6, Arg10) with the common
light/medium/heavy sets. Tag and label compositions come from UNIMOD; every mass and
reporter m/z is computed from the bundled element table. Reporter m/z values agree with
Thermo's (TMT/TMTpro) and SCIEX's (iTRAQ) published tables to 1e-5.

.. automodule:: tacular.labels
   :members:
   :undoc-members:
   :show-inheritance:

Module data
-----------

.. py:data:: tacular.labels.ISOBARIC_TAG_LOOKUP

   Singleton :class:`~tacular.labels.IsobaricTagLookup`. Query by plex name or alias
   (``"TMT10"``, ``"TMT10plex"``, ``"TMTpro18"``, ``"iTRAQ4"``).

.. py:data:: tacular.labels.SILAC_LOOKUP

   Singleton :class:`~tacular.labels.SilacLabelLookup`. Query by name or alias
   (``"Lys8"``, ``"K+8"``, ``"R10"``); sets via ``query_set("heavy")``.
