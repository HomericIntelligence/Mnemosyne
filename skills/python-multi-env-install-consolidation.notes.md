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

## Amendment: Pinned Reinstall That Drops the Extra Set (2026-11-09)

**Verification:** verified-local — the failure and the repair were both observed in one
session. The command failed with a capability error, and the same command exited zero
after the extra was restored. CI consumption is pending.

### What happened

A CLI tool was installed in a uv tool isolate from a locally built development wheel
(correct for that moment). The request was to replace it with the published release of
the same major line, so the pinned install command was run:

```bash
uv tool install --force DIST==VERSION
```

The install succeeded. `SCRIPT --version` then exited non-zero:

```
ConfigurationError: this command needs the product layer
(missing modules: <module-a>, <module-b>, <module-c>)
Recovery: install it with: pip install 'DIST[EXTRA]'
```

The version was correct. The command name was correct. The distribution was present in
`uv tool list`. Only the optional extra set was absent, because the pinned form named no
extras while the development install had brought its dependencies transitively.

### Why the version check missed it

Two checks passed and both were true:

- `SCRIPT --version` is the natural install check, but it ran against the previous
  install during planning and reported the expected version.
- The wheel metadata version matched the requested pin.

Neither check reaches a code path that imports the optional layer. The capability
error appears only when the command actually runs its product work.

### The repair

```bash
uv tool install --force 'DIST[EXTRA]==VERSION'
```

The quoted bracket form preserves the extra list through the shell. Verification
repeated all of these:

- `SCRIPT --version` printed the expected version and exited zero.
- The installed module tree contained the repaired capability and dependency policy.
- A real product command, not only `--version`, completed.

### Generalization

- Read `Provides-Extra` from the **installed working** distribution before removing it.
  That set is the contract the console script was built and used against.
- A pinned install form that omits extras is a silent regression from an unpinned or
  development install that pulled them in. The pin is not the whole specification.
- The closure check must run a command that reaches the optional dependency. `--version`
  often does not.
- The failure is not version-specific, so consulting only `info.requires_python` on the
  release API does not prevent it.
