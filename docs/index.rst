.. image:: _static/tacular_logo.png
   :alt: Tacular Logo
   :align: center
   :width: 300px

|

.. raw:: html

   <div style="text-align: center; margin-bottom: 5px;">
      <a href="https://github.com/tacular-omics/tacular/actions/workflows/ci.yml"><img src="https://github.com/tacular-omics/tacular/actions/workflows/ci.yml/badge.svg" alt="Python package"></a>
      <a href="https://codecov.io/github/tacular-omics/tacular"><img src="https://codecov.io/github/tacular-omics/tacular/graph/badge.svg?token=1CTVZVFXF7" alt="codecov"></a>
      <a href="https://tacular.readthedocs.io/en/latest/?badge=latest"><img src="https://readthedocs.org/projects/tacular/badge/?version=latest" alt="Documentation Status"></a>
      <a href="https://badge.fury.io/py/tacular"><img src="https://badge.fury.io/py/tacular.svg" alt="PyPI version"></a>
      <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.12+-blue.svg" alt="Python 3.12+"></a>
      <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License"></a>
      <a href="https://doi.org/10.5281/zenodo.18475556"><img src="https://zenodo.org/badge/1135282295.svg" alt="DOI"></a>
   </div>

|

tacular is a lookup library for the reference data every mass spectrometry and
proteomics tool needs: amino acids, elements and isotopes, fragment ion types,
neutral losses, proteases, mzPAF reference molecules, and six post-translational
modification ontologies (UNIMOD, PSI-MOD, RESID, XLMOD, GNOme and UniProt-PTM).
Everything is queried through the same ``LOOKUP[key]`` interface, the data ships
with the package, and there are no runtime dependencies.

Features
--------

* **Modifications**: UNIMOD, PSI-MOD, RESID, XLMOD, GNOme and UniProt-PTM, queryable by id, name, or approximate mass
* **Amino acids**: standard and non-standard amino acids with masses and compositions
* **Elements**: element and isotope masses and abundances
* **Fragment ions**: peptide fragment ion types and their formulas
* **Neutral deltas**: common neutral losses and gains
* **Reference molecules**: mzPAF reference molecules (reporter ions and others)
* **Proteases**: cleavage rules for common proteases
* **Refreshable**: the ``tacular update`` CLI pulls the latest ontology releases into a per-user cache (see :doc:`cli`)

Quick example
-------------

.. code-block:: python

   import tacular as t

   alanine = t.AA_LOOKUP["A"]
   print(alanine.monoisotopic_mass)  # 71.0371137851

   carbon_13 = t.ELEMENT_LOOKUP["13C"]
   print(carbon_13.mass)  # 13.00335483507

   # Identify a modification from an observed mass shift
   hits = t.UNIMOD_LOOKUP.query_mass(79.9663, tolerance=0.001)
   print(hits[0].name)  # Phospho

Related packages
----------------

tacular is the shared data layer of the tacular-omics packages:

* `peptacular <https://peptacular.readthedocs.io/>`_ parses and analyzes ProForma peptide sequences
  (mass, m/z, fragments, isotopes, digestion).
* `paftacular <https://paftacular.readthedocs.io/>`_ parses and serializes mzPAF peak annotations.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   installation
   quickstart
   cli
   migration
   api/index
   changelog
   citation


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
