---
name: derive-pin-from-source-of-truth-not-hardcoded-literal
description: "Derive a version, digest, image lineage, or other pin from its canonical source instead of comparing against a literal, treat descriptive documentation as current state rather than a rule to enforce, and keep a sealed-artifact gate strict. Use when: (1) a build, gate, or probe script asserts a specific version, digest, lineage value, or path set, (2) the asserted value also exists in a manifest, recipe, lockfile, or environment file, (3) documentation states the toolchain or lineage currently in use, (4) an existing check compares a materialized copy of a manifest instead of the manifest itself, (5) a hardcoded value sits inside a quoted heredoc where the surrounding variable cannot reach it, (6) a published artifact is refused by a gate that scans for bytes the artifact should never carry, (7) a protected-location literal is removed by guessing at its consumers instead of using a field search, or (8) an enforced policy value such as a group name, account name, or path is still a module constant after the profile that declares it gains the field, so you must decide which checks read the declaration and which keep the literal."
category: ci-cd
date: 2026-11-07
version: "1.2.0"
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
  - permitted-literal
  - byte-scan-gate
  - sealed-artifact
  - redaction-projection
  - protected-root-removal
  - policy-value-declaration
  - trust-isolation-exclusion
  - stored-record-vocabulary
  - fail-closed-refusal
  - residual-constant-deletion
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

The same rule covers an enforced policy value, such as a group name, an
account name, or a path. A value that the active profile declares is a pin.
Each check resolves it from the profile. Three classes of site keep the
literal. Trust-isolated modules must not load project configuration.
Stored-record vocabulary is a closed contract. Detectors and fixed rules are
the requirement itself.

Two failure modes follow from this. The first is a literal that cannot see
the owner. The second is a rule invented from descriptive prose.

Two limits bound the rule. Not every literal is a copy, and the detector for
a copy is not the owner. Classify each literal before you remove it, and never
loosen the detector to remove a literal.

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
- A publication gate refuses a built artifact because a file carries a
  protected value, such as an administrative root path.
- You must remove a literal that names a protected location and other code
  depends on it.
- An enforced policy value, such as a group or account name, is still a module
  constant after the profile that declares it gains the field. You must
  decide which checks read the declaration and which keep the literal.

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

A sealed-artifact gate keeps its scan. Remove the bytes from the artifact
instead, then make the manifest and the tree describe the same tree.

```bash
# The gate scans every installed file. Do not add an exception.
# Remove the payload by a fixed path rule during projection.
project --exclude-prefix <control-only-prefix>/ <source> <public>
```

### Classify the literal first

| Kind | Example | Decision |
| ---- | ------- | -------- |
| Copy of an owner | A version inside a quoted heredoc that the recipe also declares | Replace. Pass the owner's value. |
| Detector | The byte sequence a seal or privacy gate searches for | Keep. It is the requirement. |
| Fixed policy | A path prefix the projection always omits | Keep. A content test makes the result depend on current values. |
| Redaction output | A protected value split into parts to stop it matching a scan | Do not do this. Remove the need for the value instead. |
| Policy declaration copy | A group or account name in a runtime check, when the active profile declares the same name | Replace. Resolve the name from the active profile. Fail closed when the declaration is absent. |
| Trust-isolation literal | A name inside a module that checks bootstrap files and must not load project configuration | Keep. An import of the configuration loader defeats the isolation. |
| Stored-record vocabulary | A closed enum, a seed table mirrored by a database migration, or a receipt schema literal | Keep. A declared change needs a migration or a schema change, not a runtime read. |

### Decide each check site

1. Find the declaration. Read the profile schema and each profile file, and
   record the field name that the requirement text uses.
2. Classify each check site with the table above. Report the class of each
   site, and report each exclusion with its reason.
3. For a policy declaration copy, resolve the declared value at the check.
   Use an existing resolver before you add a new one.
4. Fail closed. When the declaration cannot be resolved, the check refuses
   the action. A refusal names the profile key, the expected value, and the
   observed value.
5. Keep the constant as a schema default or a function-parameter default only
   for paths that have no active profile.
6. Delete a constant that no check reads after the rewiring. Do not keep it as
   a second copy of the declared value.

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
7. Separate the detector from the artifact. When a seal refuses a published
   artifact, keep the seal and remove the bytes. Use a fixed path rule in the
   projection step. Do not scan the artifact for the protected value and
   exclude the matches. That content test makes the published tree depend on
   the current data, and the data changes on each release.
8. Keep the manifest, the tree, and the gate on one population. Delete the
   rows of an excluded member from the inventory in the same step. When you
   drop a member, also drop its directory entry. Keep the source checks that
   run before the exclusion, so a malformed excluded entry still fails
   closed.
9. Refuse the redaction shortcut. Do not assemble a protected value from
   parts, and do not rewrite it in place, to satisfy a byte scan. The value
   still exists at run time, and the bytes stay in bytecode that the build
   copies. Remove the value from shipped input, or move the supporting data
   out of the published artifact.
10. Remove a protected-location literal by field use, never by guess. Find
    every consumer first:

    ```bash
    grep -rn "PROTECTED_LITERAL_NAME" src scripts tests docs
    ```

    Then move the consumers to a declared field, such as a profile value, and
    fail closed when no declaration exists. A guessed replacement can drop a
    protection that the guess does not model.
11. Check each remaining literal with a targeted search before you finish:

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
| Assembled a protected value from parts to pass a byte scan | Wrote the value as separate path segments, then called the parts to get the same run-time value | The value still existed at run time, the source no longer described the location, and the build copied the bytes into bytecode | Remove the value from shipped input; do not redact it |
| Pruned the published tree by scanning it for the protected bytes | Deleted every payload file that contained the value before publication | The published tree then depended on the current data, and the result changed on each release | Apply one fixed path rule in the projection and keep the data out of the published artifact |
| Removed a protected-location constant after a partial consumer search | Deleted the constant and rewired only the first consumer found | A later consumer used the value differently, so a guessed replacement could have dropped a protection | List every consumer first, move each one to a declared field, and fail closed when the declaration is absent |
| Rewired a policy name in a trust-isolated module | Made the bootstrap directory check import the profile resolver to remove one more literal | The check exists to run without project configuration, so the import coupled the trust stage to the data it verifies | Classify each site first; a trust-isolation literal stays, and the exclusion is recorded |

## Results & Parameters

### Configuration

| Parameter | Value | Note |
| --------- | ------- | ------ |
| Owner file | the manifest, recipe, or lockfile that declares the pin | The only authority for the value |
| Assertion form | `cmd - "$OWNER_VAR" <<'EOF'` with `sys.argv[1]` | The form that works inside a quoted heredoc |
| Digest source | `sha256sum "$owner_file"` | Not the digest of a generated copy |
| Seal scan | the protected bytes, scanned in every installed file | Keep it; it is the requirement |
| Projection rule | a fixed path prefix that the projection omits | Not a content test of the current data |
| Inventory update | drop the rows and directory entries of excluded members | The manifest and the gate scan the same population |
| Policy value source | the profile field the requirement names | The check refuses when the declaration is absent |
| Constant after rewiring | delete it when no check reads it; keep a default only for paths with no active profile | A second copy of the declared value drifts |
| Exclusion classes | trust isolation, stored-record vocabulary, detector or fixed rule | Each exclusion is recorded with its reason |

### Expected Output

- One owner for each pin, with no second copy in a script.
- A declared owner change passes the assertion with no script edit.
- A mismatched artifact still fails closed.
- Documentation states current state and adds no unrequested constraint.
- A published artifact carries no protected bytes, and its inventory
  describes the same tree that the gate scans.
- The seal or privacy gate keeps its original strictness.

## Verified On

| Project | Context | Details |
| --------- | --------- | ------- |
| Model-serving pipeline | Container image build and gate scripts | Literals replaced with recipe arguments; syntax and argument-passing forms exercised directly. See [notes](./derive-pin-from-source-of-truth-not-hardcoded-literal.notes.md). |
| Python packaging release lane | Public wheel refused by its own self-containment gate | Fixed path-prefix exclusion in the projection with matching inventory rows, and the protected-location literal removed by a field search. The plan review confirmed the approach; focused tests and static checks passed locally. See [notes](./derive-pin-from-source-of-truth-not-hardcoded-literal.notes.md#evidence-public-artifact-refused-by-its-own-seal). |
| Python control-plane service cluster | Plan to move a required administrator group and service account from module constants into the cluster profile | Plan only. The check-site survey classified each site: policy declaration copies, trust-isolation literals, stored-record vocabulary, and test-only defaults. No source change and no test run confirmed the plan. See [notes](./derive-pin-from-source-of-truth-not-hardcoded-literal.notes.md#evidence-policy-values-moved-from-constants-to-a-profile). |

## References

- [Dependency manifest single source of truth](dependency-manifest-single-source-of-truth.md)
- [Stale version comment: version-agnostic fix](audit-stale-version-comment-version-agnostic-fix.md)
- [Container runtime dependency linkage audit](container-runtime-dependency-linkage-audit.md)