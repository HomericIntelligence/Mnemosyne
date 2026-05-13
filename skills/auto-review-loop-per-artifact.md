---
name: auto-review-loop-per-artifact
description: "Per-artifact write-review-fix-rereview-commit loop that replaces user-pause-for-review with subagent-driven correctness audits. Use when: (1) producing a series of related markdown deliverables where citation/cross-reference correctness matters, (2) long-running task that would otherwise need many user interruptions to ask 'is this OK', (3) working with a project-specialized reviewer that has WebFetch or other primary-source verification capability, (4) downstream cost of a wrong artifact is high (e.g., 25 issue bodies citing a fabricated paper)."
category: evaluation
date: 2026-05-12
version: "1.0.0"
user-invocable: false
verification: verified-local
tags: [review-loop, subagent, triage, convergence, divergence, confirmation-rereview, per-artifact-commit, audit, orchestration]
---

# Auto Review Loop — Per Artifact

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-05-12 |
| **Objective** | Replace user-pause-for-review checkpoints with a subagent-driven write-review-fix-rereview-commit loop applied per artifact, so long-running multi-artifact tasks (research docs, issue bodies, design specs) self-correct without blocking on the user. |
| **Outcome** | Operational. 13 review-loop cycles ran across 7 artifacts in one session; each cycle caught real findings (multiple critical, dozens of high-confidence). Two critical findings were caught post-merge that prior reviewers had missed. |
| **Verification** | verified-local — used 13 times across one session, with each cycle catching real findings. Documented in commit chain `84013ec..44affc3` in PRs #2/#3 of mvillmow/Random Predictive-Coding-in-Mojo. |

## When to Use

- Producing a series of related markdown deliverables (research docs, issue bodies, design specs) where citation/cross-reference correctness matters and a downstream consumer will rely on the claims.
- Long-running task that would otherwise require many user interruptions for "is this OK?" — reserve user attention for decisions, not audits.
- Working with a project-specialized reviewer subagent that has WebFetch or other primary-source verification capability beyond what the orchestrator already has.
- Cost of a wrong artifact downstream is high (e.g., 25 GitHub issue bodies citing a fabricated paper, a published research note with an inverted inequality, a design doc whose pseudocode would propagate to implementation).

## When NOT to Use

- One-shot artifacts where review can happen at the end as a single human read-through.
- Code where CI / typechecking is the better correctness gate (use TDD or pre-commit instead).
- Tasks where there's no specialized reviewer that adds signal beyond what the orchestrator already does — looping yields diminishing returns.

## Verified Workflow

### Quick Reference

```python
def auto_review_loop(artifact_path, reviewer_subagent, max_rounds=3):
    findings = None
    for round_n in range(1, max_rounds + 1):
        report = dispatch_reviewer(
            reviewer_subagent,
            artifact_path,
            prior_findings=findings if round_n > 1 else None,
        )
        if report.critical == 0:
            commit(artifact_path, message=f"... ({round_n} review rounds)")
            log_worth_checking(report.worth_checking, "notes/review-followups.md")
            return CONVERGED
        # Triage and apply
        for f in report.critical:
            apply_fix(f)
        for f in report.high_confidence:
            if f.fix_is_unambiguous:
                apply_fix(f)
            else:
                add_assumption_marker(f.location)
        findings = report
    surface_to_user(findings)  # Diverged after max_rounds
    return DIVERGED
```

Confirmation re-review prompt template:

```text
Confirmation re-review of <artifact_path> after N fixes from prior round.

**Items being verified:**
1. <Prior finding 1 description> — should now read X. Verify.
2. <Prior finding 2 description> — should now satisfy Y. Verify.
...

**Verdict criteria:** the file passes if all N items verify clean and no
new errors introduced.

Report under <budget> words.
```

### Detailed Steps

**1. Triage the reviewer's findings explicitly.** A reviewer typically returns three classes of finding; route each one differently:

- **Critical findings** → fix immediately, return to step 2 (re-review). These block the commit.
- **High-confidence concerns** → fix if the fix is unambiguous (one obvious correction); otherwise mark `[ASSUMPTION — to validate]` at the location and move on.
- **"Worth checking" items** → log to `notes/review-followups.md`; do not block the commit.

Without explicit triage, every finding becomes ambiguous and either everything blocks (slow) or nothing blocks (drift). The triage rule is the load-bearing decision.

**2. Confirmation re-review prompt names the prior round's findings.** The re-review prompt is NOT generic ("review this file again"). It explicitly enumerates each finding from the prior round and asks the reviewer to confirm the fix is present. This anchors the reviewer's attention and produces "verified item N: present, line X" outputs that are auditable. A generic re-review prompt causes the reviewer to re-derive the audit from scratch and miss confirmation of specific fixes.

**3. Convergence criterion: zero critical findings AND no new criticals introduced by the fixes.** A common failure is the fix-pass introducing a new critical (e.g., over-correcting an arithmetic claim and breaking the next paragraph's cross-reference). The convergence test is "no critical findings AND prior fixes verified clean," not just "no critical findings now."

**4. Divergence definition.** If 3 review rounds produce critical findings (any critical, even if different ones each round), the loop has diverged. Surface to user with: the divergent findings, the attempted fixes, and a recommendation. This bounds the cost of a runaway loop and prevents infinite iteration on a confused reviewer or a fundamentally broken artifact.

**5. Each artifact gets its own commit.** Don't batch-commit "Pass 1 complete." Each markdown file lands in its own commit so the reviewer's findings and the corresponding fix are colocated in `git log`. This is useful when a future session needs to understand why a particular line reads the way it does.

**6. Reviewer is read-only.** The reviewer reports findings, doesn't apply them. The orchestrating session (Claude) decides which findings to apply and how. This separation prevents the reviewer from "helpfully" rewriting the artifact in unauthorized ways and keeps the audit trail clean.

**7. Per-artifact reports stay inline; cross-artifact swarm reports land on disk.** Per-artifact review-loop reports are tool-call outputs (consumed by the orchestrator, not committed — they would clutter the repo). Cross-artifact swarm reviews (e.g., "review all 5 scoping docs across 5 dimensions") DO write findings to `notes/review_NN_role.md` so future sessions can audit which review pass caught which finding.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Pause-for-user-review at every step | Plan §3.0 originally had "stop for user review" between LITERATURE/ALGORITHM/CHARTER passes | User explicitly redirected: "don't pause for review, just update the plan to run the review using sub-agents and integrate the feedback" | Manual review pauses don't scale; reviewer agents do. Reserve user time for decisions, not audits. |
| Skipping confirmation re-review on "small" fix | After applying 8 fixes to LITERATURE.md, started to skip re-review since fixes seemed mechanical | The merged reviewer found a new finding the prior reviewer missed (ASGE VGG11 vs ResNet18-CHx4 architecture-scoping). Skipping would have shipped the broken claim. | Always re-review after fixes; the new round may catch what the prior round missed because the fixes change the context the reviewer reads. |
| Generic re-review prompts | Tried "review this again" without naming prior findings | Reviewer re-derived the audit from scratch and missed confirmation of specific fixes | Re-review prompts must enumerate prior findings ("verify item 1: should now read X") so the reviewer's output is checkable against the fix list. |

## Results & Parameters

### Loop control parameters (recommended defaults)

| Parameter | Default | Notes |
|-----------|---------|-------|
| `max_rounds` | 3 | After 3 rounds with criticals remaining, escalate to user. Bounds runaway loops. |
| Convergence test | `report.critical == 0 AND no new criticals introduced by prior fixes` | Both clauses required. The "no new criticals" clause catches over-correction. |
| Divergence test | 3 review rounds with any critical findings remaining | Any critical, even if different ones each round, counts toward the 3. |
| Per-artifact commit | One commit per artifact | Colocates findings + fixes in `git log`; do not batch. |
| Reviewer permissions | Read-only | Orchestrator applies fixes. Prevents unauthorized rewrites and keeps audit trail clean. |

### Triage matrix (apply per finding)

| Finding class | Action | Blocks commit? |
|---------------|--------|----------------|
| Critical | Fix immediately, re-review | Yes |
| High-confidence + unambiguous fix | Fix immediately, re-review | No (folded into next round) |
| High-confidence + ambiguous fix | Mark `[ASSUMPTION — to validate]` at location | No |
| Worth-checking | Log to `notes/review-followups.md` | No |

### Confirmation re-review prompt (copy-paste)

```text
Confirmation re-review of <artifact_path> after N fixes from prior round.

**Items being verified:**
1. <Prior finding 1 description> — should now read X. Verify.
2. <Prior finding 2 description> — should now satisfy Y. Verify.
3. <Prior finding 3 description> — should now satisfy Z. Verify.

**Verdict criteria:** the file passes if all N items verify clean and no
new errors introduced.

Report under <budget> words.
```

### Loop pseudocode (copy-paste)

```python
def auto_review_loop(artifact_path, reviewer_subagent, max_rounds=3):
    findings = None
    for round_n in range(1, max_rounds + 1):
        report = dispatch_reviewer(
            reviewer_subagent,
            artifact_path,
            prior_findings=findings if round_n > 1 else None,
        )
        if report.critical == 0:
            commit(artifact_path,
                   message=f"... ({round_n} review rounds)")
            log_worth_checking(report.worth_checking,
                               "notes/review-followups.md")
            return CONVERGED
        for f in report.critical:
            apply_fix(f)
        for f in report.high_confidence:
            if f.fix_is_unambiguous:
                apply_fix(f)
            else:
                add_assumption_marker(f.location)
        findings = report
    # Diverged after max_rounds
    surface_to_user(findings)
    return DIVERGED
```

### Report-routing rules

| Report type | Destination | Rationale |
|-------------|-------------|-----------|
| Per-artifact review-loop report | Inline tool output (consumed by orchestrator) | Would clutter the repo; only orchestrator needs it |
| Cross-artifact swarm review report | `notes/review_NN_role.md` (committed) | Future sessions need to audit which review caught which finding |
| Worth-checking items | `notes/review-followups.md` (committed, append-only) | Surface backlog for future sessions; do not block current commit |

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| mvillmow/Random | Predictive-Coding-in-Mojo Phase 0; ran 13 review-loop cycles across 7 artifacts (5 scoping docs + epic body + 25 issue bodies in 2 batches), caught 2 critical findings post-merge that two earlier reviewers had missed | Commit chain `84013ec..44affc3` in PRs #2/#3 |
