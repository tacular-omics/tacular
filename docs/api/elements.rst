Elements
========

The elements module provides lookups for chemical elements and their isotopes.


.. automodule:: tacular.elements
   :members:
   :undoc-members:
   :show-inheritance:

Module data
-----------

.. py:data:: tacular.elements.ELEMENT_LOOKUP

   Singleton :class:`~tacular.elements.ElementLookup`. Query by symbol (``'C'``) or isotope (``'13C'``). Symbols are case-sensitive.

Formula strings
---------------

:func:`~tacular.formula.parse_formula` turns a formula string into the same
``ElementInfo``-keyed composition that :func:`~tacular.elements.parse_composition` returns,
and :func:`~tacular.formula.formula_mass` returns its mass. Isotopes use the ProForma
bracket spelling, ``[13C6]H12O6``; the bare ``13C6H12O6`` and the UNIMOD ``H(2)C(6)``
spellings raise :class:`~tacular.errors.TacularError`.

.. testcode::

   import tacular as t

   composition = t.parse_formula("[13C6]H12O6")
   print(composition[t.ELEMENT_LOOKUP["13C"]])
   print(t.formula_mass("C6H12O6"))
   print(round(t.formula_mass("C6H12O6", monoisotopic=False), 4))

.. testoutput::

   6
   180.06338810418
   180.1561

.. automodule:: tacular.formula
   :members:
