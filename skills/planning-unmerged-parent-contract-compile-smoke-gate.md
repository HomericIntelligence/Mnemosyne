---
name: planning-unmerged-parent-contract-compile-smoke-gate
description: "Plan an issue whose dependency parent issue is NOT yet merged (verified via `gh pr list --search '<N>' --state all` returning `[]`) but has an APPROVED plan on file. Consume the parent's approved-plan contract (function signatures, struct field names, return types) instead of re-implementing or hedging — but mandate a compile-smoke-test (`pixi run mojo build --Werror`) as the FIRST verification step immediately after the parent PR merges to catch contract drift. Grep-verify every numeric count claim (parameter counts, field counts) against the current tree AND flag same-line coordination hazards when multiple planned PRs touch identical stale comments. List every external API you cite but did NOT `Read` in a dedicated 'Unverified API Assumptions' section so reviewers can target verification. For random-init deep-network convergence thresholds, use a two-tier assertion (hard floor `loss[final] < loss[0]` + aspirational `loss[final] < 0.95 * loss[0]`) — single-epoch loss decrease on random-init nets is a HYPOTHESIS, not a guarantee. Use when: (1) planning issue B where B depends on unmerged issue A but A has an approved plan comment, (2) about to cite an API signature (`randn`, `AnyTensor.store`, `cross_entropy`) you have not `Read` in the source, (3) writing a numeric count into a plan (e.g. 'total trainable parameters: 81') that another planned PR also touches, (4) asserting a loss-decrease threshold on random-init deep networks after few batches."
category: architecture
date: 2026-07-02
version: "1.0.0"
user-invocable: false
verification: unverified
tags:
  - planning
  - unmerged-parent
  - approved-plan-contract
  - compile-smoke-test
  - contract-drift
  - grep-verify-counts
  - same-line-coordination-hazard
  - unverified-api-assumptions
  - two-tier-loss-threshold
  - random-init-convergence-hypothesis
---

# Planning against an Unmerged Parent — Contract + Compile-Smoke Gate

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-07-02 |
| **Objective** | Capture the planning meta-discipline for authoring issue B whose dependency parent issue A is NOT yet merged (`gh pr list --search "<A>" --state all` returns `[]`) but has an APPROVED plan comment on file. Consume the parent's approved-plan contract instead of re-implementing or hedging, and gate the whole downstream plan on a compile-smoke-test the moment A's PR merges. Add same-line coordination-hazard scans, an Unverified-API-Assumptions section for every cited-but-unread symbol, and a two-tier loss threshold for random-init deep-network convergence claims. |
| **Outcome** | Planning artifact produced; the training epoch this plan targets has NOT been executed. Learnings are from an adversarial plan review, not from a green CI run. |
| **Verification** | unverified — planning meta-skill; the ProjectOdyssey plan itself was reviewed but the resulting training epoch has not been executed. |
| **History** | v1.0.0: initial capture from ProjectOdyssey issue #5516 plan review (parent issue #5515 unmerged; only an approved-plan comment existed). Seven learnings distilled from six unverified-API assumptions plus a same-line-coordination hazard. |

> This skill is about the **PLAN-AUTHORING** angle when the dependency parent is still just a plan on paper.
> For the case where the parent is ALREADY MERGED and just needs to be read from `main`, see
> `planning-dependent-issue-unverified-upstream`. For the general "did this issue's premise even
> survive the last refactor?" audit, see `planning-verify-issue-premise-before-implementing`.
> This skill covers the specific gap those two leave: parent-plan exists, parent-code does NOT, and you
> are about to transcribe signatures from the plan comment into your own plan as if they were merged code.

## When to Use

- Planning issue B when B depends on unmerged issue A but A has an approved plan comment (verified: `gh pr list --repo <org>/<repo> --search "<A>" --state all --json number,state` returns `[]` and the plan comment is grade-B / GO).
- About to cite an API signature (`randn`, `AnyTensor.store`, `cross_entropy`, layer constructor kwargs) you have NOT `Read` in the source of truth.
- Writing a numeric count into a plan (e.g. `"total trainable parameters: 81"`, `"6 conv layers"`, `"20 BN gammas"`) that another planned PR also touches on the same line.
- Asserting a loss-decrease threshold (e.g. `"loss drops 5% in 10 batches"`) on a random-init deep network after only a handful of batches.

## Verified Workflow

<!-- The literal token "## Verified Workflow" is required by scripts/validate_plugins.py.
This skill's verification level is "unverified" — the PROPOSED WORKFLOW subsection below
carries the real semantics. Do not read this heading as an implicit warranty. -->

### Proposed Workflow (UNVERIFIED — planning artifact only)

> **Warning:** This workflow was distilled from an adversarial review of an unexecuted plan
> (ProjectOdyssey #5516). No downstream training run has produced green CI against it. Treat
> every checklist item as a hypothesis; the compile-smoke-test is the only gate that empirically
> discharges the "parent plan == parent code" assumption.

### Quick Reference

```bash
# 1. Confirm the parent dependency is NOT yet merged (returning [] means the plan
#    is a contract, not a fact):
gh pr list --repo <org>/<repo> --search "<PARENT_ISSUE_N>" --state all --json number,state

# 2. Grep-verify every numeric count claim BEFORE writing it into the plan:
grep -cE '<pattern>' <path>

# 3. Detect same-line coordination hazards (other planned PRs touching the same file):
gh pr list --repo <org>/<repo> --state open --search "<filename>" --json number,title,headRefName

# 4. Immediately after parent PR merges, run compile-smoke-test as verification step 1:
pixi run mojo build --Werror path/to/entrypoint.mojo
# Any compile error here means the parent implementer drifted from the approved plan.

# 5. For any random-init deep-network convergence claim, encode a two-tier assertion:
#    hard floor: loss[final] < loss[0]         (must hold, else training regressed)
#    aspirational: loss[final] < 0.95 * loss[0] (target; log SOFT-FAIL if missed)
```

### Detailed Steps

1. **Confirm the parent is unmerged and its plan is approved.**
   Run `gh pr list --repo <org>/<repo> --search "<PARENT_ISSUE_N>" --state all --json number,state`.
   An empty list (`[]`) means no PR exists yet — the parent is only a plan. Then read the parent
   issue's most recent plan comment and confirm it carries an explicit approval grade (grade-B / GO
   is the minimum in this codebase). If the plan is not yet approved, STOP: you cannot consume a
   contract that hasn't been ratified.

2. **Consume the contract, do not hedge or re-implement.**
   Once the parent plan is approved, transcribe function signatures, struct field names, and return
   types verbatim from the plan comment into your child plan. Do NOT invent "just-in-case" fallback
   code paths for the case where the parent plan doesn't ship — that hedging noise buries the real
   contract and doubles review surface. If the parent plan lands with drift, the compile-smoke-test
   in step 5 catches it; don't pre-hedge.

3. **List every cited-but-unread API in an `## Unverified API Assumptions` section.**
   For every symbol you referenced without `Read`-ing its source (`randn`, `AnyTensor.store`,
   `cross_entropy` label dtype, layer constructor kwargs), add a row to a dedicated section with
   columns: Symbol | Assumed Signature | Where Cited | Verify With. This gives the reviewer a
   targeted attack surface and gives the implementer an explicit pre-flight list. See the
   template in Results & Parameters.

4. **Grep-verify every numeric count claim AND scan for same-line coordination hazards.**
   For each count assertion (e.g. `"total trainable parameters: 81"`, `"6 conv layers"`), run a
   `grep -cE` against the current tree to derive the number from source. Then run
   `gh pr list --repo <org>/<repo> --state open --search "<filename>" --json number,title,headRefName`
   to see whether any OTHER open PR is planned to touch the same file. If two PRs both plan to edit
   the same stale comment line (e.g. `train.mojo:311 "Total trainable parameters: 84"`), coordinate:
   either sequence the merges with an explicit note, or reduce one PR's scope so it doesn't touch
   the shared line.

5. **Gate everything downstream on a compile-smoke-test the moment the parent PR merges.**
   Verification step 1 of the child implementation is `pixi run mojo build --Werror
   path/to/entrypoint.mojo`. If that fails, the parent implementer drifted from the approved plan
   (renamed `ResNet18Velocities` to `Velocities`, changed return tuple order, dropped a kwarg) and
   the child plan's transcribed signatures are stale. Fix the child plan against actual merged code
   BEFORE writing any tests. Do NOT skip this step in favor of "just start writing tests and see
   what fails" — that pushes contract-drift discovery to the slowest feedback loop.

6. **Encode a two-tier assertion for random-init deep-network convergence claims.**
   A "loss drops 5% in 10 batches" claim on a randomly-initialized ResNet with untuned SGD is a
   HYPOTHESIS, not a guarantee. Random-init nets can spend the first several batches on BN /
   layernorm adjustment before loss trends monotonically down. Encode a hard floor (`loss_final <
   loss_initial`, must hold or training regressed) AND an aspirational target
   (`loss_final < 0.95 * loss_initial`, log SOFT-FAIL when missed). Only the hard floor gates CI.

7. **Read any file cited as prior-art precedent.**
   If your plan says "analogous to `examples/lenet_emnist/train.mojo`", you must have opened that
   file and quoted a line-anchored range. A filename in a plan without a line-anchored quote is an
   unverified claim; either read it and cite the actual pattern, or drop the reference.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| 1 | Assumed `randn(shape, dtype, seed=..., mean=..., std=...)` signature without reading `projectodyssey.tensor.tensor_creation`. Transcribed the signature from analogy to numpy / PyTorch. | If actual `randn` lacks `mean`/`std` kwargs or has different positional order, the synthetic-data builder fails to compile at first invocation. The plan reads plausibly but the first line of implementation errors. | Any API cited in a plan MUST have been `Read` from source OR flagged in an `## Unverified API Assumptions` section. Analogy to numpy/PyTorch is not a signature source of truth. |
| 2 | Used `AnyTensor.store[DType.float32](idx, val)` without verifying method existence. Skill confirmed `.load[dtype]` exists at `any_tensor.mojo:1479` but `.store` was NOT verified — assumed by read/write symmetry. | The setter may actually be `.set()` or `.update()`, not `.store`. Symmetry of accessor API is an assumption, not a fact — writing the plan on that assumption strands the label-tensor builder at the first setter call. | Grep for the setter form explicitly (`grep -nE 'fn (store\|set\|update)\b' any_tensor.mojo`) before citing. Read/write API symmetry is a heuristic; verify it. |
| 3 | Assigned `cross_entropy` labels as `float32` via `AnyTensor.set(idx, Float32(c))`. Mojo-tensor-design skill explicitly warns "update() requires int32 or int64 labels, got float32", but the plan authored float32 labels anyway. | Class-index targets are almost always integer-typed. Authored float32 labels are guaranteed to trip the loss function's dtype guard at the first batch. Plan-review didn't cross-check the loss callee's dtype contract. | Read the callee's label-dtype contract in the skill/source BEFORE constructing test tensors. Class indices are integer-typed by convention across every mainstream framework; treat that as a strong prior. |
| 4 | Cited `examples/lenet_emnist/train.mojo` and `examples/alexnet_cifar10/run_train.mojo` as "analogous class-mean-signal convergence tests" but never opened them. Referenced as precedent for the 5% loss-decrease threshold. | If those tests use a different threshold, different data shapes, or different assertion styles, the analogy fails silently and the reviewer has no way to check. A filename without a quote is not evidence. | Any file cited as prior-art precedent MUST be `Read` and quoted with a line-anchored range. A filename in a plan without a line-anchored quote is an unverified claim; drop it or verify it. |
| 5 | Asserted `loss[final] < 0.95 * loss[0]` on 10 batches of random-init ResNet-18 with untuned SGD-momentum (lr=0.01) as a hard CI gate. | 5% decrease over 10 batches from random init on separable-but-noisy synthetic data is plausible-but-not-guaranteed. Random-init deep nets can spend the first several batches on BN adjustment before loss trends down. A "monotone-ish" run gets flagged as regression when it isn't. | Convergence thresholds on random-init deep nets are HYPOTHESES. Use a two-tier assertion: hard floor `loss[final] < loss[0]` (real regression) plus aspirational `< 0.95 * loss[0]` (target, log SOFT-FAIL). Only the hard floor gates CI. |
| 6 | Trusted #5515's approved-plan text as if it were merged code. Read the plan comment, transcribed signatures verbatim, but the implementer may rename `ResNet18Velocities` to `Velocities`, or return `Tuple` instead of a struct, or reorder returns. | Silent drift compiles into the child plan as false facts. The child plan reads consistent but references symbols that don't exist post-merge. Discovery is pushed to the slowest feedback loop (test failures). | Consume the parent contract as a HYPOTHESIS with a mandatory `pixi run mojo build --Werror` compile-smoke-test as verification step 1 immediately after the parent PR merges. That is the ONLY step that empirically discharges the "plan == code" assumption. |
| 7 | Same-line coordination hazard on `train.mojo:311` "Total trainable parameters: 84". Both #5515's plan and this plan touch the identical stale comment line. | Whichever PR merges second gets a rebase conflict on that line — or worse, overwrites the other PR's fix silently if the conflict is auto-resolved. Neither plan flagged the collision. | When grep-verifying a count claim, ALSO grep for other planned PRs touching the same line: `gh pr list --repo <org>/<repo> --state open --search "<filename>" --json number,title,headRefName`. Either coordinate merge order explicitly or narrow one PR's scope so it doesn't touch the shared line. |

## Results & Parameters

### Verified On

| Repository | Session | Notes |
|------------|---------|-------|
| ProjectOdyssey | GitHub issue #5516 plan (dependency #5515 unmerged) | Session 2026-07-02 — plan reviewed adversarially, not executed |

### Copy-Paste: Grep for parameter count

```bash
# Count parameter fields declared in a model file. Adjust the pattern for the
# tensor-container convention used in your codebase.
grep -cE '^    var .+_(kernel|bias|gamma|beta): AnyTensor' examples/resnet18_cifar10/model.mojo
```

### Copy-Paste: Compile-smoke-test after parent merges

```bash
# Verification step 1 immediately after the parent PR merges. If this fails, the
# parent implementer drifted from the approved plan — fix the child plan's
# transcribed signatures against actual merged code before writing tests.
pixi run mojo build --Werror path/to/entrypoint.mojo
```

### Copy-Paste: Detect same-line coordination hazards

```bash
# Find every open PR that plans to touch the same file. Read each hit's diff
# region: if two PRs both plan to edit the same stale comment or numeric literal,
# coordinate merge order or reduce scope.
gh pr list --repo <org>/<repo> --state open --search "<filename>" --json number,title,headRefName
```

### Copy-Paste: Two-tier loss-threshold assertion (Mojo pseudo-code)

```mojo
# Hard floor — must hold for training to be considered functional. Gates CI.
# If loss regressed from initial, training is broken (bad gradient sign, bad LR,
# broken forward pass) — this is a real signal.
assert loss_final < loss_initial, "training regressed loss"

# Aspirational — target we want to hit but do NOT gate CI on. Random-init deep
# nets can be "monotone-ish" for many batches before hitting the aspirational
# decrease. Log the miss so it shows up in telemetry without red CI.
if loss_final < 0.95 * loss_initial:
    print("PASS: 5% decrease target hit")
else:
    print("SOFT-FAIL: loss decreased but under 5% target - investigate")
```

### Copy-Paste: Unverified API Assumptions section template

```markdown
## Unverified API Assumptions

Every symbol below was CITED in this plan but NOT `Read` from source. Reviewer must
verify each before approving; implementer must smoke-test each before writing tests.

| Symbol | Assumed Signature | Where Cited | Verify With |
|--------|-------------------|-------------|-------------|
| `randn` | `randn(shape, dtype, seed=..., mean=..., std=...)` | synthetic-data builder | Read `projectodyssey/tensor/tensor_creation.mojo` |
| `AnyTensor.store[dtype]` | `store[DType.float32](idx, val)` | label tensor construction | `grep -nE 'fn (store\|set)\b' any_tensor.mojo` |
| `cross_entropy` label dtype | tolerates float32 labels | loss computation | Read the loss source; check for dtype-guard raise |
```

### Confirm parent is unmerged

```bash
# Empty list ([]) means the parent is only a plan, not merged code. That's the
# trigger to consume the parent's plan as a CONTRACT and gate downstream work
# on a compile-smoke-test after the parent PR merges.
gh pr list --repo <org>/<repo> --search "<PARENT_ISSUE_N>" --state all --json number,state
```
