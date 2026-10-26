---
name: defect-disposition-implement-vs-release
license: BSD-3-Clause
description: "Disposition a symptom-driven fix request as new implementation, an open change to land, a release to deliver, or an already-aligned system, before designing any correction. Use when: (1) a user report or live symptom triggers a fix, repair, or realignment request for running software, (2) the same defect may already be diagnosed or fixed in the tracker or main history, (3) the deployed release may be older than the fix, so the gap is delivery, not implementation, and (4) continuing symptoms on an unfixed release must not trigger re-implementation."
category: debugging
date: 2026-10-26
version: "1.0.0"
user-invocable: false
verification: verified-local
tags: [defect-disposition, release-lag, symptom-search, deployed-version, ancestry-check, duplicate-fix, delivery-vs-implementation, tracker-search, live-symptom]
---

# Defect Disposition: Implement, Land, Deliver, or Aligned

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-26 |
| **Objective** | Select the correct class of action for a symptom-driven fix request before any correction is designed or written. |
| **Outcome** | Successful — a redundancy was avoided: an evidence-based fix design was stopped before implementation because a symptom search found the same defect already diagnosed and fixed upstream; the real action was a release, not code. |

A symptom inside a running system has four economically different resolutions.
Writing a correction is only one of them. The other three transfer work that
already exists: land an open change, deliver a merged change through the
release path, or recognize that the symptom is expected on an unfixed release
and stops being a defect signal. The checks cost minutes. A duplicate fix
costs a review cycle, a second implementation of the same rule, and a
possible regression conflict. This skill binds the classification to
deterministic commands so the choice is evidence, not memory.

## When to Use

Use this skill when one of these conditions applies:

- A user message reports a live symptom, or an investigation finds one, and
  the request is "debug this", "fix this", "realign the implementation", or
  equivalent.
- The system has a released artifact (tag, image, or recorded source digest)
  that can lag behind the default branch.
- Fast upstream rate makes "someone may already have found this" probable.
- A continuing symptom must be explained: is the fix missing, undelivered,
  or ineffective?
- The same symptom was investigated before by anyone with tracker access.

Do not use this skill for a requested new capability with no defect signal,
or for audit-issue phantom checks in source trees (a related skill covers
that variant).

## Verified Workflow

### Quick Reference

```bash
# 1. Bind the deployed ref exactly (from runtime state, not from "latest").
git describe --tags --always <deployed-source-digest>

# 2. Search the tracker for the distinctive symptom signature, all states.
gh issue list --state all --search "<mechanism or unique error text>"

# 3. For each candidate fix, test merged state and ancestry.
gh pr view <number> --json state,mergeCommit,mergedAt,headRefName
git merge-base --is-ancestor <fix-commit> origin/main
git branch -a --contains <fix-commit>

# 4. Test the same commit against the deployed ref.
git merge-base --is-ancestor <fix-commit> <deployed-ref>

# 5. Read the fix, not only its title.
git show <fix-commit> --stat
```

Select exactly one disposition from the table in Results & Parameters.

### Suggested Approach

1. **Fingerprint the symptom with a searchable signature.** Use the most
   distinctive mechanism text available: a log phrase a normal operator would
   not write, a metric with a specific shape, an exact error string. Session
   wording ("it scales too much") is not a signature.
2. **Search the tracker across all states before designing anything.** A
   closed issue with a merged fix and an open pull request are both possible
   carriers. Search the signature, not the user phrasing. Read the hit body;
   the mechanism must match, not only the title.
3. **Bind the deployed ref from recorded runtime state.** Use a source
   digest, manifest, or version marker that the running artifact itself
   reports. Then resolve it to a tag or commit. Code read in a checkout —
   including the checkout the symptom investigator happens to have — is not
   evidence of deployed behavior.
4. **Test ancestry in both directions.** A fix "on `main`" that the deployed
   ref does not contain produces exactly the observed symptom, indefinitely.
   `merge-base --is-ancestor` settles each direction. When several commits
   carry the same change (re-rolled series), enumerate them with
   `git branch -a --contains` before concluding.
5. **Read the fix content, not only its metadata.** `git show <fix> --stat`
   and the changed decision code tell whether it covers the observed
   mechanism. A title match alone is not coverage.
6. **Disclose continuing symptoms correctly.** Symptoms observed on a release
   that does not contain the fix are expected, dated no later than the fix,
   and their presence is not new evidence about implementation quality. A
   symptom observed on a release that *does* contain the fix needs a new
   diagnosis, not a re-implementation.
7. **Route without duplicating.** "deliver-release" goes to the release or
   promotion path that owns the artifact. "land-open-PR" coordinates with the
   PR owner or stacks on its branch. Never open a competing fix for the same
   mechanism.

When the tracker is unreachable or the deployed ref cannot be bound, continue
the investigation but mark the disposition unverified; do not implement a fix
whose duplicate status is unknown.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Design a correction from the symptom evidence alone | Derived a threshold policy for a noise-driven autoscaler from live logs and code, and recommended it as the fix | A tracker search after the design found the identical defect already filed, diagnosed, and fixed upstream with the same mechanism; the design was a duplicate before it was written | Search the tracker for the symptom signature first; fix design comes after the duplicate check, not before |
| Treat the implementation at the symptom investigator's checkout as production behavior | Read module code in the local checkout and attributed its behavior to the running service | The running service carried a release that predated both the checkout state and the upstream fix; checkout content overstated and understated different parts of deployed behavior | Bind the deployed ref from runtime-recorded identity first; rank all code reads against it |
| Count a continuing live symptom as proof the implementation is still broken | Initial framing: "autoscaling is broken; align the implementation" | The fix had merged the previous day; the release simply did not carry it yet, so the symptom was scheduled noise, not new evidence | Date the symptom against release contents; an old-release symptom after a merged fix updates the delivery plan, not the implementation plan |

## Results & Parameters

### Dispositions

| Disposition | Gate conditions | Routed action |
| --------- | --------------- | ------------- |
| `implement-new` | No tracker match for the signature; no candidate fix on any ref | Normal debugging and change workflow; write the issue first when policy requires one |
| `land-open-PR` | A tracker match exists with an open pull request whose content covers the mechanism | Coordinate or stack on that branch; do not open a competing change |
| `deliver-release` | A merged change covers the mechanism; `origin/main` contains it; the deployed ref does not | Route to the release or promotion path; record the carrying change as the precondition |
| `already-aligned` | A merged change covers the mechanism; the deployed ref contains it; symptom persists | New diagnosis on current behavior; do not re-implement |

### Configuration

Record these fields with the disposition:

```text
symptom_signature: <distinctive mechanism text used for the search>
tracker_hits: <issue or PR numbers examined, with mechanism match notes>
deployed_ref: <exact tag or commit the runtime reports>
carrying_change: <commit or PR that covers the mechanism>
ancestry_main: <contains | not-contained>
ancestry_deployed: <contains | not-contained>
disposition: <one of the four rows above>
```

### Expected Output

- Exactly one disposition, selected by the gate conditions, with the evidence for each gate.
- No new fix code when the disposition is `land-open-PR`, `deliver-release`, or `already-aligned`.
- A named carrying change and its promotion vehicle when the action is delivery.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| LLM360/comet | Production autoscaling symptom; upstream fix PR #3006 (issue #2858) merged to `main` while deployed v0.2.3 predated it; disposition selected: `deliver-release` | [notes.md](./defect-disposition-implement-vs-release.notes.md) |

## References

- [planning-verify-issue-premise-before-implementing](planning-verify-issue-premise-before-implementing.md) — generic premise-to-command discipline; this skill adds the deployment axis and the delivery disposition for live symptoms.
- [deployed-version-runbook-goal-feasibility](deployed-version-runbook-goal-feasibility.md) — the same bind-the-deployed-ref rule for operator directions; code read on `main` is not evidence of deployed behavior in both skills.
- [verify-audit-issue-reproduces-before-fixing](verify-audit-issue-reproduces-before-fixing.md) — the tree-side variant: phantom versus already-resolved audit findings without a deployment boundary.
