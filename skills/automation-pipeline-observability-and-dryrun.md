---
name: automation-pipeline-observability-and-dryrun
description: "Make multi-phase automation observable, dry-run safe, and compositionally live. Use when dry-run leaks into PR/learning phases, curses hides errors, cleanup deletes logs, issue implementers fail on Git/branch/import state, constructors are never wired, phase CLIs disagree on required scope arguments, or layered Bash silently aborts and should become a typed Python orchestrator."
category: debugging
date: 2026-05-26
version: "2.0.0"
license: BSD-3-Clause
user-invocable: false
verification: verified-precommit
history: automation-pipeline-observability-and-dryrun.history
tags: [dry-run, automation, observability, logs, composition-root, argparse, orchestrator]
---

# Automation Pipeline Observability and Dry-Run Safety

## Overview

An automation pipeline is reliable when no-op mode stops before every mutating follow-up, each phase
has visible start/finish/error state, logs outlive ephemeral worktrees, composition roots actually
construct runtime components, and the orchestrator adapts to each child CLI’s argument contract.
Repeated shell-control surprises are an architecture signal to move orchestration into typed Python.

Detailed cases are indexed in
[`automation-pipeline-observability-and-dryrun.notes.md`](automation-pipeline-observability-and-dryrun.notes.md).
The complete prior source is in
[`automation-pipeline-observability-and-dryrun.history`](automation-pipeline-observability-and-dryrun.history).

## When to Use

- Dry-run still reaches PR creation, learning, follow-up, or cleanup mutations.
- A curses/TUI run fails with no durable traceback or command transcript.
- Worktree cleanup removes the only logs needed for postmortem.
- Git status parsing, reused branches, or imports break an issue implementer.
- A runtime abstraction has tests but no constructor call from an entry point.
- A shell fan-out invokes heterogeneous CLIs with one uniform `--issues` policy.
- An outer `wait` is nonzero and later phase banners never appear despite inner traps.
- `set -euo pipefail`, job control, traps, subshells, and process substitution keep exposing new aborts.

## Verified Workflow

### 1. Define dry-run as a phase boundary

List every phase and whether it reads or mutates external/local state. Dry-run may discover, plan, and
render intended actions, but must return before branch creation, commits, pushes, PRs, labels,
learning writes, follow-up issues, destructive cleanup, or deployment.

Put one explicit guard at the boundary after the final read-only phase:

```python
run_discovery_and_plan()
if options.dry_run:
    report_planned_actions()
    return 0
run_mutating_phases()
```

Test that every downstream collaborator is not called in dry-run and is called once in live mode.
Do not sprinkle partial no-op checks that allow later phases to drift.

### 2. Make UI errors durable and visible

Wrap each phase at the UI/controller boundary. Record phase name, repository/item, command/session,
start time, completion status, exit code, and exception/traceback. Update status granularly through
clone/worktree, plan, implement, tests, commit, push, PR, review, merge, learning, and cleanup.

On error, leave a stable FAILED row/message, write the full traceback to the durable log, restore the
terminal in `finally`, and return nonzero. Never replace an exception with a transient curses line.

### 3. Persist logs outside ephemeral worktrees

Choose a run root before creating worktrees:

```text
<log-root>/<run-id>/<repo>/<item>/
  coordinator.log
  commands.jsonl
  stdout.log
  stderr.log
  result.json
```

Flush/copy required evidence before cleanup and record the durable location in the summary. Keep
secrets out of argv/logs and apply retention/redaction. Worktree removal must not be the operation
that destroys the only failure evidence.

### 4. Debug implementer failures from the first broken boundary

Capture the exact command, cwd, environment shape, branch/ref, and raw output. Parse porcelain/JSON
Git output instead of human-formatted text. Before reusing a branch, fetch and bind to the expected
remote head; distinguish absent branch, existing clean branch, diverged branch, and dirty worktree.

Import failures require verifying executable environment, package layout, module path, and installed
metadata rather than adding broad path hacks. Reproduce one item outside the UI with the same argv
before changing orchestration.

### 5. Audit composition-root wiring

A class/package existing and passing unit tests can still be dead code. Starting from each executable,
CLI command, service factory, dependency-injection module, or `main`, search for constructor/factory
calls and follow the object to a runtime consumer. Zero construction paths means structurally dead
functionality.

```bash
rg -n 'New<Component>|<Component>\(|build_<component>|provide_<component>' cmd src app
```

Record component, constructor, composition root, consumer, and test/runtime evidence. Do not accept
imports or type references as wiring.

### 6. Build a child-CLI contract matrix

Inspect every entry point’s parser. Record whether scope flags are required, optional, or unsupported;
whether it auto-discovers; and its dry-run/exit behavior:

```text
phase | executable | scope flag | required? | auto-discovers? | output/exit contract
```

Discover the current issue set once per repository/loop at the intended point. Pass explicit scope
only to phases that require it. Do not pass `--issues` to an auto-discovering phase that must observe
new work created mid-loop, and do not omit it from a required phase—argparse exit 2 can otherwise look
like silent orchestration failure.

Test the constructed argv for every phase, including an empty discovery set, and surface parser
stderr/exit code.

### 7. Diagnose shell orchestration with outer evidence

When later banners never appear, run with `bash -x` and add timestamps plus ERR/RETURN/EXIT evidence
at the outer function/process boundary. Inspect the status returned by subshells, `wait`, `mapfile`,
process substitution, and job-control commands. An inner trap may not execute in the context whose
status caused the parent to exit.

Avoid accumulating `set +e`, nested traps, single-command subshells, and ad hoc status preservation.
Each new layer creates another implicit control-flow contract.

### 8. Rewrite unstable fan-out as a Python module

When multiple safety-layer fixes have each exposed a new abort, stop patching Bash. Model phases as
data with executable, supported/required flags, timeout, concurrency, and dependencies. Use
`subprocess.run`/managed processes with explicit argv lists, capture output, bounded waits, structured
results, and one aggregate exit policy.

Preserve phase isolation and concurrency intentionally. Validate child parser contracts before
launch, log start/finish for every phase, continue or stop according to explicit policy, and make
dry-run render the exact argv without execution.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --- | --- | --- | --- |
| Partial dry-run checks | Guarded only implementation | PR/learn/follow-up still mutated | One boundary before all mutations |
| Curses-only error | Displayed exception transiently | Terminal reset erased evidence | Persist traceback and stable status |
| Worktree-local logs | Stored logs beside implementation | Cleanup removed postmortem | Use external run root |
| Human Git parsing | Parsed branch/status prose | Formats and edge states broke | Use porcelain/JSON and explicit refs |
| Import equals wiring | Found component import | No runtime constructor existed | Trace composition root to consumer |
| Uniform scope argv | Passed/omitted `--issues` for all phases | Required parser exited or discovery froze | Maintain per-phase contract matrix |
| Inner traps only | Added ERR/EXIT inside subshell | Parent aborted outside trapped context | Instrument outer process/status |
| More shell safety layers | Added defangs/traps/subshells repeatedly | New implicit abort modes appeared | Rewrite orchestration in typed Python |

## Results & Parameters

```text
phase inventory with read/mutation classification
dry-run boundary and forbidden collaborator assertions
run ID, durable log root, retention/redaction policy
per-phase item/argv/cwd/start/end/exit/exception result
branch/ref/worktree state and import environment
component-to-constructor-to-consumer wiring matrix
child CLI flag/discovery/output contract matrix
shell trace plus outer wait/subshell statuses
Python phase spec, dependencies, concurrency, timeout, aggregate exit policy
```

## Verified On

- Dry-run guard, curses visibility, log persistence, implementer diagnostics, and wiring audits.
- Heterogeneous CLI argument contracts and shell-to-Python orchestration design through 2026-05-26.
- Verification remains `verified-precommit`; no stronger CI claim is introduced by compaction.
