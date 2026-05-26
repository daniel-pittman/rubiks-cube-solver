# Contributing to rubiks-cube-solver

Thanks for your interest in this project. It started as a case study in
human-AI collaborative software development, but contributions that improve
correctness, accessibility, or platform coverage are very welcome.

## Development setup

```bash
git clone https://github.com/daniel-pittman/rubiks-cube-solver.git
cd rubiks-cube-solver

# Create a virtual environment and install the project + dev tools.
python3 -m venv venv
source venv/bin/activate            # On Windows: venv\Scripts\activate

# Install editable, with the dev extras (linters + pytest) and the runtime
# extras you'll exercise. `web` brings in Flask; `desktop` brings in PySide6
# and PyOpenGL (heavy — only needed if you'll touch the desktop app).
pip install -e ".[web,dev]"         # most contributors
pip install -e ".[all,dev]"         # if you'll work on the desktop app

# Install pre-commit hooks (matches what CI runs).
pre-commit install
```

See `CLAUDE.md` for the architecture overview and project conventions, and
`DEVELOPMENT_JOURNAL.md` for the design retrospective.

## Before you open a pull request

Run the full local check — CI runs exactly these:

```bash
black --check solver/
autoflake --check --remove-unused-variables --remove-all-unused-imports --recursive solver/
isort --check-only --profile black solver/
pylint --fail-under=9 solver/
pytest
```

All of these must pass. The pre-commit hook runs black, autoflake, isort, and
pylint automatically on commit; the test suite is your responsibility.

- Add tests for any new behavior. Existing tests live under `solver/core/tests/`
  (unit) and `solver/tests/` (integration).
- Keep the comment density consistent with the surrounding file — this project
  documents the *why* deliberately.
- **No personal data.** This is a public, open-source repository: examples,
  fixtures, comments, and docs use only fictional, generic content.

## Branching

- `main` — released, stable.
- `develop` — integration branch for upcoming work.

Open pull requests against `develop` unless a maintainer directs otherwise.
Releases land via a `develop → main` rebase-merge PR.

## Claude-driven review workflows

This repository runs three Claude-driven workflows on contributor activity:

- **Code review** — every PR gets an automatic review comment from Claude.
- **Security review** — PRs targeting `main` or `develop` also get a deeper,
  security-focused review.
- **`@claude` bot** — collaborators can mention `@claude` in an issue or PR
  comment to ask questions, request changes, or have it summarize. Only
  authors with collaborator access can drive it.

First-time outside contributors: your first workflow run may need a
maintainer to approve it before any review runs. After that, runs are
automatic on subsequent pushes.

## Reporting bugs

Open a GitHub issue with steps to reproduce. For **security** issues, do not
open a public issue — follow `SECURITY.md` instead.
