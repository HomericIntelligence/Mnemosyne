---
name: verification-evidence-audit
description: "Verify completion, fix, passing-check, metric, CI, or benchmark claims with fresh runnable evidence. Use when: (1) about to claim work is complete/fixed/passing/ready, (2) a measured value, CI result, benchmark, or training loss is posted, (3) a success claim cites a committed file or badge instead of a live gate"
category: testing
date: 2026-07-16
version: "1.0.0"
user-invocable: false
tags: [verification, evidence, ci, claims, integrity]
---

# Verification: Evidence Audit for Claims

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-07-16 |
| **Objective** | Determine whether a completion or measurement claim is backed by runnable evidence |
| **Outcome** | Operational — migrated from the Athena `verification` skill into standard knowledge |

## When to Use

- Before any claim that work is complete, fixed, passing, or ready.
- Whenever a measured value, CI result, benchmark, training loss, or successful-run claim is posted.
- For a completion claim, discover and freshly run the repository-defined relevant validation; a prior run, badge, or implementation diff is not evidence of the current state.
- The audit does not automatically reproduce an expensive or side-effecting run; it queries current read-only evidence and may re-execute safe, bounded verification commands.

## Inputs

1. **The claim.** A sentence like "the build passed in 4m12s" or "epoch 1 loss = 0.4123". Quoted verbatim.
2. **The evidence pointer.** A path, a URL, or a CI run id. If absent, ask before proceeding.

## Verified Workflow

### Detailed Steps

1. **Classify the claim type.**
   - **Completion/fix claim**: evidence is fresh output from the repository-defined relevant tests, validation, lint, type, build, or package commands at the claimed revision.
   - **CI gate result** ("all checks pass"): evidence is the `gh pr checks` JSON, not a PR body line.
   - **Measured metric / benchmark**: evidence is a CI-produced artifact or an independently-reproduced log; a file committed into a PR does NOT count.
   - **Training/optimization result**: accepted evidence is a CI-produced artifact or a detached-execution run record bound to the reviewed revision.
   - **Operational status** ("the daemon is running"): `systemctl status` or `podman ps` output.
2. **Locate the evidence.** Use read-only file inspection for workspace evidence. Run read-only commands such as `gh pr checks`, `systemctl status`, or `podman ps` directly when the host grants Bash. Quote user-provided identifiers, reject values beginning with `-`, and prefer structured output. Delegate an independent or long-running check when the host grants subagents. If neither execution nor delegation is available, return `CONDITIONAL` or `NO-GO` with the exact command the caller must run; never present an unexecuted command as evidence. Any command with side effects, credentials beyond read access, or material cost requires explicit user authority.
3. **Apply the evidence audit table.**

   | Claim type | Accepted evidence | Default verdict |
   | ------------ | ------------------- | ----------------- |
   | CI gate result | `gh pr checks <pr> --json name,state` showing the named gate in SUCCESS state | Run `gh pr checks`; report gate state verbatim |
   | Measured metric in PR body | (a) CI-produced artifact URL, OR (b) re-executed run output | NO-GO unless either is present |
   | Committed `epoch*.log` file in PR | n/a | **NEVER** independent evidence |
   | Training result on slow path | detached-execution run record | NO-GO unless a follow-up evidence-collection task has landed |

4. **Report** using the output contract below. **Do not soften the verdict.** A NO-GO with a clear "here is what would change it" answer is the right outcome for a fabricated claim.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Repo audit for claims | Running a whole-repository review to verify one claim | Repo audits check repositories, not individual claims | Use this per-claim audit instead |
| Emoji as evidence | Accepting a "✓" in a comment | Anyone can type a checkmark | Only runnable/queryable channels count |
| Re-reading the claim | Re-reading the same PR body line to "find" evidence | The claim is not its own evidence | Query the live gate state or re-run the safe command |
| Trusting the author | "Looks good, it's from a trusted author" | Evidentiary channel matters, not source reputation | Audit the channel every time |

## Results & Parameters

### Output contract

```markdown
## Verification verdict for <one-line claim>

| Field | Value |
|-------|-------|
| Claim | <verbatim claim text> |
| Class | CI gate / measured metric / training result / operational |
| Evidence cited | <path, URL, or PR #N> |
| Evidence channel | CI-produced artifact / re-executed run / committed file (NOT EVIDENCE) / none |
| Verdict | GO / CONDITIONAL / NO-GO |
| Action | <one-line "what would change the verdict"> |
| Policy reference | evidence-integrity policy |
```

Then a short paragraph (≤ 4 lines) explaining the verdict.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Athena | Shipped as the `verification` plugin skill; exercised across HomericIntelligence repositories | Migrated 2026-07-16 |

## References

- Athena evidence-integrity policy: `docs/policies/evidence-integrity.md` in HomericIntelligence/Athena
- Related: [finish-branch-delivery-workflow.md](finish-branch-delivery-workflow.md), [code-review-before-merge-workflow.md](code-review-before-merge-workflow.md)
