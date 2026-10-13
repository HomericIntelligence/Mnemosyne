---
name: python-multi-env-install-consolidation
description: "Consolidate divergent copies of a Python distribution across pip interpreter sites, conda environments, and uv tool isolates into one canonical newest-release install. Use when an install or upgrade request can hit several environments, when console scripts shadow each other on PATH, or when a locally built development wheel sits beside release copies."
category: tooling
date: 2026-10-09
version: "1.0.0"
user-invocable: false
verification: verified-local
tags: [python-install, pip, uv-tool, conda, multi-environment, consolidation, direct-url, path-shadowing]
---

# Python Multi-Environment Install Consolidation

## Overview

| Field | Value |
| ----- | ----- |
| Date | 2026-10-09 |
| Objective | Give one machine exactly one newest-release copy of a Python distribution when older copies exist in several environments |
| Outcome | Successful: three divergent copies removed, one newest release installed, and every surface verified |
| Verification | verified-local: the workflow ran end-to-end in a real session. CI consumption is pending. |

## When to Use

Use this skill when one or more of these conditions apply:

- A user asks to install the newest release of a Python distribution, or to remove every copy and keep only the newest.
- The machine has several Python environments: a pip user site for an older interpreter, a conda environment, or one or more uv tool isolates.
- The `pip` and `python3` executables on PATH resolve to different interpreters.
- Console scripts of the same distribution exist in more than one bin directory on PATH.
- A locally built development wheel copy exists beside release copies.

## Verified Workflow

### Quick Reference

```bash
# 1. Enumerate every copy BEFORE any change.
pip show DIST              # the interpreter that owns this pip
python3 -m pip show DIST   # the default interpreter
uv tool list               # uv tool isolates
which -a SCRIPT            # PATH shadows of the console scripts

# 2. Check the provenance of each copy.
cat .../site-packages/DIST_INFO.direct_url.json
#    https URL  -> downloaded release copy
#    file URL to a .whl -> locally built development wheel

# 3. Remove each copy with the manager that owns it.
pip uninstall -y DIST
python3 -m pip uninstall -y DIST
uv tool uninstall DIST     # also removes all entry-point scripts

# 4. Install one canonical copy of the new release.
python3 -m pip install --upgrade DIST   # import and scripts
# or: uv tool install --upgrade DIST    # CLI-only isolate

# 5. Verify closure on every surface.
python3 -c "import PKG; print(PKG.__version__)"
pip show DIST 2>&1 | grep "not found"   # in each non-canonical site
which SCRIPT && SCRIPT --help | head -3
```

### Suggested Approach

Treat install or upgrade as a state target, not a command target. The target
state is: each environment either has the newest release or has nothing. Each
environment owns an independent copy. A change to one copy does not change the
others.

1. **Enumerate before mutation.** Query each manager that can hold a copy: the
   pip of each interpreter on PATH, the default interpreter site, and uv tools.
   List console-script locations with `which -a`. A copy that you do not
   enumerate stays stale.
2. **Pair each pip with its interpreter.** A pip executable on PATH can belong
   to an older or different interpreter than `python3`. Use the
   `INTERPRETER -m pip` form for the target that you mean. Read the first line
   of `pip --version` to see which interpreter a given pip owns.
3. **Check provenance through direct_url.json.** The `direct_url.json` file in
   each dist-info directory records the origin of the copy. An `https` URL is
   a downloaded release. A `file` URL to a local wheel is a development build
   with a source tree behind it. When the request is to keep only the newest
   release, remove development-wheel copies too. When development on that
   source can continue, report the choice before you replace that copy.
4. **Select the canonical target before removal.** The new release can have a
   narrower `requires_python` range than the old copies. Read
   `info.requires_python` from the PyPI JSON API first. An older interpreter
   can be unable to accept the newest release; the only consistent end state
   for that interpreter is then removal. Use the default interpreter
   environment as the canonical target when import and console scripts both
   matter. Use a uv tool isolate when the tool is CLI-only and must stay out
   of project environments.
5. **Remove each copy with its owning manager.** pip removes only its own
   sites. `uv tool uninstall` removes the isolate and every entry-point
   script in one operation. Do not delete files in site-packages by hand:
   orphaned scripts remain and still shadow.
6. **Verify closure.** Success needs all of these results: import shows the
   new release version in the canonical environment; `pip show` reports
   not-found in every other site; `uv tool list` shows no copy; `which`
   resolves each console script into the canonical environment; one `--help`
   smoke run exits zero.

Short decision-branch examples from the verified session:

- The newest release required `>=3.13, <3.14`. The pip owned by Python 3.10
  could never accept it, so its copy could only be removed. The conda
  Python 3.13 environment became the canonical target.
- A uv tool isolate held 58 entry-point executables. One
  `uv tool uninstall` removed all of them. The terminal `which` check was
  necessary to confirm that the canonical environment scripts were on PATH.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| ------- | -------------- | ------------- | -------------- |
| N/A | The direct enumerated-then-consolidated approach was successful. | N/A | Enumeration before mutation made consolidation a single pass with no retries. |

## Results & Parameters

### Configuration

```yaml
# Canonical target selection
target_contexts:
  import_and_scripts: "default interpreter environment (INTERPRETER -m pip)"
  cli_only_isolated: "uv tool isolate (uv tool install)"
constraints:
  requires_python: "read info.requires_python from the PyPI JSON API before target selection"
  managers:
    - "INTERPRETER -m pip for each interpreter site"
    - "uv tool uninstall / uv tool install for isolates"
```

### Expected Output

- Non-canonical environments report "Package(s) not found" from `pip show`.
- `uv tool list` no longer names the distribution.
- Import in the canonical environment prints the new release version.
- `which` resolves console scripts into the canonical environment bin
  directory, and a `--help` smoke run exits zero.

## Verified On

| Project | Context | Details |
| ------- | ------- | ------- |
| Public PyPI CLI distribution in a user-owned ecosystem | Developer workstation session on Linux | Three divergent copies consolidated to one newest release; see [notes](python-multi-env-install-consolidation.notes.md). |

## References

- [pip user guide: user installs](https://pip.pypa.io/en/stable/user_guide/#user-installs)
- [uv documentation: tools](https://docs.astral.sh/uv/concepts/tools/)
- [PEP 610: direct_url.json provenance](https://peps.python.org/pep-0610/)
- Related: [env-manager-migration-python-version-drift](env-manager-migration-python-version-drift.md)
- Related: [python-packaging-pyproject-editable-install](python-packaging-pyproject-editable-install.md)
