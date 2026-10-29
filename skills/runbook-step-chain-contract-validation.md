---
name: runbook-step-chain-contract-validation
license: BSD-3-Clause
description: "Validate a hand-authored sequence of deploy or cutover step scripts as one ordered chain, not step by step. Use when (1) an executor with stop-on-first-failure runs a numbered runbook and each run exposes one new failure that an artifact or contract of a previous step causes (a clean-tree preflight rejects a helper file the pipeline itself wrote, a sourced environment-file path is expanded as an interpreter directory, an idempotency marker is written and read in different line formats), (2) an idempotent rerun branch can skip the verification that a later fix changed, or (3) every step needs one cheap proof shared by its apply branch and its already-done branch."
category: debugging
date: 2026-10-29
version: "1.0.0"
user-invocable: false
verification: verified-live
tags: [runbook, deployment, cutover, step-scripts, chain-rehearsal, executor-loop, idempotency, marker-contract, path-role-naming, preflight-gate]
---

# Validate a Deploy Runbook as One Ordered Chain, Not Step by Step

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-29 |
| **Objective** | Make a numbered sequence of deploy/cutover step scripts executable end to end the first time an executor runs the chain. |
| **Outcome** | Successful — a full-chain rehearsal with a fresh-context executor (stop on first failure, ask before any script edit) surfaced three cross-step contract bugs that per-step review could not see. One bug appeared per run, with precise evidence. After each fix the chain restarted from the interrupted step. The operator-free segment of the cutover ran green. |

Cross-step contract bugs live between steps: step N fails on something step
N-1 produced. Each step passes isolated review, syntax checks, and dry runs.
The chain still fails. The failures are precise and cheap to fix — an exit 126
`Not a directory` at the proof command, a preflight gate that rejects a file
the pipeline wrote one step earlier, a whole-line marker match that the writer
and the reader disagree about. The cost is the loop: one bug per run when the
executor stops on the first failure. Rehearsing the chain before the critical
path turns the loop from a production incident into a review cycle.

## When to Use

Use this skill when one of these conditions applies:

- You author a numbered sequence of step scripts (deploy, cutover, migration,
  promotion) that an operator, an agent executor, or a CI job runs in order,
  with stop-on-first-failure semantics.
- A step uses `git status --porcelain` (or equivalent) as a preflight gate on
  a checkout that other steps of the same pipeline populate with helper files.
- A step sources an environment file, and a later command builds an executable
  path from the same variable prefix (for example `$VAR/bin/python`).
- An idempotency or provenance marker file has a writer and a whole-line
  reader, and either side was edited after the marker was first written.
- An idempotent rerun branch would skip exactly the verification that the
  last fix changed.

Do not use this skill for queue-based worker pipelines (a separate skill owns
worker result contracts) or for trust-boundary checkout admission gates (the
clean-checkout skill owns the untracked-files rule).

## Verified Workflow

### Quick Reference

```bash
# Idempotent step skeleton: one shared proof, re-run on every rerun.
marker="$EVIDENCE/40-fix-config.applied"
run_proof() {
    "$DEPLOY_VENV_DIR/bin/python" -c 'import service_modules; assert hasattr(service_modules, "expected_entrypoint")'
}
if [ -f "$marker" ] && grep -qx "STEP $REVISION" "$marker"; then
    run_proof || fail "marker names $REVISION but the proof no longer passes"
    exit 0
fi
# ... do the work ...
printf 'STEP %s\n' "$REVISION" > "$marker"   # same exact line the reader greps
run_proof || fail "the applied change does not pass the proof"
```

```bash
# Name path variables by role. The failure mode is a mid-chain exit 126
# "Not a directory" at the proof, far from the variable definition.
DEPLOY_ENV_FILE="$CHECKOUT/.release-env"     # a file: use with . or source
DEPLOY_VENV_DIR="$CHECKOUT/.venv"            # a directory: holds bin/
"$DEPLOY_VENV_DIR/bin/python" ...            # never "$DEPLOY_ENV_FILE/bin/python"
```

```bash
# Executor rehearsal contract (agent or human):
# run the steps in order from the earliest clean state; stop on the first
# failure; report the exact failing check and the artifact that triggered
# it; never edit a script without asking the owner.
```

### Detailed Steps

1. **Rehearse the full chain in order against real predecessor artifacts.**
   Start from the earliest clean state and run every step, in order, with the
   same guards production will use. Isolated per-step validation cannot
   observe a contract that only exists between two steps. When a fresh-context
   executor (agent or operator) is available, give it stop-on-first-failure
   and ask-before-edit rules: each run then returns one precise bug report —
   the failing check and the artifact that triggered it — instead of a patched
   script with unknown side effects. Fix gates and contracts at the helper
   side, then rerun.

2. **Keep one proof function shared by the apply branch and the already-done
   branch, and run it on every rerun.** An idempotency marker says "the work
   was done". It does not say "the current verification passes" — a later fix
   can change the verification itself (for example a corrected interpreter
   path) while the marker stays. A cheap import or version proof costs
   seconds. Run it before `exit 0` in the already-done branch.

3. **Name path variables by role, and resolve executables explicitly.** A
   variable that holds a sourced file path and a variable that holds a tool
   directory are different roles. `$DEPLOY_ENV_FILE/bin/python` fails with
   exit 126 `Not a directory` at the first command that builds a path from
   the wrong role — typically the proof step, far from the assignment. A
   `_FILE` / `_DIR` naming convention makes the misuse visible in review.

4. **Give each marker writer and reader one exact line contract.** Write and
   read the full line with the same format on both sides — for example the
   writer prints `STEP <revision>`, the reader greps whole-line for
   `STEP <revision>`. After any edit to either side, prove the pair together
   against a real marker file, not a handwritten sample. For markers read
   back through an external store (release bodies, issue comments), also
   apply the CRLF rule from the sibling marker-matching skill.

5. **Fix preflight-gate failures with the canonical checkout rule, not with
   status suppression.** When a step's clean-tree preflight rejects a helper
   file the pipeline itself wrote (an env file, a log, a token marker), put
   the helper outside the checkout or under an ignore rule — for a detached
   worktree, `git/info/exclude` works without touching the repository's
   shared `.gitignore`. Do not relax the gate to `--untracked-files=no`:
   that hides arbitrary ambient content from every later consumer, exactly as
   the clean-checkout skill records as a failed approach.

6. **Preserve the evidence loop.** Keep each run's log, the executor's
   report, and the failing line. The one-bug-per-run pattern only converges
   when each fix is verified by a rerun, not by re-reading the script.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Review and syntax-check each step in isolation | Every step passed shellcheck and a solo read-through before the chain ran | The first executor run still failed three times, one bug per run, each on an artifact of a prior step | Cross-step contract bugs are invisible to per-step validation; rehearse the chain |
| Already-done branch exits without re-verification | The idempotent branch found the marker and exited 0 after the proof's interpreter path had been fixed | A rerun then succeeded without ever executing the fixed proof; the marker predated the fix | Run cheap proofs on every rerun; share one proof function across both branches |
| One variable for two path roles | A single prefix variable held the sourced env file and was also expanded as `$VAR/bin/python` | Exit 126 `Not a directory` surfaced at the proof command, three steps away from the assignment | Name variables by role (`_FILE` vs `_DIR`) and resolve executables explicitly |
| Bare whole-line marker grep after a format edit | The writer was changed to stamp `KEY <revision>` for provenance; the reader still grepped the bare revision | Every rerun took the re-apply branch and failed on the by-design-dirty tree | Writer and reader share one exact line contract; test the pair against a real marker after edits |
| Relax the clean-tree preflight to ignore untracked files | Suppressing untracked output made the pipeline's own helper file stop blocking the step | The same flag also hides arbitrary ambient executables and configuration from every later consumer of the checkout | Keep the untracked-files=all gate for trust boundaries; move or ignore the helper instead (see the clean-checkout skill) |

## Results & Parameters

- Executor-loop cost observed: three runs, three fixed bugs, zero production
  side effects, because the executor's rules (ordered, stop-first, ask-before-
  edit) made every failure a report instead of a silent workaround.
- The whole loop ran read-only relative to production: buy this safety by
  rehearsing only the steps that cannot mutate live state, and hold every
  operator-bound step behind a separate readiness gate.
- Marker format examples that satisfy the contract: `STEP <full-revision>`,
  `P <full-revision>` — a key prefix documents provenance and keeps the
  whole-line grep unambiguous.

## References

- [automation-clean-checkout-intermediate-artifacts](automation-clean-checkout-intermediate-artifacts.md) — the canonical untracked-files rule for checkout gates; this skill defers to it for every preflight fix.
- [ci-release-guard-crlf-marker-matching](ci-release-guard-crlf-marker-matching.md) — the sibling marker-contract rule for text read back through external stores (CR normalization); this skill covers locally written markers whose format was edited on one side.
- [deployed-version-runbook-goal-feasibility](deployed-version-runbook-goal-feasibility.md) — the complementary check that the runbook's terminal goal is reachable on the deployed version at all.
