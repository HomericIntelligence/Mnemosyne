---
name: fatal-check-downgrade-real-load-root
license: BSD-3-Clause
description: "Downgrade a fatal consistency check to a logged warning on the load path where its model is actually constructed. Use when a change converts blocking validation to informational drift, moves a model validator into a post-load pass, or lists validators that no production loader reaches."
category: architecture
date: 2026-11-01
version: "1.0.0"
user-invocable: false
verification: verified-local
tags:
  - fatal-to-warning
  - validation-downgrade
  - pydantic-model-validator
  - load-path
  - post-load-pass
  - unreachable-validator
  - silent-check-removal
  - plan-review
  - config-consistency
  - drift-note
---

# Downgrade a Fatal Check on Its Real Load Root

## Overview

| Field | Value |
| ----------- | ------- |
| **Date** | 2026-11-01 |
| **Objective** | Convert a blocking consistency check into a logged warning and continue, without an accidental removal of the check. |
| **Outcome** | Operational. A review discipline: a load-root map for each check, a recorded disposition for unreachable checks, and a test on the real load path. The implementation was not executed in this session. |
| **Verification** | verified-local: each premise was proven against the source tree with a read-only check. The lesson is a review result, not a runtime result. |

## When to Use

- A plan converts blocking validation to informational events (a drift log, a warning line, a metric) and continues.
- A plan moves one or more `pydantic` `model_validator` checks into a function that runs after `model_validate`.
- A plan lists the validators of a config module as one group, and the module has more than one loader.
- You review or implement a change that must keep some checks fatal and relax the rest.

## Verified Workflow

### Quick Reference

For each check that you intend to convert, prove three facts first:

```bash
# 1. Which loader constructs the model?
grep -rn "Model.model_validate\|def load_" <package>/config.py

# 2. Which models does each loader root embed?
grep -n "class <LoaderRoot>" -A80 <package>/config.py | grep -E "^\s+[a-z_]+: "
grep -n "class <NestedModel>" -A40 <package>/config.py | grep -E "^\s*[a-z_]+: [A-Z]"

# 3. Is every listed model reachable from a production loader?
grep -rn "<ModelName>" --include="*.py" . | grep -v "/config.py:"
```

Assign one of these dispositions to each check:

| Evidence | Disposition |
| -------- | ----------- |
| Model embedded by a loader root | Move the check into that root's post-load pass. |
| Model reachable only through another model that a second loader constructs | Move the check into that second loader's pass. |
| Model has no production construction path | Keep the validator fatal and record why. |
| Model is constructed only in tests | Keep the validator fatal and record why. |

### Suggested Approach

1. Draw the load-root map. For every validator that you convert, name the loader function, the root model that embeds the field, and the exact line that calls `model_validate`.
2. Walk the embedding chain to the root. A nested model does not inherit the loader of a different root. A field that a loader root does not embed never reaches that loader.
3. Split the conversion by load root, not by file. Create one check tuple for each loader and run one pass after each `model_validate` call.
4. Keep the check output identical in both loader branches. When a log directory is available, write the structured event. When it is absent, write one warning line with the same fields to standard error. Do not give a caller a silent branch.
5. Give every unconvertible check a recorded disposition. "No production load path" means the check stays fatal. Do not convert it and do not move it: both actions change behavior.
6. Split a validator that mixes check classes. Keep the format, range, and permission sub-checks in the validator. Move only the cross-field consistency sub-checks.
7. Test on the real path. Each converted check needs one test that calls the same loader that production calls, with an input that breaks the check. The test asserts that the load succeeds and that one event names the compared fields. A test that constructs the model directly proves nothing about the loader.
8. When a plan review finds one pass point for checks from two load roots, treat it as a removal defect. The checks become an accidental removal: no stop and no event.

### Failure modes to prevent

- **Accidental removal.** The validator is deleted and its pass never runs for that model. The operation stops failing and writes no event. This is worse than the original fatal check.
- **Group conversion.** A plan says "convert the config validators" and lists them from one file. The plan does not make the split, and the implementer must rediscover the load roots.
- **Dead conversion.** A validator runs on a model with no production construction path. A converted version of it can never fire. The conversion adds code and no behavior.
- **Test at the wrong level.** A test builds the model with the constructor and passes. Production uses the loader and does not run the pass.

### Parameters

- Event `where` field: name the loader and the check, for example `config.load_cluster_profile:<check>`. A reader must know which path wrote the event.
- Resolution text: state the operator action, for example republish the record or rerun the stage command.
- Log-directory seam: add one optional `log_dir=None` parameter to each loader. Do not force each call site to supply a directory in the same change.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| One post-load pass for all config checks | Wire one pass into the profile loader and move every consistency validator into it | The profile root embedded only part of the models. The other checks were on models that only a cookbook loader constructs. Implemented as written, those checks would stop failing and would write no event | Map every check to the loader that constructs its model before you choose the pass point |
| Convert a validator with no caller | Move the validators of a config group into the pass because the plan listed them | The group models had no production construction path; only tests built them | An unreachable check stays fatal; record the reason and the owner of the reachable replacement |
| Test the model instead of the loader | Assert the new pass with a direct model construction | The constructor skips the loader, so the test cannot prove that the pass runs in production | Assert the converted check through the loader that production calls |

## Results & Parameters

### Configuration

```yaml
conversion:
  granularity: one check tuple for each loader root
  output_when_no_log_dir: one warning line on standard error with the same fields
  unreachable_check: keep fatal
  mixed_validator: move only cross-field consistency sub-checks
tests:
  call_path: the same loader that production calls
  case_count: one failing input for each converted check
```

### Expected Output

- Each converted check writes one event that names the loader, the compared field, the expected value, and the observed value.
- The load returns a valid model and the caller continues.
- Each unreachable check still raises, and the plan records why.
- A review of the plan finds no single pass point that serves two load roots.

## Verified On

| Project | Context | Details |
| --------- | --------- | ------- |
| Large Python service repository | Read-only plan review of a config-validation downgrade; two loaders and about ten converted checks | The first plan used one pass point and would have removed the cookbook-rooted checks. The revision split the pass by load root and kept the unreachable group fatal. See [notes.md](fatal-check-downgrade-real-load-root.notes.md). |

## References

- [Planning: verify premises before acting](planning-verify-issue-premise-before-implementing.md) — the general premise-check discipline that this entry applies to validation downgrades.
- [Config validation and schema alignment](config-validation-and-schema-alignment.md) — validator and loader patterns that this entry complements.
- [Changed-path gate: deletion must stay classified](changed-path-gate-deletion-classification.md) — the same failure class for gate data.
