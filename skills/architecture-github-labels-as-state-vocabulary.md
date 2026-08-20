---
name: architecture-github-labels-as-state-vocabulary
description: "Use mutually exclusive state:* labels as a durable pipeline state machine. Use when comments are an unreliable gate, several components must read one signal, label swaps must be atomic, or unavailable and malformed reads must fail closed."
category: architecture
date: 2026-08-07
version: "2.0.0"
license: BSD-3-Clause
user-invocable: false
verification: verified-local
history: architecture-github-labels-as-state-vocabulary.history
tags:
  - github-labels
  - state-machine
  - mutually-exclusive-labels
  - atomic-label-swap
  - fail-closed-readback
  - graphql
  - rest-fallback
  - idempotency
---

# GitHub Labels as a State Vocabulary

## Overview

Use labels as machine state, not as decoration. Define a closed vocabulary, make every transition
an add-one/remove-all-siblings operation, and authorize work only after a strict fresh read proves
exactly one allowed state. Comments may explain a verdict, but must not be its durable source.

The original three-state implementation was exercised locally in ProjectHephaestus PR #707 (911
automation tests plus Ruff and mypy). The later re-plan, atomic-swap, strict-payload, GraphQL
sentinel, fallback, and readback refinements remain design-stage guidance from issue #1857; they
must not be represented as CI-verified behavior.

Detailed case evidence is indexed in
[architecture-github-labels-as-state-vocabulary.notes.md](architecture-github-labels-as-state-vocabulary.notes.md).
The complete prior version is in
[architecture-github-labels-as-state-vocabulary.history](architecture-github-labels-as-state-vocabulary.history).

## When to Use

- Automation currently parses a comment such as `GO` or `NOGO` to decide whether to proceed.
- Planner, reviewer, and implementer disagree because each reads a different state signal.
- Duplicate, missing, malformed, contradictory, or unavailable labels must never authorize work.
- A transition is emitted as separate add and remove calls, leaving a zero-or-two-state window.
- A batch GraphQL read needs per-item unavailable semantics and a strict REST fallback.
- Retry or post-mutation confirmation must be idempotent and fail closed.

Do not use labels as the only audit record. Keep human rationale in comments or artifacts and use
labels only for the small, explicit state vocabulary.

## State Contract

The canonical vocabulary is:

| Label | Meaning | May authorize |
| --- | --- | --- |
| `state:needs-plan` | Planning or re-planning is required | Planner work only |
| `state:plan-no-go` | Current plan was rejected | Re-plan transition only |
| `state:plan-go` | Reviewed plan is approved | Implementation only |

Invariant: a successful read contains exactly one of these labels. Zero, two, or three labels are
invalid for authorization. Unknown `state:*` labels and malformed siblings also fail closed.

Absence may be treated as `needs-plan` only by an explicitly bounded legacy backfill path. Normal
readers must not silently reinterpret absence.

## Verified Workflow

### 1. Provision the vocabulary idempotently

```bash
for spec in \
  'state:needs-plan|D4C5F9|Planning required' \
  'state:plan-no-go|D93F0B|Plan rejected' \
  'state:plan-go|0E8A16|Plan approved'
do
  IFS='|' read -r name color description <<EOF
$spec
EOF
  gh label create "$name" \
    --repo "$REPO" \
    --color "$color" \
    --description "$description" \
    --force
done
```

Quote workflow substitutions before passing them to a shell. Prefer `env:` bindings for issue
numbers or repository names; do not splice untrusted issue content into `run:` scripts.

### 2. Normalize and validate the whole payload

```python
STATE_LABELS = frozenset(
    {"state:needs-plan", "state:plan-no-go", "state:plan-go"}
)


def exclusive_state(raw_labels: object) -> str | None:
    if not isinstance(raw_labels, list):
        return None
    names: list[str] = []
    for item in raw_labels:
        if not isinstance(item, dict):
            return None
        name = item.get("name")
        if not isinstance(name, str) or not name.strip():
            return None
        names.append(name.strip())
    states = [name for name in names if name in STATE_LABELS]
    unknown_states = [
        name for name in names if name.startswith("state:") and name not in STATE_LABELS
    ]
    if unknown_states or len(states) != 1:
        return None
    return states[0]
```

Validate the entire payload. Skipping malformed siblings while accepting one valid label turns a
partial transport failure into authorization.

### 3. Make each transition one combined edit

```bash
gh issue edit "$ISSUE" --repo "$REPO" \
  --add-label state:plan-go \
  --remove-label state:needs-plan \
  --remove-label state:plan-no-go
```

Every transition uses one GitHub edit with disjoint add/remove sets:

```python
def transition(target: str) -> tuple[list[str], list[str]]:
    if target not in STATE_LABELS:
        raise ValueError(f"unknown state: {target}")
    return [target], sorted(STATE_LABELS - {target})
```

The re-plan edge is a swap to `state:needs-plan`, not a bare add:

```bash
gh issue edit "$ISSUE" --repo "$REPO" \
  --add-label state:needs-plan \
  --remove-label state:plan-no-go \
  --remove-label state:plan-go
```

Separate add/remove API calls are not atomic: crashes and concurrent readers can observe zero or
two states. If an accessor lacks a combined operation, add one and route every state writer
through it.

### 4. Read strictly, with an unavailable sentinel

For a batch GraphQL adapter, preserve the distinction between a successful empty collection and a
failed read:

```python
def labels_from_graphql(node: object) -> list[str] | None:
    if not isinstance(node, dict):
        return None
    labels = node.get("labels")
    if not isinstance(labels, dict):
        return None
    nodes = labels.get("nodes")
    if not isinstance(nodes, list):
        return None
    result: list[str] = []
    for item in nodes:
        if not isinstance(item, dict) or not isinstance(item.get("name"), str):
            return None
        result.append(item["name"])
    return result
```

- `None`: unavailable or malformed; never authorize.
- `[]`: successful read with no labels; eligible only for a bounded backfill.
- Non-empty list: pass through the exclusive-state validator.

When a batch item is `None`, perform a strict per-issue REST read. A failed fallback remains
unavailable; it must not become `[]` or a default state.

### 5. Confirm the mutation with a fresh read

After `gh issue edit` succeeds, fetch labels again without using a stale batch cache. Authorize the
next stage only if the strict reader returns the intended exclusive state. A retry repeats the same
target transition and readback; it does not emit compensating writes.

Shared predicates keep planner and implementer aligned:

```python
def should_plan(state: str | None) -> bool:
    return state == "state:needs-plan"


def may_implement(state: str | None) -> bool:
    return state == "state:plan-go"
```

### 6. Audit every edge and writer

List all state transitions, then locate the component that executes each one. A diagrammed edge
without a writer is a stuck-closed gate. Search for raw literals and direct label mutations so
ambient, standalone, and repository-scoped implementations cannot drift from the shared module.

## Decision Rules

- Labels are the authorization source; comments are explanatory evidence.
- Writers add one allowed state and remove every sibling in one operation.
- Readers accept exactly one known state and reject malformed or unknown `state:*` values.
- Transport failure is distinct from a successful empty label set.
- Batch failures fall back per item; fallback failure stays unavailable.
- Mutation success is not enough: fresh readback must prove the target state.
- Re-plan restores `needs-plan`; it never bypasses the state gate by parsing plan comments.
- Backfill is one-time, bounded, and idempotent; normal execution never reparses history.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --- | --- | --- | --- |
| 1 | Parse the latest `GO` comment | Editing, ordering, quoting, and duplicate comments make it fragile | Read an exclusive label; keep rationale in comments |
| 2 | Add the new label without removing siblings | Leaves contradictory states and can keep the gate closed | Add one and remove all siblings in one edit |
| 3 | Issue separate add and remove calls | Exposes a crash and observation window | Add a combined-edit primitive |
| 4 | Treat failed GraphQL as an empty list | Converts unavailable state into an implicit authorization path | Use `None` and strict per-item fallback |
| 5 | Accept one valid label while ignoring malformed siblings | Partial payload corruption can authorize work | Validate the whole payload |
| 6 | Draw the re-plan edge without assigning a writer | Rejection label remains and verification retries forever | Execute the swap in the re-planning owner |
| 7 | Trust a successful mutation without readback | Retries or races can leave a different state | Re-read strictly and compare with the target |

## Verification Checklist

- Exercise every allowed edge, every disallowed combination, and idempotent retries.
- Test zero, duplicate, contradictory, unknown, malformed, and unavailable label payloads.
- Prove GraphQL `None` invokes REST fallback and fallback failure never authorizes.
- Assert each transition emits one edit with disjoint add/remove sets.
- Confirm post-write reads bypass caches.
- Run the repository's focused state-machine tests, full automation suite, lint, and type checks.

## Results & Parameters

- Vocabulary: exactly three mutually exclusive labels.
- Mutation primitive: one combined edit that adds the target and removes both siblings.
- Successful authorization: exactly one known state after a fresh strict read.
- Unavailable sentinel: `None`; successful empty collection: `[]`.
- Initial evidence: 911 local automation tests plus Ruff and mypy in PR #707.

## Evidence Boundary

The three-label core and initial automation are `verified-local` from PR #707. The re-plan and
strict distributed-read refinements from issue #1857 are unverified design guidance until their
implementation and CI evidence are recorded. See the notes companion for case-level provenance.
