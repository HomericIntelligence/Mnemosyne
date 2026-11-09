---
name: table-to-manifest-fail-open-validation
description: "Keep a refusal working when in-code policy tables become an external data manifest. Use when a refactor moves literals such as path policies, allow-lists, or grants out of source into YAML or JSON that a loader reads at run time, and the loader must refuse a malformed declaration instead of accepting it."
category: architecture
date: 2026-11-09
version: "1.0.0"
user-invocable: false
verification: verified-ci
tags:
  - manifest
  - policy-tables
  - fail-open
  - placeholder-expansion
  - equivalence-test
  - packaging
  - refactor
---

# Table-to-Manifest Fail-Open Validation

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-09 |
| **Objective** | Move hard-coded policy tables into one external manifest without weakening any refusal that the compiled tables enforced. |
| **Outcome** | Successful — every table reproduced the deployed release exactly, and four fail-open paths found in review were closed before merge. |
| **Verification** | verified-ci — the merged commit passed its full check set, and the merged manifest matched the live deployment's tables row for row. |

A compiled table cannot be malformed. A manifest can. When the table leaves the
source file, the loader becomes the only thing that still refuses a bad
declaration. A loader that accepts a malformed entry converts a build-time
guarantee into a run-time liability.

## When to Use

- A change moves literals — policy rows, path rules, allow-lists, grants — out of
  a source module into YAML or JSON that a loader reads at run time.
- The moved data carries fields that name an owner, a group, a mode, or a
  permission, and a wrong value widens access instead of failing.
- The data uses placeholders that a loader expands, which leaves a chance for an
  unexpanded token to reach a consumer.
- A generator converts the old tables into the new file, so two sources of the
  same fact exist during the migration.

Do not use this skill for a dependency or version manifest, which has a different
intent. Use it when the manifest is the *policy* itself.

## Verified Workflow

### Quick Reference

```text
Moving tables into a manifest:
  ├─ 1. Freeze the current tables as a baseline fixture first.
  │       The fixture is your oracle. Generate it from the OLD code.
  ├─ 2. Move the data. Keep public accessor names unchanged.
  ├─ 3. Require an exact match against the baseline fixture.
  ├─ 4. Audit the loader for fail-open gaps (the four classes below).
  ├─ 5. Prove the manifest ships in the built artifact.
  └─ 6. Compare against the DEPLOYED release, not only the branch.

Fail-open gap = an input the old table could not express
                and the new loader accepts.
```

### Suggested Approach

1. **Freeze a baseline before you move anything.** Generate the fixture from the
   old code, not the new file. A fixture generated from the new file certifies
   only that the new file agrees with itself. Compare every row, every field.
2. **Keep the public names.** Readers that import the old table name must keep
   working. Re-check that each name still resolves, that callers can iterate it,
   and that a test that substitutes the table still takes effect.
3. **Audit for these four fail-open classes.** Each one was present in a real
   migration and each one silently accepted a bad declaration:
   - **Document-level placeholder validation.** A check that runs once per value
     lets an unknown token pass whenever a known deferred token is also present.
     Validate **per token**, against the declared deferred set.
   - **Unknown selector returns empty.** A lookup that yields the empty collection
     for an unknown key turns a typo into "no policy" rather than an error.
     Raise on an unknown key.
   - **Tie-break by default.** If rows carry an explicit order or priority and
     two rows share a value, sorting resolves the tie arbitrarily. Refuse a
     duplicate.
   - **Dropped on mismatch.** A loader that skips a row it cannot map loses a
     rule without a signal. Raise instead.
4. **Keep the generator honest.** When a migration generator still runs, make its
   output round-trip byte for byte, and make it fail on input it cannot map. A
   generator that silently skips a row turns the manifest into a partial copy.
5. **Prove the artifact ships the file.** A source-tree read can pass while the
   built artifact omits the manifest. Load the packaged copy, and extend any
   container or image build to copy the file and to assert it loads.
6. **Compare against the deployed release.** The branch and the running system
   can disagree. Load the deployed module and compare its tables against the
   merged manifest. Agreement is the strongest available evidence that the new
   form preserves behaviour; a difference is a defect found before release.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Generate the fixture from the new manifest | Built the baseline by serialising the loader output | The fixture then agreed with the loader by construction and could not detect a dropped or changed row | Generate the baseline from the old code before the move |
| Validate placeholders once per value | Ran one unknown-token check over the whole string | A value that held both a deferred token and an unknown token passed, and the unknown token reached a consumer | Check each token against the declared deferred set |
| Reuse the old fixture without regenerating | Kept a frozen fixture across a rebase | The base branch had removed rows, so the fixture asserted rows the code no longer had | Regenerate the fixture from the same base as the manifest |
| Treat a literal row as a duplicate | Dropped a literal path row because a placeholder family looked equivalent | The literal row was a separate policy that real consumers depended on; its removal changed classification | Compare rows by identity and keep a literal row that a consumer classifies |
| Assume the wheel include was enough | Added the file to the build configuration only | The container build failed because its context did not copy the file | Update every build path that the forced include reaches |
| Trust the merged-and-green state | Stopped at a green merge | The table content was never compared with the running system | Compare the merged data with the deployed release |

## Results & Parameters

### Configuration

```yaml
migration_baseline:
  generated_from: old_code_before_move   # never from the new loader
  comparison: every_row_every_field
  tables_covered: all
loader_refusals:
  unknown_placeholder: per_token
  unknown_selector: raise
  duplicate_order: raise
  unmappable_row: raise
artifact_proof:
  load: packaged_copy
  container: file copied and loaded
deployment_evidence:
  compare_against: deployed_release_module
  expected: exact_match_per_table
```

### Expected Output

- The baseline fixture reproduces all rows of all tables exactly.
- Each fail-open class has a refusal, and a malformed declaration fails the load.
- The packaged artifact loads the manifest from its own data directory.
- The merged tables equal the deployed release's tables, row for row.
- The generator round-trips to the committed file byte for byte.

## Verified On

| Project | Context | Details |
| --------- | --------- | ------- |
| LLM360/comet | PR #4566 — path policy tables moved to one manifest | [notes](table-to-manifest-fail-open-validation.notes.md) |

## References

- [dependency-manifest-single-source-of-truth](dependency-manifest-single-source-of-truth.md) — dependency and
  version manifests, a different intent
- [testing-source-package-asset-contract-mirroring](testing-source-package-asset-contract-mirroring.md) —
  keeping a packaged asset equal to its source copy
- [architecture-getattr-delegate-collapse-mypy-regressions](architecture-getattr-delegate-collapse-mypy-regressions.md)
  — static-typing fallout when a dynamic attribute serves a former literal