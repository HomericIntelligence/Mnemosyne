---
name: derive-pin-from-source-of-truth-not-hardcoded-literal
description: "Derive a version, digest, image lineage, or other pin from its canonical source instead of comparing against a literal, and treat descriptive documentation as current state rather than a rule to enforce. Use when: (1) a build, gate, or probe script asserts a specific version, digest, or lineage value, (2) the asserted value also exists in a manifest, recipe, lockfile, or environment file, (3) documentation states the toolchain or lineage currently in use, (4) an existing check compares a materialized copy of a manifest instead of the manifest itself, or (5) a hardcoded value sits inside a quoted heredoc where the surrounding variable cannot reach it."
category: ci-cd
date: 2026-11-01
version: "1.0.0"
user-invocable: false
verification: verified-local
tags:
  - hardcoded-literal
  - source-of-truth
  - pinned-version
  - drift-detection
  - heredoc-variable-scope
  - descriptive-vs-prescriptive-docs
  - enforcement-scope-creep
  - derived-pin
  - image-lineage
  - digest-verification
---

# Derive a Pin From Its Source of Truth, Not From a Literal

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-01 |
| **Objective** | Keep every asserted version, digest, or lineage value derived from its canonical source so a source change propagates without a matching edit, and resist converting descriptive documentation into a new blocking rule. |
| **Outcome** | Successful. Literal assertions inside quoted heredocs were replaced with values passed from the recipe, and an enforcement claim added to documentation was removed because the documentation described current state only. |

A pin has exactly one owner: the manifest, recipe, lockfile, or environment
file that declares it. Every script that asserts the pin reads that owner.
When a script compares against a literal, the two copies drift. The drift
appears as a confusing failure in a place that has no authority over the
value.

Two failure modes follow from this. The first is a literal that cannot see
the owner. The second is a rule invented from descriptive prose.

## When to Use

- A build, gate, or probe script asserts a specific version, digest, image
  lineage, or interpreter.
- The asserted value also appears in a manifest, recipe, lockfile, or
  environment file.
- A check compares a materialized copy of a manifest, such as a build
  evidence file, instead of the manifest itself.
- Documentation states which toolchain, runtime, or lineage is in use now.
- An assertion sits inside a quoted heredoc, `<<'TOKEN'`, where the enclosing
  shell variables do not expand.

## Verified Workflow

### Quick Reference

Pass the owner's value into the assertion. Do not type the value.

```bash
# Owner: the recipe file declares the expected value.
source ./recipe.env

python3 - "$BASE_CUDA_VERSION" <<'PY'
import sys

import torch

assert torch.version.cuda == sys.argv[1], torch.version.cuda
PY
```

Compare against the owner file itself, not against a copy of its digest.

```bash
pinned=$(sha256sum "$recipe_file" | awk '{print $1}')
```

### Suggested Approach

1. Find the owner of the pin. Prefer the file that the build already sources
   or the lockfile that the resolver already reads.
2. Classify each assertion as parametric or literal. A parametric assertion
   compares an artifact with the value the owner declares, so it stays
   correct across a declared change. A literal assertion replaces the owner
   with a copy.
3. Keep parametric assertions. They test build correctness, not a lineage
   preference. Removing them lets a mislabeled artifact pass.
4. Replace literal assertions. Pass the owner's value as an argument. A
   quoted heredoc blocks expansion, so `python3 - "$VAR" <<'PY'` with
   `sys.argv` is the reliable form.
5. Distinguish the manifest from its materialized copy. A build evidence file
   written from the manifest is a record of one build, not the authority. Read
   the manifest when you must satisfy a digest check.
6. Read documentation as description. A sentence that a value "currently is"
   or "moves with the cluster" states present state. It does not authorize a
   blocking check. Add a check only when the requirement is separate from the
   state.
7. Check each remaining literal with a targeted search before you finish:

   ```bash
   grep -rn '"13\.1"\|startswith("2\.11\.0")' scripts/*.sh scripts/*.sbatch
   ```

8. Run a syntax check on each changed script. Exercise each argument-passing
   form directly before you commit, because a heredoc argument error reaches
   a long build only after the build starts.

Supporting case detail is in [the notes](./derive-pin-from-source-of-truth-not-hardcoded-literal.notes.md).

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | --------------- |
| Asserted the version as a literal inside a quoted heredoc | Wrote `assert torch.version.cuda == "13.1"` in a `<<'PY'` block | The enclosing recipe variable cannot expand inside a quoted heredoc, so the literal became the only authority and a declared change needed a matching script edit | Pass the owner's value as an argument and read `sys.argv` |
| Satisfied a digest check by supplying the digest of a built artifact | Read the digest from a build evidence file and passed it to a check that compares the manifest | The evidence file is a copy written from the manifest, so the two differed and the check refused the input | Read the digest of the manifest itself; a materialized copy is not the owner |
| Added a blocking rule because the documentation described a requirement | Turned "the toolchain currently is X" into a new guard that refuses other values | The prose described current state only, so the guard added a constraint that no requirement asked for | Keep descriptive statements descriptive; add a check only for a separate requirement |

## Results & Parameters

### Configuration

| Parameter | Value | Note |
| --------- | ------- | ------ |
| Owner file | the manifest, recipe, or lockfile that declares the pin | The only authority for the value |
| Assertion form | `cmd - "$OWNER_VAR" <<'EOF'` with `sys.argv[1]` | The form that works inside a quoted heredoc |
| Digest source | `sha256sum "$owner_file"` | Not the digest of a generated copy |

### Expected Output

- One owner for each pin, with no second copy in a script.
- A declared owner change passes the assertion with no script edit.
- A mismatched artifact still fails closed.
- Documentation states current state and adds no unrequested constraint.

## Verified On

| Project | Context | Details |
| --------- | --------- | ------- |
| Model-serving pipeline | Container image build and gate scripts | Literals replaced with recipe arguments; syntax and argument-passing forms exercised directly. See [notes](./derive-pin-from-source-of-truth-not-hardcoded-literal.notes.md). |

## References

- [Dependency manifest single source of truth](dependency-manifest-single-source-of-truth.md)
- [Stale version comment: version-agnostic fix](audit-stale-version-comment-version-agnostic-fix.md)
- [Container runtime dependency linkage audit](container-runtime-dependency-linkage-audit.md)