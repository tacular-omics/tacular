Migrating to 2.0
================

tacular 2.0 is a breaking API cleanup. The data is the same as 1.2. Renamed names have
no aliases, so an import or attribute error tells you exactly what to change. The
tables below list every removed or renamed public name.

Renamed
-------

.. list-table::
   :header-rows: 1
   :widths: 45 55

   * - 1.x
     - 2.0
   * - ``tacular.Proteases``
     - ``tacular.Protease``
   * - ``info.dict_composition[k] = v`` (mutating in place)
     - read-only now (``TypeError``): ``info.update(dict_composition=dict(info.dict_composition) | {k: v})``
   * - ``tacular.PROTEASE_LITERALS``
     - ``tacular.ProteaseLiteral``
   * - ``tacular.PROTEASES_DICT``
     - ``tacular.PROTEASE_DICT``
   * - ``tacular.XlModInfo`` / ``tacular.XlModLookup``
     - ``tacular.XlmodInfo`` / ``tacular.XlmodLookup``
   * - ``info.mass(monoisotopic)`` (ontology entries, monosaccharides)
     - ``info.get_mass(monoisotopic=...)``
   * - ``ELEMENT_LOOKUP.mass(key, monoisotopic)``
     - ``ELEMENT_LOOKUP.get_mass(key, monoisotopic=...)``
   * - ``AA_LOOKUP.mass(key, monoisotopic)``
     - ``AA_LOOKUP.get_mass(key, monoisotopic=...)``
   * - ``AA_LOOKUP.one_letter(c)`` / ``three_letter(c)`` / ``name(n)`` (raised ``KeyError``)
     - ``AA_LOOKUP[c]`` (raises), or ``query_one_letter`` / ``query_three_letter`` /
       ``query_name`` (return ``None``)
   * - ``MONOSACCHARIDE_LOOKUP.proforma(name)``
     - ``MONOSACCHARIDE_LOOKUP[name]`` or ``MONOSACCHARIDE_LOOKUP.query_name(name)``
   * - ``RefMolInfo.chemical_formula`` (field and ``to_dict`` key)
     - ``RefMolInfo.formula``
   * - ``NeutralDeltaInfo.to_dict()["dict_composition"]``
     - ``NeutralDeltaInfo.to_dict()["composition"]``
   * - ``ElementLookup.NEUTRON_MASS``
     - ``tacular.constants.NEUTRON_MASS``
   * - ``ELEMENT_LOOKUP.element_data``
     - ``ELEMENT_LOOKUP.items()`` / ``keys()`` / ``values()``

Removed or made private
-----------------------

.. list-table::
   :header-rows: 1
   :widths: 45 55

   * - 1.x
     - Use instead
   * - ``AA_LOOKUP.one_letter_to_info`` / ``three_letter_to_info`` / ``name_to_info``
     - ``AA_LOOKUP.query_*`` or ``AA_LOOKUP.items()``
   * - ``MONOSACCHARIDE_LOOKUP.proforma_to_monosaccharide``
     - ``MONOSACCHARIDE_LOOKUP.items()``
   * - ``PROTEASE_LOOKUP.name_to_info`` / ``id_to_info``
     - ``PROTEASE_LOOKUP.query_name`` / ``query_id`` / ``items()``
   * - ``OntologyLookup.strip_id`` / ``convert_key`` / ``str(lookup)``
     - ``lookup.query_id(key)`` (accepts every prefix form); ``repr(lookup)``
   * - ``tacular.obo_entity.filter_infos``
     - a list comprehension over ``lookup.values()``
   * - ``tacular.update.OBO_SOURCES`` / ``ONTOLOGIES``
     - ``tacular status`` / ``tacular.update.update(ontologies)``
   * - ``XlmodInfo.id_tag`` override
     - inherited ``OboEntity.id_tag`` (same result)

Changed behaviour
-----------------

.. list-table::
   :header-rows: 1
   :widths: 45 55

   * - 1.x
     - 2.0
   * - ``KeyError``, ``ValueError`` or ``TypeError`` from ``lookup[key]``
     - :class:`~tacular.TacularKeyError`, which is a ``KeyError`` *and* a ``ValueError``,
       so existing ``except KeyError`` / ``except ValueError`` still work. A bad
       ``ELEMENT_LOOKUP`` tuple key no longer raises ``TypeError``.
   * - ``ValueError`` for a missing mass or composition, ``choice()`` with no match, an
       unknown ontology in ``update``
     - :class:`~tacular.TacularError` (a ``ValueError``)
   * - ``get_mass(True)``, ``to_dict(4)``, ``choice(False, False)``, ``query_mass(m, 0.1)``
     - keyword-only: ``get_mass(monoisotopic=True)``, ``to_dict(float_precision=4)``,
       ``choice(require_monoisotopic_mass=False, ...)``, ``query_mass(m, tolerance=0.1)``
   * - ``AminoAcidInfo``, ``FragmentIonInfo``, ``NeutralDeltaInfo``, ``ProteaseInfo``,
       ``RefMolInfo`` had an instance ``__dict__`` (for ``cached_property``)
     - frozen, slotted dataclasses (no ``__dict__``); use ``dataclasses.replace`` to
       derive a new one
   * - ``ElementInfo.to_dict()`` / ``AminoAcidInfo.to_dict()``
     - also include ``is_monoisotopic`` / ``is_mass_ambiguous`` and ``is_ambiguous``
   * - ``NeutralDeltaInfo.to_dict()["amino_acids"]`` in set order
     - sorted, so ``jsons/neutral_losses.json`` is deterministic
   * - ``OntologyLookup(data, name, version, prefixes, id_prefix)`` positional
     - ``OntologyLookup(data, name, *, version=, accession_prefixes=, id_prefix=)``
   * - Only long accession prefixes (``UNIMOD:21``)
     - short prefixes too (``U:``, ``M:``, ``R:``, ``X:``, ``G:``), and on names
       (``U:Phospho``)
   * - ``ElementInfo.neutron_count`` on an element entry, ``serialize(0)``
     - raise ``TacularError`` (a ``ValueError``, as before)
   * - ``UNIMOD_LOOKUP.keys()`` (every ontology lookup) returned lowercased names
       (``"phospho"``)
     - returns the raw accession ids (``"21"``), the same keys ``items()`` uses; for
       names use ``[info.name for info in lookup.values()]``
   * - ``info.update(**changes)`` on ontology entries ignored unknown keywords and
       rebuilt the entry from a fixed field list
     - ``dataclasses.replace``: an unknown keyword raises ``TypeError`` and subclass
       fields are kept
   * - ``ELEMENT_LOOKUP["013C"]`` parsed as carbon-13
     - raises :class:`~tacular.TacularKeyError` (no leading zeros)
   * - ``tacular.update.update()`` let parser ``ValueError`` s escape
     - raises :class:`~tacular.TacularError` chained from the parser's error
   * - ``tacular update`` reused a cached download forever
     - always downloads the current release; ``tacular clear`` also removes ``obo/``

New
---

- :mod:`tacular.constants`: ``PROTON_MASS``, ``ELECTRON_MASS``, ``NEUTRON_MASS``
  (CODATA 2018), ``HYDROGEN_MASS`` and ``C13_C12_MASS_DIFF`` (AME2016, matching the
  bundled isotope table).
- ``items()`` on every lookup; ``query_name`` on ``MONOSACCHARIDE_LOOKUP``.
- ``tacular.ElementKey``: the type of every key ``ELEMENT_LOOKUP`` accepts.
