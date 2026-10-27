---
name: git-tree-enumeration-prefixed-names
description: "Normalize path-prefixed git tree enumeration entries to basenames before comparing them with a manifest, and give test doubles the same prefixed output shape as the real command. Use when: (1) a shell or CI gate lists the files of a directory inside a git tree with git ls-tree and compares the result with file names from another source, (2) the comparison mismatches or vacuously passes because one side has directory-prefixed paths and the other side has bare names, or (3) you write a stub for such a listing and must choose its output shape."
category: tooling
date: 2026-10-27
version: "1.0.0"
user-invocable: false
tags: [git, ls-tree, tree-enumeration, path-prefix, basename-normalization, test-double, stub-realism, masked-defect, name-space, comparison]
---

# Normalize Git Tree Enumeration Before Name Comparison

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-27 |
| **Objective** | Compare the files of a directory inside a git tree with a manifest from another source without false mismatch or vacuous pass. |
| **Outcome** | Successful; a release gate defect that prefect test doubles had masked was found in review, corrected, and merged. |

`git ls-tree --name-only <tree> <dir>` does not return bare file names. It
returns one line per entry, and each line includes the directory prefix, for
example `migrations/0001_core.sql`. The same prefix rule applies when a path
argument selects a subdirectory.

A consumer that compares these lines directly with a manifest of bare names
fails on every real entry. Worse, a test double that returns bare names makes
the broken consumer pass: the double and the consumer agree on the wrong name
space, so the defect reaches production.

The rule has two halves. First, pick one canonical name space for the
comparison, usually the basename, and map both sides into it. Second, give
every test double the exact output shape of the real command, prefix included,
so the normalization branch is exercised.

## When to Use

- A shell, Python, or CI gate enumerates a directory inside a git tree and
  compares the entries with a manifest, a directory on disk, or a set from an
  API.
- Every real comparison mismatches, or the comparison passes only in tests.
- You write or review a stub for a tree listing and must decide whether the
  stub returns bare names or prefixed paths.
- Review finds that test evidence and production behavior diverge for a
  name-based comparison.

## Verified Workflow

### Quick Reference

```bash
# Raw output is prefixed, one line per entry:
git ls-tree --name-only origin/main migrations/
# migrations/0001_core.sql
# migrations/0002_ledger.sql

# Map to the basename name space before comparison:
git ls-tree --name-only origin/main migrations/ | while read -r entry; do
  printf '%s\n' "${entry##*/}"
done
```

```python
# Python consumer: rpartition keeps the basename, then strip the suffix.
stem = entry.rpartition("/")[2].removesuffix(".sql")
```

### Suggested Approach

1. Identify the name space of each comparison side: prefixed path, bare name,
   or stem. Pick the basename (or stem) as the canonical space and convert
   each side with one explicit function. Do not let one side stay prefixed by
   accident.
2. Compare after conversion, not before. A set difference computed on raw
   `ls-tree` output reports every file as missing-from-manifest.
3. Build the test double from observed real output. Capture one real
   `git ls-tree` invocation against a fixture tree and copy its exact line
   shape into the stub, prefix included. A double built from the consumer's
   expectation, not the command's output, reproduces the consumer's bug.
4. Assert at least one comparison that only passes when normalization ran,
   for example a manifest that contains the entry the raw output prefixes.

If a fixture tree cannot be created, a double is still acceptable; derive its
shape from the command's documented output and record the substitution.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Bare-name stub | A unit-test stub returned `0001_core.sql` for a tree listing whose real output is `migrations/0001_core.sql` | The consumer compared bare names, so stub and consumer agreed; the same consumer failed against the real tree | Build doubles from the command's real output shape; a double that mirrors the consumer mirrors its defect |

## Results & Parameters

### Configuration

```python
# Canonical comparison shape: convert both sides to stems, then diff.
def tree_stems(ls_tree_output: str) -> set[str]:
    return {
        line.rpartition("/")[2].removesuffix(".sql")
        for line in ls_tree_output.splitlines()
        if line
    }

missing = manifest_stems - tree_stems(raw_listing)
unexpected = tree_stems(raw_listing) - manifest_stems
```

### Expected Output

- The raw listing shows the directory prefix on every entry.
- After normalization, the manifest set and the tree set diff to empty for a
  synchronized pair.
- The double-based test fails when the normalization line is removed; this
  failure proves the test exercises the prefix mapping.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| A database-backed release promotion gate | One PR; review recovered the prefix defect before merge, normalization and a prefixed stub merged green | Related release-gate practices in [release-embedded-script-capability-guard](release-embedded-script-capability-guard.md) |

## Related Entries

- [enumerated-registry-assertion-drift](enumerated-registry-assertion-drift.md) — read the registry directory at the bound ref, never from a stale working tree
- [git-unmerged-branch-file-access](git-unmerged-branch-file-access.md) — read files that exist only on another ref
- [union-containment-vacuous-pass](union-containment-vacuous-pass.md) — a related shape where a comparison passes because both sides are empty
