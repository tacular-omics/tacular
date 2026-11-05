Modifications
=============

The modifications modules provide lookups for post-translational modifications from various databases.

Unimod
------

.. automodule:: tacular.unimod.lookup
   :members:
   :undoc-members:
   :show-inheritance:

.. py:data:: tacular.unimod.lookup.UNIMOD_LOOKUP

   Singleton lookup, also importable as ``tacular.UNIMOD_LOOKUP``.

.. automodule:: tacular.unimod.dclass
   :members:
   :undoc-members:
   :show-inheritance:

PSI-MOD
-------

.. automodule:: tacular.psimod.lookup
   :members:
   :undoc-members:
   :show-inheritance:

.. py:data:: tacular.psimod.lookup.PSIMOD_LOOKUP

   Singleton lookup, also importable as ``tacular.PSIMOD_LOOKUP``.

.. automodule:: tacular.psimod.dclass
   :members:
   :undoc-members:
   :show-inheritance:

RESID
-----

.. automodule:: tacular.resid.lookup
   :members:
   :undoc-members:
   :show-inheritance:

.. py:data:: tacular.resid.lookup.RESID_LOOKUP

   Singleton lookup, also importable as ``tacular.RESID_LOOKUP``.

.. automodule:: tacular.resid.dclass
   :members:
   :undoc-members:
   :show-inheritance:

XLMOD
-----

.. automodule:: tacular.xlmod.lookup
   :members:
   :undoc-members:
   :show-inheritance:

.. py:data:: tacular.xlmod.lookup.XLMOD_LOOKUP

   Singleton lookup, also importable as ``tacular.XLMOD_LOOKUP``.

.. automodule:: tacular.xlmod.dclass
   :members:
   :undoc-members:
   :show-inheritance:

GNOme
-----

.. automodule:: tacular.gno.lookup
   :members:
   :undoc-members:
   :show-inheritance:

.. py:data:: tacular.gno.lookup.GNO_LOOKUP

   Singleton lookup, also importable as ``tacular.GNO_LOOKUP``.

.. automodule:: tacular.gno.dclass
   :members:
   :undoc-members:
   :show-inheritance:

UniProt-PTM
-----------

``UNIPROT_PTM_LOOKUP`` holds the single-residue modifications of UniProt's controlled
vocabulary that carry a formula, a mass or a composition: 440 of the 750 entries in the
bundled ``2026_03`` release. The 159 ``CROSSLNK`` entries are excluded because their
``TG``/``PP`` values describe a link between two residues rather than a modification of
one residue, which a single-residue id/name/mass lookup cannot represent; 151 further
entries (69 ``MOD_RES``, 67 ``CARBOHYD``, 15 ``LIPID``) are excluded because upstream
gives them no formula, no mass and no composition. ``tacular update uniprot_ptm``
applies the same exclusions. For the whole vocabulary, crosslinks included, use
`uniprotptmpy <https://github.com/tacular-omics/uniprotptmpy>`_.

.. automodule:: tacular.uniprot_ptm.lookup
   :members:
   :undoc-members:
   :show-inheritance:

.. py:data:: tacular.uniprot_ptm.lookup.UNIPROT_PTM_LOOKUP

   Singleton lookup, also importable as ``tacular.UNIPROT_PTM_LOOKUP``.

.. automodule:: tacular.uniprot_ptm.dclass
   :members:
   :undoc-members:
   :show-inheritance:
