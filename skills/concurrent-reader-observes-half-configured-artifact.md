---
name: concurrent-reader-observes-half-configured-artifact
description: "Repair an intermittent startup or acquisition failure where a reader refuses an artifact that its own process created. Use when a create publishes a service file at its final name with an exclusive open and then applies owner, mode, or content, when a validator compares a locked descriptor to the visible path and rejects a mismatch, and when the failure needs a loaded host to reproduce."
category: debugging
date: 2026-11-02
version: "1.0.0"
user-invocable: false
verification: verified-local
tags:
  - race-condition
  - atomic-publish
  - create-then-configure
  - identity-validation
---

# A Reader That Observes a Half-Configured Artifact Refuses Its Own Creator

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-02 |
| **Objective** | Find why a concurrent-start test fails intermittently with an identity refusal, and decide whether the defect is in the test, the validation, or the publication order. |
| **Outcome** | A create sequence opened the artifact at its final name with an exclusive create, then applied owner and mode. A rival that opened the same name in that window validated a descriptor against the visible path and rejected the mismatch. The defect was the publication order, not the test and not the validator. The fix creates under a temporary name with the final attributes and publishes with an atomic no-replace rename. |

A validator that compares a descriptor to its visible path is correct. It asserts that the name still refers to the inode that this process locked. That comparison must fail when the name is replaced. The defect starts when a publisher makes an incomplete artifact visible at its final name, because every competing reader then has a real reason to refuse it.

State the difference up front: the validator is right, and the publisher is wrong. Do not relax the comparison to make the test pass. Relaxing it removes the replacement detection that it exists to provide.

## When to Use

- A concurrency test fails intermittently with a permission, ownership, or identity refusal.
- The refusal names an artifact that the same process group created moments earlier.
- A create opens the final name with an exclusive create, then applies owner, mode, or content.
- A validator compares `fstat` of a locked descriptor with `stat` of the visible path.
- The validator is reached from more than one entry point.
- The failure does not reproduce on a development host, but does appear on a loaded runner.

Do not use this for a refusal that is correct. A path replaced by a foreign actor, or one that existed with the wrong owner before the operation, must still be refused.

## Verified Workflow

### Quick Reference

```python
# Before: the artifact is visible at its final name while it is still unconfigured.
fd = os.open(NAME, O_RDWR | O_CREAT | O_EXCL | O_CLOEXEC, 0o600, dir_fd=parent_fd)
os.fchown(fd, uid, gid)      # a rival can open and validate the file in this window
os.fchmod(fd, 0o600)
os.fsync(fd)
```

```python
# After: configure under a temporary name, then publish with an atomic no-replace rename.
fd = os.open(TEMP, O_RDWR | O_CREAT | O_EXCL | O_CLOEXEC, 0o600, dir_fd=parent_fd)
os.fchown(fd, uid, gid)
os.fchmod(fd, 0o600)
os.fsync(fd)
rename_noreplace(parent_fd, TEMP, NAME)   # a reader sees absent, or complete, never partial
os.fsync(parent_fd)
```

### Suggested Approach

1. Read the full traceback, not the test summary. Find the exact frame that raised, and read the argument values printed with it. A parameter that reads `expected_state = None` or an equivalent "nothing was expected" value identifies which branch of the caller produced the mistake.
2. Compare the raising frame with the frame you expected. A shared helper can be called from several entry points. The defect often lives in the entry point that the discussion did not mention, and a fix applied to the other entry point does not remove it.
3. Classify the refusal before you change anything. If the visible artifact has the intended owner and mode and was created in the same operation, the refusal is a visibility-window defect. If it is foreign-owned or was replaced later, keep the refusal.
4. Do not weaken the identity comparison. It exists to detect replacement. Removing `st_ctime_ns`, `st_ino`, or `st_mtime_ns` from the tuple trades a rare false refusal for silent acceptance of a substituted file.
5. Fix the publish order at every creator. Move owner, mode, and content application under a temporary name, then publish with an atomic no-replace rename. A no-replace rename keeps the "create wins once" guarantee that the exclusive open provided.
6. Apply the same helper to each creator. When two modules both create the anchor file, the second module keeps the defect until it uses the same helper. Enumerate every caller that creates the name, not only the one that raised.
7. Prove it deterministically. A scheduler interleave is not a test. Either pause the creator between configure steps with a synchronization point and assert that a rival is refused, or assert the published entry is never visible in a partial state. Then run the original concurrency test many times.
8. Report the reproduction limit honestly. If the interleave does not reproduce locally, say so, and cite the traceback as the evidence.

### Deciding between "fix the test" and "fix the product"

Ask which side is wrong in principle:

| Observation | Classification | Action |
| ------- | ------- | ------- |
| The refusal names an artifact created by the same operation, with the intended owner and mode | Product defect | Reorder publication |
| The refusal names a foreign-owned or later-replaced artifact | Correct refusal | Leave the check; fix the caller |
| The test asserts a wall-clock teardown bound | Test defect | Remove the bound; keep the contract assertions |
| The failure needs a loaded host and the traceback shows the internal refusal | Product defect that presents as a flake | Fix the product; do not rerun to green |

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| ------- | ---------- | --------------- | ---------------- |
| 1 | Reproduce the interleaving on a development host with a high-iteration multi-threaded loop | 400 iterations produced no failure; the window needs a loaded runner | A rare race that does not reproduce locally is not evidence that it is not real. Use the traceback to locate the frame |
| 2 | Widen the window by adding a sleep in the creator's `fchmod` | The rival also passed, because it opened the directory itself and the injected delay did not sit between publish and validation | Speed up or delay the right step. Confirm that the injected delay is inside the window you claim |
| 3 | Blame the test as a flake and rerun the shard | Later heads passed for unrelated reasons, and the same refusal is a reachable product path | A green rerun does not classify the cause. Read the internal refusal message |
| 4 | Assume the shared helper's main entry point was the failing caller | The traceback showed a different entry point with its own create-then-configure sequence, which a fix to the other entry point would not touch | Map every creator of the artifact before you approve a fix |

## Results & Parameters

- Symptom signature: a permission or identity refusal, raised while one process creates an artifact that several processes register at the same time.
- Root-cause signature: exclusive create at the final name, followed by owner, mode, or content application.
- Fix shape: temporary name, final attributes applied, atomic no-replace rename, then directory `fsync`.
- Keep: the descriptor-to-visible-path comparison, unchanged.
- Verification: verified-local. The classification is from a CI traceback. The interleave did not reproduce on the development host across 400 high-iteration runs.

## Verified On

| Project | Context | Details |
| ------- | ------- | ------- |
| Internal service repository | A concurrent-start test for a shared administrative-root publication anchor | The traceback named an entry point that a parallel fix did not cover. See [notes](concurrent-reader-observes-half-configured-artifact.notes.md) |

## References

- [Lockless snapshot makes concurrent first creates refuse each other](lockless-snapshot-create-race-refuses-own-writer.md) — the check-then-act variant, where the fix re-validates after the create
- [Post-merge CI failure attribution](post-merge-ci-failure-attribution.md) — decide whether a red check belongs to your change before you repair it
- [ASD-STE100](../docs/asd-ste100.md)