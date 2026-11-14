---
name: plan-identity-rebind-before-review
description: "Recover a plan review that reports a requirements-digest or repository-revision mismatch. Use when a plan carrier binds a requirements digest, issue update time, or repository commit that no longer matches the live issue and default branch, when the plan's cited dependency list or dependency states differ from the issue, or when a review prompt context (issue body, plan text, prior review) is older than the live tracker."
category: tooling
date: 2026-11-04
version: "1.0.0"
user-invocable: false
verification: verified-live
tags:
  - plan-review
  - issue-plan
  - requirements-digest
  - requirements-drift
  - rebind
  - stale-binding
  - dependency-state
  - scope-drift
  - injected-context
  - review-gate
  - fail-closed
---

# Plan Identity Rebind Before Review

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-04 |
| **Objective** | Stop a plan review from grading a plan against a superseded issue snapshot, dependency list, or default-branch revision. |
| **Outcome** | Successful. A review that first recomputed the requirements identity, the default-branch head, and each dependency state found three independent mismatches and returned a no-go with evidence, instead of a verdict on plan content alone. |

## When to Use

- A plan carrier binds a requirements digest, a requirements update timestamp, or a default-branch commit, and a review must decide whether the plan is bound to the live issue.
- The plan lists required dependencies, or asserts their states, and the live issue lists other dependencies or other states.
- The plan places most of its steps on a subject that the live issue body does not contain.
- The issue carries a partition rule, such as a deduplication list, that assigns concrete work to later issues and sets matching non-goals.
- The review prompt supplies the issue body, the plan text, and prior review text as fixed blocks, and the blocks may predate a live edit.
- A prior review states that conversation recovery is required, or that context transport failed, with no findings.

Out of scope: the plan content rubric itself. Use the applicable plan review rubric after this check. This entry covers identity and scope binding only; `planning-verify-issue-premise-before-implementing` covers anchor and authority sweeps at hand-off.

## Verified Workflow

### Quick Reference

```bash
# Requirements identity: recompute with the formula that the plan states.
gh issue view <N> --repo <user>/<repo> --json id,title,body,updatedAt \
  | python3 -c 'import json,sys,hashlib
d=json.load(sys.stdin)
s=json.dumps({"id":d["id"],"title":d["title"],"body":d["body"]},
             sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
print(hashlib.sha256(s).hexdigest(), d["id"], d["updatedAt"])'

# Scope presence: is each plan subject token in the live body?
gh issue view <N> --repo <user>/<repo> --json body -q .body | grep -c '<subject-token>'

# Dependency list and states: compare with the plan's claim.
for n in <dependency-numbers>; do
  gh issue view "$n" --repo <user>/<repo> --json number,state,title \
    -q '"\(.number)\t\(.state)\t\(.title)"'
done

# Repository revision: compare the plan's cited commit with the live head.
git cat-file -t <plan-cited-commit>
git rev-parse origin/main
```

### Suggested Approach

1. Recompute the requirements identity with the exact formula in the plan. Do not accept the plan's own digest or timestamp. Compare the result with every identity that the plan and the review prompt state. Plan edit-epoch blocks often carry two identities, an "amendment" identity and a "binding" identity, and both can differ from the live value. Read the mismatch as "bound to superseded requirements", not as "bad arithmetic".
2. Compare the issue update timestamp in the recomputation with the timestamp that the prompt embeds. If the prompt has no timestamp, the recomputation is the only authority; state that the embedded body may be older than the live body.
3. Run the scope presence check for each subject that the plan uses. A subject with zero matches in the live issue while it holds most plan steps is likely to be a previous planning epoch's subject. Do this before you grade requirement alignment, because the zero-match result changes what "alignment" means.
4. List each dependency and its state. A plan that requires a subset of the issue dependencies, or that adds dependencies that the issue does not name, has a different technical basis. Wrong state claims change the branch of a plan, for example a deferral that waits for a merge of a dependency that is already closed. A closed dependency that is present in the issue but absent from the plan is a possible silent scope drop.
5. Compare the plan's cited repository commit with the live default-branch head. Do not date the plan by its text. Dependency issue states and merged commits can move two months beyond a plan whose prose looks current.
6. Apply a deduplication or partition rule from the issue body. Concrete gates and scripts that the rule transfers to other issues cannot be re-owned by the plan. If the plan owns them, the surplus is scope drift, not thoroughness.
7. Check plan-internal identity consistency. A plan that says "no previous plan existed" and also cites a previous plan digest contains two epochs in one artifact. Do not spend this as a content finding; record it as evidence that the artifact was composed from more than one source.
8. Use the recomputed facts as review evidence. Report each mismatch with the command, the observed value, and the value that the plan claims. Report the recovery artifact as no findings; do not infer its lost content.
9. Select the disposition:
   - All identity fields match and the scope tokens are present: continue to the content rubric.
   - Any identity, dependency, or scope-token mismatch: return a no-go. List each mismatch and state the rebind that unblocks the next revision: the live digest, the live head, the live dependency set with states, and the live subject. The author rebinds and resubmits.
   - The blocking fact needs a human decision, such as which of two live scopes is authoritative: report a block and name the exact decision.
10. For a durable fix at the producer, give the plan one canonical identity producer. Check that the producer recomputes the digest from the live issue at publication time and that it rejects a plan whose stated digest differs. Treat a hand-built digest block as unverified input.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Grade only the content rubric | Applied the plan review dimensions and the principles to the plan text and returned a verdict. | The plan bound superseded requirements, named dependencies that the issue does not contain, and cited a default-branch commit two months old, so every dimension graded the wrong scope. | Verify the identity and the scope binding before you grade content. |
| Trust the prompt's identity fields | Read the requirements digest and the plan fingerprint from the review prompt, which also supplied an older snapshot of the issue body. | The prompt context was correct for the session, but the plan was bound to bytes that the live issue no longer had. | Recompute from the live tracker. The prompt describes the plan; it does not describe the issue now. |
| Accept a prior review as the plan | The prior review was a recovery artifact with no findings, so a plan appeared to have no prior acceptance. | The rubric forbids treating the prior review text as the plan; the current plan block is the plan. | Grade the plan block. Use prior review text only to know which findings to verify. |
| Treat a superseded subject as minor drift | Found that a subject token was absent from the live issue and treated its steps as extra detail. | The subject held most plan steps, and the live acceptance criteria were unaddressed. | Run scope presence first. A zero-match subject with high step share is a scope error, not a detail error. |
| Wait on a dependency that is closed | The plan deferred install, upgrade, and schema steps until a named dependency merged. | The dependency was already closed, so the deferral had no condition to wait for and hid unplanned design work. | Read each dependency state. A closed dependency converts a deferral into a design gap. |

## Results & Parameters

### Configuration

- `requirements_identity`: the digest value that the plan states.
- `identity_formula`: the plan's own stated method, for example a SHA-256 of compact, sorted UTF-8 JSON that holds the issue `id`, `title`, and `body`, with `ensure_ascii=False` and no final newline.
- `dependency_set`: the issue dependency list, with one state for each entry, from `gh issue view <n> --json state`.
- `subject_share`: the part of plan steps that address one subject token, and the token count in the live issue body.
- `plan_revision`: the default-branch commit that the plan cites, and the live `origin/main`.

### Expected Outputs

- One recomputed identity per comparison, with the observed digest, the issue node ID, and the update time.
- One line for each dependency: number, state, and present or absent in the plan.
- One verdict: continue to the content rubric, no-go with a rebind list, or block with a named human decision.

### Verified On

| Project | Context | Details |
|---------|---------|---------|
| Mnemosyne | Read-only plan review of one release issue | [notes.md](./plan-identity-rebind-before-review.notes.md) |