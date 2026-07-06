---
name: planning-code-block-is-the-contract
description: "In a TASK/PLAN/REVIEW pipeline the plan reviewer and the downstream implementer both treat the plan's fenced code blocks as the CONTRACT — more authoritative than the surrounding prose — so any prose/code contradiction, self-contradictory/placeholder example code, mis-specified import (TYPE_CHECKING vs runtime), under-specified hardest artifact, or false 'mirrors sibling X' parity claim is a first-class defect that draws a NOGO even when the DESIGN is sound. Use when: (1) you are writing an implementation plan whose fenced code blocks will be graded by a plan reviewer and handed verbatim to an implementer, (2) your prose describes an import as TYPE_CHECKING-only but you have not confirmed the name is used only in annotations (a name used as a default field value / base class / decorator / isinstance target must be a RUNTIME import), (3) one test or artifact in the plan is materially harder (graph traversal, hypothesis property strategies, non-trivial algorithm) than the others and you are tempted to specify it at a LOWER altitude (prose-only) than the trivial ones, (4) you wrote 'mirrors sibling X' / 'like Y' / 'AST-based as in Z' without reading X's ACTUAL mechanism, (5) you left a placeholder or known-broken snippet with a 'the linter will catch this / replace if mypy flags it' fix-it note, (6) the target repo has a pr-policy gate and your plan omits the exact `Closes #<n>` close line and the `git commit -S -s` (GPG + DCO) signing requirement from the Implementation Order."
category: documentation
date: 2026-07-04
version: "1.1.0"
user-invocable: false
verification: unverified
history: planning-code-block-is-the-contract.history
tags:
  - planning
  - plan-review
  - code-block-contract
  - prose-code-parity
  - type-checking-vs-runtime-import
  - hypothesis-property-test
  - nogo-tightening
  - self-consistency
  - handoff-altitude
  - mirror-parity-claim
  - placeholder-snippet
  - pr-policy-compliance
  - hephaestus
  - myrmidons
---

# Planning: The Plan's Own Code Block Is the Contract

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-07-04 |
| **Objective** | Write an implementation plan (ProjectHephaestus issue #1811, a new pure-data `pipeline/` package) whose fenced code blocks survive plan review, given that the reviewer and downstream implementer treat those blocks as the authoritative contract |
| **Outcome** | R0 plan graded **B / NOGO** — the DESIGN was affirmed sound, but the NOGO was driven almost entirely by defects INSIDE the illustrative code blocks (prose/code contradiction, an under-specified hardest test, a self-contradictory placeholder assertion, a false "mirrors sibling X" parity claim, missing pr-policy items). R1 re-plan addressed four of five but "fixed" the fifth (a broken example assertion) only in a PROSE FOOTNOTE while leaving the broken line in the fence — so R1 was graded **B / NOGO AGAIN** on a SINGLE blocking finding that cited this skill by name. R2 finally converged by DELETING the broken line and writing the assertions correct-first in the code block, carrying no fix in prose. Plan not executed. This session is a CONFIRMED, end-to-end instance of this skill's OWN failure mode 3: a footnote fix does not clear a code-block defect. |
| **Verification** | unverified — this is a PLANNING artifact: no code was executed, no `pytest`/`mypy`/`ruff`/CI was run, and the plan (now R2) has NOT been re-reviewed to GO |

The central, generalizable insight from the #1811 R0→R1→R2 plan-review NOGOs:

**In a TASK/PLAN/REVIEW pipeline, the plan reviewer and the downstream implementer
both treat the plan's fenced code blocks as the CONTRACT — more authoritative than
the surrounding prose. So any contradiction between prose and code, or any
self-contradiction / placeholder inside the example code, is a first-class defect
that draws a NOGO, even when the design is correct.** A plan is not "prose with
illustrative snippets"; the snippets ARE the spec. The reviewer graded the #1811
R0 plan **B / NOGO** while explicitly affirming the design (a pure-data `pipeline/`
package with `WorkItem`/queues/routing) was sound. Every blocking finding lived
inside a code block or in a prose claim that a code block contradicted.

## When to Use

Apply this skill whenever you are authoring an implementation plan that a reviewer
will grade and an implementer will follow — i.e. any plan in a pipeline where the
plan is a handoff artifact, not a private scratchpad. Concrete triggers:

- You are **writing an implementation plan whose code blocks will be reviewed and handed to an implementer.** Treat every fenced block as spec text the implementer may paste verbatim; it must be internally consistent and green-able as written.
- Your plan's **prose describes an import as TYPE_CHECKING-only** ("we import `X` under `TYPE_CHECKING` to avoid a cycle") but you have NOT confirmed the name is used only in annotations. A name used as a runtime VALUE — a default field value (`stage: StageName = StageName.REPO`), a base class, a decorator, or an `isinstance` target — must be a REAL runtime import; a `TYPE_CHECKING`-only import would `NameError` at class-definition time.
- **One test or artifact is materially harder than the others** (graph traversal, `hypothesis` property strategies, a non-trivial algorithm) and you are about to specify it at a LOWER altitude (prose-only or a letter-reference) than the trivial artifacts that got full code blocks.
- You wrote **"mirrors sibling X" / "like Y" / "AST-based as in Z"** without reading X's actual mechanism.
- You left a **placeholder or known-broken snippet with a fix-it note** ("if mypy/ruff flags this, replace with …").
- The target repo has a **pr-policy gate** and your Implementation Order omits the exact `Closes #<n>` close line and the `git commit -S -s` (GPG + DCO) signing requirement.

**Key trigger:** you catch yourself writing prose that says one thing while the
adjacent code block does another — or shipping a snippet you already know is broken
"because the linter will catch it." In a plan, the code block is the contract; that
snippet is a NOGO magnet.

## Verified Workflow

> **Warning:** This is a PLANNING artifact. The workflow below has NOT been validated
> end-to-end — no code was executed, no `pytest`/`mypy`/`ruff`/CI was run, and the
> #1811 R1 plan has not been re-reviewed to GO. Treat every step as a hypothesis
> until CI confirms. The section is titled `Verified Workflow` only to satisfy the
> skill-file validator's required-heading check; the operative content is the
> **Proposed Workflow** below.

### Proposed Workflow

> **Warning:** This workflow has not been validated end-to-end. Treat as a hypothesis
> until CI confirms.

#### Quick Reference

```text
# The plan's fenced code blocks ARE the contract. Before submitting a plan for review:
1. prose/code parity      -> every claim in prose must match the adjacent code block VERBATIM.
2. import correctness      -> annotation-only name => TYPE_CHECKING (+ from __future__ import annotations);
                              runtime-value name (default arg, base class, decorator, isinstance)
                              => REAL runtime import. Verify the cycle you claim to avoid EXISTS.
3. hardest-artifact altitude -> the artifact with non-trivial algorithm/strategies needs a FULL
                              code block MORE than the trivial ones, not less.
4. no known-broken snippets -> never ship code you know is red with a "linter will catch it" note.
5. honest parity claims    -> read sibling X before writing "mirrors X"; if you use a STRONGER
                              mechanism (real ast.parse/ast.walk vs a text .splitlines() scan), SAY so.
6. pr-policy in the plan   -> Implementation Order must state the exact `Closes #<n>` line and
                              `git commit -S -s` (GPG + DCO).
```

Import decision rule, stated once:

```python
# Name used ONLY in annotations  ->  TYPE_CHECKING-only import + `from __future__ import annotations`
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .routing import StageName   # used only as `stage: StageName` annotations

# Name used as a RUNTIME VALUE  ->  real runtime import (default arg / base class / decorator / isinstance)
from .routing import StageName        # StageName.REPO is a default field VALUE at class-definition time

@dataclass
class WorkItem:
    stage: StageName = StageName.REPO   # <- evaluated at class-definition time => needs runtime import
```

#### Detailed Steps

1. **Establish prose/code parity, verbatim.** For every fenced block, re-read the surrounding prose and confirm it describes EXACTLY what the code does. In #1811 R0 the prose said `WorkItem.stage` was type-annotated `StageName` "via a `TYPE_CHECKING` import to avoid a cycle," but the code block wrote `from .routing import StageName` as a RUNTIME import (outside `TYPE_CHECKING`) plus a vestigial `if TYPE_CHECKING: pass`. An implementer could follow EITHER the prose (annotation-only) or the code (runtime) and get different, possibly broken, results — a MAJOR finding. Pick ONE, make prose and code agree word-for-word, and state WHY.

2. **Get the import mechanism right, and verify the cycle you claim.** The rule: a name used ONLY in annotations → `TYPE_CHECKING`-only import (requires `from __future__ import annotations`); a name used as a runtime VALUE (default arg, base class, decorator, `isinstance`) → a real runtime import. In #1811 the correct answer was a RUNTIME import, because `StageName` is a default field value (`stage: StageName = StageName.REPO`) evaluated at class-definition time — a `TYPE_CHECKING`-only import would `NameError`. Also verify the cycle you claim to avoid actually exists: in #1811, `routing.py` imports nothing from `work_item.py`, so there was never a cycle — the stated "TYPE_CHECKING to avoid a cycle" justification was itself wrong. Do NOT invoke `TYPE_CHECKING` as a reflex; prove the cycle first.

3. **Specify the HARDEST artifact at the HIGHEST altitude.** When some artifacts get full code blocks, the one with non-trivial algorithmic logic needs a full code block MORE than the trivial ones, not less. In #1811 R0, four production files and three simple test files got full or near-full treatment, but `test_routing_properties.py` — the `hypothesis` property test requiring graph traversal (every cycle passes through a budget key; budget+1 failures land at the fail target) — was left as a letter-reference to the issue with NO code. The MOST complex, highest-risk test was the LEAST specified, forcing the implementer to independently derive graph algorithms and hypothesis strategies — a MAJOR finding. Ship the explicit strategies (`st.sampled_from(...)`, `st.lists(..., unique=True)`), the graph helpers, and enumerate the concrete facts a reviewer can hand-check (e.g. "the only cycles are PLANNING↔PLAN_REVIEW, IMPLEMENTATION↔PR_REVIEW, IMPLEMENTATION↔CI, each guarded by budget key X").

4. **Never ship a known-broken snippet with a fix-it footnote — a footnote fix does NOT clear a code-block defect.** The code block is the contract, so it must be green-able as written. In #1811 R1 the property-(c) test still contained a tautological assertion `assert current != stage or route.fail_routes["*"] == stage and False` — the `and False` makes the right disjunct always false, so the whole assert collapses to `assert current != stage` and silently DROPS the intended "landed at the declared fail target" check — papered over with a prose "note for the implementer: if mypy/ruff flags this, replace with …". This re-triggered the SAME NOGO: R1 was graded **B / NOGO** on a single blocking finding that named this skill, because moving the correction into surrounding prose while leaving the broken code in the fence is not a fix — the reviewer treats the fence as the contract and NOGOs again. R2 converged only by DELETING the broken line entirely and writing property (c) correct-first with direct, self-contained assertions: `assert attempts == budget + 1`, `assert current == fail_target`, `assert fail_target != stage` — carrying NO fix in prose. Two specific smells to recognize and refuse: (a) **`X and False` / `... or <always-false>` tautologies** — a compound boolean whose intent is "landed at target AND target differs from source" must be TWO separate `assert` statements, never one `or`/`and` expression whose short-circuit semantics silently neuter half the check; prefer multiple simple asserts over one clever compound assert. (b) **A "the linter will catch this" placeholder** in any plan code block. Both cost an ENTIRE extra review round (R1→R2) that a correct-first R0/R1 code block would have avoided.

5. **Make "mirrors sibling X" claims name the sibling's ACTUAL mechanism.** Before writing "mirrors/like/AST-based as in sibling X," read X. In #1811 R0 the zero-I/O guard was repeatedly called "AST-based, mirroring `test_automation_boundary.py`" — but that sibling uses a `read_text().splitlines()` + `startswith` TEXT scan, not AST — a MINOR misdirection. If you are deliberately using a STRONGER mechanism (a real `ast.parse` / `ast.walk` that catches indented or in-function imports a line-prefix scan misses), SAY that explicitly rather than falsely claiming parity.

6. **Put pr-policy compliance items IN the plan.** A plan for a repo with a pr-policy gate must state, in the Implementation Order, the exact PR-body close line (`Closes #<n>` — capital C, no colon, on its own line) and the signing requirement (`git commit -S -s` for GPG signature + DCO Signed-off-by), or the plan is incomplete on policy. #1811 R0 omitted both — a MINOR finding.

#### R2 Confirmation — Failure Mode 3, Observed End-to-End

The #1811 R1→R2 round is a direct, real-world confirmation of failure mode 3 above.
R1 had already been told its ONLY remaining blocker was the broken assertion left in a
code block. It "fixed" it in a PROSE FOOTNOTE ("if mypy/ruff flags this, replace with …")
while leaving the broken line IN the fence. The R1 plan reviewer graded it **B / NOGO**
with a SINGLE blocking finding, explicitly citing this skill: "This is exactly the failure
mode the `planning-code-block-is-the-contract` skill was created to prevent … the reviewer
is being asked to confirm this finding, not override it." Two further durable lessons the
R2 fix surfaced:

- **When a plan reviewer cites the very skill that predicts the defect, do not argue — apply the skill's prescription verbatim (correct-first code, no footnote).** A reviewer's citation of a named skill is a convergence signal, not a debate opening. The convergent move is to edit the fenced code so it is correct as written, then resubmit; anything else re-triggers the same NOGO.
- **Ambiguous test helpers invite the exact fuzz the property is meant to catch — enumerate the domain explicitly.** R1's `_budget_key_for` / `_stage_has_budget` helpers looped over a key list and could pick a NON-loop-guarding budget for a stage, so the hypothesis strategy could sample stages the property does not actually cover. R2 replaced them with an explicit mapping — `_LOOP_GUARDED = {PLAN_REVIEW: "plan_review_iter", PR_REVIEW: "pr_review_iter", CI: "ci_fix"}` — so the strategy samples ONLY genuinely loop-guarded stages and the simulation is unambiguous. When a property test's domain is "the loop-guarded stages," ENUMERATE them explicitly rather than deriving them with a heuristic that can misfire.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Let prose and the code block disagree on an import | R0 prose said `WorkItem.stage` used a `TYPE_CHECKING` import "to avoid a cycle," but the code block wrote `from .routing import StageName` as a RUNTIME import with a vestigial `if TYPE_CHECKING: pass` | The reviewer/implementer treat the code block as the contract; the two conflicting instructions let an implementer follow EITHER path and get different (possibly broken) results — MAJOR | Pick ONE, make prose and code agree verbatim, and state WHY. A name used as a runtime VALUE (default arg/base class/decorator/isinstance) needs a REAL runtime import; only annotation-only names use `TYPE_CHECKING`. Verify the claimed cycle actually exists (here `routing.py` imports nothing from `work_item.py`, so there was no cycle) |
| Leave the hardest test as prose-only while trivial artifacts got code | R0 gave full code for 4 production files and described `test_work_item.py`/`test_queues.py`/`test_routing.py` behaviorally, but left `test_routing_properties.py` (a `hypothesis` property test needing graph traversal) as a letter-reference to the issue with NO code | The MOST complex, highest-risk test was the LEAST specified, forcing the implementer to independently derive the graph algorithm and hypothesis strategies — MAJOR (handoff-altitude mismatch) | Specify the HARDEST artifact at the HIGHEST altitude. When some artifacts get full code blocks, the one with non-trivial algorithmic logic needs a full code block MORE than the trivial ones. Ship explicit strategies (`st.sampled_from`, `st.lists(unique=True)`), graph helpers, and the enumerable facts a reviewer can check |
| Ship self-contradictory example code with a "linter will catch it" note | Even the R1 fix contains `assert current != stage or route.fail_routes["*"] == stage and False` (the `and False` makes the right disjunct always false), papered over with a prose note telling the implementer to replace it if mypy/ruff flags it | The code block is the contract; a known-broken snippet with a fix-it footnote is itself a defect and a NOGO magnet — the reviewer still has to flag it, and the implementer may paste it as-is | Do NOT ship example code you already know is broken. Write the correct assertion the first time: `assert current == route.fail_routes["*"]` plus `assert route.fail_routes["*"] != stage`. This is the highest-risk residual item in the R1 plan |
| "Fix" a flagged code-block defect in a PROSE FOOTNOTE instead of the fence (R1→R2) | R1 had been told the broken `assert current != stage or route.fail_routes["*"] == stage and False` line was the ONLY remaining blocker, and "fixed" it by adding a prose note ("if mypy/ruff flags this, replace with …") while leaving the broken line IN the code block | The reviewer treats the fence as the contract, so the footnote fix cleared nothing — R1 was graded **B / NOGO AGAIN** on a SINGLE blocking finding that cited this skill by name ("the reviewer is being asked to confirm this finding, not override it"). A whole extra review round was burned | A footnote fix does NOT clear a code-block defect. DELETE the broken line and write the assertions correct-first, self-contained, in the fence — R2 used `assert attempts == budget + 1` / `assert current == fail_target` / `assert fail_target != stage` with NO prose fix. `X and False` / `... or <always-false>` tautologies are a recognizable smell: split a compound "landed at target AND target differs" claim into TWO simple asserts. When a reviewer cites a named skill, apply its prescription verbatim rather than arguing. Enumerate a property's domain explicitly (`_LOOP_GUARDED = {…}`) instead of a heuristic helper (`_budget_key_for`) that can sample the wrong stages |
| Claim "mirrors sibling X" without reading X's mechanism | R0 called the zero-I/O guard "AST-based, mirroring `test_automation_boundary.py`" | That sibling uses a `read_text().splitlines()` + `startswith` TEXT scan, not AST — the parity claim was false and misdirected the reviewer — MINOR | Read sibling X before writing "mirrors/like/AST-based as in X." If you are deliberately using a STRONGER mechanism (real `ast.parse`/`ast.walk` to catch indented/in-function imports a line-prefix scan misses), SAY so explicitly rather than falsely claiming parity |
| Omit pr-policy items from the plan | R0's Implementation Order left out the `Closes #1811` PR-body line and the `git commit -S -s` (GPG + DCO) signing requirement | A repo with a pr-policy gate rejects PRs missing the exact close line or unsigned/undated commits; the plan was incomplete on policy — MINOR | A plan for a pr-policy repo MUST state the exact `Closes #<n>` line (capital C, own line) and the `git commit -S -s` signing requirement in the Implementation Order |

## Results & Parameters

**Grade and disposition.** R0 plan for ProjectHephaestus issue #1811 (a new pure-data
`pipeline/` package with `WorkItem`, queues, and routing): **B / NOGO**. The reviewer
affirmed the DESIGN as sound; the NOGO was driven by the five in-code-block / prose-code
defects above. R1 addressed four but "fixed" failure mode 3 (the broken example assertion)
only in a PROSE FOOTNOTE while leaving the broken line in the fence — so R1 was graded
**B / NOGO AGAIN** on a single blocking finding that cited this skill by name. R2 finally
converged by DELETING the broken line and writing property (c) correct-first in the code
block (`assert attempts == budget + 1` / `assert current == fail_target` /
`assert fail_target != stage`) and replacing the ambiguous `_budget_key_for` helper with an
explicit `_LOOP_GUARDED` stage→budget-key mapping so the hypothesis strategy samples only
genuinely loop-guarded stages. The plan was never executed. The R1→R2 round is a CONFIRMED
end-to-end instance of failure mode 3: a footnote fix does not clear a code-block defect.

**The correct import decision, stated once (the durable rule):**

```python
# annotation-only name -> TYPE_CHECKING (requires `from __future__ import annotations`)
# runtime-value name (default arg / base class / decorator / isinstance) -> real runtime import
# In #1811: `stage: StageName = StageName.REPO` is a default VALUE => RUNTIME import required.
# And: verify the cycle you claim to avoid exists — routing.py imports nothing from work_item.py.
```

**Uncertain assumptions / weakest points a future planner MUST re-check** (honesty framing,
since `verification: unverified`):

- The routing-graph properties (b)/(c) — "every cycle passes through a budget key" and "budget+1 failures land at the fail target" — are asserted **by construction but STILL NEVER executed**; the `hypothesis` tests were not run in R2 either. Whether `ROUTES` actually satisfies "every cycle passes a budget key" depends on the three back-edges (`PLAN_REVIEW→PLANNING`, `PR_REVIEW→IMPLEMENTATION`, `CI→IMPLEMENTATION`); a reviewer should HAND-TRACE these. This remains the weakest point of the plan.
- The R2 property-(c) code block is now correct-first (the broken assertion was DELETED, not footnoted), so failure mode 3 is no longer a live defect in the plan — but it was never *executed*, only made green-able by inspection. It should still be run under `hypothesis`/`pytest` at implementation time.
- All cited `file:line` numbers (`pyproject.toml:299-300`, `_review_phase.py:87/95`, `ci_driver.py:104`, `loop_runner.py:373`, `test_omit_allowlist.py:35/57`, `test_orchestration_smoke.py:3/8/11-16`) are **point-in-time**; a future planner MUST re-grep by content, not trust the line numbers.
- The "17 unique automation `.py` omit entries → 16" count was verified via `grep -oE '"hephaestus/automation/[a-z_]+\.py"' pyproject.toml | sort -u | wc -l` in-session, but a **concurrent omit-list edit landing first would invalidate it** — re-run the grep before relying on the count.
- This remains a PLANNING artifact: the R2 plan has NOT itself been re-reviewed to GO at capture time.

**Related skills** (linked by reference, not merged — each teaches a distinct planning-hygiene
lesson): `architecture-executable-convention-guard-pattern` (making a prose convention into a
tested guard; the NOGO→GO tightenings a plan reviewer demands on a sound design),
`planning-frozen-registry-guard-co-update` (co-update or drop an edit behind a frozen
exact-set guard), and `hypothesis-property-fuzz-llm-output-parsers` (property-based testing
patterns for the kind of `hypothesis` strategies failure mode 2 says to specify in full).
