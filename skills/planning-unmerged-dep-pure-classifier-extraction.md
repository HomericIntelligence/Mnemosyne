---
name: planning-unmerged-dep-pure-classifier-extraction
description: "Plan a stage against an unmerged dependency while extracting a pure classifier from a blocking poll loop. Use when epic prose is the temporary interface, a coordinator must timer-park instead of sleep, overloaded sentinels need separation, or wall-clock budgets risk becoming poll-count budgets."
category: architecture
date: 2026-07-04
version: "2.0.0"
license: BSD-3-Clause
user-invocable: false
verification: unverified
history: planning-unmerged-dep-pure-classifier-extraction.history
tags:
  - planning
  - unmerged-dependency
  - pure-classifier
  - non-blocking-poll
  - timer-heap
  - sentinel-separation
  - compatibility-probe
  - state-machine
---

# Planning an Unmerged Dependency and Pure Classifier Extraction

## Overview

Two risks interact when a pipeline stage depends on code that has not landed: the plan cannot know
the real stage API, and moving a blocking poll loop into a single-threaded coordinator can freeze
all work. Use the approved dependency contract only as a temporary specification, begin
implementation with a compatibility probe, and extract only the data classification—not fetching,
sleeping, or deadline ownership—into a cycle-free leaf.

This is an unimplemented planning artifact from ProjectHephaestus issue #1816. Evidence and source
links are in
[planning-unmerged-dep-pure-classifier-extraction.notes.md](planning-unmerged-dep-pure-classifier-extraction.notes.md),
and the complete prior version is in
[planning-unmerged-dep-pure-classifier-extraction.history](planning-unmerged-dep-pure-classifier-extraction.history).

## When to Use

- Issue N depends on unmerged issue N-1 and its package, branch, or PR is absent.
- The approved epic body is temporarily the only interface specification.
- A proposed stage contains `sleep` or a polling loop in a single-threaded coordinator.
- A legacy helper returns one sentinel for no checks, pending work, and timeout.
- A pure `list[dict]` to enum classifier can be separated from GitHub I/O.
- A wall-clock deadline risks being replaced with a number of timer-park cycles.
- A proposed module imports private symbols from a god module and may create a cycle.
- `on_job_done` or another completion transition is left as a stub.

## Verified Workflow

The workflow is proposed and remains unverified; the required heading does not imply execution.

### 1. Prove the dependency is unmerged

```bash
test -d src/package/pipeline
git branch -a --contains HEAD | rg 'dependency-branch'
gh pr list --repo "$REPO" --state all --search 'issue-number'
```

Record the observations. Only after source, branch, and PR discovery confirm absence should the plan
use an epic's frozen contract. Label every borrowed symbol as assumed and cite its dependency issue.

### 2. Make compatibility probing implementation step one

After the dependency merges, read the real modules before authoring stage code:

```bash
rg -n 'class (WorkItem|Stage|StageOutcome|AgentJob)|ROUTES|fail_routes' src/package/pipeline
rg -n 'def (retry|advance|fail_back)|attempts|state' src/package/pipeline
rg -n 'class (FakeGitHub|FakeWorkerPool)' tests
```

Pin constructor signatures, enum members, context methods, route keys, budget semantics, work-item
fields, and available fakes. Any mismatch requires revising the plan, not guessing an adapter.

### 3. Separate pure classification from effects

The classifier takes already-fetched check data and returns a total enum:

```python
class CiConclusion(Enum):
    GREEN = auto()
    FAILING = auto()
    PENDING = auto()
    NO_CHECKS = auto()


def classify_ci_state(checks: list[dict[str, object]]) -> CiConclusion:
    if not checks:
        return CiConclusion.NO_CHECKS
    conclusions = {check.get("conclusion") for check in checks}
    if conclusions <= {"success", "skipped", "neutral"}:
        return CiConclusion.GREEN
    if conclusions & {"failure", "cancelled", "timed_out", "action_required"}:
        return CiConclusion.FAILING
    return CiConclusion.PENDING
```

Keep repository fetches, `gh` calls, sleep/backoff, logging, and mutation in the caller. Passing a
PR number to the classifier makes it an I/O wrapper rather than a pure decision seam.

### 4. Place the classifier in a cycle-free leaf

Prefer the module that already owns the legacy loop or a public leaf that already represents check
state. Confirm the new stage imports from that leaf and the leaf never imports the stage. Do not
import a god-module-private helper merely because it is textually nearby.

### 5. Uncollapse only semantically distinct outcomes

`NO_CHECKS` can mean successful absence and advance. `PENDING` means park and revisit. A coordinator
deadline expiry is not classifier input; it is scheduler state. Keep a single sentinel only when
the caller truly assigns one meaning to it.

### 6. Preserve the wall-clock deadline

Moving from a blocking loop to timer parking changes where elapsed time lives. Store a monotonic
start/deadline on the durable work item and compute remaining time after each wake:

```python
remaining = deadline_monotonic - monotonic()
if remaining <= 0:
    return StageOutcome.timeout()
delay = min(next_backoff, remaining)
return StageOutcome.park_for(delay)
```

Do not replace a 1,800-second bound with `N` attempts unless a product decision explicitly defines
the new maximum. Backoff windows do not sum to a stable wall-clock duration when jobs and queue
delays occur between polls.

### 7. Specify every completion transition

`on_job_done` is the state-machine design, not boilerplate. Enumerate result and state combinations:
success, retryable failure, terminal failure, stale completion, duplicate completion, cancellation,
and budget/deadline expiry. For each, state the work-item mutation, route, persistence order, and
whether a new job or timer is scheduled.

### 8. Verify legacy behavior at the correct seam

Refactor the existing poll helper to call the classifier so both paths share semantics. Tests that
patch the whole helper prove only its caller seam, not the new classifier. Add table-driven
classifier tests and stage-transition tests. Copy legacy scenario rows when both old and new paths
must remain tested; do not silently move them.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --- | --- | --- | --- |
| 1 | Write stage imports from epic prose | Unmerged dependency may ship different APIs | Probe merged source before implementation |
| 2 | Move the entire sleep loop into the stage | Single-threaded coordinator blocks all work | Extract pure classification and timer-park |
| 3 | Let classifier fetch by PR number | Couples policy to GitHub I/O and sleep seams | Accept already-fetched data |
| 4 | Keep one `None` for no checks and pending | Caller cannot choose advance versus park | Use explicit enum outcomes when meanings differ |
| 5 | Replace wall-clock timeout with poll count | Queue and backoff time change the bound | Persist a monotonic deadline/elapsed budget |
| 6 | Leave `on_job_done` as a stub | State, retry, and durability semantics remain unspecified | Enumerate every completion transition |
| 7 | Import a private god-module classifier | Creates a likely stage-to-orchestrator cycle | Use an existing public leaf or cycle-free owner |
| 8 | Cite a fully mocked legacy helper test | Test never executes the classifier | Add direct classifier and transition coverage |

## Results & Parameters

- Source planning bound: issue #1816, epic #1809, dependency #1815.
- Legacy wall-clock maximum observed in planning: `HEPH_PR_MERGE_MAX_WAIT=1800` seconds.
- Classifier contract: already-fetched checks in; `GREEN`, `FAILING`, `PENDING`, or `NO_CHECKS` out.
- Scheduler owns monotonic deadline, backoff, timer heap, retry budgets, and timeout.
- Implementation step one revalidates every assumed type, method, route, field, budget, and fake.
- Acceptance requires focused classifier/transition tests and the full affected pipeline suite.

## Evidence Boundary

Repository reads during issue #1816 planning confirmed absence and legacy anchors, but the proposed
pipeline API, classifier extraction, timer parking, and transition design were never implemented or
tested. Keep `verification: unverified` until linked implementation evidence exists.
