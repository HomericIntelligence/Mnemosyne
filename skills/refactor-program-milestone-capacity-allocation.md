---
name: refactor-program-milestone-capacity-allocation
description: "Allocate a multi-phase refactor across existing release milestones by theme fit and open-issue load. Use when a phase-per-milestone plan would overload a release, when deep splits must be deferred before GA, or when a refactor must share a board with an active release train."
category: tooling
date: 2026-11-17
version: "1.0.0"
user-invocable: false
verification: unverified
tags:
  - refactor
  - milestones
  - release-planning
  - capacity
  - modularization
  - issue-queue
  - deferral
  - ga-risk
---

# Refactor Program Milestone Capacity Allocation

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-17 |
| **Objective** | Put each phase of a multi-phase refactor in a release milestone that has a matching theme and enough capacity. |
| **Outcome** | Operational. The rule produced a backlog across six release milestones and release-candidate milestones in one planning session. No implementation has validated the schedule. |
| **Verification** | unverified. The rule was applied in one planning session. Execution evidence is not available. |

A refactor program usually does not get its own release train. It must fit the milestones that already exist. Allocate each slice by theme fit and open-issue load. Do not assign one phase to each milestone in dependency order.

## When to Use

Use this skill when these conditions apply:

- A refactor or modularization program has 10 or more reviewable slices.
- The repository already has release milestones with themes, due dates, and open items.
- A one-phase-per-milestone mapping would put a high-risk slice in a short pre-GA window.
- Some slices are low-risk moves and some are deep splits of large modules.
- The program must share the board with an active release train.

Do not use this skill for these cases:

- Audit remediation waves. Use [audit epic sequencing and milestone attachment](audit-epic-sequencing-milestone-attachment.md).
- A board realignment after a schedule change. Use [GitHub release-board realignment](github-release-board-realignment.md).
- A single pull request or a refactor that fits one milestone.

## Verified Workflow

### Quick Reference

```bash
gh api "repos/{owner}/{repo}/milestones?state=open" --paginate \
  --jq '.[] | "\(.title)\t\(.due_on)\t\(.open_issues)"'
```

Decision rule: select the milestone by theme fit first. Then compare the open-issue load. Cap the refactor pull request count for each milestone. Defer deep splits to release-candidate or later milestones.

### Suggested Approach

1. **Read the milestone board.** Record each milestone title, theme, due date, open-issue count, and existing release epic. The theme and the load are both evidence.

2. **Classify each slice by risk and blast radius.** Use these classes:
   - guardrail or measurement;
   - low-risk package merge;
   - dependency inversion or cycle break;
   - domain consolidation;
   - hot-file split;
   - shim removal and strict enforcement.

3. **Match the slice to a milestone theme.** Put guardrails in a CI or test-hygiene milestone. Put low-risk merges in a documentation or architecture milestone, or in the milestone with the lowest load. Put domain merges in the milestone that names the domain. Put the cycle break in an open-design-decisions milestone. Put the first hot-file splits in the pre-GA milestone.

4. **Use open-issue load as capacity evidence.** A milestone with 50 to 70 open items gets 1 to 2 refactor pull requests. A milestone with 10 to 29 open items gets 3 to 5. A due date alone does not show capacity.

5. **Cap the program per milestone.** Do not fill a milestone with refactor work. Leave room for its existing issues. A cap of 1 to 2 slices is usually correct for a loaded milestone.

6. **Do not put the highest-risk slice last.** A cycle break or a deep module split days before GA has a large blast radius and little recovery time. Put the cycle break in the design milestone. Defer deep splits to release-candidate milestones or later.

7. **Create separate issues for deferred work.** Assign each deferred slice to the deferral milestone. Do not bury a deferral in a comment or in the parent epic.

8. **Record the map in the parent epic and in each child issue.** Each child issue states its milestone, its dependencies, and its cut criteria. The parent epic lists the full map.

9. **Recheck the same metrics at each milestone cut.** Use the import-graph report, the largest-file size, the root package size, and the boundary-violation count. Do not schedule the next phase from stale numbers.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| ------- | ---------------- | --------------- | --------------- |
| One phase per milestone | Assigned phases in dependency order to consecutive milestones. | The mapping ignored theme fit and existing load. It put the highest-risk work in the shortest pre-GA window. | Allocate by theme and load first. Order by dependency second. |
| Dependency-only ordering | Sorted all slices only by technical dependency. | A loaded milestone received more work while a lightly loaded milestone stayed idle. | Use the open-issue count as capacity evidence. |
| Deep splits before GA | Put god-class and large-store splits in the pre-GA milestone. | A deep split near GA has a large blast radius and little recovery time. | Defer deep splits to release-candidate milestones or later. |
| New milestone for the refactor | Created a separate milestone for the program. | It fragmented tracking and hid the work from the release plan. | Use the existing release train. Link the child issues to the release epics. |

## Results & Parameters

### Configuration

Suggested refactor pull request budget:

| Milestone condition | Suggested budget |
| ------------------- | ---------------- |
| 50 to 70 open items | 1 to 2 |
| 30 to 49 open items | 2 to 3 |
| 10 to 29 open items | 3 to 5 |
| Fewer than 10 open items | 4 to 5, if the theme fits |

Deferral rule: put a slice in a release-candidate milestone or later when it changes a module above 5,000 lines, a schema, or a process entry point. The exception is a slice that removes a GA blocker.

Milestone theme map:

| Slice type | Preferred milestone theme |
| ---------- | ------------------------- |
| Guardrail or measurement | CI or test hygiene |
| Low-risk package merge | Documentation, architecture, or the lowest-load milestone |
| Domain consolidation | The milestone that names the domain |
| Cycle break or dependency inversion | Open design decisions |
| First hot-file split | Pre-GA catch-all |
| Remaining hot-file split | Release candidate 1 or 2 |
| Schema or process split | Release candidate 1 or 2 |
| Shim removal and strict gate | Final pre-GA or release candidate |

### Expected Output

- One parent epic with the milestone map.
- One child issue for each slice, assigned to the selected milestone.
- A separate issue for each deferred slice, assigned to the deferral milestone.
- A per-milestone cap that leaves capacity for existing work.
- A cut checklist with cycle count, largest file, root package LOC, and boundary violations.

## Verified On

| Project | Context | Details |
| ------- | ------- | ------- |
| A private Python service repository | Planning session, 2026-11-17 | The rule produced a backlog across six release milestones and release-candidate or GA milestones. No implementation merged. The evidence is planning-only. |

## References

- [Audit epic sequencing and milestone attachment](audit-epic-sequencing-milestone-attachment.md)
- [Automation loop backlog cost scaling](automation-loop-backlog-cost-scaling.md)
- [GitHub release-board realignment](github-release-board-realignment.md)
- [God-package shim-first decomposition](automation-god-package-shim-first-decomposition.md)
- [Python module decomposition and refactor patterns](python-module-decomposition-and-refactor-patterns.md)