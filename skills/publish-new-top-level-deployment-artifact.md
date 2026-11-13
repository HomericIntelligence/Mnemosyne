---
name: publish-new-top-level-deployment-artifact
description: "Add a new top-level file to a live public deployment root. Use when a validator enumerates the deployment root with a literal allowlist, when a release readiness gate skips work by version metadata, or when a rollback can start an older component against the new file."
category: architecture
date: 2026-11-13
version: "1.0.0"
user-invocable: false
tags:
  - deployment
  - public-projection
  - allowlist
  - readiness-gate
  - rollback
  - atomic-publish
  - permissions
  - shared-storage
---

# Publish a New Top-Level Deployment Artifact

## Overview

| Field | Value |
| ------- | ------ |
| **Date** | 2026-11-13 |
| **Objective** | Publish a new top-level file to a live deployment root without a literal allowlist refusing it and without a readiness gate accepting stale bytes. |
| **Outcome** | Successful. The publisher wrote the file atomically with fixed permissions. The allowlist derived from the path inventory. The readiness gate compared the released bytes. The rollback procedure removes the file before an older component starts. |

A deployment root can hold only the names that its validator approves. A
literal allowlist in one component is a current-state check, not a rollout
contract. When a new name appears, every older component still carries the old
literal list. A rollback to one of those components then refuses the name at
startup.

A second gap is a readiness check that compares only existence, owner, group,
and mode. A partial publish can leave the previous file with the correct
metadata. The next run then skips the install and keeps stale bytes.

## When to Use

- A validator lists the allowed top-level names of a deployment root with a
  literal set.
- You add a top-level file that must appear while components are live.
- A release readiness gate skips work when a version selector or revision
  matches.
- A rollback can start a component older than the new file.
- The deployment root is on shared storage, so a file lock is not allowed.

## Verified Workflow

### Quick Reference

```python
# One authority for the allowed top-level names.
allowed = {
    path.relative_to(root).parts[0]
    for path in path_inventory(root).path_values()
    if path != root
}

# Readiness: compare the released bytes, not only owner and mode.
ready = metadata_matches(published) and read_file_no_follow(published) == release_bytes

# Rollback: remove the new top-level file before the older component starts.
```

### Suggested Approach

1. **Find every validator.** Search for the directory listing and the refusal
   message. A second literal set can live in a different component, a status
   publisher, or a startup check. Record each site before you change one.
2. **Make the path inventory authoritative.** Add the new path to the inventory
   and to the protected-path declaration. Derive every validator's allowed set
   from the inventory. Do not add only the new literal to each set: the next
   artifact gets the same problem, and the rollback barrier stays hidden.
3. **Plan the rollback boundary.** An older component still has the old literal
   set. It refuses the new name at startup. Remove the new file before a
   rollback to that component. If removal is not acceptable, split the rollout:
   release a tolerant validator first, then publish the file in a later release.
4. **Bind readiness to the release bytes.** Compare the published bytes with the
   release source, or publish the file before the version selector moves. The
   byte check is the stronger option when a failed publish can outlive the
   selector change.
5. **Publish atomically.** Write a unique exclusive temporary name in the same
   directory. Set owner, group, and mode on the descriptor. Sync the descriptor,
   replace the target, and sync the directory. Refuse a symlink, a directory, a
   hard link, and a foreign-owned target. Take no file lock on shared storage.
   The [atomic anchor publication](publish-anchor-files-fully-configured.md)
   entry explains the visibility race that this order prevents.
6. **Repair on every run.** Set the owner, group, and exact mode on every
   publish. A re-run must repair a missing file or a wrong mode, not only a
   changed version.
7. **Read from the release source.** Read the bytes from the selected commit or
   a clean export. Do not read a dirty work tree. Prove that the entry is one
   regular file and bound the read size.
8. **Clean temporary residue.** A killed publish can leave a temporary name that
   the validator refuses. Remove service-owned stale temporary names before the
   write. Make the refusal message name each unexpected entry so the residue is
   visible.
9. **Verify the installed file.** Reopen with no-follow semantics. Compare the
   bytes, owner, group, mode, and link count. Prove that the directory entry
   still names the same inode. Log the digest.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | -------------- |
| Add the new name to each literal allowlist | The new component accepted the name. An older component refused it after a rollback. | Every older component still carries the old literal list. | Derive the allowlist from one inventory. Remove the file before a rollback, or split the rollout. |
| Check only mode and owner in the readiness gate | A failed publish left the old file with the correct metadata. The next run skipped the install. | Metadata cannot distinguish old bytes from release bytes. | Compare the released bytes, or publish before the selector moves. |
| Read the file from the checkout | Uncommitted or ignored changes could reach the deployment. | The work tree is mutable and is not the release source. | Read the committed blob or a clean export and prove it is a regular file. |

## Results & Parameters

### Configuration

Use the narrowest mode that the reader needs. An executable user script can use
mode `0755`; a data record can use `0444` or `0644`. Use `presence: lifecycle`
in the path declaration so an existing deployment without the file is not a
divergence.

```python
# Derive the allowed top-level names from the inventory.
allowed = {
    path.relative_to(deployment_root).parts[0]
    for path in path_inventory(deployment_root).path_values()
    if path != deployment_root
}

# Bind readiness to the released bytes.
observed = read_file_no_follow(published_path)
expected = read_release_file(release_source_path)
ready = metadata_matches(published_path) and observed == expected
```

Use a temporary name that starts with a dot and a fixed prefix, for example
`.<name>-<pid>-<random>`. Remove service-owned stale names with that prefix
before the write.

### Expected Output

- The target name is one regular file with the declared owner, group, and mode.
- The file bytes equal the release source bytes.
- A re-run repairs a missing file or a wrong mode.
- The validator accepts the new top-level name.
- An older component refuses the name only if the file remains after a
  rollback.

## Verified On

| Project | Context | Details |
| --------- | --------- | ------- |
| A public deployment service | Corpus validator and fast test tier; source change exercised the allowlist and readiness gate | The corpus validator passed. The fast tests passed. The published file was a service-owned executable at the deployment root. |

## References

- [Publish anchor files fully configured](publish-anchor-files-fully-configured.md)
- [Capability-guard scripts embedded in a release](release-embedded-script-capability-guard.md)
- [Repair a directory leaf without widening permissions](directory-repair-leaf-only.md)