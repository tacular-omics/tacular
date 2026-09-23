# Copilot instructions for tacular

Read [`CLAUDE.md`](../CLAUDE.md) at the repo root: it is the canonical guide (commands,
architecture, public API, conventions, gotchas). Library usage is in
[`llms-full.txt`](../llms-full.txt).

Key rules:

1. Never hand-edit `src/tacular/*/data.py`. Fix parsing in `src/tacular/_datagen/<name>.py`,
   then regenerate with `just -f data_gen/justfile gen-<name>` and diff against `jsons/`.
2. Do not use `peptacular` or `paftacular` to verify tacular's masses; check the OBO
   source, the mzPAF spec, or element-mass arithmetic.
3. Google-style docstrings; typed Python >= 3.12; tests in `tests/` use `tmp_path` and set
   `TACULAR_DATA_DIR` for anything touching the cache.
4. Before a commit: `uv run ruff check src tests`, `uv run ruff format --check src tests`,
   `uv run ty check src`, `uv run pytest tests`.
5. Never bump the version, tag, or publish; only the tacular-omics overseer releases.
