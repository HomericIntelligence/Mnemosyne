# Pytest Async Mock Isolation Patterns — Notes

## Case index

| Case | Source | Verification | Disposition |
| --- | --- | --- | --- |
| Process-wide sleep mock caused OOM/hang | [ProjectHephaestus PR #412](https://github.com/HomericIntelligence/ProjectHephaestus/pull/412) | `verified-ci`: 113 tests passed after fix | Retained as patch-the-wait-boundary rule |
| Patch target became stale after module reload | [ProjectHephaestus PR #644](https://github.com/HomericIntelligence/ProjectHephaestus/pull/644) | `verified-ci`: full unit suite passed | Retained as string-patch rule |
| Stateful async HTTP fault fixture | [ProjectTelemachy issue #48](https://github.com/HomericIntelligence/ProjectTelemachy/issues/48) | Verified in recorded integration suite | Retained as one-context ordered-side-effect pattern |
| Chaos mocks needed observable side effects | [ProjectCharybdis PR #88](https://github.com/HomericIntelligence/ProjectCharybdis/pull/88) | Verified in chaos integration tests | Retained as fidelity rule |
| Executor worker outlived test and reopened shared breaker | [ProjectHephaestus PR #1060](https://github.com/HomericIntelligence/ProjectHephaestus/pull/1060) | `verified-ci` | Retained as stop-producers, not fixture-reset-only rule |
| Empty input activated failing-PR and bot discovery branches | [ProjectHephaestus PR #1060](https://github.com/HomericIntelligence/ProjectHephaestus/pull/1060) | `verified-ci` | Retained as input-conditional call-graph rule |

## Isolation checklist

- Determine the exact lookup path used by the unit under test.
- Inventory tasks, threads, subprocesses, HTTP mocks, singleton state, caches, and environment
  mutations created by the test.
- For autouse reset fixtures, import lazily and reset before and after.
- Await or join producers before teardown; a state reset cannot defend against a later writer.
- Configure mock return values to satisfy the real protocol (`WorkerResult`, context manager,
  awaitable, response object).
- For optional external CLIs, reproduce CI by hiding the executable and assert the intended gate.
- Run the exact empty/non-empty and option combinations that change the call graph.

## Timeout interpretation

| Symptom | Likely boundary to inspect |
| --- | --- |
| Stack ends in epoll/select | Pending event/task or ineffective signal timeout |
| CPU/memory rises rapidly | Sleep/wait mock removed retry pacing |
| Only suite order fails | Singleton, cache, background worker, or loop-bound object leak |
| Calls missing after reload | Object patch targets stale module instance |
| FastAPI still uses real settings | Dependency callable captured before patch |
| Real GitHub call appears only for empty list | Input-conditional discovery branch was not mocked |

## Evidence boundary

The indexed cases carry differing levels of integration evidence. Preserve their case-specific
status; `verified-ci` at skill level does not imply that every framework permutation has been
tested.
