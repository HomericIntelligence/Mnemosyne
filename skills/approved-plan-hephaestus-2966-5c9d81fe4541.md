---
name: "approved-plan-hephaestus-2966-5c9d81fe4541"
description: "Use when implementing the approved plan from HomericIntelligence/Hephaestus#2966."
category: "tooling"
date: "2026-09-06"
version: "1.0.0"
user-invocable: false
verification: "production-host"
tags: [automation, learning, mnemosyne]
---

# Approved implementation plan learning for #2966

## Overview

Use when implementing the approved plan from HomericIntelligence/Hephaestus#2966.

## When to Use

Use this learning when the same repository workflow, constraint, or failure mode recurs.

## Verified Workflow

### Objective

    Make forced automation shutdown stop all owned process groups within one fixed additional time bound. The first Ctrl+C will start the configured graceful drain. Grace-period expiry or a second Ctrl+C will stop main-lane and auxiliary-lane processes, return exit code 130, and keep interrupted work resumable.

### Approach

    - Keep process-group ownership in `hephaestus/utils/subprocess_registry.py`. The current `terminate_all()` clears `_live_pgids` before it sends `SIGTERM` at line 54. Retain each process-group ID until an existence check confirms that the group is gone.
    - Use one coordinator-owned registry lifecycle for both worker pools. `Coordinator` will open registration once before it creates either pool. Global shutdown will close registration once after both pools stop admission. Worker-pool construction and shutdown will not open, reset, or close the shared lifecycle.
    - Make lifecycle operations idempotent. Repeated open calls during the same active lifecycle will not clear registrations. Repeated close calls will keep registration closed. A new lifecycle can open only after the prior lifecycle has no registered groups.
    - Close registration before the termination snapshot. If `track_process_group()` races with shutdown, it will add the group to the retained set and send `SIGKILL` immediately. The final sweep will include that group.
    - Split pool shutdown into two phases. `begin_shutdown()` will reject submissions and cancel the executor once. `finish_shutdown(deadline)` will wait for futures only until the shared monotonic deadline. `shutdown()` will remain as the direct-use convenience method and will use these phases with registry termination.
    - In coordinator shutdown, call `begin_shutdown()` for the main and auxiliary pools before process termination. Then close the shared registry and call `terminate_all()` once. This order prevents one lane from changing registry state while the other lane still admits work.
    - Use one absolute deadline from `time.monotonic()` for all forced-shutdown work. The default sequence will allow up to one second for `SIGTERM` and use the remaining fixed bound for `SIGKILL`, direct-child reaping, final registry sweeps, and future release. No sequential pool wait can extend this deadline.
    - Poll process groups with `os.killpg(pgid, 0)`. Send `SIGKILL` to survivors after the `SIGTERM` deadline. Remove only groups that return `ProcessLookupError`. Keep and log all unresolved process-group IDs at the final deadline.
    - Reap a direct group leader with `os.waitpid(pgid, os.WNOHANG)`. Treat `ChildProcessError` as evidence that its normal `Popen` owner already reaped it.
    - Let the shared force event interrupt the `SIGTERM` polling period. A second Ctrl+C will set this event and wake the coordinator. The termination loop will then send `SIGKILL` without waiting for the remaining graceful or `SIGTERM` time.
    - Keep `_pool_shut_down` as a guard for one-time executor cancellation, completion draining, and item parking. Do not use it to suppress registry escalation.
    - Use real process trees in the normal test suite. Each regression child will create a descendant, put both processes in the owned group, and ignore `SIGTERM`.
    - Add a cross-lane lifecycle regression. Register a main-lane group, initialize and begin shutdown of the auxiliary lane, and confirm that these operations do not reset, reopen, close, or remove the main registration. Then run shared forced termination and confirm that it kills the group.
    - Preserve the provider tracking seams. Repository search found registry termination use in `WorkerPool`, `MnemosyneSkillHost`, registry tests, and learning-lane tests. All callers will use the same retained-ownership and deadline contract.

### Implementation Order

    1. Add the coordinator-owned, idempotent registry lifecycle without changing signal behavior.
    2. Add registry tests for shared lifecycle ownership, cross-lane preservation, close behavior, and late registration.
    3. Replace registry clear-before-signal behavior with retained ownership, bounded escalation, direct-child reaping, and unresolved-group reporting.
    4. Add registry tests for `SIGTERM` resistance, descendants, `SIGKILL`, fixed deadlines, and unresolved groups.
    5. Update the automation registry compatibility declarations.
    6. Split `WorkerPool` shutdown into executor-cancellation and deadline-bounded completion phases.
    7. Apply the same pool contract to `AuxiliaryWorkerPool` and update `MnemosyneSkillHost`.
    8. Make `Coordinator` the only owner of the shared registry lifecycle and pass one force event to both pools.
    9. Refactor `CoordinatorRuntime` to stop both lanes, close registration, terminate the shared registry once, and wait for both lanes under one monotonic deadline.
    10. Add the real main-lane, cross-lane, second-signal, grace-expiry, and auxiliary-lane regressions.
    11. Run the focused process tests, provider tracking tests, full unit suite, Ruff, and mypy.

### Verification

    ```bash
    uv run pytest --no-cov -q tests/unit/automation/pipeline/test_coordinator_shutdown.py -k first_signal_stops_admission
    # Criterion 1: the first Ctrl+C stops admission and permits work to drain only for the configured period.
    ```
    
    ```bash
    uv run pytest --no-cov -q tests/unit/automation/pipeline/test_coordinator_shutdown.py -k grace_expiry_kills_real_agent_tree_and_exits_130
    # Criterion 2: grace-period expiry kills all owned groups and exits with code 130 within one fixed additional bound.
    ```
    
    ```bash
    uv run pytest --no-cov -q tests/unit/automation/pipeline/test_coordinator_shutdown.py -k second_signal_kills_real_agent_tree_and_exits_130
    # Criterion 3: the second Ctrl+C kills owned groups without the remaining graceful-drain wait.
    ```
    
    ```bash
    uv run pytest --no-cov -q tests/unit/automation/test_subprocess_registry.py -k bounded_termination_kills_sigterm_ignoring_tree_and_reaps_leader
    # Criterion 4: a child and descendant that ignore SIGTERM receive SIGKILL and do not remain alive.
    ```
    
    ```bash
    uv run pytest --no-cov -q tests/unit/automation/test_subprocess_registry.py -k termination_retains_group_until_exit
    # Criterion 5: sending a signal does not remove process-group ownership.
    ```
    
    ```bash
    uv run pytest --no-cov -q tests/unit/automation/pipeline/test_worker_pool.py -k later_force_escalates_after_executor_shutdown
    # Criterion 6: a later force request escalates an earlier shutdown attempt.
    ```
    
    ```bash
    uv run pytest --no-cov -q \
      tests/unit/automation/pipeline/test_worker_pool.py::TestShutdownReapsSubprocess \
      tests/unit/automation/pipeline/test_learning_lane.py -k forced_auxiliary_shutdown
    # Criterion 7: main-lane and auxiliary-lane jobs use the same bounded termination behavior.
    ```
    
    ```bash
    uv run pytest --no-cov -q tests/unit/automation/pipeline/test_coordinator_shutdown.py -k shared_registry_lifecycle_preserves_main_group_across_auxiliary_shutdown
    # Criteria 2, 3, 5, and 6: auxiliary-pool setup and shutdown cannot reset or remove main-lane ownership, and shared force teardown kills the group.
    ```
    
    ```bash
    uv run pytest --no-cov -q tests/unit/automation/pipeline/test_coordinator_shutdown.py -k "resumable or real_agent_tree"
    # Criterion 8: queued and active interrupted items remain RESUMABLE and do not become FAILED.
    ```
    
    ```bash
    uv run pytest --no-cov -q -m "not nightly" tests/unit/automation/pipeline/test_coordinator_shutdown.py -k "grace_expiry_kills_real_agent_tree or second_signal_kills_real_agent_tree"
    # Criterion 9: real-process interrupt regressions run in the normal test suite.
    ```
    
    ```bash
    uv run pytest --no-cov -q tests/unit/automation/pipeline/test_coordinator_shutdown.py -k "fixed_deadline or real_agent_tree"
    # Fixed-bound contract: registry waits, both pool waits, reaping, and coordinator exit use one monotonic deadline.
    ```
    
    ```bash
    uv run pytest --no-cov -q tests/unit/automation/pipeline/test_worker_pool.py::TestShutdownReapsSubprocess tests/unit/agents/test_runtime.py -k "process_tracker or opencode or pi"
    # Provider regression: Claude, Codex, OpenCode, and admitted Pi process tracking remains valid.
    ```
    
    ```bash
    uv run pytest --no-cov -q \
      tests/unit/automation/test_subprocess_registry.py \
      tests/unit/automation/pipeline/test_coordinator_shutdown.py \
      tests/unit/automation/pipeline/test_worker_pool.py::TestShutdownReapsSubprocess \
      tests/unit/automation/pipeline/test_learning_lane.py
    # Focused issue verification.
    ```
    
    ```bash
    uv run pytest tests/unit
    # Required repository unit and coverage gate.
    ```
    
    ```bash
    uv run ruff check hephaestus/ tests/
    # Required lint gate.
    ```
    
    ```bash
    uv run mypy hephaestus/ scripts/ tests/
    # Required type-check gate.
    ```

### Changes from Review

    - Assigned shared registry lifecycle ownership to `Coordinator`. Removed pool-owned open, reset, and close behavior.
    - Defined idempotent lifecycle operations and protected unresolved registrations from reopen or reset.
    - Added a two-phase shutdown that stops both lanes before one shared registry termination sequence.
    - Added a cross-lane regression that preserves and kills a main-lane group across auxiliary-lane setup and shutdown.
    - Defined one absolute monotonic deadline for signal waits, reaping, future release, and coordinator exit.
    - Added elapsed-time assertions for grace-expiry, second-signal, main-lane, and auxiliary-lane real-process tests.

## Failed Attempts

No failed attempt is asserted beyond the bounded source material above.

## Results & Parameters

- Source repository: `HomericIntelligence/Hephaestus`
- Issue: `#2966`
- Canonical plan revision: `2`
- Canonical comment database ID: `5560134621`
- Plan fingerprint: `2b2ecff94c9d4c8324125c5ca8b1dbeb13cb4a7eb378dd9937498fcbc8d1f0ee`

## Verified On

Prepared by the provider-neutral Mnemosyne host boundary.
