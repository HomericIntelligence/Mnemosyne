---
name: retired-config-key-silent-drop-resurrection
description: "Prevent a new configuration file from reviving a retired configuration key that the loader silently drops. Use when a config model tolerates and discards retired keys for compatibility, when new files are copied from an older sibling, or when a field reads as an active gate but no code enforces it."
category: testing
date: 2026-10-31
version: "1.0.0"
user-invocable: false
tags:
  - retired-config-key
  - silent-drop-validator
  - dead-config
  - copy-forward-regression
  - claim-without-enforcement
  - resurrection-guard
  - config-model-strictness
---

# Retired Config Keys: Silent Drop and New-File Resurrection

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-31 |
| **Objective** | Stop new configuration files from carrying a retired key that the loader accepts and discards, so the file never claims a guarantee that nothing enforces. |
| **Outcome** | Successful — the dead keys were removed, the model stayed unchanged, and a test now fails when a new file reintroduces one. |

When a configuration feature is removed, a loader often keeps accepting its old
keys. A pre-validation step strips them so that old files and old artifacts
still load. The model itself is strict for unknown keys, but these named keys
pass through the strip step and vanish.

That tolerance is correct for files that predate the removal. It is a defect in
a file written after the removal. The new file states the retired setting, a
reader trusts it as an active guarantee, and no code enforces it. The file looks
gated while it is not.

## When to Use

- A configuration model has a pre-validation strip step for retired keys, and
  strict handling for every other unknown key.
- You add configuration files by copying or adapting a sibling that predates a
  feature removal.
- A review or test says a field "does not exist" on the model although the file
  clearly sets it.
- A recipe, profile, or manifest claims a safety property through a setting
  name instead of through a check that runs.

Do not use this entry for a lever that still has a runtime branch. That case
needs an inertness guard with a non-vacuity control, which is a different
deliverable.

## Verified Workflow

### Quick Reference

```bash
# 1. Find the strip step and the retired-key set it uses.
rg -n 'retired|mode="before"' src/            # the strip validator
rg -n 'RETIRED|_RETIRED_' src/                # the key set

# 2. Which files still name a retired key? New files are the defect.
rg -l '<retired_key>' config/                 # then check each file's age

# 3. Prove the loader discards it instead of rejecting it.
python3 -c 'from pkg.config import load_file; m = load_file("config/new.yaml"); print(hasattr(m, "<retired_key>"))'
```

### Suggested Approach

1. **Decide by file age, not by key presence.** Retained legacy files are why
   the strip step exists; leave them. A file added after the removal must not
   name a retired key. Compare the files that carry the key against the change
   that removed the feature. If only the new files carry it, the fix is local to
   the new files.
2. **Read the strip step before you edit.** Confirm three things: the loader
   drops the key instead of raising, the model rejects genuinely unknown keys,
   and the retired value has no effect on any derived behavior. When the drop is
   silent, removing the key from the new file changes no runtime behavior. The
   edit is therefore safe and needs no migration.
3. **Remove the claim, keep the intent.** A retired key usually encoded a
   property the author wanted, such as "not yet qualified for production." When
   you delete the key, keep the property through something that is enforced, for
   example an explicit enabled/disabled state, a capacity or replica floor, or a
   separate admission record. Do not delete the claim and stop there.
4. **Guard the whole class, not one key.** Assert on the retired key set that
   the loader itself exports, so a newly retired key joins the guard without a
   second edit. Load the set from code, never restate it in the test.

```python
from pkg.config import RETIRED_KEYS, load_file

def test_new_profiles_carry_no_retired_key():
    for path in sorted(NEW_PROFILES.glob("*.yaml")):
        raw = yaml.safe_load(path.read_text())
        assert not RETIRED_KEYS & set(raw), path.name
```

5. **Expect the type checker to find it first.** Because the attribute is gone
   from the model, a type checker rejects `model.<retired_key>` in a test or a
   helper before CI reaches the assertion. Treat that error as the same defect,
   not as a separate typing problem. The repair is to assert on the raw document,
   as above.
6. **State the retirement, not the setting.** When the new file carries a
   comment about the property, describe the enforcing mechanism. A comment that
   names the removed setting keeps the claim alive after the key is gone.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Copy the sibling file and keep its gate line | New files were adapted from an older sibling and kept the gate setting, which read as a deliberate "not yet approved" marker | The loader dropped the key silently, so every new file was ungated while every reader believed otherwise; no other file in the tree carried it, which made the copy-forward origin visible | A key that the loader tolerates is not a key that still works; check whether the removal predates the file |
| Assert on the model attribute in the new test | The new guard read the property through the model object | The attribute no longer exists, so the test raised an attribute error instead of a meaningful failure, and the type checker failed the same line in the lint gate | Assert on the raw document against the loader's own retired-key set; never read a retired key through the model |
| Treat the type error as its own defect | Planned a separate typing fix for the failing attribute access | The error was the same resurrection defect seen from a different gate, so a separate fix would have left the dead key in the files | Attribute each failure to the earliest cause; one repair covers several gates |
| Delete the claim with the key | Removed the retired line from the new files and stopped | The property the author wanted was then recorded nowhere | Re-express the property through a mechanism that is enforced |

## Results & Parameters

### Configuration

```yaml
# Retired: the loader drops this key, so it gates nothing.
retired_gate: required

# Kept: these are enforced.
enabled: false
min_replicas: 0
max_replicas: 1
```

### Expected Output

- No file added after the removal names a retired key.
- The loader and the model are unchanged; legacy files still load.
- The guard fails on a reintroduced key and passes on the retained legacy
  files that the strip step exists to serve.
- The property that the retired key described is enforced by an explicit
  mechanism.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| A Python serving-configuration monorepo | Thirteen new config files copied a gate key from an older sibling; the loader had dropped that key since an earlier change; the guard and the lint gate both failed on the dead attribute, and the corrected head merged | Counts and command results in [notes](retired-config-key-silent-drop-resurrection.notes.md) |

## References

- [testing-retired-lever-inertness-guard](testing-retired-lever-inertness-guard.md) — the opposite case: a lever that still has a runtime branch needs an inertness guard
- [descriptor-digest-readmission-additive-fields](descriptor-digest-readmission-additive-fields.md) — adjudicating a rotation when a config model gains fields instead of losing them