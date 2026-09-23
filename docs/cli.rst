Command-line interface
======================

tacular ships a small CLI for refreshing the bundled ontology data without
reinstalling the package. It is installed as the ``tacular`` console script
and is also available as ``python -m tacular``.

.. code-block:: text

   usage: tacular [-h] [-v] {update,status,clear,where} ...

   tacular update [ontologies ...]   download latest sources and regenerate cached data
   tacular status                    show bundled vs cached data versions
   tacular clear                     remove cached data (revert to bundled)
   tacular where                     print the cache directory

Global option ``-v`` / ``--verbose`` raises the log level beyond warnings
(``-v`` for info, ``-vv`` for debug with tracebacks). It goes **before** the
subcommand, for example ``tacular -vv update unimod``. Parsing failures always
print a warning with the offending entry and a traceback, whatever the verbosity.

How the cache works
-------------------

Every refreshable ontology ships baked into the package. ``tacular update``
writes regenerated data to a per-user cache, and each lookup prefers the cached
copy over the bundled one when it exists. A refresh takes effect on the next
``import tacular``. If the cache is missing, disabled, or unreadable, tacular
logs a warning (for an unreadable file) and falls back to the bundled data.

The refreshable ontologies are ``unimod``, ``xlmod``, ``psimod``, ``resid``,
``gno`` and ``uniprot_ptm``. The other lookups (amino acids, elements, ion
types, neutral deltas, proteases, monosaccharides, reference molecules) are
static and only change with a new tacular release.

``tacular update``
------------------

.. code-block:: bash

   tacular update                  # refresh all six ontologies
   tacular update unimod xlmod     # refresh a subset
   tacular update --offline DIR    # regenerate from local source files, no download

With no arguments every ontology is refreshed, including GNOme, which is a
large download (the command prints a note first). Name a subset to skip it.

Downloaded source files are kept in the ``obo/`` folder of the cache directory
and reused on later runs ("using cached ..."). To fetch a newer upstream release,
delete that file (or the whole ``obo/`` folder) first. ``tacular clear`` does
not remove it.

Sources:

.. list-table::
   :header-rows: 1

   * - Ontology
     - Source file
     - Downloaded from
   * - ``unimod``
     - ``UNIMOD.obo``
     - ``https://www.unimod.org/obo/unimod.obo``
   * - ``psimod`` and ``resid``
     - ``PSI-MOD.obo``
     - ``https://purl.obolibrary.org/obo/mod.obo`` (RESID is derived from PSI-MOD)
   * - ``xlmod``
     - ``XLMod.obo``
     - ``https://purl.obolibrary.org/obo/xlmod.obo``
   * - ``gno``
     - ``GNOme.obo``
     - ``https://purl.obolibrary.org/obo/gno.obo``
   * - ``uniprot_ptm``
     - ``ptmlist.txt``
     - UniProt ``ptmlist.txt`` (UniProt's flat-file format, not OBO)

``--offline DIR`` reads the source files from ``DIR`` instead of downloading.
The files must use the names in the table above.

The exit code is ``0`` on success and ``1`` for an unknown ontology name, a
missing offline file, or a download or file error. The error is printed as one
line. Add ``-vv`` to see the full traceback:

.. code-block:: console

   $ tacular update bogus
   error: ValueError: unknown ontologies ['bogus']; choose from ['unimod', 'xlmod', 'psimod', 'resid', 'gno', 'uniprot_ptm']

If an ontology release contains entries whose stated mass disagrees with their
composition, ``update`` prints a note with the count and one example. Those
entries are cached as published upstream.

``tacular status``
------------------

Shows the cache directory, whether the cache is enabled, and for each ontology
whether a cached copy exists, the version currently in use, and its entry count:

.. code-block:: console

   $ tacular status
   cache dir: /home/user/.cache/tacular
   cache enabled

   ontology     cached   active version           entries
   unimod       no       17:02:2026 11:36         1560
   xlmod        no       1.5.1                    189
   psimod       no       1.032.4                  1558
   resid        no       1.032.4                  535
   gno          no       2025-10-10               3534
   uniprot_ptm  no       2026_01 of 28-Jan-2026   438

The versions and counts above are the data bundled with tacular 1.1.2.

``tacular clear``
-----------------

Deletes the cached ontology data (the ``data/`` folder of the cache directory),
so every lookup goes back to the bundled copy on the next import. Downloaded
source files in ``obo/`` are kept.

``tacular where``
-----------------

Prints the cache directory.

Environment variables
---------------------

``TACULAR_DATA_DIR``
   Cache directory. Default: ``$XDG_CACHE_HOME/tacular``, or
   ``~/.cache/tacular`` when ``XDG_CACHE_HOME`` is unset.

``TACULAR_DISABLE_CACHE``
   Set to ``1``, ``true``, ``yes`` or ``on`` to ignore the cache and always use
   the bundled data. ``tacular status`` reports the cache as ``DISABLED``.

Python API
----------

The same refresh is available from Python:

.. autofunction:: tacular.update.update
