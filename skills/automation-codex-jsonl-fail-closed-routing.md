---
name: automation-codex-jsonl-fail-closed-routing
description: "Fail closed when a headless Codex invocation reports fatal provider, sandbox, or tool events inside JSONL even if the CLI exits zero or writes a plausible final answer. Use when: (1) Codex reports `error`, `turn.failed`, or any failed/declined completed item but orchestration treats the run as successful, (2) nested macOS execution emits `sandbox_apply: Operation not permitted`, (3) a timeout-recovered final message could hide an earlier fatal event, (4) documented recoverable command or stream-lag events need narrow exceptions, or (5) provider failures must reach a provider-neutral worker/stage error path without broadening sandbox access."
category: debugging
date: 2026-08-04
version: "2.0.1"
user-invocable: false
verification: verified-ci
history: automation-codex-jsonl-fail-closed-routing.history
tags:
  - automation
  - codex
  - jsonl
  - agent-runtime
  - provider-adapter
  - sandbox
  - sandbox-apply
  - tool-failure
  - fail-closed
  - worker-pool
  - state-machine
  - pr-review
  - exact-head
  - host-receipt
---

# Codex JSONL Fail-Closed Routing for Agent Automation

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-08-04 |
| **Objective** | Make automation recognize fatal failures reported through Codex's structured JSONL and stderr channels, including a nested macOS child-sandbox initialization failure, and route them through the existing provider-neutral agent-error path. |
| **Outcome** | ProjectHephaestus PR #2637 implemented the classifier, neutral exception boundary, WorkerPool mapping, and stage regressions. Reviews across three distinct heads corrected the proposed finite allowlist, preserved the documented stream-lag exception, and required an executed host receipt before GO. |
| **Verification** | `verified-ci` — final head `4daac9b4` passed required checks and was conditionally squash-merged as `5f10af3b`. |
| **History** | [changelog](./automation-codex-jsonl-fail-closed-routing.history) |

## When to Use

- A headless Codex process exits zero while its JSONL contains `error`, `turn.failed`, an
  error item, or any failed/declined completed item that is not explicitly recoverable.
- A nested worktree execution on macOS reports
  `sandbox_apply: Operation not permitted`, but a later final message such as “No edits were
  made” causes orchestration to enter a successful no-change or skip path.
- A subprocess timeout recovery reads a final-output file and may accept it without checking
  fatal events emitted before the timeout.
- An orchestration stage contains provider-specific parsing that belongs in the shared agent
  runtime adapter.
- A failed repository command must remain recoverable agent activity, while an infrastructure
  failure inside that command must fail the agent run.
- A provider-specific exception must cross a worker boundary as an ordinary failed result so
  existing retry, worktree preservation, review, signing, branch-lease, and exact-head contracts
  remain unchanged.
- Review evidence names a boundary test but does not prove that the reviewed head executed it.

## Verified Workflow

### Quick Reference

```python
class AgentExecutionError(RuntimeError):
    """An agent CLI reported a fatal provider, sandbox, or tool failure."""


_CODEX_NESTED_SANDBOX_MARKER = "sandbox_apply: Operation not permitted"
_CODEX_FAILED_TOOL_STATUSES = frozenset({"failed", "declined"})
_CODEX_APP_SERVER_STREAM_LAG_PREFIX = (
    "in-process app-server event stream lagged; dropped "
)
_CODEX_APP_SERVER_STREAM_LAG_SUFFIX = " events"
```

Classification contract:

| Structured input | Fatal? | Reason |
|------------------|--------|--------|
| Event type `error` or `turn.failed` | Yes | Terminal provider failure. |
| Completed item whose item type is `error` | Yes, except exact stream-lag notice | Structured error item; the documented numeric lag notice is recoverable. |
| Any other completed item with status `failed` or `declined` | Yes | Unknown and future item kinds fail closed instead of reaching no-change cleanup. |
| Failed `command_execution` containing the exact nested-sandbox marker | Yes | Child sandbox could not initialize. |
| Failed `command_execution` without the marker | No | Tests, searches, and repository commands may fail before the agent recovers. |
| Exact app-server stream-lag error item followed by successful completion | No | Codex documents it as a nonfatal transport notice. |
| Model prose mentioning errors or the marker | No | Prose is untrusted task output, not a machine-readable status channel. |

### Detailed Steps

1. **Put provider semantics in the provider adapter.** Locate the shared runtime method that
   builds, starts, communicates with, and parses the Codex CLI. Add the classifier there, not
   in individual planning, implementation, review, or merge stages. Keep provider-specific
   JSONL details behind this boundary.

2. **Introduce a provider-neutral exception.** Raise an `AgentExecutionError` (or the local
   equivalent) when a completed CLI invocation contains a fatal provider, sandbox, or tool
   event. The name and public contract must not mention Codex so other adapters can use the
   same worker boundary later.

3. **Parse only bounded structured channels.** Iterate JSON objects already extracted by the
   runtime's JSONL parser and inspect `event["type"]`, completed-item type/status, and stderr.
   Never scan the final model message or arbitrary assistant prose. Truncate the selected
   diagnostic before it crosses logs or result boundaries.

4. **Default failed items to fatal.** Treat terminal `error` and `turn.failed` events,
   completed error items, and every other failed/declined completed item as fatal. Do not
   enumerate today's item kinds: a finite allowlist lets new items such as
   `web_search_call` fall through to no-change cleanup. Extract a small human-actionable field
   such as message, error, output, or status rather than serializing the entire event.

5. **Special-case failed shell commands narrowly.** Do not make every failed
   `command_execution` fatal. Implementation agents legitimately run a failing test, probe an
   absent file, or issue a search that returns nonzero before recovering. Inspect failed command
   output only for the case-insensitive exact marker
   `sandbox_apply: Operation not permitted`; return a stable diagnostic explaining that the
   outer automation loop must run outside the enclosing API sandbox and that child permissions
   were not broadened.

6. **Recognize only the exact nonfatal stream-lag notice.** An `item.completed` error is
   recoverable only when its message starts with
   `in-process app-server event stream lagged; dropped `, ends with ` events`, and contains
   an ASCII decimal count between them. Keep the exception shape-specific so unrelated error
   items remain fatal.

7. **Check every process-completion route.** Run the same classifier:
   - after normal zero-exit communication and before accepting a final response;
   - inside the nonzero-exit handler, using bounded/coerced stdout and stderr before re-raising
     an ordinary process error; and
   - before accepting a final-message file recovered after a timeout.

   A late “no edits” response must never override an earlier fatal structured event.

8. **Map the typed exception once at the worker boundary.** Catch
   `AgentExecutionError` before the generic exception handler and return the orchestration's
   ordinary failed result, for example `ok=False` with a bounded
   `agent_error: <diagnostic>` string. Do not branch on provider in the worker or stages.

9. **Reuse the existing stage failure route.** Feed the failed worker result to the stage's
   current `agent_error` transition. Assert that the stage preserves branch/worktree reservation
   state and does not set no-commit flags, mutate skip labels, call commit/push completion, or
   perform successful no-change cleanup.

10. **Lock behavior at three layers.** Runtime tests cover zero-exit fatal JSONL, terminal
    provider errors, failed and declined unknown/web-search items, the recoverable stream-lag
    sequence, nonzero-process nested-sandbox diagnostics, timeout-final-message recovery, and
    an ordinary failed-command counterexample. A worker test proves the typed exception becomes
    a bounded failed agent result. A stage test proves tool-error plus no-diff output remains on
    the retry/error path and never reaches commit, skip, or successful cleanup.

11. **Require an executed host receipt before GO.** Registering a WorkerPool regression or
    proving that immutable host validation selects it does not prove the boundary executed.
    Keep NOGO until a reviewed-head receipt shows the test passing and demonstrates that
    `AgentExecutionError` becomes `agent_error:`.

12. **Re-run safety-contract tests.** Keep CLI command construction unchanged: preserve the
    requested working directory, sandbox mode, approval policy, and workspace-write-only
    metadata directories. Run read-only review, cryptographic signing/DCO, remote branch lease,
    and exact-reviewed-head merge tests alongside the new regressions. Never introduce a
    `danger-full-access` fallback to make nested sandboxing succeed.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Trust process exit code | A zero Codex exit was treated as success without inspecting structured events. | Non-interactive CLIs can report provider or tool failure inside machine-readable output while the wrapper process still exits zero. | Success requires both an acceptable process outcome and absence of fatal structured events. |
| Trust the final message | A final “no edits” response was accepted after an earlier tool failure. | Later prose does not cancel a prior machine-reported failure and can send the state machine into no-commit cleanup. | Check fatal events before accepting normal or timeout-recovered final messages. |
| Scan model prose for error strings | Broad text matching was considered for all stdout/final content. | Agent prose may discuss errors, quote fixtures, or contain the sandbox marker as task data, producing false positives and prompt-injection risk. | Parse JSONL structure and stderr only; never classify from model prose. |
| Treat every failed command as fatal | Any `command_execution` status of `failed` was considered an agent error. | Agents intentionally run failing tests and searches while diagnosing and can recover successfully. | A failed shell command is fatal only when its structured output carries the narrow infrastructure marker. |
| Add detection to each pipeline stage | Provider event parsing was placed near implementation/no-commit handling. | This duplicates provider semantics, misses other agent roles, and couples stages to Codex's schema. | Classify in the shared provider adapter, raise a neutral exception, and reuse existing orchestration error routing. |
| Handle only the zero-exit path | Structured classification was applied after normal communication but not on nonzero or timeout recovery. | The same infrastructure event can accompany a nonzero process exit, and a recovered final file can mask an earlier fatal event. | Apply one classifier consistently to normal, exceptional, and timeout-recovered completion routes. |
| Broaden sandbox permissions | A permissive sandbox fallback was considered as a way around nested macOS sandbox initialization failure. | It weakens the existing child sandbox and least-privilege contract and changes the security model. | Fail with an actionable diagnostic; run the outer loop outside the enclosing API sandbox instead. |
| Let the generic worker catch handle it | The typed provider failure fell into a broad exception boundary. | The result may lose a stable `agent_error` prefix or become indistinguishable from worker bugs. | Catch the neutral execution error explicitly before the generic handler and preserve bounded diagnostics. |
| Enumerate known fatal item types | The first implementation recognized only selected failed tool kinds. | A failed web-search item fell through to `None`, so later no-edit output could be classified as success. | Default every failed/declined completed item to fatal; allow only explicit, tested exceptions. |
| Treat every error item as fatal | The follow-up classifier rejected any completed error item. | Codex can emit a documented nonfatal app-server stream-lag notice and then complete successfully. | Match the exact prefix, suffix, and numeric count; leave every other error item fatal. |
| Treat host-plan selection as execution evidence | The remediation registered and selected the WorkerPool regression. | Review still lacked a passing receipt proving the error crossed the WorkerPool boundary on the reviewed SHA. | Keep NOGO until the host receipt shows that exact boundary test passing. |

## Results & Parameters

### Stable classifier parameters

| Parameter | Value | Contract |
|-----------|-------|----------|
| Nested sandbox marker | `sandbox_apply: Operation not permitted` | Case-insensitive exact substring match in stderr or failed command output. |
| Fatal event types | `error`, `turn.failed` | Always fatal when present as structured event types. |
| Fatal completed-item policy | Default fatal for status `failed` or `declined` | Applies to unknown and future item kinds as well as known tools. |
| Error-item exception | Exact stream-lag prefix + ASCII decimal count + ` events` suffix | Narrowly recognizes the documented nonfatal event; malformed lookalikes remain fatal. |
| Failed command policy | Marker-only | Ordinary failed commands remain recoverable agent activity. |
| Diagnostic prefix | `codex_tool_or_provider_failure:` | Bound the extracted detail (for example, to 300 characters) before returning it. |
| Worker error prefix | `agent_error:` | Lets existing stages reuse their provider-neutral error transition. |
| Permission fallback | None | Preserve the requested sandbox; never substitute `danger-full-access`. |

### Nested-sandbox diagnostic

```text
codex_nested_sandbox_unsupported: Codex could not initialize its child sandbox
(sandbox_apply: Operation not permitted). Run the outer automation loop outside
the enclosing API sandbox; the child sandbox permissions were not broadened.
```

### Verified acceptance checks

```bash
# Runtime classification and the recovered ordinary-command counterexample.
uv run pytest <runtime-tests> -k \
  'nested_sandbox or structured_fatal or stream_lag or recovered_command_failure' -q

# Provider-neutral worker result and fail-closed implementation-stage routing.
uv run pytest <worker-tests> <implementation-stage-tests> -k \
  'event_failure or tool_failure_with_no_diff' -q

# Existing permission, signing, lease, and exact-head contracts.
uv run pytest <runtime-tests> <review-scope-tests> <signing-tests> \
  <lease-tests> <merge-wait-tests> -q
```

Expected state after a fatal event plus a plausible no-diff final message:

```text
runtime: AgentExecutionError
worker:  JobResult(ok=False, error="agent_error: ...")
stage:   RETRY / agent_error
absent:  no_commits, skip-label mutation, commit/push completion, successful cleanup
kept:    worktree/branch reservation and existing safety contracts
```

### PR #2637 review and merge audit

| Event | Evidence |
|-------|----------|
| Initial review | Head `84f3ba59`; finite fatal-item allowlist rejected; NOGO added at `05:45:51Z`. |
| Follow-up review | Head `a0350eda`; exact WorkerPool passing receipt still missing, so NOGO remained. |
| Final review | Head `4daac9b4`; recoverable exceptions and executed WorkerPool boundary regression accepted. |
| Authorization | `state:implementation-go` added at `06:23:25Z`; NOGO removed at `06:23:27Z`. |
| Merge contract | Required-checks gate completed at `06:31:22Z`; conditional squash merge `5f10af3b` followed at `06:31:28Z`; native auto-merge was null. |

Related skills:

- `automation-529-overload-not-retried-classifier-gap` covers retryable quota/overload
  classification and exit-zero Claude error envelopes; it does not cover fatal Codex tool or
  sandbox events.
- `automation-agent-tool-scopes-least-privilege` covers allowed-tool and sandbox policy; this
  skill preserves that policy while making initialization failures explicit.
- `agent-background-task-failure-recovery` covers operator recovery after a silently failed
  background task; this skill prevents the silent-success state at the runtime boundary.

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| ProjectHephaestus | Issue #2634 / PR #2637 | Verified-ci on final head `4daac9b4a463fa3724db541288bced7a95be4690`. Reviews across three distinct heads kept NOGO until the default-fatal classifier, stream-lag exception, and executed WorkerPool receipt were complete; required checks then passed and conditional squash merge `5f10af3b03571679ab7a28cf1e3d93eee18dfe0a` followed. |
