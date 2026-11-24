---
name: tooling-codex-plugin-cache-validation-metadata
license: BSD-3-Clause
description: "Separate harness install metadata from plugin content when repository validation fails in an installed Codex plugin cache. Use when: (1) a validator passes in the source checkout and fails in the installed cache; (2) the failure names a harness-written install metadata file; (3) a self-contained or forbidden-reference check matches a repository URL in that file."
category: tooling
date: 2026-11-24
version: "1.0.0"
user-invocable: false
tags: [codex, plugin, marketplace, validation, install-metadata, cache]
---

# Codex Plugin Cache Validation Metadata

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-24 |
| **Objective** | Decide whether a validation failure in an installed Codex plugin cache is a content defect or an effect of harness install metadata. Prove the result with a clean-copy check. |
| **Outcome** | Successful. The validator failed in the installed cache and passed on a copy without the harness metadata file. The plugin content was correct. |

## When to Use

- A repository validation command passes in the source checkout and fails in the installed plugin cache.
- The failure names a harness-written file such as `.codex-marketplace-install.json`.
- A self-contained check rejects a repository URL that only the harness metadata contains.
- An operator asks whether the installed plugin has a content defect.

## Verified Workflow

### Quick Reference

```bash
# Reproduce validation on the plugin content without harness install metadata.
D=$(mktemp -d)
tar -C "<installed-plugin-dir>" --exclude=.codex-marketplace-install.json -cf - . | tar -C "$D" -xf -
cd "$D" && python3 scripts/validate_plugins.py
```

### Suggested Approach

1. Run the validator in the source checkout first. Record the result.
2. Run the same validator in the installed plugin cache. Record the exact failed check and the file name.
3. Inspect the named file. Codex writes `.codex-marketplace-install.json` with `source`, `ref_name`, `revision`, and related fields. This file is install provenance, not plugin content.
4. Copy the installed tree to a temporary directory. Exclude the harness metadata file. Run the validator on the copy.
5. If the clean copy passes, report a metadata-only failure. Do not change plugin content for this result.
6. If the clean copy fails, report a content defect and continue normal diagnosis.
7. Do not remove the metadata file from the installed cache. The harness uses it for update and provenance checks.
8. A repository validation that must run inside the cache needs an explicit exclusion for harness metadata. Change the repository only when its owner requests that behavior.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | --------------- |
| Re-run in the marketplace checkout | Ran the validator in a second installed location. | Codex writes the same metadata file into the marketplace checkout and the plugin cache. | Change the input tree, not the install location. Exclude the harness metadata file. |

## Results & Parameters

### Configuration

```text
installed-plugin-dir: <plugin cache version directory>
harness-metadata-file: .codex-marketplace-install.json
validator: python3 scripts/validate_plugins.py
```

### Expected Output

- Installed cache: the validator reports one self-contained failure on the harness metadata file.
- Clean copy: the validator passes.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------------- |
| Codex plugin cache | Athena plugin 0.7.0 installed from a Git marketplace at a release tag | The cache run reported one self-contained failure. The clean-copy run passed. The installed skills ran correctly. |

## References

- [Athena repository](https://github.com/HomericIntelligence/Athena)
- Related: [tooling-codex-plugin-symlink-empty-cache-fix](tooling-codex-plugin-symlink-empty-cache-fix.md)
