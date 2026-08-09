---
name: planning-queue-priority-aging-dependency-safe-overlap-admission
description: "Plan starvation-resistant priority aging for a queue whose admission path combines dependency ordering, file-overlap serialization, and worker-cap checks. Use when: (1) repeatedly overlap-deferred work must gain priority, (2) aging must never violate dependency edges, (3) deferral age must survive selection without actual admission, or (4) warning thresholds need persistent visibility above the boundary."
category: architecture
date: 2026-07-20
version: "1.0.0"
user-invocable: false
verification: unverified
tags:
  - priority-aging
  - starvation-prevention
  - queue-admission
  - file-overlap
  - dependency-ordering
  - stable-sort
  - worker-cap
  - deferral-visibility
  - tdd-planning
---

# Planning Queue Priority Aging Without Breaking Dependencies or Overlap Serialization

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-07-20 |
| **Objective** | Add priority aging to a file-overlap admission gate so repeatedly deferred work gains dispatch priority without bypassing dependency ordering or allowing overlapping work to run together. |
| **Outcome** | A review-refined implementation plan identified the state location, ordering seam, reset point, warning boundary, and integration-test strategy. No production change was executed. |
| **Verification** | `unverified` — plan and source references only; no targeted test, lint run, implementation, or CI result was produced in this session. |

## When to Use

- A queue repeatedly chooses the same peer while another ready item is deferred because their planned files overlap.
- The queue already has a topological or dependency-ordering function whose edge guarantees must remain authoritative.
- An overlap selector must remain the single serialization authority, but its input order can express fairness among dependency-ready peers.
- Selection and actual admission are separate events because shutdown, per-repository limits, or global worker capacity can block a selected item.
- Operators need deferred work to remain visible after it crosses a warning threshold, not merely on the single crossing event.
- Tests need to prove the integration with the real overlap selector while controlling only its external file-plan lookup seam.

## Proposed Workflow

> **Warning:** This workflow has not been validated end-to-end. Treat it as a hypothesis until implementation tests and CI confirm it.

<!-- The repository validator requires the literal heading below. The workflow remains
     proposed because this skill's verification level is unverified. -->
## Verified Workflow

> **Warning:** This workflow has not been validated end-to-end. Treat it as a hypothesis until CI confirms.

### Quick Reference

```python
DEFERRALS_KEY = "file_overlap_deferrals"
WARNING_THRESHOLD = 10

# Age supplies ready-peer priority; dependency ordering remains authoritative.
infos.sort(
    key=lambda info: int(items[info.number].payload.get(DEFERRALS_KEY, 0)),
    reverse=True,
)
ordered = order_for_implementation(infos)

dispatch, deferred = select_non_overlapping(ordered, repo_of=repo_of)
for number in deferred:
    item = items[number]
    count = int(item.payload.get(DEFERRALS_KEY, 0)) + 1
    item.payload[DEFERRALS_KEY] = count
    (logger.warning if count > WARNING_THRESHOLD else logger.info)(
        "implementation #%s deferred (file overlap); deferrals=%s threshold=%s",
        number,
        count,
        WARNING_THRESHOLD,
    )

for item in dispatch_items:
    if shutdown.is_set() or not admit(item):
        continue
    item.payload.pop(DEFERRALS_KEY, None)  # Clear only on actual admission.
    run_item(item)
```

### Detailed Steps

1. **Map queue entries back to their lifecycle state.** Build the issue-number-to-work-item map at the coordinator drain boundary. Store the consecutive overlap-deferral count in the existing coordinator-owned, in-memory payload; avoid a persistent schema when fairness state dies with the process and is cleared on dispatch.
2. **Age before dependency ordering.** Stable-sort issue metadata by descending deferral count, then pass that order to the existing dependency-aware ordering function. This is safe only when that function preserves input priority among currently ready peers while still enforcing every in-queue dependency edge.
3. **Keep the overlap selector unchanged.** Let the existing selector remain the authority that prevents overlapping plans from being selected in one drain round. Aging changes which dependency-ready peer reaches it first; it does not weaken serialization.
4. **Increment only real overlap deferrals.** Update the count only for issue numbers returned in the selector's `deferred` result. Do not age ambiguous items, shutdown-skipped items, or selected items blocked later by capacity.
5. **Separate selection from admission.** A selected item can still fail the repository/global worker-cap gate. Retain its age in that case. Clear the payload key only after the admission predicate succeeds and immediately before dispatch.
6. **Define the visibility boundary mathematically.** For threshold `10`, resulting counts `1..10` log at `INFO`; every resulting count `>10` logs at `WARNING`. Choose the logger on every deferral, rather than emitting a warning only when the count first crosses the threshold.
7. **Write regression tests before production changes.** Run the focused tests and observe failures for absent age state, absent escalation, and absent aged-priority behavior before implementing the constants and drain logic.
8. **Exercise the production selector.** Mock only the planned-file fetch so two issues return the same path. In round one, fill the worker cap after overlap selection: the preferred issue is selected but cannot dispatch, while its peer is genuinely overlap-deferred and ages. Open capacity in round two and assert the aged peer is dispatched first.
9. **Pin dependency safety independently.** Give a highly aged issue a dependency on its peer, record the order passed to the overlap selector, and assert the dependency still comes first. This proves aging is ready-peer priority rather than a post-topology reorder.
10. **Test the threshold as a boundary and an invariant.** Parameterize starting counts `9`, `10`, and `11`; after one deferral, assert counts `10`, `11`, and `12` log at `INFO`, `WARNING`, and `WARNING` respectively.
11. **Verify narrowly, then broadly.** Run the focused aging, dependency, overlap, and logging tests first; then the complete pipeline unit suite and static checks for the touched files.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Reorder after topological sorting | Apply a final age sort to the dependency-ordered issue list | A post-topology sort can place an aged dependent before its prerequisite | Supply age as stable input priority before dependency ordering; never override the dependency result afterward |
| Reset on overlap selection | Clear age as soon as an issue appears in the selector's dispatch list | Selection is not dispatch: worker or repository capacity can still reject the item, erasing fairness state without progress | Clear age only after the actual admission predicate succeeds |
| Age every item not run | Increment all queue entries left behind after a drain | Items can remain for ambiguity, shutdown, or capacity reasons unrelated to file overlap, corrupting the meaning of the counter | Increment only the selector's explicit overlap-deferred set |
| Modify the overlap selector to implement fairness | Mix age tracking and lifecycle mutation into the serialization function | This couples coordinator-owned state to a pure selection mechanism and risks weakening the single overlap authority | Keep selection pure; prepare aged input and record returned deferrals in the coordinator |
| Mock the selector in the starvation regression | Return a hand-authored dispatch/deferred tuple | The test proves coordinator bookkeeping but not that identical planned paths flow through the real selector | Mock only planned-file lookup and use genuinely overlapping paths |
| Write production code before regression tests | Add aging logic, then add tests | This loses the required RED evidence and can produce tests that merely mirror the implementation | Add the three focused tests and run them failing before production edits |
| Warn only at the first crossing | Emit `WARNING` only when the new count equals threshold plus one | Counts above the first crossing can fall back to `INFO`, hiding persistently starved work | Use `count > threshold` on every deferral |
| Test only the crossing value | Cover resulting count `11` but not `10` or `12` | The test cannot distinguish `>=` from `>` and cannot prove warnings persist | Cover below/at boundary, first value above, and a later value above |
| Persist age in a new schema | Add durable storage for a coordinator-local scheduling hint | The state is process-local, consecutive, and cleared on successful dispatch; persistence adds migration and cleanup without a requirement | Reuse the existing in-memory work-item payload |

## Results & Parameters

**Verification level: `unverified`.** The source-informed plan was reviewed and tightened, but none of the implementation or verification commands below ran in this session.

**State and boundary parameters:**

| Parameter | Value | Semantics |
|-----------|-------|-----------|
| Payload key | `file_overlap_deferrals` | Consecutive deferrals returned by the file-overlap selector |
| Warning threshold | `10` | Counts strictly greater than this value use `WARNING` |
| Reset event | Successful admission immediately before dispatch | Selection without capacity does not reset age |
| Priority location | Stable descending sort before dependency ordering | Affects only dependency-ready peer preference |
| Serialization authority | Existing non-overlap selector | Aging does not permit overlapping dispatch |

**Logging boundary:**

| Starting count | Resulting count | Expected level |
|----------------|-----------------|----------------|
| 9 | 10 | `INFO` |
| 10 | 11 | `WARNING` |
| 11 | 12 | `WARNING` |

**Proposed verification commands:**

```bash
<package-manager> pytest <coordinator-test-path> \
  -k "priority_aging or warning_threshold or dependency_order" -v

<package-manager> pytest <coordinator-test-path> <admission-test-path> \
  -k "dependency_order or non_overlapping_selection" -v

<package-manager> pytest <pipeline-test-path> -q

<package-manager> ruff check <coordinator-source-path> <coordinator-test-path>
```

**Rollback:** remove the coordinator constants, stable age sort, overlap-deferral payload updates, and associated tests. Because the payload key is process-memory-only and cleared on dispatch, no migration or persistent cleanup is required.

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| ProjectHephaestus | Implementation-queue priority-aging plan | [Session notes](./planning-queue-priority-aging-dependency-safe-overlap-admission.notes.md); implementation, local tests, and CI pending |
