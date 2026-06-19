---
name: architecture-container-secret-cmdline-leak-fix
description: "Use when: (1) a secret like ANTHROPIC_API_KEY is passed to a container via `-e VAR=value` on a podman/docker run command line, (2) planning to fix a credential leak observable through `ps auxww` or `/proc/<pid>/cmdline`, (3) deciding whether to relocate a secret to a file, delete it, or switch to name-only `-e VAR` because the value must still reach the container, (4) a 'safe to remove/change' argument is about to be applied across multiple call sites — confirm each site invokes the SAME binary/auth path first, (5) writing a regression test for a credential change — a string-absence test is NOT an auth-regression test, (6) citing a test runner in a verification plan — confirm the runner actually exists in pixi.toml/justfile."
category: architecture
date: 2026-06-19
version: "1.1.0"
user-invocable: false
verification: unverified
history: architecture-container-secret-cmdline-leak-fix.history
tags: [security, secrets, container, podman, docker, cmdline-leak, anthropic-api-key, oauth, credentials, proc, planning, env-name-only, per-callsite-binary, auth-regression-test, verify-the-runner]
---

# Container Secret on Command Line Leak — Delete-Before-Relocate Fix

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-06-19 |
| **Objective** | Plan the fix for a secret (ANTHROPIC_API_KEY) leaking to all host users via the container command line (`ps auxww` / `/proc/<pid>/cmdline`) for GitHub issue #180 in the Odysseus repo |
| **Outcome** | Plan refined after a reviewer NOGO: do NOT share one "safe to remove" argument across structurally different workers — the single worker runs the mounted standalone `claude-host` (OAuth-capable, env var droppable) while the multi worker runs the image-baked npm `claude` with no `claude-host` mount and an unverified auth path. The behavior-preserving fix is podman/docker name-only `-e VAR` (value off the cmdline, still injected). Plan was NOT executed; CI never ran it. |
| **Verification** | unverified — implementation plan only; the container was never run with the change applied |
| **History** | [changelog](./architecture-container-secret-cmdline-leak-fix.history) |

## When to Use

- A secret is injected into a container with `-e SECRET=value` on the `podman run` / `docker run` command line
- A security review flags that the secret is readable via `ps auxww`, `ps -ef`, or `/proc/<pid>/cmdline` by any host user for the process lifetime
- You are about to "fix" the leak by moving the secret to a different `-e` var or another command-line mechanism (this is the same class of bug)
- You are deciding between relocating a secret to a file, deleting it entirely, or switching to name-only `-e VAR`
- You are about to apply a single "safe to remove/change this argument" judgement across MULTIPLE call sites — first confirm each site invokes the SAME binary and auth path
- The containerized CLI may authenticate via mounted OAuth credentials (`~/.claude/.credentials.json`, `~/.claude.json`) and may ignore the env var altogether — but a sibling worker may run a different binary that does NOT
- Planning a regression test for a secret-on-cmdline leak and judging whether that test actually proves auth still works (it does not — a string-absence test is not an auth-regression test)
- Citing a test runner in a verification plan — confirm the runner actually exists in `pixi.toml` / `justfile` and matches the directory's test idiom

## Verified Workflow

> **Warning (Proposed Workflow):** This workflow has NOT been validated end-to-end. It is an implementation plan for issue #180 that was never executed, and CI never ran it. Treat every step as a hypothesis until a live container run confirms auth still works. Verification level: `unverified`.

### Quick Reference

```bash
# 1. PROVE the leak class: a secret on the run command line is world-readable on the host.
ps auxww | grep -i ANTHROPIC_API_KEY          # any host user sees it
cat /proc/<container-runtime-pid>/cmdline | tr '\0' ' '   # also exposes it

# 2. Find every injection site (do NOT assume there are only two) AND the binary each site runs.
grep -rn ANTHROPIC_API_KEY e2e/*.py            # found exactly 2 here — but see scope caveat below
grep -rn ANTHROPIC_API_KEY .                   # also check Dockerfiles, entrypoints, Nomad HCL, compose
#  CRITICAL: the two workers run DIFFERENT binaries with DIFFERENT auth paths:
#    claude-myrmidon.py:257       -> runs the MOUNTED standalone `claude-host` (OAuth-capable)
#    claude-myrmidon-multi.py:289 -> runs the IMAGE-BAKED npm `claude` (@anthropic-ai/claude-code), NO claude-host mount
#  Do NOT share one "safe to drop the env var" argument across both.

# 3. Choose the MINIMAL behavior-preserving fix when the value must still reach the container:
#    podman/docker name-only `-e VAR` (no =value). The value is read from podman's OWN
#    environment and injected; only the NAME lands on the cmdline. Verified: `podman run --help`
#    (podman 4.9.3). Alternatives: --env-file, --env-host.
#    -e VAR=$ANTHROPIC_API_KEY   # LEAKS the value on the cmdline (bad)
#    -e ANTHROPIC_API_KEY        # name-only: value injected from host env, NOT on cmdline (good)

# 4. CAVEAT: name-only `-e VAR` silently injects NOTHING if the host env lacks the var.
#    Add a pre-flight check that WARNS when unset (the value is no longer eyeball-visible).
[ -n "${ANTHROPIC_API_KEY:-}" ] || echo "WARN: ANTHROPIC_API_KEY unset; name-only -e injects nothing"

# 5. Verify the test runner EXISTS before citing it.
grep -nE 'pytest|test' pixi.toml justfile      # Odysseus: NO pytest; [tasks] test = "just test" -> ctest only
ls e2e/tests/**/*.sh                            # the e2e idiom here is standalone bash scripts

# 6. A string-absence test is NOT an auth-regression test. Build the PRODUCTION command via the
#    actual command-builder and run it against the real image, asserting non-error (gated on
#    runtime/image availability so it skips cleanly without them — but present as a runnable step).
```

### Steps (Proposed)

1. Reproduce / confirm the leak: the secret appears in `ps auxww` and `/proc/<pid>/cmdline` because it is an `-e VAR=value` argument on the `podman run` line. The exposure lasts the entire process lifetime and is visible to every host user.
2. Enumerate all injection sites with `grep -rn ANTHROPIC_API_KEY` — including Dockerfiles, container entrypoints, Nomad HCL, and compose env, not just the Python e2e harness.
3. **For each injection site, confirm the actual binary it invokes BEFORE generalizing any safety argument.** Here the two workers differ: `claude-myrmidon.py:257` runs the mounted standalone `claude-host` (OAuth-capable, can drop the env var), while `claude-myrmidon-multi.py:289` runs the image-baked npm `claude` (`@anthropic-ai/claude-code`) with NO `claude-host` mount — its auth path was never verified, so the env var may be its only working auth. The first plan's fatal flaw was assuming removing `-e ANTHROPIC_API_KEY` was behavior-neutral for both.
4. Pick the minimal behavior-preserving fix: switch `-e ANTHROPIC_API_KEY=$VALUE` to name-only `-e ANTHROPIC_API_KEY`. The value is read from podman's own process environment and injected into the container; only the variable NAME lands on the command line, so `ps auxww` / `/proc/<pid>/cmdline` no longer expose the value. This is preferable to removal when you cannot prove the value is unused. (`--env-file` / `--env-host` are alternatives.)
5. Add a pre-flight check that WARNS when `ANTHROPIC_API_KEY` is unset on the host — name-only `-e` silently injects nothing, and the value is no longer eyeball-visible in the command.
6. (Only where you can PROVE the value is unused — e.g. the single worker's `claude-host` OAuth path) deleting the line is acceptable; verify the mounted OAuth credential files exist, are bind-mounted, and are readable by the in-container UID (`--userns=keep-id` maps the host UID; `chmod o+r` makes a 0600 file readable as the mapped UID).
7. Verify the test runner exists and matches the directory idiom: grep `pixi.toml` / `justfile` (Odysseus has NO pytest — `[tasks] test = "just test"` runs ctest against C++ submodules; the e2e idiom is standalone bash scripts under `e2e/tests/**/*.sh`).
8. Add a regression test asserting the secret value is absent from the assembled command list — BUT treat this as necessary-not-sufficient. Pair it with a real runtime auth probe: build the production command via the actual command-builder function (not a hand-rolled one), run it against the real image, and assert a non-error result, gated on runtime/image availability so it skips cleanly in CI without them.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Assert removal of `-e ANTHROPIC_API_KEY` is behavior-neutral for all workers | Applied one "safe to remove the env var" judgement to BOTH `claude-myrmidon.py` and `claude-myrmidon-multi.py` | Wrong: the workers run different binaries with different auth paths — the single worker invokes the mounted standalone `claude-host` (OAuth, env var droppable), the multi worker invokes the image-baked npm `claude` with NO `claude-host` mount, whose auth was never verified | Before generalizing a "safe to remove/change" argument across call sites, confirm each site invokes the SAME binary/auth path — grep the actual invoked command per site |
| Prove the fix with a cmdline string-absence test only | Add a test asserting `ANTHROPIC_API_KEY` is not in the assembled command args | Proves the leak is closed but proves NOTHING about whether auth still works after the change; a green test = false confidence | Add a live runtime auth probe: build the production command via the real command-builder and run it against the real image, gated on availability |
| Cite `pixi run pytest` as the verification runner | Wrote the verification plan around `pixi run pytest` | This repo (Odysseus) has NO pytest: `pixi.toml [dependencies]` has none, `[tasks] test = "just test"`, and `just test` runs ctest against C++ submodules only; the e2e idiom is standalone bash scripts | Verify the runner exists (grep `pixi.toml` / `justfile`) and match the directory's existing test idiom before writing verification commands |
| Remove the secret entirely when it must still reach the container | Delete the `-e ANTHROPIC_API_KEY` line everywhere as the KISS fix | Breaks auth where the env var is the only working path (e.g. the multi worker's npm `claude`) | Use podman/docker name-only `-e VAR` so the value stays off the cmdline but is still injected from the host environment |
| Relocate the secret to a different `-e` var / pass it via the command line differently | Move ANTHROPIC_API_KEY to another env flag still set as `-e VAR=value` on the `podman run` line | Still leaks — any `-e VAR=value` argument is visible via `ps auxww` and `/proc/<pid>/cmdline` to all host users; same class of bug | Command-line args are world-readable. Remove the VALUE from the cmdline (name-only `-e`, file, stdin, or delete), not move it to another flag |
| Treat a unit test asserting absence from the command list as sufficient proof | Add a pytest asserting `ANTHROPIC_API_KEY` is not in the assembled command args | Proves the string is gone but nothing about whether auth still works; a green suite gives false confidence | A regression test for a leak must be paired with a live auth check; absence-of-string ≠ functionality-preserved |
| Pass per-process secrets the host can observe (team KB) | Inject secrets as process arguments / env on the run line for any host-visible process | Other host users can read `/proc/<pid>/environ` and `/proc/<pid>/cmdline`; secrets belong in files with restrictive perms or runtime secret stores | Never put secrets where a host process listing can reveal them |
| Rely on ANTHROPIC_API_KEY pre-flight checks for the containerized CLI (team KB) | Gate the container start on the env var being set, assuming the CLI needs it | The standalone `claude`/`claude-host` CLI authenticates via OAuth credential files and ignores the env var; the pre-flight check guards a value the binary never reads | Verify what the binary actually consumes before adding guards or relocating values around it |

## Results & Parameters

### UNCERTAIN ASSUMPTIONS / UNVERIFIED RELIANCES (read this first, reviewer)

This is the most important section. The plan rests on the following claims that were NOT validated by running the container.

**Resolved / refined since v1.0.0:**

- **Asymmetric binary finding — now verified by grep.** The two workers invoke different binaries: `claude-myrmidon.py:257` runs the mounted standalone `claude-host`; `claude-myrmidon-multi.py:289` runs the image-baked npm `claude` (`@anthropic-ai/claude-code`) with no `claude-host` mount. A single "safe to remove the env var" argument does NOT hold across both.
- **Name-only `-e VAR` is behavior-preserving — verified via `podman run --help` (podman 4.9.3).** Name-only `-e VAR` reads the value from podman's own process environment and injects it; only the variable NAME lands on the command line, so `ps auxww` / `/proc/<pid>/cmdline` no longer expose the value. Caveat: it silently injects nothing if the host env lacks the var — a pre-flight warning is required because the value is no longer eyeball-visible.
- **Test runner absence — verified.** Odysseus has NO pytest: `pixi.toml [dependencies]` has none, `[tasks] test = "just test"`, `just test` runs ctest against C++ submodules only; the e2e idiom is standalone bash scripts (`e2e/tests/**/*.sh`).

**Still UNVERIFIED — the reviewer should watch these:**

- **(a) Multi worker auth path never run.** Name-only `-e` is intended to PRESERVE the multi worker's npm `claude` auth, but the multi worker was never run end-to-end with the change applied. The regression would only surface at container runtime, which no proposed test exercises.
- **(b) achaean-claude image not inspected.** The image entrypoint / Dockerfile were not in the checkout, so whether the image itself expects `ANTHROPIC_API_KEY` is unconfirmed. Confirm the image does not require the env var.
- **(c) Live auth probe requires unavailable inputs.** The runtime auth probe requires podman + the achaean-claude image + a populated key — none guaranteed in CI. Present it as a runnable acceptance step gated on availability, not a commented-out optional.
- **(d) Hosts lacking OAuth creds.** For the single worker's `claude-host` OAuth path, hosts without populated OAuth credentials would break if the env var were removed with no fallback. Name-only `-e` mitigates this only where the host env actually has the key.
- **Test coverage gap.** A string-absence test proves the secret is off the cmdline; it proves nothing about whether auth still works. A green suite gives false confidence. Require a live auth probe before merge.
- **Stale, untouched code (deferred).** `claude-myrmidon.py:217` hardcodes standalone version `2.1.120`, which does not exist locally (only 2.1.176–178 are present); a glob fallback masks the mismatch. Out of scope for #180 but flagged for a follow-up.

### Parameters / Facts Established

```
Leak vector:        `-e ANTHROPIC_API_KEY=<value>` on the `podman run` command line
Observable via:     ps auxww | ps -ef | /proc/<pid>/cmdline | /proc/<pid>/environ
Audience:           every host user, for the full process lifetime
Issue:              GitHub #180 (Odysseus repo) — plan only, NOT executed

Two workers, two binaries, two auth paths (verified by grep):
  claude-myrmidon.py:257        -> mounted standalone `claude-host`  (OAuth-capable; env var droppable)
  claude-myrmidon-multi.py:289  -> image-baked npm `claude`          (@anthropic-ai/claude-code; auth path UNVERIFIED)

Behavior-preserving fix (verified via `podman run --help`, podman 4.9.3):
  -e ANTHROPIC_API_KEY=$VALUE   # LEAKS the value on the cmdline
  -e ANTHROPIC_API_KEY          # name-only: value read from podman's env, injected; NAME-ONLY on cmdline
  Alternatives:                 --env-file, --env-host
  Caveat:                       name-only -e injects NOTHING if host env lacks the var -> add pre-flight warn

Credential files (host, dev machine — for the single worker's OAuth path):
  ~/.claude/.credentials.json    perms 0600 (must be o+r / 0604 for in-container UID)
  ~/.claude.json                 perms 0600
  --userns=keep-id   maps host UID into container so mounted creds are owned by it
  chmod o+r          adds S_IROTH so a 0600 file becomes readable by the mapped UID

Test runner reality (verified):
  pixi.toml [dependencies]: NO pytest
  [tasks] test = "just test"  ->  ctest against C++ submodules only
  e2e idiom: standalone bash scripts under e2e/tests/**/*.sh

Injection sites found:   2 (in e2e/*.py)  — UNVERIFIED as complete; achaean-claude image not in checkout
Fix chosen:              name-only `-e ANTHROPIC_API_KEY` (value off cmdline, still injected)
Required before merge:    live container auth probe via the real command-builder (NOT covered by string-absence test)
```

### Test Plan Checklist (for the reviewer)

```
[ ] Regression test: ANTHROPIC_API_KEY VALUE absent from assembled command args (necessary, not sufficient)
[ ] LIVE container auth probe built via the real command-builder, run vs the real image (the load-bearing check)
[ ] Confirm BOTH workers' binaries before sharing any safety argument (claude-host vs npm claude)
[ ] Confirm name-only `-e` preserves the multi worker's npm `claude` auth (run it end-to-end)
[ ] Pre-flight warning when ANTHROPIC_API_KEY is unset on the host
[ ] grep -rn ANTHROPIC_API_KEY across Dockerfiles / entrypoints / Nomad HCL / compose
[ ] Confirm achaean-claude image entrypoint does not require the env var (image not in checkout)
[ ] Confirm OAuth creds exist + are readable in-container on ALL target hosts (single worker)
[ ] Verify the cited test runner exists (pixi.toml/justfile) and matches the dir's test idiom
[ ] Follow-up: claude-myrmidon.py:217 hardcoded version 2.1.120 mismatch
```
