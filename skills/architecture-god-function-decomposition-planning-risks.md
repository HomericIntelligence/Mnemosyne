---
name: architecture-god-function-decomposition-planning-risks
description: >-
  Use when: planning an extraction pass on over-long functions (god functions)
  OR an over-long god CLASS in hephaestus/automation/ or similar large Python
  codebases, especially when working from an issue that cites specific line
  numbers, function sizes, or file locations — before finalizing an extraction
  plan that waives work on a function, verify on disk that the cited size matches
  reality; apply the sentinel return pattern for extracted poll loops; verify
  test file existence before writing stubs; and audit plan documents for
  helper-defined-but-never-called inconsistencies. For god-CLASS decomposition,
  the dominant constraint is preserving existing patch.object(instance, "_method")
  test seams via thin delegation stubs, and the intra-class-helper vs
  injected-provider-collaborator decision is driven by the count of sibling
  self._ calls each method makes. The #1 non-obvious failure when extracting a
  collaborator is a circular import — if the moved method body uses a module-level
  helper defined in the god module, relocate that helper to a cycle-free leaf module
  and re-export it (name as name) rather than back-importing from the god module.
category: architecture
date: 2026-06-30
version: "1.3.0"
user-invocable: false
history: architecture-god-function-decomposition-planning-risks.history
verification: unverified
tags:
  - python
  - refactoring
  - god-function
  - planning
  - extraction
  - risk-management
  - line-number-validation
  - poll-loop
  - sentinel-pattern
  - test-stubs
  - planning-risks
  - arithmetic-verification
  - control-flow-signals
  - scope-validation
  - pipeline-stages
  - loop-body-measurement
  - docstring-budget
  - return-type-tracing
  - god-class
  - collaborator-extraction
  - patch-object-seams
  - delegation-stub
  - injected-provider
  - srp
  - circular-import
  - import-cycle
  - leaf-module
  - re-export
---

# Architecture: God-Function Decomposition — Planning Risks

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-06-30 |
| **Source issue** | ProjectHephaestus #1180 — decompose 5 god-functions in `hephaestus/automation/`; (v1.3.0) ProjectHephaestus #1462 — decompose the 2103-line `CIDriver` god **CLASS** (6 over-cap methods) |
| **Verification** | unverified (planning-phase learnings; no code ran) |
| **Objective** | Document recurring planning-phase failure modes when working from issue-cited metadata rather than disk reality — for both god-FUNCTION extraction (v1.0.0–v1.2.0) and god-CLASS collaborator extraction where preserving `patch.object` test seams is the dominant constraint (v1.3.0) |

These risks surface whenever an engineer or agent plans god-function extractions from
an issue description that cites line numbers, function sizes, or file paths. The
issue body may be weeks or months old; the code on disk is authoritative.

---

## When to Use

Use this skill when:

1. Planning an extraction pass on over-long (god) functions in any Python codebase, especially when the task originates from a GitHub issue that cites specific line numbers, function sizes, or file locations.
2. Reviewing a decomposition plan before approving it — check that each cited function size was measured from disk, not from the issue body.
3. Implementing a decomposition plan produced by another agent or engineer — verify all arithmetic, helper call sites, and test file assumptions before writing code.
4. Authoring decomposition plans for ProjectHephaestus `hephaestus/automation/` modules (where the 80-line orchestrator cap is enforced).
5. **(Class-level, v1.3.0)** Planning the decomposition of an over-long god **CLASS** (e.g. a 2000+-line `CIDriver`) by extracting collaborators or intra-class helpers — where an extensive `test_<class>.py` suite already monkeypatches the class internals via `patch.object(instance, "_method")`. The load-bearing constraint here is NOT line arithmetic but **preserving those patch seams** (see Risk 10 + Risk 11 below).
6. **(Class-level, v1.3.0)** Deciding, for each over-cap method, between an **intra-class private helper** vs a **new injected-provider collaborator** — the criterion is the count of sibling `self._` calls the method makes (Risk 11).

---

## Verified Workflow

### Quick Reference

| Step | Action |
| ------ | ------- |
| 1 | Run AST measurement on each named function — never trust issue-cited sizes |
| 2 | For functions that must reach ≤N lines, write the explicit subtraction chain |
| 3 | For each new helper, confirm at least one call site appears in the plan |
| 4 | For control-flow sentinel returns, enumerate ALL signal states in docstring |
| 5 | Verify test file existence before writing stubs |
| 6 | Check empty/sentinel values passed to downstream functions |

### Step 1: Measure Functions from Disk

Before writing any extraction plan, measure every named function via AST:

```python
python3 -c "
import ast
src = open('<project-root>/path/to/file.py').read()
tree = ast.parse(src)
for node in ast.walk(tree):
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        size = node.end_lineno - node.lineno + 1
        if size > 80:
            print(f'{node.name}: {node.lineno}–{node.end_lineno} ({size}L)')
" | sort -t'(' -k2 -rn
```

If the issue cites a file+line, grep for the function name first — it may have moved:

```bash
grep -rn "def _target_function" <project-root>/src/
```

### Step 2: Plan Extractions with Arithmetic Proof

For each function that must reach ≤N lines, write the subtraction chain before claiming the target is met:

```text
_example_function: 250L
  − _helper_1: 30L
  − _helper_2: 45L
  = 175L (still over 80L cap — plan additional extractions)
```

### Step 3: Audit Helper Call Sites

After writing the plan, for each helper defined in "New helpers" / "Extracted functions":

```text
grep the replacement code blocks for `helper_name(`
- Zero matches → either delete the helper or add the call site
- Never ship a plan where a defined helper has no shown call site
```

### Step 4: Document Sentinel Return Contracts

When a helper encodes control-flow signals in its return value, enumerate all states in the docstring and show all branches in the caller's replacement block.

---

## Risk 1: Issue-Cited Line Numbers May Be Stale — Always Re-read Before Planning

**What happened**: Issue #1180 cited `_implement_issue` as 354 lines (at line 255).
Direct `Read` of `implementer_phase_runner.py` showed the function spans lines 180–307:
127 lines, not 354. The plan correctly waived extraction for this function — but only
because the planner read the file first.

**The failure mode**: If the planner trusts the issue's cited size and plans extraction
for a 354-line function, it designs helpers that don't exist, splits non-existent blocks,
and writes a plan that is wrong from line 1.

**Rule**: Before deciding to extract *or* waive extraction for any named function, run:

```python
python3 -c "
import ast, sys
src = open('path/to/file.py').read()
tree = ast.parse(src)
for node in ast.walk(tree):
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        if node.name == '_target_function':
            print(f'Lines {node.lineno}–{node.end_lineno}: {node.end_lineno - node.lineno + 1} lines')
"
```

Or use the Read tool and count from the `def` line to the last line of the body.
**Never trust the issue's line count as the decision input.**

**Corollary**: If the plan says "waive extraction — function is only 127 lines", cite
the disk evidence (`file.py:180-307, 127 lines`) so the reviewer can verify without
re-reading the whole file.

---

## Risk 2: Cited File/Line Reference May Point to a Refactored Location

**What happened**: Issue #1180 cited `_run_impl_review_loop` at line 1513 of
`ci_driver.py`. After a prior refactor the function was moved to `_review_phase.py`
at lines 374–503. The plan found it only because a subagent searched by name
rather than by file+line.

**The failure mode**: An agent that opens `ci_driver.py:1513` sees a completely
different function or a blank line and either (a) extracts the wrong function, or
(b) panics with a "function not found" error.

**Rule**: When an issue cites `file.py:N`, grep for the function name across the
package first:

```bash
grep -rn "def _run_impl_review_loop" hephaestus/automation/
```

Accept the grep result as the authoritative location; treat the issue's file+line
citation as a hint, not a fact.

---

## Risk 3: The Helper-Defined-But-Not-Called Inconsistency

**What happened**: The decomposition plan for `_address_issue` defined a
`_finalize_address_state` helper in the "New helpers" section, but the replacement
code block shown for lines 561–635 inlined the state finalization directly rather
than calling the helper. The helper was defined but its call site was never shown.

**The failure mode**: An implementer writes both the helper and the inlined version,
leaving dead code. Or the reviewer approves a plan that has an unreachable function.
Either path wastes review cycles or introduces a dead-code lint failure.

**Rule**: Before finalizing a decomposition plan, audit every helper defined in the
plan document:

```text
For each helper H defined in "New helpers" / "Extracted functions":
  - grep the replacement code blocks for `H(`
  - if zero matches: either (a) delete H from the plan, or (b) add the call site
  - NEVER ship a plan where a defined helper has no shown call site
```

**Detection heuristic**: After writing the plan, search the plan document itself for
each helper name. If it appears only in its own definition section and nowhere else,
flag it as inconsistent.

---

## Risk 4: Sentinel Return Pattern for Extracted Poll Loops

**What happened**: The plan extracted a `_poll_ci_until_concluded` helper from
`_drive_issue`. The helper's return contract was:
- `None` — timeout; CI still pending after deadline
- `[]` (empty list) — no CI checks found at all
- `list[CheckResult]` (non-empty) — CI concluded with results

The caller must handle both `None` and `[]` as "treat as success=True / proceed".

**The failure mode**: If the caller treats `[]` as "no checks ran → failure" (a natural
intuition), it will abort the issue drive unnecessarily on repos with no required CI checks.
If the caller treats `None` as "timed out → hard failure", it will never retry a
transiently-slow CI.

**Rule**: When extracting any polling loop into a helper, document the full sentinel
contract in a docstring before merging:

```python
def _poll_ci_until_concluded(
    pr_number: int,
    deadline: float,
    gh_fn: Callable,
) -> list[CheckResult] | None:
    """Poll CI checks until all conclude or deadline is reached.

    Returns:
        list[CheckResult]: All checks concluded (may be empty if no checks exist).
            An empty list means no CI checks are configured — treat as success.
        None: Deadline reached before checks concluded — caller should
            treat as "still pending" (not a hard failure).
    """
```

And add a unit test asserting the `[]` vs `None` distinction explicitly:

```python
def test_poll_returns_empty_list_when_no_checks(mock_gh):
    mock_gh.return_value = []
    result = _poll_ci_until_concluded(pr=42, deadline=time.time() + 60, gh_fn=mock_gh)
    assert result == []           # not None
    assert result is not None     # caller must not treat as timeout
```

---

## Risk 5: Verify Test File Existence Before Writing Test Stubs

**What happened**: The plan added tests to `tests/unit/automation/test_ci_driver.py`
and `tests/unit/automation/test_address_review.py`. Neither file was verified to exist
or inspected for fixture patterns before the plan was finalized.

**The failure mode**: The implementer discovers the file does not exist and must invent
a fixture structure from scratch, or the file exists but uses a project-wide fixture
(`autouse` conftest, class-based test structure, `@pytest.fixture(scope="module")`) that
the new tests must follow to avoid import errors or fixture-collision failures.

**Rule**: Before writing any test stubs in a plan, run:

```bash
# Verify file exists
ls tests/unit/automation/test_ci_driver.py 2>/dev/null || echo "FILE DOES NOT EXIST"

# If it exists, read the first 60 lines to identify fixture patterns
head -60 tests/unit/automation/test_ci_driver.py
```

If the file does not exist, the plan must include a "Create test file" step that
describes the required imports and any fixture scaffolding to match the conftest.

If the file exists, the plan must note the dominant fixture pattern (e.g.,
`class TestCIDriver: ...` vs module-level functions, `@pytest.fixture(autouse=True)` vs
per-test setup) so the new tests are consistent.

---

## Risk 6: The Empty-Replies-Dict Edge Case in Extracted State Helpers

**What happened**: The plan's `_finalize_address_state` helper passed `replies={}`
(empty dict) to `_resolve_addressed_threads`. This is correct when the replies are
already handled by the caller before the helper is invoked — but the plan did not
verify whether `_resolve_addressed_threads` accepts an empty dict or requires a
non-empty one.

**The failure mode**: If `_resolve_addressed_threads` has a guard like
`if not replies: raise ValueError(...)` or iterates `replies` with an assumption that
at least one entry exists, passing `{}` silently skips the resolution logic and leaves
threads unresolved.

**Rule**: When an extracted helper passes a sentinel/empty value to a downstream
function, read the downstream function's signature and body before finalizing the call:

```bash
grep -n "def _resolve_addressed_threads" hephaestus/automation/*.py
# then read the first 20 lines of that function to check for empty-input guards
```

Document the expected behavior explicitly in the plan:

> `_resolve_addressed_threads(addressed, replies={}, thread_ids)` — passing `replies={}`
> is safe because the function iterates `thread_ids` (not `replies`) as the primary
> driver. Verified at `address_review.py:312-335`.

---

## Risk 7: Arithmetic Verification Before Claiming Line-Count Targets (R1 Learning)

**What happened**: R0 plan claimed `_run_ci_fix_session` would reach "~190 lines" after
extracting a sync helper, yet also claimed AC1 (≤80L orchestrator) would pass. The numbers
were contradictory. R1 explicitly counted the subtractions:

```
250L  (starting length)
− 30L (extract sync helper)
− 25L (extract prompt helper)
− 27L (remove duplicate push tail)
= 168L remaining → still over the 80L cap
```

Two more extractions were required: `_invoke_codex_ci_fix` (45L) + `_invoke_claude_ci_fix`
(72L). Only after all 5 helpers does the orchestrator reach ~55L.

**The failure mode**: Claiming a target line count without performing the subtraction chain
leads the reviewer to approve a plan that provably cannot meet its acceptance criterion.
The reviewer is expected to verify the arithmetic; a wrong number fails the NOGO gate.

**Rule**: For each function that must reach ≤N lines, write the subtraction chain explicitly
in the plan before stating the result:

```
<function>: <current>L
  − <helper_1>: <extracted_lines>L
  − <helper_2>: <extracted_lines>L
  = <remaining>L (target ≤ <cap>L)
```

**Only claim the target is met after the subtraction proves it.** If the remaining count
is still over the cap, plan additional extractions before finalizing.

### Risk 7a: The Chain Is on AST SPAN, Not Executable Body — Count Signature + Docstring

**What happened (ProjectHephaestus #1464)**: The R0 plan to decompose the 204-line god
function `validate_prior_comments_addressed` in
`hephaestus/automation/review_validator.py` extracted 2 helpers and claimed the
orchestrator reached "~70L executable body" and was therefore "≤80L". It got a **NOGO**.

The acceptance-criterion verification command measures **AST span** —
`node.end_lineno - node.lineno + 1` — which INCLUDES the signature (14L here) AND the
full docstring (43L here), not just executable statements. The function decomposed as:

```
204L span = 14L signature + 43L docstring + 147L executable body
```

The reviewer's subtraction on SPAN:

```
204L  (AST span)
− 78L (2 extractions)
− 21L (docstring trim, 43→22)
= 105L span   →  still > 80L cap   →  NOGO
```

The R0 plan asserted an AC it could not meet because it subtracted from an
**executable-body estimate** (~147L) rather than from the **AST span** (204L) the AC
command actually measures. The two diverge by exactly `signature + docstring` — here a
57L gap. A large docstring is a first-class line-budget consumer: 43L was 21% of the
204L function.

**The R1 fix** reached a 67L span (13L margin) by:

1. Adding a THIRD extraction `_run_validation_and_reconcile` (absorbing the ~48L
   session-dispatch / reconcile prelude that R0 left untouched), and
2. Trimming the docstring 43L → 22L, counting that **−21L as an explicit numbered term**
   in the chain, and
3. Making the docstring trim **concrete** — pasting the full ~22L replacement docstring
   into the plan so the −21L term is auditable from the plan itself, not hand-waved as
   "trim to ~22 lines".

**The failure mode**: Estimating from "executable body lines" while the AC verifies AST
span guarantees a NOGO whenever the function has a non-trivial signature or docstring.
The planner believes it cleared the cap; the reviewer's span measurement says otherwise.

**Rule**: When proving a function reaches a ≤N-line cap, the subtraction chain MUST start
from the **AST span** and account for ALL three components — signature lines + docstring
lines + executable body lines. Measure each via AST:

```python
python3 -c "
import ast
src = open('FILE').read()
for n in ast.walk(ast.parse(src)):
    if getattr(n, 'name', None) == 'TARGET' and isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
        d0 = n.body[0]  # docstring node when present
        print('span', n.end_lineno - n.lineno + 1, 'sig', d0.lineno - n.lineno, 'docstring', d0.end_lineno - d0.lineno + 1)
"
```

If the docstring is a large fraction of the cap, plan an explicit docstring trim AND
count it as a numbered term in the chain (e.g. `− 21L (docstring 43→22)`). **Show the
full replacement docstring in the plan** so the term is auditable. Verify with the SAME
span command the AC uses (`end_lineno - lineno + 1`) — never an "executable body"
eyeball estimate, because the two differ by exactly signature + docstring.

> **Relation to the `_address_issue` lesson below**: that earlier failed attempt noted
> the docstring must be *counted* in the span. Risk 7a adds the operational consequence:
> the AC command measures SPAN, so the chain must be span-based end-to-end (start from
> `end_lineno - lineno + 1`, not from a body estimate), and the docstring trim must be a
> concrete, shown, numbered term — not an aspirational "trim to ~22 lines".

---

## Risk 8: Control-Flow Sentinel Return Values — Enumerate All Signal States

**What happened**: R1's `_run_address_step_if_needed` helper encodes three distinct
control-flow signals in its return value:

- `None` — continue the loop (nothing needed this iteration)
- `([], False)` — break out of the loop (final iteration, no prior addressed)
- `(prior_addressed, addressed)` — normal result (caller processes and continues)

The caller must handle all three. In R0, only the "normal" and "break" cases were
documented; the `None`-continue path was implicit. A reviewer reading the plan could
not safely verify the caller handled all three paths correctly.

**The failure mode**: If the caller has `if result is None: continue` but the function
only documents two return values, any future refactor that adds a fourth sentinel will
silently fall through to the wrong branch.

**Rule**: When a helper encodes control-flow signals in return values (not just data),
enumerate **all signal states** in the docstring — not just the happy path:

```python
def _run_address_step_if_needed(
    iteration: int,
    max_iterations: int,
    ...
) -> tuple[list, bool] | None:
    """Run one address step if the loop should continue.

    Returns:
        None: This iteration requires no action — caller should continue the loop.
        ([], False): Final iteration reached — caller should break the loop.
        (prior_addressed, addressed): Normal result — caller updates state and continues.

    All three cases MUST be handled by the caller. Missing a case silently
    falls through to the wrong branch.
    """
```

And in the plan's caller replacement block, show all three `if/elif/else` branches
explicitly — not just the common case.

---

## Risk 9: Scope Against Actual Disk State, Not Issue-Cited State (R1 Learning)

**What happened**: Issue #1180 verified "functions exist at cited line numbers with stated
lengths". R1 found via AST measurement:

- `_implement_issue`: issue said 354L → AST showed 128L (in `implementer_phase_runner.py`)
- `_run_impl_review_loop`: issue said `implementer_phase_runner.py:1513` → AST showed it
  lives at `_review_phase.py:374`, 130L

R0 treated the issue's AST evidence as authoritative. R1 re-measured and discovered
significant drift.

**The failure mode**: A plan scoped to issue-cited sizes will extract helpers from the
wrong locations (if the function moved) or waive functions that are actually over the cap
(if the function shrank) or plan too few extractions (if the function grew).

**Rule**: **Always run the AST measurement yourself before planning**, even if the issue
includes a measurement:

```python
python3 -c "
import ast
src = open('hephaestus/automation/implementer_phase_runner.py').read()
tree = ast.parse(src)
for node in ast.walk(tree):
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        size = node.end_lineno - node.lineno + 1
        if size > 80:
            print(f'{node.name}: {node.lineno}–{node.end_lineno} ({size}L)')
" | sort -t'(' -k2 -rn
```

Treat the issue's line numbers as **starting hints** — confirm or correct them before
writing a single extraction step. If your measurement contradicts the issue, note the
discrepancy in the plan and proceed from disk reality.

---

## God-CLASS Decomposition (v1.3.0 — ProjectHephaestus #1462)

> **Verification level: unverified.** Everything in the risks below comes from
> *producing a plan* — and then REVISING it after a NOGO — for #1462 (decompose the
> 2103-line `CIDriver` class; 6 methods over the 80L cap). **No code was executed
> end-to-end.** The "Proposed Workflow" decision tree and every line-count are planning
> estimates the reviewer must re-measure. See the Proposed Workflow section for the
> honesty banner. The #1 non-obvious failure that earned the NOGO was a **circular import**
> when extracting a collaborator (Risk 10a) — read it first.

Class-level decomposition differs from function-level in one decisive way: an over-long
*function* is extracted into helpers whose only consumers are the function itself, so test
seams rarely move. An over-long *class* sits behind a large `test_<class>.py` suite that
monkeypatches its internals with `patch.object(instance, "_method")`. **Those seams are the
load-bearing constraint** — break one and a swath of tests silently stop exercising real
code (or crash with `AttributeError`). The line-count arithmetic from Risks 1–9 still
applies, but it is secondary to seam preservation.

### Proposed Workflow (UNVERIFIED — no code ran end-to-end)

> **Honesty gate:** the steps below were written while planning #1462 and have NOT been
> executed. Treat them as a proposal to validate, not a verified procedure.

```text
Decomposing a god CLASS (methods over the cap)?
└─ STEP 0  (BEFORE planning): count the patch seams — this is the risk metric.
     grep -c 'patch.object(<instance>' tests/unit/.../test_<class>.py
     (#1462: 296 patch.object(driver, ...) sites in test_ci_driver.py)
     Every extracted method MUST keep a thin delegation stub on the original class
     so each of those 296 seams still intercepts at call time.
└─ STEP 1  AST-measure every method on disk (Risk 9 command, but for methods).
     Run the NEW ≤80L-cap test RED FIRST — it asserts ALL methods, so it enumerates
     the TRUE over-cap set, which may exceed the issue's named list.
└─ STEP 2  For each over-cap method, choose helper vs collaborator (Risk 11):
     trace sibling `self._` calls via grep.
       many sibling self._ calls  → intra-class private helper (small provider surface)
       cohesive sub-responsibility,
       few external sibling calls  → new injected-provider collaborator
└─ STEP 3  For each method moved onto a collaborator, leave a 3-line delegation stub
     on the original class (Risk 10) and inject lambda providers in __init__ so the
     existing patch.object seams intercept at call time (the #1357 precedent).
└─ STEP 3a CIRCULAR-IMPORT CHECK (Risk 10a — this earned the NOGO):
     List EVERY module-level symbol the moved method body references (not just self._
     calls — module-level helpers + constants too). Confirm none forces
     new_module → god_module at import time. If a needed helper lives in god_module,
     RELOCATE it to a cycle-free LEAF module and re-export via `name as name`.
     Verify:  python -c "import god_module; import new_module; print('no cycle')"
     And assert the leaf stays leaf: grep "from .god_module" leaf_module.py  (→ no match)
└─ STEP 4  Sweep the WHOLE test tree for patches of any INTERNAL name that moves onto
     the collaborator — not just the public method names (Risk 12, unverified reliance b).
```

---

## Risk 10: Preserving `patch.object` Test Seams Is the Dominant Class-Decomposition Constraint

**What happened (planning #1462)**: `test_ci_driver.py` contains **296** `patch.object(driver, "_method")`
call sites. The plan extracted two methods (`_wait_for_pr_terminal`, `_check_arming_on_drive_start`)
onto a new `ArmingLifecycle` collaborator and shrank four others via intra-class helpers — but
every one of those 296 seams targets a method **on the `CIDriver` instance**. If an extracted
method simply moves to the collaborator and is deleted from `CIDriver`, the matching
`patch.object(driver, "_wait_for_pr_terminal")` raises `AttributeError` (or worse, silently
patches a now-dead attribute) and the test stops exercising real code.

**The failure mode**: A "clean" extraction that deletes the method from the original class breaks
N test seams at once. The breakage is proportional to the patch-site count — which is why that
count is the risk metric to gather BEFORE planning, not after.

**Rule**: Before planning any class decomposition, count the seams:

```bash
grep -c 'patch.object(driver' tests/unit/automation/test_ci_driver.py   # → 296 for #1462
```

For **every** extracted method, keep a thin delegation stub on the original class so the seam
still resolves and still intercepts at call time. The established precedent is #1357
(`PRDiscovery` / `CIFixOrchestrator` / `PostMergeProcessor`): a 3-line stub on `CIDriver`
delegates to the collaborator, and **lambda providers injected in `__init__`** let the patch
intercept at the call boundary:

```python
class CIDriver:
    def __init__(self, ...):
        # inject narrow callables so patch.object(driver, "_x") still intercepts
        self._arming = ArmingLifecycle(
            wait_for_terminal=lambda pr, deadline: self._wait_for_pr_terminal(pr, deadline),
            mark_green=lambda *, succeeded: self.mark_drive_green_learn_result(succeeded=succeeded),
        )

    def _wait_for_pr_terminal(self, pr, deadline):   # 3-line delegation stub
        return self._arming.wait_for_pr_terminal(pr, deadline)
```

The stub costs three lines per method; breaking 296 seams costs the whole review cycle.

---

## Risk 10a: Circular Import When Extracting a Collaborator — Relocate Shared Helpers to a Cycle-Free Leaf + Re-export (this earned the NOGO)

**This is the #1 non-obvious failure when extracting a collaborator from a god class, and the one
that earned the #1462 plan a NOGO.** When you extract class `Foo` from `god.py` into `foo.py`, and
`god.py` imports `Foo` at top level, then `foo.py` must **NOT** import any symbol back from `god.py`
at top level — that is a genuine import cycle (`god → foo → god`).

**The trap (planning #1462)**: the extracted method's body uses a **stateless module-level helper**
(`_without_auto_merge_policy` and its constant `_AUTO_MERGE_POLICY_CHECK`) defined in `ci_driver.py`.
Naively importing that helper into the new `foo.py` collaborator (`from .ci_driver import
_without_auto_merge_policy`) creates the cycle, because `ci_driver.py` already imports the
collaborator class at top level. The dependency is invisible if you only look at `self._` calls —
you must enumerate **module-level** symbols the moved body touches, not just instance methods.

**The failure mode**: A collaborator extraction that looks clean (seams preserved, providers
injected) still fails at import time with `ImportError: cannot import name ... (most likely due to a
circular import)`. The poll loop / arming logic that referenced one module-level helper drags the
whole god module into the collaborator's import graph.

**FIX (lowest-risk, follows the file's own precedent)**: relocate the shared **stateless** helper to
a cycle-free **LEAF** module that neither file's import creates a cycle with — here
`ci_check_inspector.py`, confirmed leaf via `grep "from .ci_driver" ci_check_inspector.py` → no
match. Then **re-export** it from `god.py` (`ci_driver.py`) via the `name as name` alias idiom for
backward compat, preserving all existing call sites and any external import, and have the new
collaborator import it **from the LEAF**:

```python
# ci_check_inspector.py  (the cycle-free leaf — must NOT import from ci_driver)
_AUTO_MERGE_POLICY_CHECK = "..."
def _without_auto_merge_policy(...): ...

# ci_driver.py  (god module — re-export for backward compat, NO `# ruff: noqa: F401`)
from .ci_check_inspector import _without_auto_merge_policy as _without_auto_merge_policy
from .ci_check_inspector import _AUTO_MERGE_POLICY_CHECK as _AUTO_MERGE_POLICY_CHECK

# foo.py  (the new collaborator — imports from the LEAF, never from ci_driver)
from .ci_check_inspector import _without_auto_merge_policy
```

This exactly mirrors the file's own prior precedent: `FAILING_CHECK_CONCLUSIONS` was moved to the
leaf in #1357 and re-exported from `ci_driver`. **Prefer leaf-relocation** over "inject the helper
as an 11th provider lambda" when the helper is (a) stateless **and** (b) still needed by the god
module itself at other call sites the collaborator cannot reach — injecting it as a provider would
leave the god module without its own access.

**Detection rule (run BEFORE finalizing any collaborator extraction)**: list every **module-level**
symbol the moved method body references (constants, module functions — not just `self._` calls) and
confirm none forces `new_module → god_module` at import time. Then verify with a real import:

```bash
# 1. Prove no cycle exists after the relocation/re-export
python -c "import hephaestus.automation.ci_driver; import hephaestus.automation.foo; print('no cycle')"

# 2. Assert the leaf stays a leaf (no back-edge to the god module)
grep "from .ci_driver" hephaestus/automation/ci_check_inspector.py   # → MUST print nothing
```

**Rule**: never write `from .god_module import X` at the top of a freshly-extracted collaborator.
If the collaborator needs a god-module symbol, relocate that symbol to a cycle-free leaf and
re-export it (alias idiom, no `# ruff: noqa: F401` — RUF100 guards the unnecessary suppression).

---

## Risk 11: Intra-Class Helper vs Injected-Provider Collaborator — Decide by Sibling `self._` Call Count

**What happened (planning #1462)**: Six methods were over the cap. Two
(`_wait_for_pr_terminal`, `_check_arming_on_drive_start`) form a cohesive
"arming state machine" sub-responsibility and were planned as a new injected-provider
collaborator (`ArmingLifecycle`). The other four (`run`, `_discover_prs`, `_attempt_ci_fixes`,
`_recheck_and_arm_after_fix`) call **many sibling `self._` methods**, so extracting them into
a collaborator would force a wide injected-provider surface (one lambda per sibling call) —
violating KISS/YAGNI. They were planned as **intra-class private helpers** instead
(`_run_worker_pool`, `_finalize_open_prs_remaining`, `_widen_discovery`,
`_run_one_ci_fix_iteration`, `_poll_post_fix_ci`), which keep the provider surface minimal.

**The failure mode**: Blindly extracting every over-cap method into a new collaborator
explodes the injected-provider surface (a lambda for every sibling `self._x` the method
touched), adding more coupling than it removes. Conversely, leaving a cohesive
sub-responsibility as scattered private helpers misses an SRP opportunity.

**Rule**: For each over-cap method, grep its body for sibling `self._` calls and count them:

```bash
# Count distinct sibling self._ calls inside one method's line range
sed -n '<start>,<end>p' hephaestus/automation/ci_driver.py \
  | grep -oE 'self\._[a-z_]+' | sort -u | wc -l
```

| Sibling `self._` call count | Choose | Why |
| --------------------------- | ------ | --- |
| Many (method is glue over siblings) | **intra-class private helper** | Keeps injected-provider surface small (KISS/YAGNI); the helper still has `self`, so sibling calls stay free |
| Few + cohesive sub-responsibility | **new injected-provider collaborator** | A clean SRP boundary; inject only the handful of callables it actually needs |

This is the genuinely new decision criterion beyond function decomposition: a *function*
helper always keeps the enclosing scope, but a *class* collaborator must re-acquire every
sibling it calls as an injected provider, so the sibling-call count is the cost signal.

---

## Risk 12: Unverified Class-Decomposition Reliances the Reviewer MUST Re-check

**What happened (planning #1462)**: The plan rested on several assumptions that were NOT
verified on disk because no code ran. Each is a place where the plan can be silently wrong.

**The unverified reliances (reviewer focus list):**

1. **Per-extraction line arithmetic is eyeballed, not measured.** Estimates like
   `_widen_discovery ~50L` were read off block boundaries, not AST-measured. Re-run the
   AST measurement (Risk 9) on the REAL post-edit methods before trusting any "≤80L" claim.
2. **No existing test patches an INTERNAL name that moves onto the collaborator.** The plan
   spot-checked only the two PUBLIC method names. Only a **whole-test-tree grep** at
   implementation time confirms no test patches a private name that relocates to
   `ArmingLifecycle`:

   ```bash
   grep -rn 'patch.*\.\(_wait_for_pr_terminal\|_check_arming\|<every internal moved name>\)' tests/
   ```
3. **`mark_drive_green_learn_result` signature was assumed keyword-only (`*, succeeded`).**
   The injected lambda `lambda *, succeeded: ...` was written WITHOUT re-reading the real
   signature on disk. Re-read it; if the real signature is positional, the lambda is wrong.
4. **The new collaborator lands under `hephaestus/automation/`**, so the
   library/automation import-boundary tests (`test_import_surface.py`,
   `test_automation_boundary.py`) must still pass — **assumed, not run.** Run them.
5. **The verbatim move of `_wait_for_pr_terminal`'s BLOCKED/sentinel control flow** (6 distinct
   return states) must survive the `self._x` → provider rewrite intact. One missed rewrite
   silently changes behavior. Diff the moved body against the original branch-by-branch.
6. **The new 80L-cap test is a NEW invariant** that asserts ALL `CIDriver` methods — on first
   run it may flag pre-existing over-cap methods BEYOND the 6 named in the issue. **Run it RED
   first** to enumerate the true over-cap set before sizing the extraction budget.

**Rule**: A class-decomposition plan written without running code MUST ship this reviewer
focus list explicitly. Each item is a concrete `grep`/`Read`/`pytest` the implementer runs
to convert an assumption into a fact before writing the extraction.

---

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | -------- |
| R0 #1464: claimed ≤80L from "~70L executable body" after 2 extractions | 2-helper extraction, span asserted via executable-body estimate | AC command measures AST span (sig+docstring+body); true span ≈105L > 80L cap → NOGO | Subtract on SPAN; add a 3rd extraction + a concrete numbered docstring-trim term; verify with `end_lineno - lineno + 1` |

### R1: Single Helper Insufficient for `_run_implementation_and_review` (130L)

**What was tried**: R1 plan extracted only `_run_advise_and_implement` (37L), leaving 98L.
Claimed the target (≤80L) was met.

**Why it failed**: 98L > 80L. The function has 2 distinct pipeline stages (implement + review).
A second extraction `_run_review_loop_and_label` (43L) was needed to reach 58L.

**Lesson**: When a function has 2+ distinct pipeline stages, count them all before choosing
helpers. One extraction rarely suffices for functions > 120L.

---

### R1: `_run_impl_review_loop` Needed 2 Helpers, Not 1

**What was tried**: R1 extracted only `_run_address_step_if_needed` (22L), leaving 118L
(target 80L).

**Why it failed**: 118L still over the cap. The for-loop body itself (53L) needed extraction
as `_process_review_iteration` to reach 68L.

**Lesson**: Measure the loop body separately from its header + finalize block. A for-loop
whose body exceeds 40L is itself a god-pattern. Use:
`loop_body_lines = (loop_end - loop_start + 1)`.

---

### R1: `_address_issue` Arithmetic Was Wildly Off

**What was tried**: R1 initially claimed 2 extractions leaving 74L. Actual subtraction gave 136L.

**Why it failed**: The docstring (27L) was not counted in the function's line total.
A 27L docstring contributes 17% of a 159L function's span. Required 3 extractions + docstring trim.

**Lesson**: Count the docstring as part of the function span. Subtract it from budget or
plan to trim it before allocating extraction budget.

---

### R1: `_prepare_worktree_for_existing_pr` Return Type Changed Mid-Plan

**What was tried**: Plan initially specified return type `tuple[Path, str]`. Mid-planning,
discovered `issue.title`/`issue.body` were also needed by the caller for the review loop.

**Why it failed**: The helper absorbed the only call to `fetch_issue_info`. The caller now
needed those fields back but the return type did not include them.

**Lesson**: Before specifying a helper's return type, trace every variable the caller uses
after the call. If the helper consumed the only call to a data-fetching function, the
return tuple must include those fields.

---

### R0: Waiving Functions at 128–130L as "Marginal"

**What was tried**: R0 plan waived `_implement_issue` (128L) and `_run_impl_review_loop`
(130L) as "marginal" overages, arguing YAGNI applied since these were close to the 80L cap.

**Why it failed**: The reviewer rejected this. 128L is 60% over the 80L cap. YAGNI does
not excuse under-scoping when a function is explicitly named in the issue and is over the
stated threshold. Functions named in the issue + over 80L must all be addressed; "marginal"
is not a valid waiver ground unless the function is already below the cap.

**Lesson**: **Do not waive on "marginal" grounds.** If a function is named in the issue
and measured over 80L, it is in scope. The only valid waiver is: measured size ≤ cap on disk.

---

### R0: Wrong Signature in `_finalize_address_state` (Sentinel vs Real Argument)

**What was tried**: R0's `_finalize_address_state` helper was defined with `replies={}`
(empty dict sentinel) where the original code passed the actual `replies` dict collected
during the address loop.

**Why it failed**: A helper that silently drops data (the real `replies`) is worse than no
extraction. The extracted helper would pass `{}` to `_resolve_addressed_threads`, causing
all reply-based thread resolution to be skipped silently. The reviewer caught this because
the replacement block showed `replies={}` hardcoded, not the variable.

**Lesson**: Before extracting, read every argument the extracted code passes to its
callees. **Never substitute a sentinel for a real argument** unless you have verified the
downstream function treats the sentinel identically to the real value. Show the argument
mapping explicitly in the plan:

```text
Original: _resolve_addressed_threads(addressed, replies=replies, ...)
Extracted helper call: _finalize_address_state(addressed, replies, ...)
  → helper passes: _resolve_addressed_threads(addressed, replies=replies, ...)
```

---

### R0: New Helpers Defined but Call Sites Not Shown in Replacement Blocks

**What was tried**: R0 defined `_finalize_address_state` in the "New helpers" section but
the replacement code block for the address loop inlined the same state-finalization logic
directly, never calling the helper.

**Why it failed**: The inconsistency meant either (a) the helper is dead code, or (b) the
replacement block is wrong and should call the helper. In either case, an implementer
following the plan would produce incorrect code. The reviewer rejected this as "plan is
internally inconsistent."

**Lesson**: For each new helper defined in the plan, **explicitly show its call site in
the same plan section**. Run a self-check: search the plan document for each helper name.
If it appears only in its own definition and nowhere else, flag it. Ship only plans where
every defined helper has at least one shown call site.

---

### #1462 (Class-level, UNVERIFIED): Extracting Every Over-Cap Method Into a New Collaborator

**What was tried**: An early framing of the #1462 plan considered extracting all six over-cap
`CIDriver` methods into collaborators for a uniform "no method over 80L lives on the god class"
shape.

**Why it failed (in planning review)**: Four of the six (`run`, `_discover_prs`,
`_attempt_ci_fixes`, `_recheck_and_arm_after_fix`) are glue over **many** sibling `self._`
methods. Extracting them would force one injected lambda per sibling call — a wide provider
surface that adds more coupling than the extraction removes (KISS/YAGNI violation).

**Lesson**: Choose by sibling `self._` call count (Risk 11). Many sibling calls → intra-class
private helper (keeps the provider surface tiny); few calls + cohesive sub-responsibility → new
injected-provider collaborator. Only `_wait_for_pr_terminal` + `_check_arming_on_drive_start`
(the cohesive "arming state machine") justified the `ArmingLifecycle` collaborator.

---

### #1462 (Class-level, UNVERIFIED): Deleting an Extracted Method From the Class Breaks 296 Patch Seams

**What was tried**: The intuitive "clean" extraction — move `_wait_for_pr_terminal` onto
`ArmingLifecycle` and delete it from `CIDriver`.

**Why it failed (in planning review)**: `test_ci_driver.py` has **296** `patch.object(driver, "_method")`
seams. Deleting the method makes `patch.object(driver, "_wait_for_pr_terminal")` raise
`AttributeError` (or silently patch a dead attribute), so those tests stop exercising real code.

**Lesson**: Count the seams BEFORE planning (`grep -c 'patch.object(driver'`), and keep a 3-line
delegation stub on the original class for EVERY extracted method, with lambda providers injected
in `__init__` so the patch intercepts at call time (#1357 precedent). The seam count is the risk
metric.

---

### #1462 (Class-level, UNVERIFIED): Writing the Injected-Lambda Signature Without Re-reading the Real Method

**What was tried**: The injected provider was written as
`lambda *, succeeded: self.mark_drive_green_learn_result(succeeded=succeeded)` — assuming the
target is keyword-only.

**Why it (could) fail**: The `*, succeeded` keyword-only form was assumed, not confirmed by
reading `mark_drive_green_learn_result`'s real signature on disk. If the real signature is
positional or has extra params, the lambda is wrong and the delegation silently breaks.

**Lesson**: Before writing any injected-provider lambda, Read the target method's real signature
on disk. Never reconstruct a callable's signature from memory in a plan (this is the class-level
analogue of Risk 6 / the R0 sentinel-argument failure).

---

### #1462 (Class-level, UNVERIFIED — earned the NOGO): Importing a God-Module Helper Into the New Collaborator at Top Level

**What was tried**: The first `ArmingLifecycle` collaborator imported the stateless module-level
helper it needed straight from the god module — `from .ci_driver import _without_auto_merge_policy`
(plus its constant `_AUTO_MERGE_POLICY_CHECK`) — because the moved method body referenced it.

**Why it failed (NOGO in planning review)**: `ci_driver.py` already imports `ArmingLifecycle` at
top level, so the new top-level back-import creates a genuine cycle (`ci_driver → arming → ci_driver`),
which fails at import time. The trap is that the dependency is a **module-level** helper, not a
`self._` call — enumerating only instance methods misses it entirely.

**Lesson**: Relocate the shared **stateless** helper to a cycle-free **leaf** module
(`ci_check_inspector.py`, verified leaf), re-export it from the god module via the `name as name`
alias idiom (no `# ruff: noqa: F401`), and import it into the collaborator **from the leaf** — the
exact `FAILING_CHECK_CONCLUSIONS` precedent from #1357. Verify with
`python -c "import ci_driver; import arming; print('no cycle')"` and
`grep "from .ci_driver" ci_check_inspector.py` (→ no match). See Risk 10a.

---

### #1462 (Class-level, UNVERIFIED): Eyeballing Extracted-Helper Line Counts From Block Boundaries

**What was tried**: Per-helper sizes (`_widen_discovery ~50L`, etc.) were read off visual block
boundaries to claim each post-extraction method lands ≤80L.

**Why it (could) fail**: Visual block boundaries are not AST measurements — docstrings, blank lines,
and continuation lines shift the real count. A helper "obviously ~50L" can land over cap after the
real extraction, silently failing the ≤80L invariant the new cap-test enforces.

**Lesson**: AST-measure every helper on the REAL post-edit method (Risk 9 command), never from
eyeballed boundaries. Treat every "≤80L" claim in a plan as unverified until measured on disk.

---

## Planning Checklist for God-Function Decomposition

Before submitting or approving a god-function decomposition plan:

```text
[ ] For each function named in the issue:
    [ ] Run AST measurement yourself — do NOT trust the issue's cited size
    [ ] Cite file:start-end and actual LOC from your own measurement
    [ ] If waiving extraction: cite the disk evidence (measured size ≤ cap)
    [ ] "Marginal" overage is NOT a valid waiver — if over cap, it is in scope
    [ ] If the issue's file+line doesn't match disk: note the discrepancy

[ ] For each function that must reach ≤N lines:
    [ ] Write the explicit subtraction chain (current − helper1 − helper2 = remaining)
    [ ] Only claim the target is met if the arithmetic proves it
    [ ] If remaining > cap after planned extractions: plan additional helpers

[ ] For each new helper defined in the plan:
    [ ] Confirm at least one call site appears in the plan's replacement blocks
    [ ] If no call site shown: delete the helper or add the call
    [ ] Show the argument mapping explicitly (original arg → helper arg → downstream)
    [ ] Never substitute a sentinel for a real argument without verifying equivalence

[ ] For each helper that encodes control-flow signals in its return value:
    [ ] Enumerate ALL signal states in the docstring (not just the happy path)
    [ ] Show all branches (if/elif/else) in the caller's replacement block

[ ] For each extracted poll/retry loop:
    [ ] Document the full sentinel return contract (what each return value means)
    [ ] Add a unit test distinguishing the empty-list vs None sentinels

[ ] For each test stub added by the plan:
    [ ] Verify the target test file exists (ls command)
    [ ] If it exists, read its fixture pattern (first 60 lines)
    [ ] If it doesn't exist, include a "Create test file" step in the plan

[ ] For each helper that passes an empty/sentinel value downstream:
    [ ] Read the downstream function's first 20 lines
    [ ] Confirm it handles the empty value correctly
    [ ] Cite the verification in the plan (file:line range)

[ ] FOR GOD-CLASS DECOMPOSITION (v1.3.0) — additionally:
    [ ] Count patch.object(<instance>, ...) seams BEFORE planning (this is the risk metric)
    [ ] CIRCULAR-IMPORT CHECK (Risk 10a): list EVERY module-level symbol the moved body uses;
        if it lives in the god module, relocate to a cycle-free leaf + re-export (name as name),
        verify `python -c "import god; import collaborator"` and `grep "from .god" leaf.py` (no match)
    [ ] Keep a 3-line delegation stub on the original class for EVERY extracted method
    [ ] Inject lambda providers in __init__ so patch.object seams intercept at call time (#1357)
    [ ] Choose helper vs collaborator by sibling self._ call count (many → helper; few+cohesive → collaborator)
    [ ] Run the new ≤cap test RED FIRST — it asserts ALL methods, enumerating the TRUE over-cap set
    [ ] Re-read every injected lambda's target method signature on disk (no signatures from memory)
    [ ] Grep the WHOLE test tree for patches of any INTERNAL name that moves onto a collaborator
    [ ] If the collaborator lands under hephaestus/automation/: run import-boundary tests
    [ ] Diff any verbatim-moved control-flow body branch-by-branch after self._x → provider rewrites
```

---

## Results & Parameters

### Successful Patterns

| Pattern | Context | Outcome |
| --------- | --------- | --------- |
| AST re-measurement before planning | ProjectHephaestus #1180 R1 | Caught 354L→128L drift; prevented planning extractions on wrong function size |
| grep-by-name before grep-by-line | ProjectHephaestus #1180 R1 | Found `_run_impl_review_loop` moved from `ci_driver.py:1513` to `_review_phase.py:374` |
| Subtraction arithmetic chain | ProjectHephaestus #1180 R1 | Revealed 5 extractions needed (not 3) for `_run_ci_fix_session` to reach ≤80L |
| Sentinel return contract docstring | ProjectHephaestus #1180 R1 | Made all 3 control-flow states explicit; prevented silent fall-through bugs |

### Key Thresholds (ProjectHephaestus)

- Orchestrator line cap: **80 lines** (enforced via unit tests)
- "Marginal" overage is NOT a valid waiver — any function named in the issue and over the cap is in scope
- Valid waiver only when: measured disk size ≤ cap

### Copy-Paste: AST Measurement Command

```python
python3 -c "
import ast
src = open('path/to/file.py').read()
tree = ast.parse(src)
for node in ast.walk(tree):
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        size = node.end_lineno - node.lineno + 1
        if size > 80:
            print(f'{node.name}: lines {node.lineno}–{node.end_lineno} ({size}L)')
" | sort -t'(' -k2 -rn
```

### Copy-Paste: Subtraction Chain Template

```text
<function_name>: <current>L
  − <helper_1>: <extracted>L  (extracted: <description>)
  − <helper_2>: <extracted>L  (extracted: <description>)
  = <remaining>L (target ≤ <cap>L) ✓/✗
```

---

## Verified On

| Project | Context |
| --------- | --------- |
| ProjectHephaestus (R0) | Planning session for issue #1180 — decompose 5 god-functions in `hephaestus/automation/`; `_implement_issue` cited as 354 lines in issue, found as 127 lines on disk; `_run_impl_review_loop` cited at `ci_driver.py:1513`, found at `_review_phase.py:374-503`; `_finalize_address_state` defined in plan but not called in replacement block; test file existence unverified; `_poll_ci_until_concluded` sentinel contract risk identified |
| ProjectHephaestus (R1) | Second planning iteration for issue #1180 after R0 NOGO review; AST re-measurement confirmed `_implement_issue` is 128L not 354L and `_run_impl_review_loop` is at `_review_phase.py:374`; arithmetic subtraction chain revealed `_run_ci_fix_session` needs 5 helpers (not 3) to reach ≤80L; `_run_address_step_if_needed` sentinel return pattern documented with all 3 control-flow states; R0 waiver-on-"marginal" grounds rejected — 128L = 60% over cap and is in scope |
| ProjectHephaestus | Issue #1180 R2 plan (2026-06-13) — 3rd TASK/PLAN/REVIEW cycle; all 7 target functions scoped to ≤80L |
| ProjectHephaestus | Issue #1464 plan (2026-06-30) — decompose 204L god FUNCTION `validate_prior_comments_addressed` in `review_validator.py`; R0 NOGO for asserting ≤80L from a ~70L executable-body estimate while the AC measures AST span (204L = 14L sig + 43L docstring + 147L body; 2-extraction R0 ≈105L span > 80L); R1 reached 67L span via a 3rd extraction `_run_validation_and_reconcile` + a concrete docstring trim 43→22 counted as an explicit −21L term |
