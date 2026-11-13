---
name: control-plane-allocation-move-inventory
license: BSD-3-Clause
description: "Inventory everything that lives inside an old scheduler allocation before you move a gateway or operator to a new one. Use when: (1) a control-plane service is moved to a new scheduler allocation, (2) an operator process runs the move command as a step of the old allocation, (3) tunnels, claims, public records, or keepers belong to the old allocation, or (4) a new allocation cannot publish because the old record remains."
category: architecture
date: 2026-11-13
version: "1.0.0"
user-invocable: false
verification: verified-local
tags: [control-plane, scheduler, allocation, migration, tunnel, discovery-record, keeper, operator]
---

# Control-Plane Allocation Move: Inventory First

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-13 |
| **Objective** | Move a gateway or operator to a new allocation with no piece left behind. |
| **Outcome** | Operational. The operator ran as a step of the old allocation and died with it. The old public record blocked the new publish, the database tunnel was gone so key requests stayed queued, and a person repaired each piece. |

## When to Use

- A service is moved to a new scheduler allocation (planned or after expiry).
- Any helper runs as a step or child of the old allocation.
- The service publishes a discovery record, holds claims, or needs a network forward.

## Verified Workflow

### Quick Reference

```text
Before: list every item inside the old allocation -> owner + start step in the new one.
After : old record retired | new record published | tunnel listening
        | operator heartbeat fresh | keeper restarts each piece
```

### Suggested Approach

1. List all items that live inside the old allocation: the operator process (and the process that runs the move command), network forwards or tunnels, claims and leases, public discovery records, and keepers or supervisors.
2. Give each item one owner and one explicit start step in the new allocation. An item with no start step is a defect.
3. Do not run the operator as a step of the allocation it replaces. Run it outside, or start a new one in the new allocation.
4. Make the new publish able to replace a stale old record (compare generation or allocation id), or retire the old record in the move.
5. After the move, check each item by a positive signal: record state, tunnel listening, heartbeat age, keeper status. A queue that does not drain is a symptom of a missing tunnel or operator.
6. A keeper must restart each piece again if it dies. Do not rely on a person.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Operator as allocation step | The move command ran inside the old allocation. | The operator died when the old allocation ended. | Own the operator outside the old allocation. |
| Publish over an old record | The new service published while the old record stayed. | The old record blocked the publish. | Retire or supersede the old record. |
| Move without a tunnel step | Only the service was started in the new allocation. | The database tunnel was gone; requests stayed queued. | Every forward needs a start step. |

## Results & Parameters

```yaml
move_checklist:
  inventory: [operator, tunnels, claims, discovery_records, keepers]
  per_item: [owner, start_step_in_new_allocation]
  verify: [old_record_retired, new_record_published, tunnel_listening, heartbeat_fresh, keeper_active]
```

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Project-neutral scheduler-backed gateway | Release and deployment session | Each piece needed a manual repair after a move. |

## References

- [Scheduler service replacement identity continuity](scheduler-service-replacement-identity-continuity.md)
- [Cutover: stop the previous release daemon](cutover-stop-previous-release-daemon.md)
