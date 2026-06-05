---
name: demo-scripts-dynamic-version-from-package-attr
description: "Use a package's public __version__ attribute in demo/example scripts rather than hardcoded strings or direct importlib.metadata calls. Use when: (1) demo/example scripts display or reference the package version, (2) you want sample code to stay in sync with releases automatically, (3) replacing a placeholder version string with the actual installed version, (4) teaching users how to consume version the same way their own code should."
category: documentation
date: "2026-06-05"
version: "1.0.0"
user-invocable: false
verification: verified-local
tags:
  - version-management
  - demo-scripts
  - example-code
  - package-public-interface
  - idiomatic-python
---

# Demo Scripts: Dynamic Version from Package Attribute

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-06-05 |
| **Objective** | Replace hardcoded version strings in demo/example scripts with the package's public `__version__` attribute, so example code stays in sync with releases automatically and demonstrates the idiomatic way users should consume version information. |
| **Outcome** | scripts/example_usage.py updated to import `__version__` from the package; script runs with dynamic version; demo remains authoritative and up-to-date across releases. |
| **Verification** | verified-local (script executed successfully with dynamic version) |

## When to Use

- A demo or example script contains a hardcoded version string (e.g., `version = "1.0.0"` or `VERSION = "0.7.1"`)
- The script is meant to show users how to use the package in their own code
- The version needs to update automatically when the package is released
- You want to avoid maintaining a separate version constant in the demo script
- A PR or issue flags a hardcoded version string in a sample file as a nitpick to fix

## Verified Workflow

### Quick Reference

**The pattern**: Import `__version__` from the package at the top of the demo script, then use it directly in code that displays or references the version.

```python
#!/usr/bin/env python3
"""Demo script showing how to use the package."""

from mypackage import __version__

def show_version():
    """Display the currently installed package version."""
    print(f"Using mypackage version {__version__}")

if __name__ == "__main__":
    show_version()
```

**Key principle**: Demo scripts should consume the package version the same way users consume it — by importing the package and accessing its public interface (`__version__`). This keeps the sample **idiomatic, automatically in sync with releases, and consistent** with how real user code operates.

### Detailed Steps

**Step 1: Identify hardcoded version in demo/example script**

```bash
# Find demo scripts (common patterns: example*, demo*, sample*)
find scripts/ -name "*example*" -o -name "*demo*" -o -name "*sample*" | head -10

# Check for hardcoded version strings
grep -n "version\s*=" scripts/example_usage.py
grep -n "VERSION\s*=" scripts/example_usage.py
grep -n "[0-9]\+\.[0-9]\+\.[0-9]\+" scripts/example_usage.py  # semver pattern
```

**Step 2: Identify the package name and how `__version__` is exported**

Verify that the package's `__init__.py` defines or imports `__version__`:

```bash
# Check package __init__.py
grep -n "__version__" hephaestus/__init__.py
# Should show: from importlib.metadata import version as _pkg_version
#              __version__ = _pkg_version("PackageName")
```

The `__version__` attribute is the public interface for version lookup. It's the correct way for users and demo code to reference the version.

**Step 3: Replace hardcoded string with import**

In the demo script, remove the hardcoded version line and add an import at the top:

```python
#!/usr/bin/env python3
"""Demo script showing how to use hephaestus."""

# Before:
# VERSION = "0.7.1"  # Hardcoded, never updated

# After:
from hephaestus import __version__
```

**Step 4: Update code that references the version**

Any code in the demo that used the hardcoded string now uses the imported `__version__`:

```python
# Before:
VERSION = "0.7.1"
print(f"hephaestus v{VERSION}")

# After:
from hephaestus import __version__
print(f"hephaestus v{__version__}")
```

**Step 5: Run the script locally to verify it works**

```bash
# Execute the demo script to verify it imports and displays the version correctly
python3 scripts/example_usage.py

# Should print something like: "hephaestus v0.7.1" (actual version from installed package)
```

**Step 6: No new tests needed**

For a one-line literal replacement in a demo script without an existing test suite, **smoke-run verification is sufficient**. Run the script, verify it outputs the correct version, and commit. No unit test is needed for this simple change.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Use `importlib.metadata.version()` directly in the demo | `from importlib.metadata import version; print(version("MyPackage"))` | Correct but not idiomatic for demo code — it teaches users to call importlib.metadata directly instead of consuming the package's public interface. Users should import the package and use its `__version__`, not reach into importlib themselves. | Demo code should show the idiomatic pattern: import the package, use `__version__`. This teaches users the right way to consume the library's version. |
| Keep the hardcoded string; update it manually on each release | `VERSION = "0.7.1"` in the demo, bump manually in release PR | Doesn't scale; the demo always lags behind actual version; requires discipline to remember the update; becomes stale and teaches users to hardcode versions | Never hardcode package versions in demo/example code. Use the package's public `__version__` so demos stay current automatically. |
| Replace with a placeholder like `__version__` | `VERSION = "__version__"` (literal string) | Confusing; users see the literal string `__version__` in output instead of an actual version number; defeats the purpose of the demo | Replace with the actual imported `__version__`, not a placeholder. |

## Results & Parameters

### Pattern Details

| Aspect | Details |
|--------|---------|
| **Import statement** | `from <package> import __version__` at the top of the demo script |
| **How to reference** | Use `__version__` directly (no function call needed) |
| **How `__version__` is defined** | Package's `__init__.py` imports it from installed metadata via `importlib.metadata.version("<distribution-name>")` |
| **Synchronization** | Automatic — whenever the package is released with a new git tag, `hephaestus.__version__` reflects the new version |
| **Scope** | Applies to demo scripts, example files, sample code — any code meant to teach users how to use the package |

### Expected Outcome

After the change:

- Demo script imports `__version__` from the package (line 3-5 of script)
- Any code that displays or references version uses the imported `__version__` attribute
- Running the script shows the actual installed package version
- No hardcoded version strings remain in the demo file
- The demo automatically reflects the correct version across all package releases

### Example: hephaestus

**File**: `scripts/example_usage.py`

**Before**:
```python
#!/usr/bin/env python3
"""Example usage of hephaestus utilities."""

VERSION = "0.7.1"  # Hardcoded, stale

def show_version():
    print(f"Using hephaestus version {VERSION}")
```

**After**:
```python
#!/usr/bin/env python3
"""Example usage of hephaestus utilities."""

from hephaestus import __version__

def show_version():
    print(f"Using hephaestus version {__version__}")
```

**Verification**:
```bash
$ python3 scripts/example_usage.py
Using hephaestus version 0.7.1
```

## Key Insight: Demo Code as Documentation

Demo scripts are not just runnable code — they **teach users how to consume your package**. When they see:

```python
from hephaestus import __version__
print(__version__)
```

...they learn that `__version__` is the right way to check the version in their own code. If instead the demo hardcodes a version string, users might incorrectly assume they should do the same.

**Quality of demo code directly impacts quality of user code**. Keep demos idiomatic, current, and minimal.

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| ProjectHephaestus | Issue #787 (GitHub — version nitpick) | Replaced hardcoded `VERSION = "0.7.1"` in `scripts/example_usage.py` with `from hephaestus import __version__`; script executed successfully; version displayed correctly; verified-local. |
