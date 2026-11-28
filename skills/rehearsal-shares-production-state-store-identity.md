---
name: rehearsal-shares-production-state-store-identity
license: BSD-3-Clause
description: "Handle a name or record collision when a rehearsal deployment shares a state store with production. Use when: (1) a test registration is refused because a live record with the same name already exists, (2) a status or list command on the rehearsal deployment shows production records, (3) the rehearsal service logs errors about records it does not own, or (4) the only fast fix seems to be deleting a record that production created."
category: architecture
date: 2026-11-28
version: "1.0.0"
user-invocable: false
verification: verified-local
tags:
  - rehearsal
  - shared-state
  - identity
  - name-collision
  - production-safety
  - deregister
  - namespacing
---

# Rehearsal Shares a Production State Store

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-28 |
| **Objective** | Test a feature on a rehearsal deployment that shares its state store with production, without changing or removing a production record. |
| **Outcome** | Successful. The collision was treated as a stop. The test then used a different owner identity, and a defect report asked for per-deployment scoping. No production record changed. |
| **Verification** | verified-local on a shared cluster. The rehearsal and production deployments used one registry database. |

## When to Use

- A test request is refused with a message such as "a live registration already holds this name with different content".
- A list or status command, run against the rehearsal deployment, shows records that production owns. The command is not scoped to the deployment.
- The rehearsal service reads the shared store and logs one error for each production record that it cannot act on. Treat a high count as evidence of the same collision.
- A cleanup command (deregister, delete, cancel) would clear the refusal, but it would act on a record that production created.
- Both deployments use the same account for the service, so a record cannot be told apart by owner.

## Verified Workflow

### Quick Reference

```bash
# 1. Read the refusal. Find the owner and name of the record that blocks you.
<tool> status                    # note: on a shared store it can list production records

# 2. Decide who owns the record. If production created it: do not delete it.
# 3. Pick a distinct identity for the test (another user, or a name suffix if supported).
# 4. Re-run the test as that identity. File one defect for the missing per-deployment scope.
```

### Suggested Approach

1. Stop at the refusal. A refusal on a name that a live record holds is a protection. It is not a request to clean up.
2. Identify the owner of the blocking record from the record fields and the job or process behind it. A running job or an active lease means that production is using it.
3. Do not run a cleanup command on a record that you did not create. A deregister on a production record ends production capacity. A rehearsal grant does not cover that action. Ask the owner, and name the exact records, only if they decide to remove one.
4. Prefer a distinct identity. A different user for the test, or a deployment suffix when the product has one, avoids the name. Check that the identity can get a credential on the rehearsal deployment before you rely on it.
5. Check the shared limits before you add load. A production job that already waits on a quota will compete with the test.
6. Record the cross-deployment effect as one defect. Ask for records that carry the deployment, status and cleanup commands that act on one deployment, and records without a deployment that count as production. Add the supporting log evidence (the count of ignored production records) to that same report.
7. Keep delegated agents inside this rule. Tell each one that production records are read-only for the test, and that a cleanup needs an owner decision.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Re-run the same request | Registered again with the same owner and the same name on the rehearsal deployment. | The shared store still held a live production record with that name, so the service refused it. | A name that production holds blocks the rehearsal, whatever the deployment flag says. |
| Deregister the blocking record | Considered ending the matching record. | The command acts on the shared store. It would have ended production capacity. | Do not use cleanup to clear a collision with a record you do not own. |
| Read the status as the rehearsal view | Treated the status list as the rehearsal deployment's records. | The command was not scoped by deployment and listed production records. | On a shared store, check the scope of each list command before you act on its output. |

## Results & Parameters

### Configuration

```text
Rule: a record that production created is read-only for a rehearsal test.
Allowed fixes: distinct identity (user or suffix); owner-named removal only after an explicit owner decision.
Report: one defect for per-deployment scope, with the log evidence added to it.
```

### Expected Output

- The test runs under a distinct identity and creates its own record.
- No production record is changed or removed.
- One defect exists for per-deployment scoping of records, status, and cleanup.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Shared GPU cluster, donation feature rehearsal | A rehearsal deployment and production shared one registry. A registration by the service account was refused because production already held the name. | The owner chose a different user for the test. The rehearsal service also logged 77 errors for production records that it did not own. |

## References

- [Cross-swarm scheduler resource collision](cross-swarm-slurm-resource-collision.md): two sessions competing for one scheduler cap; this entry covers a shared state store between deployments.
