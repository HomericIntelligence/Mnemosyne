---
name: directory-repair-leaf-only
description: "Repair directory mode or ownership on the leaf a call owns only; validate every existing ancestor without changing its metadata, and keep the observed form of a leaf that its own mode rule permits. Use when (1) an ensure-style helper creates a missing chain below a root that another lane or deployment shares, (2) a recursive normalization can run on ancestors it does not own, (3) a shared or production root unexpectedly lost its mode, setgid bit, or owner while its deployed inputs stayed unchanged, or (4) a repair of a declared leaf normalizes one conforming mode form, such as a bootstrap setgid form, to another."
category: architecture
date: 2026-10-28
version: "1.1.0"
user-invocable: false
verification: verified-ci
tags:
  - permissions
  - chmod
  - setgid
  - shared-storage
  - mkdir-parents
  - recursive-repair
  - fail-closed
  - shared-root
---

# Repair the Leaf a Call Owns, Validate its Ancestors

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-28 |
| **Objective** | Stop an ensure-style directory helper from changing a shared or production root while it creates a private leaf below that root. |
| **Outcome** | Successful. A production incident repair was proven by regression tests that fail before the correction and pass after it, and the corrected helpers are deployed. |

## When to Use

- You write or review an ensure-style helper: it creates each missing parent of a private chain and normalizes existing directories to a declared mode, owner, or group along the way.
- The derived path can cross a root that the call does not own: a shared cluster root, a shared deployment root, or a root that a different lane of the same deployment uses.
- A shared or production root lost its declared mode twice or more, lost its setgid bit, or appeared at a umask-shaped mode (for example `0755`), and every declared input was identical across the events. The event time correlates with a non-production lane that created a private chain below that root.
- You review a `mkdir(parents=True)` (or equivalent) call that can fabricate a boundary root: the missing chain appears with the caller umask, not with the declared policy mode.
- You repair a declared leaf that its own policy rule admits in more than one conforming form: a declared mode and a bootstrap form that carries a set-group-ID bit. A repair that writes only the declared mode drops the observed form as a side effect.

Do not use this entry only to pick stable `stat` fields for a same-object check; that intent has its own entry. The distinction: this entry decides where a write repair may act; the same-object entry decides which fields a read-only identity check compares.

## Verified Workflow

### Quick Reference

```text
An ensure-style helper MUST:
  - repair mode, owner, and group only on the leaf it owns and on the
    directories it creates in this call;
  - validate each existing ancestor (owner, file type, no symlink)
    through one descriptor opened with no-follow, and change no
    metadata on it;

- refuse before any write when an ancestor fails validation, and
  name the offending path in the refusal;
- treat the boundary root as pre-existing: refuse to fabricate a
  missing boundary root (no parents=True creation at umask modes);
- create a shared directory at its declared policy mode, never by
  inheritance from the caller umask;
- keep the observed mode form of the leaf while the leaf's own
  policy rule permits that form, so the repair does not normalize
  one conforming form to another.
```

### Suggested Approach

1. Draw the ownership line through the recursion. The leaf of the call is the only directory the helper owns. Every existing ancestor above it is foreign state, even when the same account owns it: its mode, owner, and setgid bit can be declared by a policy the caller does not know.
2. Replace recursive normalization with validation. Open the existing ancestor once (`O_RDONLY | O_DIRECTORY | O_NOFOLLOW` on POSIX), `fstat` it, confirm the service owner and the directory type, and return. Do not `fchown` or `fchmod` it. New directories the call creates in the same run still get the private repair `(fchown, fchmod)` bound to their own descriptor.
3. Fail closed before any write. A mismatching ancestor (a regular file, a symlink, foreign ownership) refuses the whole call and names its path. The call does not skip the mismatch and does not continue to the leaf.
4. Guard the lane boundary at the mutation entry point too. A non-production lane whose deployment root IS the shared production root must be refused before any protected effect, with the lane and the public root named. An ambient or fallback context can bind that root wrongly; do not trust that the registry prevented it.
5. Keep the mode source single. The declared mode belongs in one policy table; creation sites consume the table. A call-site constant next to the policy table drifts from it.
6. Test both arms, deterministically, with no timing dependence: one benign arm proves that an existing correct ancestor (declared mode, owner, group, setgid) passes with no metadata change; one refusal arm proves that a non-directory or wrong-owner ancestor refuses before any write and that the tree below stays absent. Add a repair arm only for the leaf: the owned leaf still gets its declared private mode.
7. Where an existing contract pins ancestor-repair behavior (a documented drift repair for a mid-chain directory), make that mid-chain directory its own explicit leaf instead of restoring ancestor repair.
8. Decide the leaf mode from the leaf's own rule, not from one stored mode. Read the rule that admits modes for this leaf. When the rule permits a form that the observed leaf already has, repair to that observed form. For a permitted set-group-ID form, add the bit to the declared mode. When the rule forbids the bit, write the declared mode and no set-group-ID bit. Do not assume that the filesystem re-forces the bit from the parent: a repair that drops it changes an operator-visible form on a filesystem that does not.

### Failure Shapes to Recognize

- Production root repaired repeatedly from a declared mode (for example `0o2755` with setgid) into a private mode (`0o700`) with the setgid bit dropped: the recursive normalization reached an ancestor it did not own.
- A chain below the public root appeared at `0755`: a makers call used `parents=True` (or equivalent) at the caller umask across a missing boundary root.
- A transition lock or control file appeared inside the production public root: the mutation entry point trusted a context whose deployment root was the public root.
- A registered root created at the bootstrap `0o2750` form reads back `0o750` after one core write: the leaf repair wrote the declared mode alone and dropped the permitted set-group-ID bit. Every mode check accepts both forms, so no check reports the change, and a reader can mistake it for drift.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Fix only the observed writer | Repair each creation site that the incident log showed. | The same helper class has several callers; the unlocated callers keep the incident open. | Fix the helper contract (leaf-only), not one call site. |
| Substring or relative-to lane check | Refuse a deployment root that sits anywhere below the public root. | The check breaks test fixtures and in-tree layouts that nest a public root inside a context root; it also refuses legitimate nested deployments that the incident never covered. | Bind the boundary to identity (equality with the declared public root); naming the lane and the root makes the refusal actionable. |

## Results & Parameters

### Configuration

- Leaf-only repair bound to one descriptor per directory; ancestors opened with no-follow for validation only.
- Leaf repair mode comes from the leaf rule: the declared mode alone, or the declared mode plus a set-group-ID bit when the rule permits and the observed leaf already has the bit.
- Refusal message carries the offending path; the lane-boundary refusal also carries the lane and the public root.
- Shared directory creation uses the policy mode from the single policy table.

### Verification

Production incident forensics identified three harm shapes at the same shared root (declared mode repaired to private mode twice; one chain at umask mode). Regression tests for each shape fail before the correction and pass after it, and the complete change (sources and tests) passed the full applicable local suites plus the hosted gates before merge.

A fourth shape was found in review of a later repair: a registered root at the permitted `0o2750` form was rewritten to `0o750` by a root-child write. A test pins the `0o2750` form across a root-child write and the covering test files passed locally.
