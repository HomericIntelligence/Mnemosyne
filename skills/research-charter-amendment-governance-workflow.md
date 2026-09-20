---
name: research-charter-amendment-governance-workflow
license: BSD-3-Clause
description: "Handle research-charter amendments when hardware, policy, or evidence changes. Distinguish descriptive updates from protected acceptance-criteria changes."
category: documentation
date: 2026-07-11
version: "1.1.0"
user-invocable: false
verification: verified-ci
tags: [research-governance, charter-amendment, pinned-thresholds, trigger-matrix, descriptive-vs-contractual, status-labels, falsifiable-exit-conditions, mid-run-pivot, anchor-traceability, strict-audit, experiment-charter, failure-cascade]
history-source: "https://github.com/HomericIntelligence/Mnemosyne/blob/ed1bd4f54fd4aaba446af92c8b3ab9aff2589ae3/skills/research-charter-amendment-governance-workflow.history"
history-cleanup-date: "2026-09-20"
---

# Research Charter Amendment Governance Workflow

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-07-11 |
| **Objective** | Amend a pinned research charter (contractual thresholds/criteria) safely when a trigger event fires mid-project, without improvising governance or silently rewriting the contract |
| **Outcome** | CHARTER-AMEND-01 merged after a 2-round adversarial strict audit at ~92% weighted score, zero critical/major findings; entire flow completed in one session alongside parallel implementation work |
| **Verification** | verified-ci |

## When to Use

- A research project pinned its success criteria (gate thresholds, phase criteria, outcome labels) in a charter doc and a real-world event now forces a change.
- A trigger event fires mid-project: hardware allocation reduced/pulled, a dependency breaks, a phase issue closes `refuted`, or the user pivots training policy mid-run.
- You must classify edits into "can land immediately" vs "needs user approval" against a contract document.
- You are defining a `blocked:*` / `hold:*` status label and it will face a strict audit.
- A budget or schedule line derives from an anchor number (e.g., hours/epoch) and auditors will ask where the number comes from.
- A long training run must be stopped partway because policy changed, and you must decide what to do with the partial epochs.

## Verified Workflow

### Quick Reference

```bash
# 1. Confirm the trigger maps to a pre-committed matrix row
grep -n "<trigger event>" FAILURE_CASCADE.md   # trigger -> cancels/replans/amends -> surface-to-user?

# 2. File the amendment issue BEFORE editing any pinned value
gh issue create --title "[CHARTER-AMEND] <clause>: <old> -> <new>" \
  --body "Clause: ... | New value: ... | Justification: ... | Affected issues: #a #b #c"

# 3. Classify every edit: descriptive lands now; contractual waits for approval
# 4. Amendment PR = PROPOSAL + descriptive records ONLY; verify pinned files untouched:
git show --stat HEAD -- EXPERIMENT_CHARTER.md SHARED_PRELUDE.md   # must be empty pre-approval

# 5. Post-approval second pass: apply charter edits, original values preserved as strikethrough
```

### Detailed Steps

1. **Pin the governance before you need it.** The workflow only works because the project pre-committed three artifacts: (a) a pinned charter whose thresholds are explicitly contractual, (b) an amendment procedure — file a `[CHARTER-AMEND]` issue containing clause + new value + justification + affected-issues list; the amendment merges only after every listed issue is edited; original values are preserved as strikethrough, never deleted — and (c) a FAILURE_CASCADE trigger matrix mapping each trigger event to what cancels, what replans, what requires amendment, and whether to surface to the user. When the user pulled GPU hardware mid-project, the response was mechanical (look up the "hardware allocation differs" row), not improvised.
2. **Distinguish descriptive records from changes to agreed criteria.** The recorded
   charter amendment procedure reserved threshold, phase-criteria, and outcome-label
   changes for user approval. That requirement protects the pinned research contract.
   A current explicit user directive can supply that authority; do not ask again for
   the same change. When authority is missing, prepare the concrete amendment and
   continue descriptive updates or independent work while the decision is pending.
3. **Give status labels falsifiable exit conditions.** A `blocked:hardware` label was rejected by audit until it defined all four: the setter (executor, on trigger-class events), the clearer (user only), the falsifiable un-block condition (a recorded strikethrough-and-repin of the hardware note in the pinned doc — an observable repo event, not "when hardware is back"), and the scope (pauses scheduling; assigns no outcome label). Precedent-match your label namespace: an existing `hold:*` label with a 5-day SLA was the in-repo pattern to mirror, and any deliberate asymmetry (no SLA for procurement, since procurement has no bounded timeline) must be stated explicitly, not left implicit.
4. **Handle mid-run policy pivots without discarding or silently counting data.** When the user pivoted to 1-epoch-only training while a 12-epoch run was at epoch 7: stop the run (per-epoch metric writes mean data through epoch N is already on disk); the epoch-0 record becomes the policy-compliant datapoint; epochs 1..N are retained as a clearly-labeled pre-policy bonus trajectory — never silently discarded, never silently counted toward gates; the stop event is recorded with date + the directive quoted [sic] in config/notes/issue logs; any re-anchored gate values are PROPOSED with options and derivation shown, never silently picked by the executor.
5. **Make every anchor number trace to an observable artifact.** State the derivation method (e.g., log start marker + file mtime divided by logged events), give an uncertainty band, and mark where a closed measurement will supersede the estimate. If an earlier figure is discredited, it may survive only as an uncertainty-band edge explicitly labeled superseded-history.
6. **Resolve classification from the charter and the proposed effect.** An annotation
   that changes contractual meaning follows the applicable amendment procedure; an
   evidence update that resolves an assumption may fit ordinary documentation work.
   Inspect the trigger matrix and precedent. Ask only when a material ambiguity
   remains, naming the protected clause and the exact proposed change.
7. **Continue through review and correction as needed.** Select review depth from the
   consequences of the amendment. The recorded two-round audit is an example, not a
   fixed quota. Present any genuinely missing approval as one concrete decision with
   its consequences, and keep independent authorized work moving.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Unsupported anchor number | Asserted a wall-clock anchor of ~20.9 h/epoch citing a training log | Audit MAJOR: the cited log had no per-batch timestamps; mtime arithmetic gave 15.8 h (24% off), and the error propagated linearly into five budget lines | Derive anchors from observable artifacts (log start marker + file mtime / logged events), state the method + uncertainty band, and mark where a closed measurement supersedes; a discredited figure survives only as a superseded-history uncertainty-band edge |
| Undefined status label | Introduced `blocked:hardware` with only a prose description | Audit MAJOR: no setter, no clearer, no falsifiable un-block condition, no scope statement — the label could never be provably cleared | Every status label defines setter, clearer (user only), a falsifiable exit condition anchored to an observable repo event, and scope; precedent-match the existing label namespace and state deliberate asymmetries |
| Bundle-blur | Bundled an `[ASSUMPTION]`-marker resolution into the charter-amendment PR alongside contractual items | Audit minor: marker resolutions are explicitly not amendments; bundling blurred the descriptive/contractual boundary auditors verify by `git show --stat` | Keep the amendment PR to proposal + descriptive records only; resolve assumption markers under normal precedent in separate commits |
| Precedent-direction mismatch | Modeled the new label's SLA behavior without checking the existing `hold:*` pattern's direction | Audit minor: the in-repo precedent (`hold:*`, 5-day SLA) pointed the other way, and the deviation was unexplained | Precedent-match first; where you deliberately deviate (no SLA for procurement), say so explicitly in the label definition |

## Results & Parameters

**Measured outcome (predictive-coding-mojo CHARTER-AMEND-01, PR #42):**

- Merged after 2-round adversarial strict audit, ~92% weighted, zero critical/major findings remaining; verification level `verified-ci`.
- Full flow (trigger → proposal → 2 internal reviews → strict audit round 1 with 2 majors → fixes → round 2 confirmation → pre-sign-off softenings → merge) fit in one session, run alongside parallel implementation work.
- User decision surface: exactly one approval, with all consequences enumerated up front.

**Amendment issue template (recorded charter procedure):**

Use this lifecycle only where the applicable charter requires it. Existing explicit
authorization can satisfy its approval step; do not impose a second approval for the
same action.

```markdown
Title: [CHARTER-AMEND] <clause id>: <old value> -> <new value>
Body:
- Clause: <charter § and current pinned text>
- New value: <proposed text; original preserved as strikethrough on landing>
- Justification: <trigger event + trigger-matrix row that makes this required by definition>
- Affected issues: #a #b #c  (amendment merges only after all are edited)
- Classification: contractual — charter § edits land in a second pass post-approval
```

**Descriptive vs contractual quick test:**

| Edit | Class | Lands |
|------|-------|-------|
| Fired-trigger note, measured-value row, budget re-estimate | Descriptive | Immediately, under precedent |
| Gate threshold, phase criterion, outcome label, sequence-enforcement clause | Contractual | Second pass, post-approval only |
| Additive annotation to a pinned section (not on either list) | Route as amendment | State why (§-category change is the trigger) |
| `[ASSUMPTION — to validate]` marker resolution | NOT an amendment | Normal precedent, separate commit |

**Status-label definition checklist:** setter (role + trigger class), clearer (user only), falsifiable un-block condition (observable repo event), scope (what it pauses; what it does NOT assign), precedent match + stated asymmetries.

**Mid-run pivot record fields:** stop date, directive quote [sic], last completed epoch, policy-compliant datapoint id, pre-policy bonus-trajectory label, PROPOSED re-anchor options with derivations.

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| predictive-coding-mojo | CHARTER-AMEND-01, PR #42, GO ~92% weighted, 2-round strict audit, zero critical/major | Charter amendment triggered by mid-project GPU-hardware pull + 1-epoch policy pivot; verified-ci |
