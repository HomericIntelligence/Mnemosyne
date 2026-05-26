---
name: architecture-estimate-rewrite-read-substrate-first
description: "Before estimating a large refactor or rewrite, read the existing substrate code in full — TODO.md and roadmap LOC estimates are commonly pessimistic by 3-5x because they don't credit infrastructure that already exists. Use when: (1) starting a substrate-rewrite epic, (2) a TODO.md or roadmap estimates thousands of LOC or weeks of work, (3) an audit flags a CRITICAL gap based on docs, (4) before committing to a multi-week refactor estimate to a user or stakeholder."
category: architecture
date: 2026-05-26
version: "1.0.0"
user-invocable: false
verification: verified-ci
tags: []
---

# Read the Substrate Before Estimating a Rewrite

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-05-26 |
| **Objective** | Avoid 3-5x pessimistic effort estimates on large refactors by reading the existing substrate code before trusting roadmap/TODO LOC numbers. |
| **Outcome** | Successful — revised a "5000 LOC, 2-4 weeks" TODO estimate down to ~1400 LOC after a Phase 0 substrate read; actual landed PR was +937 LOC. |
| **Verification** | verified-ci — ProjectOdyssey PR #5457 landed Phase 2 autograd substrate at +937 LOC, within the revised 1400 estimate, far below the 5000 in the original TODO. CI passed on merge. |

## When to Use

- Before starting a substrate-rewrite epic (autograd, scheduler, executor, runtime, etc.)
- When a `TODO.md`, roadmap, or design doc estimates "thousands of LOC" or "weeks" of work
- When an audit flags a CRITICAL gap based on docs ("autograd doesn't exist", "no scheduler") — verify against the code, not the README
- Before committing to a multi-week refactor estimate to a user or stakeholder
- When scoping a parallel-agent swarm dispatch — bad estimates lead to bad parallelization plans

## Verified Workflow

### Quick Reference

```bash
# Phase 0: Read the substrate BEFORE estimating.
# 1. Locate the existing substrate files relevant to the rewrite.
find src/ -name "*.mojo" -path "*<subsystem>*" | xargs wc -l

# 2. Read each file in full — not just the public interface.
#    For each file, write down: what works today, with line citations.

# 3. List the actual gaps with minimum-needed signatures.

# 4. THEN estimate. Treat TODO.md LOC numbers as upper bounds, not targets.
```

### Detailed Steps

1. **Resist the urge to trust the TODO.** When a roadmap or TODO file states "Phase X: ~N000 LOC future major release", treat N as an upper bound from a pessimistic author, not a target.

2. **Inventory the substrate.** List every file in the subsystem with `find` + `wc -l`. Note what each file claims to do (top docstring) and its size.

3. **Read each substrate file in full.** Not skim — full read. For each file, record:
   - Public functions/types that already work
   - Internal invariants the code relies on (e.g., "forward execution order = topo order")
   - Storage/state already polymorphic enough for the planned extension (e.g., a `List[AnyTensor] + List[List[Int]] + List[Float64]` struct that already handles arbitrary saved-tensor shapes)
   - Dispatch tables, registries, or vtables already in place

4. **Cite line numbers as evidence.** Don't claim "X already works" without a `file.mojo:123` citation. The citations become the substrate-read receipt.

5. **List the actual gaps.** For each missing capability, write the minimum-needed signature/contract — not a full design. This separates "real new code" from "wiring".

6. **Revised estimate = new code only.** Do not re-count code that already works. If existing infrastructure handles 70% of the planned epic, the LOC estimate is 30% of the TODO number.

7. **Validate by landing.** Ship the smallest end-to-end slice of new code. Compare actual LOC against the revised estimate, not the original TODO. If revised estimate was right (within ~50%), the substrate read paid off.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| 1 | Trusted `src/projectodyssey/autograd/TODO.md` "Phase 2: ~5000 LOC future major release" as the authoritative effort estimate without reading the substrate. | Estimate was 3-5x too high. Existing `GradientTape.backward()`, `VariableRegistry.set_grad()` accumulation, and `SavedTensors` polymorphism already covered ~70% of the planned work. Acting on the 5000 LOC number would have made the epic look unschedulable and forced an unnecessary multi-week breakdown. | TODO.md describes aspirations; code describes actual state. Read the code before estimating. |
| 2 | Trusted a repo audit's "CRITICAL: autograd missing" framing without verifying against `tape*.mojo` and `variable.mojo`. | The audit conflated "documented feature" with "implemented feature". The autograd substrate was already implemented at the tape/registry layer — only op coverage and a few dispatch arms were missing. Treating the gap as "missing" instead of "incomplete" would have justified a from-scratch rewrite. | Audits that flag CRITICAL gaps based on README/TODO scans must be re-verified against the code. "Missing" and "incomplete" are different remediation profiles. |

## Results & Parameters

**Phase 0 substrate-read checklist** (copy-paste into the issue/PR description before estimating):

```markdown
## Phase 0 — Substrate Read (complete BEFORE estimating)

Files read in full:
- [ ] `path/to/substrate1.mojo` (N LOC) — what works: …
- [ ] `path/to/substrate2.mojo` (N LOC) — what works: …
- [ ] `path/to/substrate3.mojo` (N LOC) — what works: …

What already works (with line citations):
- `substrate1.mojo:123` — feature A
- `substrate2.mojo:45`  — feature B
- `substrate3.mojo:200` — feature C

What is actually missing (minimum-needed signatures only):
- `op_foo(x: Tensor) -> Tensor` — not yet implemented
- dispatch arm for `OpKind.BAR` in `dispatch.mojo`

Revised LOC estimate: ~X (vs TODO.md "~Y")
Justification: ~Z% of planned work already in substrate.
```

**Heuristic ratios** (from observed cases):

| TODO/Roadmap Estimate | Typical Actual (after substrate read) | Ratio |
|-----------------------|----------------------------------------|-------|
| "5000 LOC, 2-4 weeks" | ~937 LOC, days | ~5x pessimistic |
| "Major version rewrite" | Incremental amendment | varies |
| "CRITICAL: missing" (per audit) | "incomplete, 30% gap" | re-classify |

**Verified case — ProjectOdyssey Phase 2 autograd (PR #5457):**

- Original TODO: `src/projectodyssey/autograd/TODO.md` → "Phase 2 full tape-based autograd: ~5000 LOC future major release"
- Substrate-read discoveries:
  - `GradientTape.backward()` already iterates nodes in linear reverse order — works because forward execution is topo order. No DAG topo sort needed.
  - `VariableRegistry.set_grad()` already accumulates gradients (`has_grad ? add : copy`). Multi-use parameter case already solved.
  - `SavedTensors` already had `tensors: List[AnyTensor] + shapes: List[List[Int]] + scalars: List[Float64]` — sufficient polymorphism for all conv/pool hyperparams. No new struct types needed.
  - 11 `variable_*` ops + 10 dispatch arms already existed.
- Revised estimate: ~1400 LOC.
- Actual landed: +937 LOC (PR #5457, merged, CI green).
- Ratio: 5000 / 937 ≈ 5.3x pessimism in original TODO.

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| ProjectOdyssey | Phase 2 autograd substrate, PR #5457 (merged) — TODO claimed 5000 LOC, actual 937 LOC after Phase 0 substrate read | Repo audit flagged autograd as CRITICAL gap (C3); Phase 0 read of `tape_types.mojo`, `tape.mojo`, `variable.mojo`, `backward_ops.mojo` revealed substrate was ~70% complete |
