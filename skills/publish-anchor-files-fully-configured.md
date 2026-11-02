---
name: publish-anchor-files-fully-configured
license: BSD-3-Clause
description: "Publish an anchor, lock, or marker file under a temporary name and rename it into place, so a concurrent reader never observes a half-configured entry. Use when a file is created with O_CREAT|O_EXCL at its final name and then given its owner, mode, or content, and a second process can stat or open that name in the same window, especially when the failure appears as a rare intermittent permission or changed-during-acquisition error in CI."
category: debugging
date: 2026-11-02
version: "1.0.0"
user-invocable: false
verification: verified-local
tags:
  - race-condition
  - atomic-publish
  - create-then-configure
  - renameat2
  - rename-noreplace
  - fchmod
  - fchown
  - st-ctime
  - fail-closed
  - flaky-test
  - permission-error
  - startup
  - lockfile
---

# Publish Anchor Files Fully Configured

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-02 |
| **Objective** | Remove an intermittent concurrent-startup refusal that a single-process test cannot reproduce on every host. |
| **Outcome** | A startup anchor was created at its final name with `O_CREAT|O_EXCL`, and its owner, mode, and synced content were applied after that name was already visible. A second starter opened the anchor in that window and compared `fstat` on the descriptor with `stat` on the path. A write that landed between the two calls changed the compared tuple, so the loser rejected a correct anchor and failed startup. Creating the anchor under a temporary name and publishing it with a no-replace rename removed the visible half-configured state. |

## When to Use

- A process creates a lock, anchor, or marker file with `O_CREAT|O_EXCL` at its final name, then calls `fchown`, `fchmod`, `write`, or `fsync`.
- A second process can `stat`, `open`, or compare that same name while the first process is still configuring it.
- A concurrency test fails intermittently with a permission, ownership, or changed-during-acquisition refusal that names a file the code itself just created.
- The failure appears in CI but not locally, and the local host reports identical metadata for both reads.

Do not use this entry when only one process can ever create the file, or when the file is written in place by design and readers already tolerate partial content. Do not use it for a *stale snapshot* refusal, where the reader's own earlier observation is out of date; that intent has its own entry.

## Verified Workflow

### Quick Reference

```text
A file that another process may inspect MUST become visible
in its final configuration. Never create it at the final name
and configure it afterwards.

  WRONG: open(final, O_CREAT|O_EXCL) -> fchown -> fchmod -> fsync
  RIGHT: open(temp,  O_CREAT|O_EXCL) -> fchown -> fchmod -> fsync
         -> rename_noreplace(temp, final) -> fsync(dir)
```

### Suggested Approach

1. **Read the failing frame before the failing message.** An intermittent refusal names one function, but the message often fits several code paths. Walk the traceback from the test entry point to the raise, and confirm which create path the test actually calls. A plausible neighbouring function that the test never invokes proves nothing. In this session the first repair patched a publication function that the failing test called zero times, and an independent review rejected it.
2. **Classify the window.** For each create site, list the syscalls between the moment the name becomes visible and the moment the file reaches its final state. If any reader can observe the file inside that list, the site has the defect. `fchown`, `fchmod`, `write`, and truncation all count as configuration.
3. **Build under a temporary name, publish once.** Create the temporary in the same directory, apply the owner, mode, and content, `fsync` the descriptor, then publish with a no-replace rename. A reader then sees either no entry or the complete entry. Keep the descriptor open across the rename; it still refers to the published inode.
4. **Use the no-replace rename, not a link-then-unlink publish.** A hard-link publish shows a transient second link, which a reader that checks `st_nlink` will reject. A no-replace rename keeps one link throughout.
5. **Translate the lost race into the caller's own contract.** When two starters publish at once, the loser gets `EEXIST` from the rename. Map it to the error type each caller already handles, so the loser falls back to opening the published entry instead of surfacing a raw `OSError`. Keep one helper and pass the owner and group explicitly, because call sites can differ.
6. **Do not relax the reader's comparison to hide the window.** Dropping fields from the compared tuple makes the symptom rarer while leaving a reader able to accept a partially written file. Correct the publisher; keep the reader strict.
7. **Prove the invariant with a test that fails on the old code.** Inject a failure during configuration and assert that no entry exists at the final name. That test fails on the create-at-final-name version and passes after the change. A test that tries to reproduce the interleaving is usually not practical; state that limitation and rely on the invariant test plus the CI traceback.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Repair a neighbouring create path | Fixed the publication and reconciliation create functions, which had the same shape, and added them to the same pull request. | An independent review instrumented the failing test and showed it calls the startup create path 0 times. The reported failure stayed possible. | Walk the traceback to the function that actually raised. A shared defect shape does not prove the reported site. |
| Reproduce by parallel repetition | Ran the single failing test hundreds of times in parallel on the development host, with a probe that logged which fields differed. | Zero failures in 144 runs and an empty probe log, because the host does not update the compared timestamp on the permission change. | A local zero-failure rate is not evidence of absence when the host's metadata behaviour differs. Treat the CI traceback as evidence and reason from the code ordering. |
| Trust "flaky, re-run it" | Re-ran the failed CI job. | The job re-ran the lint gate only; the failing shard kept its original timestamps, and the second run failed again. | Confirm that the re-run actually re-executed the failing job before you attribute a second failure to the same flake. |
| Read the empty trimmed log | Used the failed-log view on a job whose log was empty. | The trimmed view returned nothing, so the real `FAILED ...` line was invisible. | Read the full job log and filter for the error marker and `FAILED` when the failed-log view is empty. |

## Results & Parameters

### Configuration

```yaml
create_then_configure_defect:
  detect:
    - create_at_final_name: "open(final, O_CREAT|O_EXCL)"
    - configured_after_visible:
        - fchown
        - fchmod
        - write
        - fsync
  repair:
    temp_name: same_dir_unique_token
    apply_before_publish:
      - fchown
      - fchmod
      - write
      - fsync_descriptor
    publish: rename_noreplace
    after_publish: fsync_directory
  reader_contract:
    keep: strict_descriptor_vs_path_compare
    do_not: drop_compared_fields
  regression_test:
    inject: failure_during_configuration
    assert: final_name_absent
```

### Expected Output

- A concurrent starter observes either no anchor or a fully configured anchor, never a partial one.
- The loser of the create race takes its normal fallback path and does not surface a raw `OSError`.
- The new invariant test fails on the create-at-final-name version with an assertion on the final name, and passes after the change.
- No temporary file and no descriptor remain open after a failed configuration.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Private shared-cluster control plane (identifiers withheld) | Concurrent startup of a control-plane component that must converge on one published anchor; failure appeared as a rare CI-only permission refusal | Ordering analysis, review evidence, cross-host reproduction limits, and measurements are in [notes.md](publish-anchor-files-fully-configured.notes.md). |

## References

- Related, different intent: `lockless-snapshot-create-race-refuses-own-writer` covers a reader whose *own earlier snapshot* is stale and refuses a path that a peer created later. The repair there is to narrow the snapshot's authority. Here the reader's observation is current; the publisher exposes an incomplete file.
- Related, different intent: `directory-identity-check-stable-stat-fields` covers which metadata fields a same-object check should compare. That entry keeps the reader strict; this entry removes the writer's exposure.
- `renameat2` with the no-replace flag, and POSIX `stat(2)` and `fchmod(2)` field-update rules.