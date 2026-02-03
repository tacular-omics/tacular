.. image:: _static/tacular_logo.png
   :alt: Tacular Logo
   :align: center
   :width: 300px

Welcome to tacular's documentation! This package provides comprehensive lookups for modifications, amino acids, elements, and other biochemistry data types commonly used in mass spectrometry and proteomics.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   installation
   quickstart
   api/index

Features
--------

* **Amino Acids**: Standard and non-standard amino acid lookups with properties
* **Modifications**: Support for Unimod, PSI-MOD, RESID, XLMOD, and GNOme
* **Elements**: Chemical element data with isotope information
* **Fragment Ions**: Common ion types for peptide fragmentation
* **Neutral Deltas**: Neutral loss calculations
* **Reference Molecules**: mzPAF reference molecules
* **Proteases**: Common protease cleavage patterns

Quick Example
-------------

.. code-block:: python

   import tacular as t

   # Query amino acids
   alanine = t.AA_LOOKUP['A']
   print(f"Alanine mass: {alanine.monoisotopic_mass}")

   # Query elements
   carbon_13 = t.ELEMENT_LOOKUP['13C']
   print(f"Carbon-13 mass: {carbon_13.mass}")

   # Query modifications
   acetyl = t.UNIMOD_LOOKUP['Acetyl']
   print(f"Acetyl mass: {acetyl.monoisotopic_mass}")

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
