# Contributing to tacular

Bug reports, fixes and new features are welcome. Use the
[issue tracker](https://github.com/tacular-omics/tacular/issues) for bugs and
questions, with a minimal example and the tacular and Python versions. Report
security problems privately as described in [SECURITY.md](SECURITY.md).

## Claiming an issue

Comment on the issue to say you are taking it before you start, and check that nobody has
already done so. One issue, one contributor: when two pull requests arrive for the same issue,
the first one that was claimed is reviewed and the other is closed, however good it is. If a
claim has had no pull request or update for 14 days, comment to take it over.

Issues labelled `good first issue` need no knowledge of the codebase. Issues labelled
`help wanted` do: each one names the files to read first and the test that shows it is done.

## Development setup

You need Python 3.12 or newer, [uv](https://docs.astral.sh/uv/) and
[just](https://just.systems/).

```bash
git clone https://github.com/tacular-omics/tacular.git
cd tacular
just install
```

`just --list` shows the other recipes.

Install the commit hooks once per clone with `uvx pre-commit install`. On every
commit they run `ruff check`, `ruff format --check` and a few file checks
(`uvx pre-commit run --all-files` runs them on everything). Type checks and
tests are not in the hooks; run `just check` for those.

## Running checks

CI runs these on every pull request. Run them before you push:

```bash
uv run ruff check src tests
uv run ruff format --check src tests
uv run ty check src
uv run pytest tests
python scripts/release_version.py check
```

Some tests skip, for two unrelated reasons, and the summary line does not say
which you are looking at. The fragment-ion offset checks skip permanently for
the ion types whose offset is resolved per residue rather than fixed, so nothing
you install or download makes those run. The checks that rebuild the bundled
UNIMOD and XLMOD data from their original OBO sources skip only because those two
files are not in the repository. Fetch them with
`just -f data_gen/justfile download-uni download-xlmod` and the checks then run.
They compare the rebuilt data against the bundled snapshot, so an upstream
release newer than the snapshot makes them fail. That is a signal to refresh the
bundled data, not a problem with your change.

If you change the documentation, build it the way CI does:

```bash
uv run sphinx-build -W -b html docs docs/_build/html
```

## Pull requests

- Branch from `main` and keep each pull request to one change.
- Add tests for new behaviour and fixed bugs.
- Add a line under `## [Unreleased]` in `CHANGELOG.md` for user-visible changes.
- Do not change the version number; the maintainers set it when releasing.
- CI must pass: lint, type check, tests on Python 3.12 to 3.14, and the wheel build.

## CLAUDE.md and AI agents

`CLAUDE.md` is the maintained developer guide: commands, architecture,
conventions and known gotchas. `AGENTS.md` points other coding agents to it.
Read it before a larger change, and update it in the same pull request when your
change makes part of it wrong. AI-assisted contributions are welcome; you are
responsible for reviewing and testing what you submit.
