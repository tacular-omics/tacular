"""Internal data-generation package.

Parses ontology ``.obo`` source files into tacular ``*Info`` objects. This is
the single source of truth for the parsing logic: it powers both the developer
build pipeline (``data_gen/``, which renders the bundled ``data.py`` modules)
and the runtime ``tacular update`` command (which regenerates data into the user
cache; see :mod:`tacular.update`).

Not part of the public API.
"""
