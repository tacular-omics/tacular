Quick Start Guide
=================

Basic Usage
-----------

Import tacular and access the various lookup modules:

.. testcode::

   import tacular as t
   print("Tacular imported successfully")

.. testoutput::

   Tacular imported successfully

Amino Acid Lookups
------------------

Query amino acids by single-letter code, three-letter code, or name:

.. testcode::

   # By single-letter code
   ala = t.AA_LOOKUP['A']
   
   # By three-letter code
   ala = t.AA_LOOKUP['Ala']
   
   # By name
   ala = t.AA_LOOKUP['Alanine']
   
   # Access properties
   print(f"Mass: {ala.monoisotopic_mass}")
   print(f"Formula: {ala.formula}")
   print(f"Composition: {ala.dict_composition}")

.. testoutput::

   Mass: 71.0371137851
   Formula: C3H5NO
   Composition: {'C': 3, 'H': 5, 'N': 1, 'O': 1}

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

.. testoutput::

   Symbol: C
   Mass: 13.00335483507
   Abundance: 0.0107

Modification Lookups
--------------------

Query modifications from various databases:

.. testcode::

   # Unimod
   acetyl = t.UNIMOD_LOOKUP['Acetyl']
   print(f"Acetyl ID: {acetyl.id}")
   
   acetyl_by_id = t.UNIMOD_LOOKUP['1']
   print(f"Acetyl by ID: {acetyl_by_id.name}")
   
   # PSI-MOD
   phospho = t.PSIMOD_LOOKUP.query_name('phosphorylated residue')
   print(f"PSI-MOD found: {phospho is not None}")
   
   # Query by mass
   mods = t.UNIMOD_LOOKUP.query_mass(42.01, tolerance=0.01)
   print(f"Mods at mass 42.01: {len(mods)}")

.. testoutput::

   Acetyl ID: 1
   Acetyl by ID: Acetyl
   PSI-MOD found: True
   Mods at mass 42.01: ...

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

   # Query water loss
   water = t.NEUTRAL_DELTA_LOOKUP['H2O']
   print(f"Water loss name: {water.name}")
   
   # Calculate possible loss sites in sequence
   sites = water.calculate_loss_sites('PEPTIDE')
   print(f"Possible water loss sites: {sites}")

.. testoutput::

   Water loss name: Water
   Possible water loss sites: ...

Protease Lookups
----------------

Query protease cleavage patterns:

.. testcode::

   # Query by name
   trypsin = t.PROTEASE_LOOKUP['Trypsin']
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
   
   # Get ordered amino acids
   ordered = t.AA_LOOKUP.ordered_amino_acids
   print(f"Ordered AAs count: {len(ordered)}")
   
   # Get only unambiguous amino acids
   unambiguous = t.AA_LOOKUP.unambiguous_amino_acids
   print(f"Unambiguous AAs count: {len(unambiguous)}")

.. testoutput::

   Acetyl modification exists
   ...
   NonExistent mod: None
   Ordered AAs count: ...
   Unambiguous AAs count: ...
