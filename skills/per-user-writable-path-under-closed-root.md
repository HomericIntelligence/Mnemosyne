---
name: per-user-writable-path-under-closed-root
description: "Prove an end-to-end write and read path for a per-user directory before a plan claims a user can reach it. Walk every ancestor and apply the access class that supplies the bit. Use when (1) a plan or issue derives a user-writable path below a root that a service owns, (2) a drop directory is copied from an existing reachable pattern, (3) a service account must create a per-user directory for an ordinary user, or (4) an API reports or lists entries of a directory that ordinary users cannot enumerate."
category: architecture
date: 2026-11-07
version: "1.0.0"
user-invocable: false
tags:
  - permissions
  - posix-modes
  - traverse
  - drop-directory
  - least-privilege
  - plan-review
  - setgid
  - sticky-bit
  - ownership
---

# Prove the Whole Path to a Per-User Writable Directory

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-07 |
| **Objective** | Stop a design from declaring a user-writable path that no ordinary user can reach, and stop a service from creating a directory that its user cannot use. |
| **Outcome** | Successful. Three review rounds found the same class of defect in a plan: a copied drop directory behind closed ancestors, then a service-created leaf that the user cannot write or remove. The third round stated one mode per directory and one creator per directory and removed both defects. |

## When to Use

- A plan or an issue derives a per-user path below a root that a service account owns, for example a path of the form root, context, a shared drop directory, then a user leaf.
- You copy a reachable pattern, such as a requester drop directory, into a new place.
- A service process must create a directory that an ordinary user will use.
- An API response, a status report, or a readiness check would list names from a directory that ordinary users cannot enumerate.

## Verified Workflow

### Quick Reference

```text
For each directory on the path from the anchor to the file:
  1. Write the owner, the group, the mode, and the access class that
     supplies the needed bit (owner, group, or other).
  2. Confirm the reader holds that class: the user is not the owner and
     usually is not in the service group.
  3. Require traverse (x) on each ancestor and the specific bit only on
     the final directory. Do not grant read (r) or write (w) on ancestors.
  4. Check every verifier that pins the mode, not only the creation call.
For each directory on the path, name exactly one creator.
Copy the whole chain, not only the last directory.
```

### Suggested Approach

1. Draw the chain from the anchor to the file, one row for each directory. For each row, give the owner, the group, the mode, the class that supplies access, and the identity that holds that class. A row with no qualified reader is a defect, not a detail.
2. Apply the class rule. An ordinary user is the owner only of its own directory. It is not in the administrator or service group. Access to a service-owned ancestor comes only from the other class, so that class needs `x`. A mode such as `0o750` gives the other class nothing, and `0o750` on every ancestor, including one named an "administrator-traverse" form, closes the path.
3. Keep ancestors traverse-only. `0o711`-form and `0o751`-form ancestors let the user pass and do not let it list or create. Put `w` and the set-group-ID and sticky bits only on the shared drop directory. That directory uses the `0o3733` form: other class `w+x`, set-group-ID so each new entry takes the service group, and sticky so an entry owner can remove only its own entry.
4. Check every consumer of the mode. A mode is often pinned in more than one place: a loader predicate (`mode != 0o2750`), a verifier predicate (`mode & 0o777 != 0o750`), a declared repair mode, and a policy table row. A one-bit change that passes one predicate can fail another, or be repaired back to the old form. Name each predicate in the plan and change them together.
5. Name one creator for each directory. A service account without `CAP_CHOWN` that creates a user leaf produces a service-owned leaf. Such a leaf gives the user no rights, and the sticky parent stops the user from removing it, so the leaf is permanently unusable. Let the user create its own leaf under the writable drop directory. Let the operator create it as the user with `install -d -m 0750 -o USER -g GROUP`. A missing leaf is a client-coded refusal that names the creation command.
6. Check the final file, not only the directories. The service reads the file through the group class. A user file with mode `0o600` belongs to the user's primary group, so the service cannot read it. Require group read, and document the umask and the `chmod`.
7. Do not publish a name list from a directory that the other class cannot enumerate. A drop directory without other-read hides its entries on purpose. A readiness or status response that lists them gives any caller the set of account names.

### Failure Shapes to Recognize

- A plan copies a `0o3733` drop directory below a `0o2750` and `0o750` chain. The drop directory is correct and unreachable, because the other class cannot traverse the ancestors.
- Two sentences of one plan state two modes for the same path, such as `0o2750` and then `0o750`. Neither candidate admits the other class.
- A service creates the user leaf on first use. The first submission makes the leaf permanent and unusable for the user.
- A readiness report credits ordinary users with listing a drop directory that it keeps unlistable.
- A test pins the unusable result, such as a service-owned leaf, as a contract.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | --------------- |
| Copy only the drop directory | Reuse the existing writable directory mode in a new place. | The ancestors stayed closed to the other class. | Copy the whole chain, or prove each ancestor. |
| Widen the deployment container to `0o750` | Set the shared parent to the declared root mode. | `0o750` is the group class only. The other class gets no bit. | Give the other class `x` explicitly. |
| Create the leaf as the service | Create the leaf on first use to avoid an operator step. | The leaf is service-owned, and the sticky parent stops the user from removing it. | Give each directory one creator that holds the owner class. |
| List leaf names in readiness | Assume that the user can enumerate its own leaf. | The drop directory hides its entries by design. | Report presence and mode only. |

## Results & Parameters

### Configuration

```text
anchor root        service : administrators   0o2751   other x
deployment child   service : administrators   0o751    other x
drop directory     service : administrators   0o3733   setgid, sticky
user leaf          user    : administrators   0o2750   owner rwx, group r-x
user file          user    : user primary     0o640    group r
umask for the user: 027
```

### Expected Output

- Each directory on the path has one mode and one creator.
- An ordinary user can create its leaf, write its file, and read its own data.
- A submitted path under another user's leaf is refused before any filesystem call.
- A missing leaf is refused with a message that names the creation command.
- The readiness report names no leaf.

## Verified On

| Project | Context | Details |
| --------- | --------- | ------- |
| An internal platform repository | Four plan revisions on a batch-input path issue, 2026-11 | Three review rounds used the checks above. The first found the closed ancestors, the second found the service-owned leaf, and the third made one mode and one creator per directory. No code was merged in the session. See [notes](per-user-writable-path-under-closed-root.notes.md). |

## References

- [Related: repair the leaf a call owns, validate its ancestors](directory-repair-leaf-only.md)
- [Related: plan review with a strict rubric](plan-review-strict-rubric-iteration.md)
- [POSIX access control: permission bits and the sticky bit](https://pubs.opengroup.org/onlinepubs/9699919799/basedefs/V1_chap04.html)