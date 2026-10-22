---
name: comet-user-credential-lifecycle-diagnosis
license: BSD-3-Clause
description: "Diagnose Comet ordinary-user credential lifecycle failures end to end with read-only checks. Use when: (1) `comet request-key` hangs or ends with `Credential request state: pending.`, (2) a saved credential gets HTTP 401 after the propagation window, (3) `request-key` ends with `PermissionError: credential lifecycle intent does not match saved credential`, (4) unauthenticated reads work for an account but every authenticated call fails, (5) an operator asks which subsystem owns a user-reported key problem."
category: debugging
date: 2026-10-22
version: "1.0.0"
user-invocable: false
verification: verified-local
tags: [comet, credentials, request-key, api-key, rendezvous, gateway, "401", hang-diagnosis, proc-sampling, privacy-masking]
---

# Comet User Credential Lifecycle Diagnosis

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-10-22 |
| **Objective** | Classify which link of the Comet ordinary-user credential lifecycle failed, with read-only evidence, and route the evidence to the owning issue. |
| **Outcome** | Operational. Four links, four failure signatures, and one decision table classified two live account failures in one session. |

The ordinary-user credential lifecycle has four links. Each link has one durable
failure signature. Classify the broken link before you retry anything. Retries
reuse the input state, so a dead-end branch fails the same way every time.

| # | Link | Actor | Healthy terminal sign |
|---|------|-------|-----------------------|
| 1 | Prepare + publish | user client | CLI accepts or republishes the request and starts the watch |
| 2 | Fulfillment | credential service | request state becomes `registered` / delivered in the wait window |
| 3 | Admission | gateway key cache | `comet whoami` returns 200 within ~60 s of the save |
| 4 | Save + use | user client | stored credential authenticates API calls |

## When to Use

Use this skill when one of these conditions applies:

- `comet request-key` does not return, or returns `Credential request state:
  pending.` with exit code 0.
- `comet whoami` returns HTTP 401 and the saved credential is older than the
  propagation window (~60 s).
- `request-key` ends quickly with a traceback, for example `PermissionError:
  credential lifecycle intent does not match saved credential`.
- An account can run unauthenticated reads (`comet status`, `comet endpoint`)
  but no authenticated call succeeds.
- You must decide whether a reported hang is client polling, a blocked external
  resource, or a shared-filesystem mount stall.

Do not use this skill for operator-side key administration defects
(`comet-admin keys ...`) or for offline CLI review without cluster access; see
[comet-cli-offline-review-evidence-reporting](comet-cli-offline-review-evidence-reporting.md)
for the offline case.

## Verified Workflow

### Quick Reference

Match the observed signature to the broken link, then check the named evidence:

| Signature | Broken link | First check |
|-----------|-------------|-------------|
| Fast exit 1, traceback at prepare time (for example `PermissionError: credential lifecycle intent does not match saved credential`) | Link 1, prepare + publish | The traceback frame; the saved-credential state (`whoami` can still pass with a different saved key) |
| Exit 0 with `Credential request state: pending.` after stacked waits | Link 2, fulfillment | Rendezvous `results`/`deliveries` parent mtimes; fulfillment dependency (database DSN) in the service launch environment |
| Persistent HTTP 401 on `whoami` beyond the propagation window while older keys authenticate | Link 3, admission | Credential file mtime vs window; operator-side key-cache/key-sync state |
| Mount-stall-looking hang (no output, long elapsed) | None of the above yet | Time `stat` on the rendezvous dirs and the client shim; ~0 s excludes a mount stall |

### Suggested Approach

Run these steps in order. Each step is read-only and supplies the input for the
next decision.

1. Confirm the public read surface from the same host: `comet status` and
   `comet endpoint`. If these fail, the cause is client, network, or context
   selection, not the credential lifecycle. Fix that first.
2. Establish the credential-store state without reading secret values. Run
   `stat ~/.config/comet/credentials` and record existence, mode (expect 0600),
   and mtime. A recent mtime means a delivery completed recently. If the JSON
   structure matters, mask with a single-level jq filter and never print key
   values; see the notes for the filter and for the recursive-mask failure.
3. Run `comet whoami` once, under a timeout. Interpret the result:
   - `200` with the expected user: the lifecycle is healthy. Stop.
   - `401` with a file older than ~60 s: link 3 (admission) failed.
     Re-running `comet login` does not repair admission; it re-imports the same
     rejected key.
   - No credentials file: no delivery has completed. Go to step 4.
4. Run `comet request-key` with a bounded wait under `timeout` (for example
   `--wait 15` under a 120 s timeout, then `--wait 1` to time the recovery
   path). Record the exit code, the elapsed time, and the terminal line:
   - Fast exit 1 with a prepare-time traceback: link 1 dead end. Collect the
     frame. Do not retry; the same state produces the same branch.
   - Exit 0 with `Credential request state: pending.`: link 1 published, link 2
     did not complete. Treat exit 0 on `pending` as a designed-behavior trap:
     scripts see success while no credential can arrive.
   - `registered`/delivered: healthy; verify with `whoami` after the window.
5. If the process is still running, prove that the wait is local polling and
   not a blocked resource. Sample `/proc/<pid>/wchan` and list
   `/proc/<pid>/fd`. `hrtimer_nanosleep` with file descriptors only to
   `/dev/null`, the output file, and `/dev/urandom` means a local sleep-poll
   for a service result that is not being written. Rule out a mount stall
   separately: `stat` of the rendezvous directories and of the client shim
   completes in ~0 s on a healthy mount.
6. Assess service-side liveness through the rendezvous parent directories with
   `stat` only. Group-writable sticky parents (mode `3733`,
   `drwx-ws-wt`) mean clients can publish. `results`/`deliveries` parent mtimes
   that are weeks old mean the consume/deliver loop is not moving. Listing a
   `--x` parent fails with EACCES by design; ENOENT for the per-user request
   subdirectory means the request never created an object. Check only your own
   artifacts and parent metadata; the contents are service-owned.
7. Do not reproduce the failure under another person's account. Give the
   affected account a read-only debug script that self-collects: identity and
   group state, client build identity, public read results, masked store state,
   rendezvous metadata, bounded `request-key` runs with exit codes and elapsed
   times, `/proc` sampling, and mount-latency probes. The script writes a
   report file and masks every credential value. The notes contain the section
   list and the masking rules.
8. Route the classified link to its owning issue. Search for duplicates first;
   add evidence comments to existing owners. Known owners on the m2 lane
   (2026-10): fulfillment disabled because the gateway launch omits the
   database DSN — LLM360/comet#2874 and LLM360/comet#2157; admission blocked
   because the key-cache database partition stays empty — LLM360/comet#2784;
   prepare-time lifecycle-record dead ends and missing rotation —
   LLM360/comet#2868 and LLM360/comet#2161; no admin-side path to issue an
   ordinary-user credential — LLM360/comet#2162.

### Degraded Conditions

- `py-spy` absent and `strace` attach refused (`yama/ptrace_scope=1` blocks
  non-child attach for the same uid): use `/proc/<pid>/wchan` and the fd list.
  They give the same hang-vs-poll signal.
- Service-owned directory contents not listable: use parent mtimes and the
  caller's own artifacts only. Parent mtimes still show whether the service
  loop is alive.
- No credentials file at all: skip admission checks; classify from the
  `request-key` terminal line directly.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Wait longer, retry `request-key` after `pending` | Repeated bounded `request-key` runs on an account whose fulfillment was disabled | Every run republished and re-polled, then printed `pending` with exit 0; no error, no progress | Classify from the exit code plus terminal state string, not from retry behavior; exit 0 hides the failure from scripts |
| Re-run `comet login` to repair a persistent 401 | Re-imported the saved credential against a gateway that never admitted it | The admission link had failed upstream, so the identical key stayed rejected; the "allow time for key propagation" message stayed true forever | Check key age against the propagation window first; a 401 beyond the window is an admission-side defect, not an import problem |
| Attach `strace` / `py-spy` to the hanging process | `strace -p` as the same uid, then `py-spy` dump | Kernel `yama/ptrace_scope=1` refused the non-child attach; `py-spy` was not installed | Sample `/proc/<pid>/wchan` and `/proc/<pid>/fd` instead; `nanosleep` with no external fds proves a local poll loop |
| Recursive masked `jq` dump of the credentials file | `jq` with a recursive `def mask` over every nested value | The filter ended with `error: cannot allocate memory`, no output | Use a single-level mask over top-level entries; it covers the store schema and never prints values |
| Read the raw traceback as a transient or a user error | Retried `request-key` after `PermissionError: credential lifecycle intent does not match saved credential` | The prepare branch reads durable state (lifecycle record vs saved credential), so every retry raised the same exception at the same frame | A prepare-time `PermissionError` is a durable dead end; check `whoami` with the existing credential to separate "dead end, key still valid" from "no working key" |

## Results & Parameters

### Configuration

Environment and limits used for the verified runs:

```yaml
environment:
  COMET_ROOT: "<deployment public client root>"   # supplies the client shim on PATH
  COMET_API_KEY: unset-or-masked                  # probes must not print it
timeouts:
  whoami: 45 s
  request-key wait: "--wait 15 under timeout 120 s; then --wait 1 under timeout 90 s"
sampling:
  hang_proof: "/proc/<pid>/wchan and ls -l /proc/<pid>/fd, ~25 s after start"
  mount_stall_exclusion: "time stat on rendezvous dirs and client shim; expect ~0 s"
masking:
  credential_values: "single-level jq mask; never print api key material"
```

### Expected Output

A successful diagnosis ends in exactly one terminal classification:

| Classification | Terminal evidence | Owning link |
|----------------|-------------------|-------------|
| Prepare/publish dead end | exit 1 traceback frame at prepare time | Link 1 |
| Fulfillment dead | exit 0 + `pending`; `results`/`deliveries` parent mtimes old | Link 2 |
| Admission dead | 401 on `whoami` beyond the window; comparison key of an older vintage authenticates | Link 3 |
| Lifecycle healthy | `whoami` 200 with the expected user | None (stop) |

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| LLM360/comet | m2 production deployment, release `69db2296`, 2026-10-22; two accounts (an ordinary test account, a staff account) | [notes.md](comet-user-credential-lifecycle-diagnosis.notes.md) |

## References

- [LLM360/comet#2874 — fulfillment disabled when the gateway launch omits the database DSN](https://github.com/LLM360/comet/issues/2874)
- [LLM360/comet#2157 — runtime template withholds the DSN the credential lifecycle requires](https://github.com/LLM360/comet/issues/2157)
- [LLM360/comet#2784 — proxy key sync never completes; key cache holds no database rows](https://github.com/LLM360/comet/issues/2784)
- [LLM360/comet#2868 — stale/conflicting saved credential dead-ends in a PermissionError traceback](https://github.com/LLM360/comet/issues/2868)
- [LLM360/comet#2161 — request-key demands a rotation no CLI command can perform](https://github.com/LLM360/comet/issues/2161)
- [LLM360/comet#2162 — no supported admin-side ordinary-user credential issuance](https://github.com/LLM360/comet/issues/2162)
- [comet-cli-offline-review-evidence-reporting](comet-cli-offline-review-evidence-reporting.md) — offline CLI review counterpart
