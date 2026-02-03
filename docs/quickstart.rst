Quick Start Guide
=================

All lookups are case-insensitive, except element symbols which are case-sensitive.

Basic Usage
-----------

Import tacular and access the various lookup modules:

.. testcode::

   import tacular as t


Amino Acid Lookups
------------------

Query amino acids by single-letter code, three-letter code, or name:

.. testcode::

   # By single-letter code
   ala = t.AA_LOOKUP['A']
   
   # By three-letter code
   ala = t.AA_LOOKUP['Ala']
   
   # By name 
   ala = t.AA_LOOKUP['AlaNine']
   
   # Access properties
   print(f"Mass: {ala.monoisotopic_mass}")
   print(f"Formula: {ala.formula}")
   print(f"Composition: {ala.dict_composition}")

.. testoutput::

   Mass: 71.0371137851
   Formula: C3H5NO
   Composition: {'C': 3, 'H': 5, 'N': 1, 'O': 1}

Amino Acid Collections
~~~~~~~~~~~~~~~~~~~~~~

The amino acid lookup provides several predefined collections:

.. testcode::

   # Groups of amino acids by category
   ordered = t.AA_LOOKUP.ordered_amino_acids
   ambiguous = t.AA_LOOKUP.ambiguous_amino_acids
   mass_aas = t.AA_LOOKUP.mass_amino_acids
   unambiguous = t.AA_LOOKUP.unambiguous_amino_acids
   mass_unambiguous = t.AA_LOOKUP.mass_unambiguous_amino_acids
   
   print(f"Ordered count: {len(ordered)}")

.. testoutput::

   Ordered count: ...

Element Lookups
---------------

Query elements and isotopes:

.. testcode::

   # Query element
   carbon = t.ELEMENT_LOOKUP['C']
   
   # Query specific isotope
   carbon_13 = t.ELEMENT_LOOKUP['13C']
   
   # Access properties
   print(f"Symbol: {carbon_13.symbol}")
   print(f"Mass: {carbon_13.mass}")
   print(f"Abundance: {carbon_13.abundance}")

   # Get monoisotopic element (most abundant isotope)
   mono_carbon = t.ELEMENT_LOOKUP.get_monoisotopic('C')
   print(f"Monoisotopic Carbon Mass: {mono_carbon.mass}")

   # Get all isotopes of an element
   isotopes = t.ELEMENT_LOOKUP.get_all_isotopes('C')
   print(f"Number of Carbon isotopes: {len(isotopes)}")

.. testoutput::

   Symbol: C
   Mass: 13.00335483507
   Abundance: 0.0107
   Monoisotopic Carbon Mass: 12.0
   Number of Carbon isotopes: 3

Element Info
------------

The return type for element lookups is ``ElementInfo``, which contains the following properties:

.. code-block:: python

   from dataclasses import dataclass

   @dataclass(frozen=True, slots=True)
   class ElementInfo:
       number: int
       mass_number: int | None
       symbol: str
       mass: float
       abundance: float | None
       average_mass: float
       is_monoisotopic: bool | None

- ``number`` is the atomic number
- ``mass_number`` is the atomic number + neutron number
- ``symbol`` is the element symbol
- ``mass`` is the isotopic mass
- ``abundance`` is the natural abundance (``None`` for synthetic isotopes)
- ``average_mass`` is the average atomic mass for the element
- ``is_monoisotopic`` can be ``False``, ``True``, or ``None``

  - ``None`` indicates that the ElementInfo is not specified, in other words it represents the element as a whole rather than a specific isotope
  - ``True`` indicates that this isotope is the most abundant isotope for the element
  - ``False`` indicates that this isotope is not the most abundant isotope for the element 


Modification Lookups
--------------------

Since modification databases can be large, they are lazily loaded on first access.
Supported databases include Unimod, PSI-MOD, RESID, XLmod, and GNOme. Currently only valid
modifications are included (must have at least one valid mass or composition).

RESID IDs have an ``AA`` prefix (e.g., ``AA0002``), which is optional when querying.
GNOme IDs have a ``G`` prefix (e.g., ``G00008BG``), which is optional when querying.
In addition, all leading zeros are removed, and when applicable, integer IDs can be used.

Query modifications from various databases:

.. testcode::

   # Unimod
   acetyl = t.UNIMOD_LOOKUP['Acetyl']
   print(f"Acetyl ID: {acetyl.id}")
   
   acetyl_by_id = t.UNIMOD_LOOKUP[1]  # Can also use int IDs
   print(f"Acetyl by ID: {acetyl_by_id.name}")
 
   # PSI-MOD
   phospho = t.PSIMOD_LOOKUP.query_name('phosphorylated residue')
   print(f"PSI-MOD found: {phospho is not None}")

   phospho_by_id = t.PSIMOD_LOOKUP['00696']  # Can also use int IDs: 696
   print(f"Phospho by ID name: {phospho_by_id.name}")
   
   # Query by mass (default: tolerance=0.01, monoisotopic=True)
   mods1 = t.UNIMOD_LOOKUP.query_mass(42.01)
   print(f"Mods at mass 42.01: {len(mods1)}")

   mods2 = t.UNIMOD_LOOKUP.query_mass(42.01, tolerance=0.02, monoisotopic=False)
   print(f"Mods at mass 42.01 (tol=0.02, avg): {len(mods2)}")

   # Other databases
   t.GNO_LOOKUP
   t.RESID_LOOKUP
   t.XLMOD_LOOKUP

.. testoutput::

   Acetyl ID: 1
   Acetyl by ID: Acetyl
   PSI-MOD found: True
   Phospho by ID name: phosphorylated residue
   Mods at mass 42.01: ...
   Mods at mass 42.01 (tol=0.02, avg): ...

Fragment Ion Lookups
--------------------

Query fragment ion types:

.. testcode::

   # Query by ID
   b_ion = t.FRAGMENT_ION_LOOKUP['b']
   y_ion = t.FRAGMENT_ION_LOOKUP['y']
   
   # Check properties
   print(f"Is forward: {b_ion.is_forward}")
   print(f"Is backward: {y_ion.is_backward}")

.. testoutput::

   Is forward: True
   Is backward: True

Neutral Delta (Loss) Lookups
-----------------------------

Query neutral losses:

.. testcode::

   # Query water loss by formula
   water = t.NEUTRAL_DELTA_LOOKUP['H2O']
   print(f"Water loss name: {water.name}")

   # Can also query by name
   water_by_name = t.NEUTRAL_DELTA_LOOKUP['water']
   print(f"Water loss name: {water_by_name.name}")
   
   # Calculate possible loss sites in sequence
   sites = water.calculate_loss_sites('PEPTIDE')
   print(f"Possible water loss sites: {sites}")

.. testoutput::

   Water loss name: Water
   Water loss name: Water
   Possible water loss sites: ...

Protease Lookups
----------------

Query protease cleavage patterns:

.. testcode::

   # Query by name
   trypsin = t.PROTEASE_LOOKUP['trypsin']
   print(f"Trypsin name: {trypsin.name}")
   
   # Access regex pattern
   pattern = trypsin.pattern
   print(f"Has pattern: {pattern is not None}")

.. testoutput::

   Trypsin name: Trypsin
   Has pattern: True

Reference Molecule Lookups
---------------------------

Query mzPAF reference molecules:

.. testcode::

   # Query by name
   tmt126 = t.REFMOL_LOOKUP['TMT126']
   print(f"TMT126 name: {tmt126.name}")
   
   # Query by label type
   tmt_ions = t.REFMOL_LOOKUP.query_label_type('TMT')
   print(f"TMT ions found: {len(tmt_ions)}")
   
   # Query by molecule type
   reporters = t.REFMOL_LOOKUP.query_molecule_type('reporter')
   print(f"Reporter ions found: {len(reporters) > 0}")

.. testoutput::

   TMT126 name: TMT126
   TMT ions found: ...
   Reporter ions found: True

Iteration and Advanced Usage
-----------------------------

Most lookups support iteration and contain checks:

.. testcode::

   # Check if entry exists
   if 'Acetyl' in t.UNIMOD_LOOKUP:
       print("Acetyl modification exists")
   
   # Iterate over first 3 amino acids
   for i, aa in enumerate(t.AA_LOOKUP):
       if i >= 3:
           break
       print(aa.name)
   
   # Get with default
   mod = t.UNIMOD_LOOKUP.get('NonExistent', default=None)
   print(f"NonExistent mod: {mod}")

.. testoutput::

   Acetyl modification exists
   ...
   NonExistent mod: None

