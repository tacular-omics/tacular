.. image:: _static/tacular_logo.png
   :alt: Tacular Logo
   :align: center
   :width: 300px

|

.. raw:: html

   <div style="text-align: center; margin-bottom: 5px;">
      <a href="https://github.com/pgarrett-scripps/tacular/actions/workflows/python-package.yml"><img src="https://github.com/pgarrett-scripps/tacular/actions/workflows/python-package.yml/badge.svg" alt="Python package"></a>
      <a href="https://codecov.io/github/tacular-omics/tacular"><img src="https://codecov.io/github/tacular-omics/tacular/graph/badge.svg?token=1CTVZVFXF7" alt="codecov"></a>
      <a href="https://tacular.readthedocs.io/en/latest/?badge=latest"><img src="https://readthedocs.org/projects/tacular/badge/?version=latest" alt="Documentation Status"></a>
      <a href="https://badge.fury.io/py/tacular"><img src="https://badge.fury.io/py/tacular.svg" alt="PyPI version"></a>
      <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.12+-blue.svg" alt="Python 3.12+"></a>
      <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License"></a>
      <a href="https://doi.org/10.5281/zenodo.18475556"><img src="https://zenodo.org/badge/1135282295.svg" alt="DOI"></a>
   </div>

|

.. raw:: html

   <div style="text-align: center; font-size: 1.0em; margin-bottom: 20px;">
      Welcome to tacular's documentation! This package provides comprehensive lookups for modifications, amino acids, elements, and other biochemistry data types commonly used in mass spectrometry and proteomics.
   </div>


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


.. toctree::
   :maxdepth: 2
   :caption: Contents:

   installation
   quickstart
   api/index



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
