Quantitative Labels
===================

Isobaric tags (TMT 0/2/6/10/11, TMTpro 0/16/18, iTRAQ 4/8) with their reporter ion
channels, and SILAC labels (Lys4, Lys6, Lys8, Arg6, Arg10) with the common
light/medium/heavy sets. Tag and label compositions come from UNIMOD; every mass and
reporter m/z is computed from the bundled element table.

- TMT/TMTpro reporter m/z agree with Thermo's TMTpro user guide (MAN0018773, Table 2)
  to 1e-5.
- iTRAQ reporter m/z are computed the same way (ion composition minus one electron).
  Legacy SCIEX/MSnbase tables (114.1112, 115.1083, 116.1116, 117.1150, ...) are about
  0.0005 higher, consistent with no electron subtraction.
- Each :class:`~tacular.labels.ReporterIon` carries its channel's UNIMOD tag. iTRAQ
  channels differ: 4-plex 114 is UNIMOD:532, 115 is UNIMOD:533, 116/117 are UNIMOD:214;
  8-plex 115/118/119/121 are UNIMOD:731, the rest UNIMOD:730. The plex-level
  ``unimod_id`` is the tag search engines set.
- ``average_mass`` uses the bundled element table and differs from UNIMOD's average by
  up to 6e-4 Da.

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
