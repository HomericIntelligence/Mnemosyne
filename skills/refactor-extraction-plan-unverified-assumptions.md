---
name: refactor-extraction-plan-unverified-assumptions
description: "The uncertain assumptions and reviewer risks baked into a verbatim-move cluster-extraction PLAN that extracts a group of functions from a large module into a new sibling module with backward-compat `import X as X` re-exports in the parent. Use when: (1) reviewing or authoring a plan that moves a function cluster out of a god-module and re-exports the moved names from the original module to preserve mock patch paths, (2) the plan claims `patch(\"...old_module._fn\")` keeps working after the move, (3) the plan cites exact line numbers for a multi-step sequential edit, (4) the plan depends on a 'frozen' allowlist/magic-number invariant, (5) the plan asserts 'no circular import' or 'unused import removable' by static reasoning rather than execution, (6) the plan borrows type/function/field names from an UNMERGED dependency issue or an epic body's prose design (not from landed source) — every such symbol is an assumption until the dependency merges, (7) reviewing/authoring a plan that PROMOTES a shared helper (extract-and-reuse) and must decide pure-return vs impure-executor-callable, whether a boundary/import-surface test even applies, and whether a cited verification test actually exercises the promoted symbol."
category: architecture
date: 2026-07-04
version: "1.2.0"
user-invocable: false
verification: unverified
history: refactor-extraction-plan-unverified-assumptions.history
tags: [refactoring, extraction, cluster-extraction, backward-compat, re-export, mock-patch-path, planning, reviewer-risks, line-number-drift, circular-import, assumptions, dependency-chain, unmerged-dependency, epic-prose-api, assumed-not-grepped, stage-extraction, test-fake-assumption, pipeline, promote-shared-helper, pure-vs-impure-helper, fully-mocked-method, false-verification-command, boundary-test-applicability, import-surface-preservation, nogo-revision]
---

# Refactor Extraction Plan — Unverified Assumptions & Reviewer Risks

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-06-15 |
| **Objective** | Capture the uncertain assumptions a verbatim-move cluster-extraction PLAN makes — extracting a 12-function repo-management cluster from `hephaestus/automation/loop_runner.py` into a new `loop_repo_manager.py` with backward-compat `import X as X` re-exports (issue #1360) — so a reviewer knows exactly what to check before approving. |
| **Outcome** | Plan produced; NOT executed. These are the assumptions a reviewer must verify and an implementer must not take on faith. |
| **Verification** | unverified — planning artifact only; no code was written or run |
| **History** | v1.2.0 (2026-07-04): extends the skill with **promote-a-shared-helper review corrections** from issue #1814's NOGO→revise cycle (pure-return vs impure-executor-callable helper design, import-surface preservation, boundary-test applicability, and citing a verification test that actually exercises the promoted symbol). v1.1.0 (2026-07-04): extends the skill to the **unmerged-dependency assumption class** from issue #1814 (planning a stage extraction whose base types come from an unmerged `Depends on` chain / epic-body prose, not landed source). v1.0.0: initial capture of 5 uncertain assumptions + reviewer focus checklist from issue #1360 extraction plan. See `refactor-extraction-plan-unverified-assumptions.history`. |

> This skill is about the **PLANNING-RISK** angle, not the mechanics of *how* to extract a cluster.
> For the how-to mechanics see `python-module-decomposition-and-refactor-patterns` and
> `testing-module-patch-target-after-extraction`. For DRY *consolidation* (two modules → one)
> see `dry-refactoring-plan-assumption-audit`. This skill covers a *single module → two modules*
> verbatim move with re-exports, and what silently breaks.

## When to Use

- Reviewing or authoring a plan that extracts a cluster of functions out of a large module into a new sibling module.
- The plan keeps the original module importable by adding `from .new_module import _fn as _fn` re-exports (backward-compat shim) and claims existing `unittest.mock.patch("...old_module._fn")` calls still work.
- The plan cites exact line numbers (`module.py:566-942`, `pyproject.toml:263`) for a sequence of edits that delete/insert large blocks.
- The plan depends on a "frozen" list or magic number (e.g. an omit/coverage allowlist "frozen at N modules") that must be bumped in multiple places.
- The plan asserts "introduces no circular import" or "this import is now unused and can be removed" by static reasoning rather than by actually importing/linting.
- The plan re-houses control flow into a new module whose base types/functions/constants come from an **unmerged `Depends on #NNNN` dependency** (a strictly-serialized epic chain) or from an **epic body's prose API design** — the imports, constructor shapes, routing tables, and test fakes it builds on cannot be grepped from landed source because that source does not exist yet.
- The plan **PROMOTES a shared helper** (extract-and-reuse: an in-place method → a shared module function reused by two call sites) with a shim-first relocation, and a reviewer will check whether the promoted helper is **pure (returns computed data)** rather than impure (takes executor `Callable`s), whether the promotion **adds new imports** to the target module, whether the boundary/import-surface tests it cites even **apply** to the changed module, and whether every cited verification test actually **exercises the promoted symbol** (not a same-family shim it never touches).

## Verified Workflow

<!-- Section title per honest verification level: PROPOSED WORKFLOW (unverified). The
"## Verified Workflow" heading is retained only because scripts/validate_plugins.py requires that
literal token; this content is a PROPOSAL, not a verified procedure. See the warning banner below. -->

### Proposed Workflow (UNVERIFIED — planning artifact only)

> **Warning:** This workflow has not been validated end-to-end. No code was written or run. It is the
> reviewer/author checklist distilled from an *unexecuted* plan. Treat every item as a hypothesis
> until CI confirms.

### Quick Reference

```bash
# === Reviewer / implementer pre-flight for a cluster-extraction-with-re-export plan ===
# Replace OLD_MODULE with the dotted path being extracted FROM (e.g. hephaestus.automation.loop_runner)
# and run from the repo root.

OLD_MODULE="hephaestus.automation.loop_runner"   # the module losing functions
OLD_PATH="hephaestus/automation/loop_runner.py"  # its file
NEW_MODULE="loop_repo_manager"                    # the new sibling (bare name as imported within the pkg)

# 1. CENTRAL CHECK — does ANY module import the moved private names directly (not via the namespace)?
#    Re-exports only preserve patch paths for callers that look up the name through OLD_MODULE
#    at call time. A `from OLD_MODULE import _fn` anywhere ELSE binds a separate name that
#    patching OLD_MODULE._fn will NOT affect. Grep the WHOLE repo, not just OLD_PATH + its test.
grep -rn "from ${OLD_MODULE} import" hephaestus/ tests/ scripts/
#    Inspect every hit: any moved symbol imported by name into another module = a patch path that breaks.

# 2. MAGIC-NUMBER / FROZEN-LIST CHECK — find EVERY occurrence of the invariant count/list literal,
#    then READ the assertion body (is it `len(...) == 16` literal, or set membership?). Don't trust the comment.
grep -rn "16" pyproject.toml | grep -i "omit\|allowlist\|module"   # adjust literal/keyword
grep -rn "allowlist\|omit" tests/ pyproject.toml
#    Open the test and read whether it asserts a count literal vs a set membership before bumping anything.

# 3. NO-CYCLE CHECK — prove by EXECUTION, not by reading comments.
python -c "import ${OLD_MODULE}; from hephaestus.automation import ${NEW_MODULE}; print('import OK')"

# 4. RE-EXPORT IDENTITY SMOKE TEST — prove the shim actually re-binds the moved object.
python -c "import ${OLD_MODULE} as o; from hephaestus.automation import ${NEW_MODULE} as n; \
assert o._gh_list_repos is n._gh_list_repos, 'identity broken'; print('re-export identity OK')"

# 5. UNUSED-IMPORT CHECK — let ruff be the source of truth, do NOT hand-judge.
ruff check ${OLD_PATH} --select F401   # then `ruff check --fix` only after the deletion

# 6. LINE-NUMBER DRIFT REMINDER — after the FIRST block deletion, every later cited line number is stale.
#    Re-derive targets by stable marker, not by the plan's pre-edit numbers:
grep -n "# Repo discovery\|^def _gh_list_repos\|^def _gh_" ${OLD_PATH}
```

### Detailed Steps

1. **Verify re-export patch-path preservation against the WHOLE repo (the central assumption).**
   The plan's load-bearing claim is that `patch("...loop_runner._gh_list_repos")` keeps working after
   the function moves, because the re-export makes the name a real attribute of `loop_runner` and
   callers resolve it through the `loop_runner` namespace at call time. This is **only true** when
   every internal caller does a bare global lookup in `loop_runner` (or `loop_runner._gh_list_repos`).
   It **breaks** if any other module did `from ...loop_runner import _gh_list_repos`: that binding is a
   separate name in the other module, and patching `loop_runner._gh_list_repos` will not touch it.
   Grep `from <old_module> import` across **`hephaestus/`, `tests/`, and `scripts/`** — not just the
   module and its own test file.

2. **Anchor multi-edit instructions to stable markers, not absolute line numbers.**
   In a sequential multi-edit plan, deleting the first block (e.g. `:566-942`) shifts every later cited
   line. Use function names, unique strings, or section banners (`# Repo discovery`) as anchors, OR state
   explicitly in the plan that line numbers are pre-edit and must be re-derived after each deletion.

3. **Enumerate every place the frozen invariant appears, and read the assertion body.**
   When the plan bumps a "frozen-at-16" allowlist to 17, grep the literal `16` and the keyword across
   `pyproject.toml` and `tests/`. Open the test and confirm whether it is a hardcoded count
   (`len(expected) == 16`) or a set-membership check — the required edits differ. The comment count
   and the asserted count can live in different files; miss one and CI fails.

4. **Prove "no circular import" by execution.**
   "New module → ci_driver introduces no cycle because ci_driver only mentions loop_runner in comments"
   is static reasoning. ci_driver may import another automation module that transitively loads
   loop_runner at import time. The claim is only proven when the import smoke test actually runs.
   Flag it as "verify by execution," never "verified by reading."

5. **Defer conditional import removals to ruff, gated by per-symbol grep.**
   "Drop `urlparse`/`gh_cli_timeout` only if no other references remain" is exactly where hand-judgement
   slips. Removing a still-used import breaks the module; leaving an unused one fails ruff F401. After the
   deletion, grep each symbol in the file and let `ruff check --select F401` (then `--fix`) be the source
   of truth instead of eyeballing it.

### Extra steps for planning against UNMERGED dependencies (issue #1814 assumption class)

When the extraction target is a new module whose foundation lives in an unmerged `Depends on #NNNN`
chain, or in an epic body's prose "core types" section, add these steps on top of 1–5.

6. **Label every symbol borrowed from an unmerged dependency as "assumed from #NNNN, unverified until merged."**
   If the plan cites a type/function/field/constant that comes from an UNMERGED dependency issue or an
   epic body's prose design (e.g. `WorkItem`, `StageOutcome`, `Disposition`, `StageName`, the `ROUTES`
   table + its budget values like `plan_review_iter 3` / `plan_cycles 2`, the `AgentJob` shape, the
   `Stage` protocol signature in `pipeline/stages/base.py`, `JobResult`), mark it EXPLICITLY as
   assumed-until-merged. Never present epic-prose API shapes as if they were grepped from source — the
   epic body describes intended contracts, not landed code. The plan may even have to hedge ("authors
   `stages/base.py` … if #1813 has not"), which is an admission it cannot know the state of its own
   foundation; keep those hedges visible instead of smoothing them over.

7. **At implement time, re-verify every borrowed symbol against the ACTUAL merged dependency.**
   The dependency author may rename or reshape symbols during their own review cycle, so a symbol that
   matched the epic prose at plan time can be wrong by merge time. Before writing the extraction, grep
   the real merged code:

   ```bash
   grep -rn "class AgentJob\|def parse\|ROUTES\|class StageOutcome\|class WorkItem\|class Stage" \
     hephaestus/automation/pipeline/
   ```

   Confirm names, signatures, field names, and where constants actually live (e.g. is the budget in
   `routing.py` or somewhere else?) before importing them.

8. **Treat "test fakes that don't exist yet" as a DOUBLE assumption — interface AND existence.**
   `FakeGitHub` / `FakeWorkerPool` assumed to arrive from a sibling issue are two bets at once: that the
   fake exists, and that its interface matches. `grep -rn "class FakeGitHub\|class FakeWorkerPool"` may
   return ZERO matches at plan time. Confirm with grep at implement time; be ready to author the fakes
   locally if the sibling issue did not ship them.

9. **Recognize a `Depends on #NNNN` chain as a hypothesis layered on hypotheses, and split verified from assumed.**
   In a strictly-serialized chain (#1814 depends on #1813 → #1812 → #1811, none merged at plan time),
   every base type is an assumption, not a fact. The reviewer's job is to separate what was verified
   against CURRENT main (e.g. `prompts/planning.py:223 get_plan_prompt` — real and grep-confirmed) from
   what was assumed against FUTURE code (the `pipeline/` types from the unmerged chain). A plan that
   blurs the two is unreviewable; a plan that labels each symbol's provenance is checkable.

### Extra steps for PROMOTING a shared helper (issue #1814 R0→R1 NOGO corrections)

When the plan promotes an in-place method into a shared module function reused by two call sites
(extract-and-reuse, shim-first), add these steps. They come from a reviewer NOGO (grade C) whose
findings generalize to ANY promote-a-shared-helper / extraction-with-shim plan.

10. **Before budgeting effort for "byte-for-byte behavior unchanged," check whether the legacy test FULLY MOCKS the method you are refactoring.**
    A method that the legacy test stubs whole — e.g. `test_planner_loop.py:229` does
    `patch.object(planner.review_loop, "_apply_state_label")` and never asserts its internal log format
    or gh-call sequence — has NO internal-format contract to preserve. That single fact collapses the
    entire "must preserve exact warning-log wording / call order" risk: the shim only needs to remain a
    patchable method computing the same NET effect. Rule: grep the legacy test for
    `patch.object(<obj>, "<method>")` / `patch("...<method>")` on the exact symbol you're changing BEFORE
    budgeting effort for internal-format parity.

11. **When PROMOTING a shared helper, prefer a PURE helper that RETURNS the computed data over an impure one that TAKES executor callables.**
    Promoting `apply_plan_verdict(issue, *, is_go, add_labels: Callable, remove_labels: Callable)` — an
    impure, dual-calling-convention function — is surprising per POLA/P7 and forces new imports
    (`logger`, `issue_ref`) into a previously import-clean module. Make it pure instead:
    `apply_plan_verdict(*, is_go) -> tuple[str, list[str]]` returns `(label_to_add, labels_to_remove)`;
    BOTH the legacy caller and the new caller do their OWN side effects (gh writes + logging). Rule: a
    promoted "shared" transition should compute-and-return; let each caller own its I/O. Passing
    `Callable` executors into the shared function to serve two call sites is a smell.

12. **A promotion/extraction into module M must not silently expand M's import surface.**
    Verify what M currently imports (`grep -n "^import\|^from\|logger =" <M>`) and design the promoted
    helper so it needs NOTHING new. Here `state_labels.py:32-35` imports only `Iterable`/`Sequence`/`Any`
    and has no `logger`/`issue_ref`; a pure helper adds zero imports. Rule: read the target module's
    import block first; if your promoted code would add a logger or an I/O import to a pure-vocabulary
    module, redesign it as pure.

13. **Do NOT invoke a boundary / import-surface / architecture test as "verification" without first proving it APPLIES to the module you touched.**
    A plan that lists `test_automation_boundary.py` + `test_import_surface.py` for a change to
    `state_labels.py` is confused if that module has zero external importers:
    `grep -rn "state_labels" hephaestus/ --include=*.py | grep -v "hephaestus/automation/"` returns
    ZERO — the module is automation-internal, so the library-vs-automation boundary tests do not
    constrain it. Citing them is a false-applicability verification. Rule: before mapping an
    architecture/boundary test to a criterion, grep the actual importer set of the file you changed to
    confirm the test's precondition holds.

14. **Cite the RIGHT verification file — a same-family test that covers DIFFERENT symbols is a FALSE verification command.**
    Citing `state/test_shim_parity.py` to verify the `apply_plan_verdict` promotion is worse than no
    command: that file only parametrizes `planner_state`/`implementer_state`/`review_state` shims
    (confirmed by reading it) — it would PASS while the promotion is completely broken, fabricating
    confidence. The correct citation is the ALREADY-EXISTING `tests/unit/automation/test_state_labels.py`
    with a new `-k apply_plan_verdict` case. Rule: open the test file you plan to cite and confirm it
    actually exercises the symbol under change; a green run of an unrelated test fabricates confidence.
    (Companion rule: resolve "migrate/move scenario rows" ambiguity explicitly — COPY-then-adapt when
    the constraint says "originals stay green / legacy untouched"; it is NOT a DRY violation when the
    copied rows assert a DIFFERENT system-under-test.)

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Assume re-export preserves all mock patch paths | Plan claimed `patch("...loop_runner._gh_list_repos")` keeps working post-move because the `import X as X` re-export makes the name a real attribute, and only grepped within `loop_runner.py` + `test_loop_runner.py` | True only if every caller resolves the name through the `loop_runner` namespace at call time; a `from loop_runner import _gh_list_repos` in ANY other module is a separate binding that patching `loop_runner` does not affect — and that scope was never grepped | Before claiming re-exports preserve patch paths, grep the ENTIRE repo (`hephaestus/` AND `tests/` AND `scripts/`) for `from <old_module> import _<name>`, not just the two files you happened to read |
| Cite exact line numbers for a sequential multi-edit | Plan referenced `loop_runner.py:566-942`, `:1198`, `:1359`, `pyproject.toml:263`, `test_omit_allowlist.py:40-53` read at plan time | An implementer edits sequentially; deleting the `566-942` block shifts every later line, so literal line-number targeting after step 1 hits the wrong lines | Anchor multi-edit instructions to stable markers (function names, section banners, unique strings), or explicitly state line numbers are pre-edit and must be re-derived after each deletion |
| Trust the "frozen at 16 modules" comment | Plan asserted the omit allowlist is frozen at 16 and only the comment + one test need bumping to 17, without running the test or reading its assertion body | The "16" figure and the assertion mechanism (count literal vs set membership) were read, not verified; a hardcoded `len(...) == 16` elsewhere, or a third copy of the count, would be missed and fail CI | When a plan depends on a frozen-list/magic-number invariant, READ the actual assertion body (don't trust the comment) and grep the literal to enumerate EVERY place it appears |
| Reason about circular imports statically | Plan claimed `loop_repo_manager → ci_driver` adds no cycle because ci_driver references loop_runner only in comments | Static reasoning; ci_driver could import another automation module that transitively imports loop_runner at module load, creating a cycle the comment-scan never sees | The import-graph claim is only proven by the smoke-test step actually executing — label it "verify by execution," not "verified by reading" |
| Hand-judge conditional unused-import removal | Plan said to drop `urlparse` and `gh_cli_timeout` from loop_runner "only if no other references remain," left to manual judgement | Removing a still-used import breaks the module; leaving a genuinely-unused one fails ruff F401 — both directions of hand-judgement are wrong | Gate each import removal on a per-symbol grep AFTER the deletion and make `ruff check --select F401` / `--fix` the source of truth, not eyeballing |
| Present epic-prose API shapes as if grepped from source (issue #1814) | Plan read `WorkItem`, `StageOutcome`, `Disposition`, `StageName`, `ROUTES` + budgets (`plan_review_iter 3`, `plan_cycles 2`), the `AgentJob`/`Stage`/`JobResult` shapes from the epic #1809 body's "Core types" prose and wrote imports + `JobRequest`/`Continue` usage as if those were landed facts | Those types come from unmerged deps (#1811–#1813); the epic body describes intended contracts, not code. If a dep lands with a different name/signature/field, every import and test fake is wrong — and nothing can be verified until the deps merge | Label every symbol borrowed from an unmerged dependency or epic prose as "assumed from #NNNN, unverified until merged"; re-grep the actual merged dep (`grep -rn "class AgentJob\|def parse\|ROUTES\|class StageOutcome" hephaestus/automation/pipeline/`) at implement time |
| Assume sibling-issue test fakes already exist (issue #1814) | Plan wrote table-driven stage tests against `FakeGitHub` / `FakeWorkerPool` assumed to arrive from a sibling issue | `grep -rn "class FakeGitHub\|class FakeWorkerPool"` returned ZERO matches — the fakes don't exist yet; this is a double assumption (interface AND existence) | Confirm fake existence + interface with grep at implement time; be ready to author the fakes locally if the sibling issue did not ship them |
| Build imports on an unmerged `AgentJob`/`Stage`/`ROUTES` shape (issue #1814) | Plan hedged "authors `stages/base.py` … if #1813 has not" yet still committed to the `Stage` protocol signature, the `AgentJob(prompt_builder=…, parse=…)` constructor, and `ROUTES` budget values from the epic prose | The hedge itself admits the plan cannot know the state of its own foundation; a strictly-serialized `Depends on` chain (#1814 → #1813 → #1812 → #1811, none merged) is a hypothesis layered on hypotheses | Treat a `Depends on #NNNN` chain as unverified until each dep merges; separate what was grep-confirmed against CURRENT main from what was assumed against FUTURE code, and re-verify signatures after the deps land |
| Budget effort for internal log/call-order parity of a fully-mocked method (issue #1814 R0→R1) | Reviewer raised (and the first plan budgeted for) preserving the exact warning-log wording and gh-call order of `_apply_state_label` when promoting it | The legacy test `test_planner_loop.py:229` does `patch.object(planner.review_loop, "_apply_state_label")` — it stubs the whole method and never asserts its internal format or call sequence, so there is no internal contract to preserve; the shim need only stay patchable and compute the same NET effect | Before budgeting internal-format parity, grep the legacy test for `patch.object(<obj>, "<method>")` / `patch("...<method>")` on the exact symbol; if it's fully mocked, internal-format parity is a non-risk |
| Promote a shared helper as IMPURE with `Callable` executors (issue #1814 R0→R1) | First plan promoted `apply_plan_verdict(issue, *, is_go, add_labels: Callable, remove_labels: Callable)` — a dual-calling-convention function taking executor callables to serve both call sites | Impure + dual-convention is surprising per POLA/P7, and it forces NEW imports (`logger`, `issue_ref`) into `state_labels.py`, a previously import-clean pure-vocabulary module | Make a promoted shared transition PURE — `apply_plan_verdict(*, is_go) -> tuple[str, list[str]]` returns `(label_to_add, labels_to_remove)` and each caller owns its own gh writes + logging; passing `Callable` executors into a shared function to serve two sites is a smell |
| Cite boundary/import-surface tests for a module with ZERO external importers (issue #1814 R0→R1) | First plan listed `test_automation_boundary.py` + `test_import_surface.py` as verification for a change to `state_labels.py` | `grep -rn "state_labels" hephaestus/ --include=*.py | grep -v "hephaestus/automation/"` returns ZERO — the module is automation-internal, so the library-vs-automation boundary tests do not constrain it; citing them is a false-applicability verification | Before mapping an architecture/boundary test to a criterion, grep the actual importer set of the file you changed to confirm the test's precondition holds |
| Cite a shim-parity test that covers DIFFERENT symbols (false verification) (issue #1814 R0→R1) | First plan cited `state/test_shim_parity.py` to verify the `apply_plan_verdict` promotion | That file only parametrizes `planner_state`/`implementer_state`/`review_state` shims (confirmed by reading it) — it would PASS while the promotion is broken, fabricating confidence; worse than no command | Open the test file you plan to cite and confirm it exercises the symbol under change; here the correct citation is the existing `tests/unit/automation/test_state_labels.py` with a new `-k apply_plan_verdict` case |
| Leave "migrate scenario rows" ambiguous (move vs copy) (issue #1814 R0→R1) | Plan said "migrate/move the scenario rows" for stage tests without specifying move vs copy, while also constraining "originals stay green / legacy untouched" | An ambiguous move-vs-copy instruction is contradictory with a "legacy untouched" constraint; a reader could delete the originals and break the legacy suite | Resolve explicitly: COPY-then-adapt when the constraint says originals stay green; copied rows asserting a DIFFERENT system-under-test are NOT a DRY violation |

## Results & Parameters

### What the plan got RIGHT (keep these strengths)

- **Read the actual code before planning** — confirmed the issue's line numbers were approximately right and that the 12 functions are genuinely self-contained pure helpers safe to move verbatim.
- **Enumerated call sites and patch sites with grep before asserting re-exports are safe** — correct instinct; the only defect was incomplete scope (see assumption #1).
- **Added an identity smoke test** (`assert loop_runner.X is loop_repo_manager.X`) to prove the re-export wiring binds the same object.
- **Mapped a per-criterion verification command to each acceptance criterion** so the plan is checkable rather than narrative.

**Issue #1814 (pipeline planning/plan-review stage extraction) got these RIGHT too:**

- **The prompt-builder reuse claims WERE verified against current main** — `get_plan_prompt`, `get_plan_loop_review_prompt`, `get_advise_prompt_builder`, and `build_learn_prompt` were all grep-confirmed to exist with the cited signatures, not merely asserted from prose.
- **The `_apply_state_label` promotion source was read directly** (`planner_review_loop.py:441-483`), along with the state-label constants (`state_labels.py:39-41`), rather than assumed.
- **A per-acceptance-criterion verification command was provided**, keeping the plan checkable — the same strength as the #1360 plan, and the discipline that lets a reviewer separate verified from assumed symbols.

**Issue #1814 R0→R1 (the plan REVISION after the reviewer NOGO) got these RIGHT — keep them:**

- **Resolved the "highest-risk, no-fallback mutation-return" finding by making durable writes an observable ordering, not a field on the outcome object.** Mutations are NOT carried on the returned outcome; the stage performs the durable write through a coordinator-owned accessor (`ctx.github`) IMMEDIATELY BEFORE returning a plain outcome, so "durable write precedes queue push" is directly observable as ordering in a recorded `mutation_log`. Rule: when a reviewer flags a mutation returned for a caller to apply later ("what if the queue push happens first?"), make the durable write happen inside the stage right before the return and assert the ordering, rather than shipping the mutation as data.
- **Designed the test-fake interfaces up front.** `FakeGitHub` / `FakeWorkerPool` method signatures were written INTO the plan rather than deferred — a reviewer had flagged deferring them as a stage-handoff gap. Rule: write fake/adapter method signatures into the plan itself when a later stage depends on them; deferring the interface is a handoff gap.

### Reviewer focus (the 5 things to check hardest in such a plan)

```
## Cluster-extraction-with-re-export plan review checklist

- [ ] Did the grep for cross-module private-name imports cover the WHOLE repo
      (hephaestus/ + tests/ + scripts/), not just old_module.py + its test file?
- [ ] Are edit instructions anchored to stable markers (function names / banners),
      or to soon-stale absolute line numbers?
- [ ] Was the frozen-list/magic-number assertion mechanism actually READ
      (count literal vs set membership) and EVERY occurrence of the number grepped?
- [ ] Is the "no circular import" claim validated by an EXECUTED import smoke test,
      not just a comment scan / static reasoning?
- [ ] Are conditional import removals deferred to ruff (F401), not hand-judged?
- [ ] Is every symbol borrowed from a `Depends on` dependency labeled
      assumed-until-merged, and separated from symbols verified against current main?
- [ ] Is the method being refactored fully mocked in the legacy test
      (if so, internal-format / call-order parity is a non-risk)?
- [ ] Is the promoted shared helper PURE (returns computed data) rather than
      taking executor callables to serve two call sites?
- [ ] Does the promotion add any NEW import to the target module
      (grep its current import block first)?
- [ ] Does every cited verification test actually exercise the changed symbol,
      and does every cited boundary/import-surface test actually APPLY to the
      changed module (grep its external-importer set)?
```

### Issue #1360 specific findings

| Assumption in the plan | Status | What a reviewer must do |
|------------------------|--------|-------------------------|
| Re-export preserves all `patch("...loop_runner._fn")` paths | UNVERIFIED (scope too narrow) | Grep `from hephaestus.automation.loop_runner import` across hephaestus/, tests/, scripts/ — any direct private-name importer breaks |
| Cited line numbers (`:566-942`, `:1198`, `:1359`, `pyproject.toml:263`) are actionable as-is | FRAGILE | Re-derive by marker after the first block deletion; numbers are pre-edit snapshots |
| Omit allowlist "frozen at 16," bump in pyproject comment + one test | UNVERIFIED | Read the assertion body (count literal vs set membership); grep `16` for a third location |
| `loop_repo_manager → ci_driver` adds no cycle | REASONED, NOT RUN | Run `python -c "import ...loop_runner; from ...automation import loop_repo_manager"` |
| `urlparse` / `gh_cli_timeout` are safely removable | CONDITIONAL | Per-symbol grep after deletion; let `ruff --select F401` decide |

### Issue #1814 specific findings

Plan re-houses control flow out of legacy orchestrators (`planner.py::Planner._plan_issue`,
`planner_review_loop.py::PlanReviewLoop.run`) into a new queue-based pipeline
(`pipeline/stages/planning.py`, `plan_review.py`), promotes `_apply_state_label`
(`planner_review_loop.py:441`) into a shared `state_labels.apply_plan_verdict` with a shim-first
re-import, and adds table-driven stage tests. #1814 `Depends on #1813 → #1812 → #1811`, none merged
at plan time.

| Symbol / claim in the plan | Status | What a reviewer must do |
|----------------------------|--------|-------------------------|
| `get_plan_prompt`, `get_plan_loop_review_prompt`, `get_advise_prompt_builder`, `build_learn_prompt` (prompt-builder reuse) | VERIFIED-against-main (grep-confirmed with cited signatures) | Trust as-is; these are the plan's real foundation on current main |
| `_apply_state_label` promotion source (`planner_review_loop.py:441-483`) + state-label constants (`state_labels.py:39-41`) | VERIFIED-against-main (read directly) | Trust as-is; confirm the shim-first re-import preserves existing import paths |
| `WorkItem`, `StageOutcome`, `Disposition`, `StageName` | ASSUMED-from-#1811/#1812/#1813 (from epic #1809 prose, not landed source) | Re-grep the merged deps; names/spelling may differ (`StageOutcome` may be spelled differently) |
| `ROUTES` table + budgets (`plan_review_iter 3`, `plan_cycles 2`) | ASSUMED-from-epic-prose | Confirm the table exists and lives where assumed (`routing.py`?) and that the budget values match after the dep merges |
| `AgentJob` shape (carries `prompt_builder` + optional in-worker `parse`?) | ASSUMED-from-epic-prose | Grep `class AgentJob` / `def parse` in merged `pipeline/`; the constructor may have no `parse` param |
| `Stage` protocol signature in `pipeline/stages/base.py`, `JobResult`, `JobRequest`/`Continue` | ASSUMED-from-#1813 (plan hedges "authors `stages/base.py` … if #1813 has not") | Verify the protocol signature against merged #1813; author `base.py` locally only if the dep did not ship it |
| `FakeGitHub` / `FakeWorkerPool` test fakes | ASSUMED-to-exist-from-sibling (grep returned ZERO matches) | Confirm existence AND interface with grep at implement time; author locally if the sibling did not ship them |

### Issue #1814 R0→R1 NOGO corrections (promote-a-shared-helper)

The first plan (R0) got a reviewer NOGO (grade C). The revision (R1) addressed each finding. These
corrections generalize to ANY promote-a-shared-helper / extraction-with-shim plan.

| Reviewer finding (severity) | Correcting decision (R1) | Generalizable rule |
|-----------------------------|--------------------------|--------------------|
| "Must preserve exact warning-log wording / call order of `_apply_state_label`" (raised as high risk) | Found the legacy test `test_planner_loop.py:229` FULLY MOCKS the method (`patch.object(planner.review_loop, "_apply_state_label")`) — no internal contract to preserve; shim only needs to stay patchable and compute the same NET effect | Grep the legacy test for `patch.object`/`patch` on the exact symbol BEFORE budgeting internal-format parity; a fully-mocked method has no internal-format risk |
| Promoted `apply_plan_verdict(issue, *, is_go, add_labels: Callable, remove_labels: Callable)` — impure, dual-convention (P7/POLA surprise) | Made it PURE: `apply_plan_verdict(*, is_go) -> tuple[str, list[str]]`; both callers do their own gh writes + logging | A promoted shared transition should compute-and-return; passing `Callable` executors into a shared function to serve two sites is a smell |
| Impure helper would add `logger`/`issue_ref` imports to import-clean `state_labels.py` | Pure helper adds ZERO imports — `state_labels.py:32-35` still imports only `Iterable`/`Sequence`/`Any` | A promotion into module M must not expand M's import surface; read M's import block first and design the promoted code to need nothing new |
| Cited `test_automation_boundary.py` + `test_import_surface.py` as verification for `state_labels.py` | Grep showed ZERO external importers (`grep -rn "state_labels" hephaestus/ --include=*.py | grep -v "hephaestus/automation/"`) — boundary tests do not apply; dropped them | Before mapping a boundary/architecture test to a criterion, grep the changed file's external-importer set to confirm the test's precondition holds |
| Cited `state/test_shim_parity.py` to verify the `apply_plan_verdict` promotion (false verification) | That file only covers `planner_state`/`implementer_state`/`review_state` shims — re-pointed at the existing `tests/unit/automation/test_state_labels.py` with a new `-k apply_plan_verdict` case | Open the cited test and confirm it exercises the changed symbol; a green run of an unrelated same-family test fabricates confidence |
| "Highest-risk, no-fallback" mutation returned for the caller to apply later | Mutations are NOT a field on the outcome; the stage does the durable write through `ctx.github` IMMEDIATELY BEFORE returning a plain outcome, so "durable write precedes queue push" is observable ordering in a recorded `mutation_log` | When a mutation is returned for later application, make the durable write happen inside the stage right before the return and assert the ordering instead |
| Deferring `FakeGitHub`/`FakeWorkerPool` interfaces to a later stage (handoff gap) | Wrote the fake method signatures INTO the plan up front | Write fake/adapter method signatures into the plan when a later stage depends on them; deferring the interface is a handoff gap |
| Ambiguous "migrate/move scenario rows" against a "legacy untouched" constraint | Resolved to COPY-then-adapt (originals stay green); copied rows assert a different system-under-test | Resolve move-vs-copy explicitly; copying rows that assert a DIFFERENT SUT is not a DRY violation |

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| ProjectHephaestus | Planning phase for issue #1360 (extract 12-function repo-management cluster from `automation/loop_runner.py` into `loop_repo_manager.py` with backward-compat re-exports) | Plan produced, NOT executed; this skill records the unverified assumptions and reviewer risks. Implementation pending. |
| ProjectHephaestus | Planning phase for issue #1814 (pipeline planning + plan-review stages, epic #1809) — re-house control flow out of `planner.py` / `planner_review_loop.py` into `pipeline/stages/planning.py` + `plan_review.py`, promote `_apply_state_label` to shared `state_labels.apply_plan_verdict` | Plan produced, NOT executed. Novel finding: the extraction builds on an UNMERGED `Depends on #1813 → #1812 → #1811` chain, so every base type (`WorkItem`, `StageOutcome`, `AgentJob`, `Stage`, `ROUTES`, test fakes) is an assumption from epic-#1809 prose until the deps merge; prompt-builder reuse + `_apply_state_label` source were verified against current main. |
| ProjectHephaestus | Issue #1814 R0→R1 re-plan (plan REVISION after a reviewer NOGO, grade C) — promote-a-shared-helper corrections | Plan revised, NOT executed. Durable lessons are the review-driven corrections that generalize to any promote-a-shared-helper / extraction-with-shim plan: check whether the refactored method is fully mocked (internal-format parity non-risk), prefer a PURE compute-and-return helper over an impure executor-callable one, do not expand the target module's import surface, do not cite boundary/import-surface tests that don't apply (zero external importers) or verification tests that don't exercise the promoted symbol; keep-this-strength: durable write via `ctx.github` before the return (observable ordering) and test-fake signatures designed up front. |
