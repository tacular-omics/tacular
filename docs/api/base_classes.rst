Base Classes
============

Base classes used across multiple modules.

OBO Entity
----------

.. automodule:: tacular.obo_entity
   :members:
   :undoc-members:
   :show-inheritance:

OBO Lookup
----------

.. automodule:: tacular.obo_lookup
   :members:
   :undoc-members:
   :show-inheritance:

Errors
------

Every error tacular raises on purpose is a :class:`~tacular.TacularError`
(a ``ValueError``). A lookup miss, ``LOOKUP[key]``, raises
:class:`~tacular.TacularKeyError`, which is also a ``KeyError``, so both
``except KeyError`` and ``except ValueError`` catch it.

.. automodule:: tacular.errors
   :members:
   :show-inheritance:

Constants
---------

.. automodule:: tacular.constants
   :members:
