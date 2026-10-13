# Raw Session Notes: Python Multi-Environment Install Consolidation

## Session Details

**Date:** 2026-10-09
**Duration:** ~15 minutes
**Participants:** User + coding agent
**Target:** a public PyPI-published CLI distribution in the user's own ecosystem
**Environment:** Linux workstation; conda base (Python 3.13); pip user site for
Python 3.10; uv tool isolates

The distribution name and local absolute paths are omitted on purpose for
privacy. The decision rules do not depend on them.

## Initial Request

1. Install the newest version of the distribution from its PyPI project page.
2. Then: "remove them all so we only have the most recent".

## Enumerated State (before mutation)

| Environment | Manager | Version observed | Provenance |
| ----------- | ------- | ---------------- | ---------- |
| pip user site, Python 3.10 | pip (user) | 0.10.0 | PyPI release |
| conda base, Python 3.13 | interpreter pip | 0.10.7.dev31 | locally built wheel, `file` URL in `direct_url.json` |
| uv tools | uv tool | 0.10.6.dev11 | development install, 58 entry-point executables |

PyPI JSON API facts for the newest release:

- `info.version`: 0.11.0
- `info.requires_python`: `>=3.13, <3.14`
- Source: `https://pypi.org/pypi/<distribution>/json`

Key consequence: the Python 3.10 site could never accept 0.11.0, so removal
was the only consistent end state for that interpreter. This
requires_python check is the branch most likely to surprise.

## Commands Executed

All commands succeeded; each manager changed only its own scope.

```bash
pip uninstall -y DIST              # removed 0.10.0
python3 -m pip uninstall -y DIST   # removed 0.10.7.dev31 (dev wheel)
uv tool uninstall DIST             # removed 0.10.6.dev11; uv reported 58 executables
python3 -m pip install --upgrade DIST  # downloaded the 0.11.0 wheel, installed
```

## Verification Evidence

- Import in the conda Python 3.13: version 0.11.0, single `Location` in the
  conda site-packages.
- The Python 3.10 pip: "Package(s) not found".
- `uv tool list`: distribution absent.
- `which SCRIPT` resolved into the conda bin directory; `--help` printed usage
  and exited zero.

## Generalization Notes

- Provenance through PEP 610 `direct_url.json` separates development wheels
  from release copies. That decides whether replacement loses local
  development state.
- The `pip` on PATH belonged to an older interpreter than `python3`. The
  `INTERPRETER -m pip` form prevented the unsafe assumption that one pip
  covers the default interpreter.
- A blind `pip install --upgrade` would have upgraded, at most, the site of
  the pip on PATH and left two divergent copies in place. Enumeration first
  changed that into a one-pass consolidation.
