---
name: refactor-extraction-plan-unverified-assumptions
description: "The uncertain assumptions and reviewer risks baked into a verbatim-move cluster-extraction PLAN that extracts a group of functions from a large module into a new sibling module with backward-compat `import X as X` re-exports in the parent. Use when: (1) reviewing or authoring a plan that moves a function cluster out of a god-module and re-exports the moved names from the original module to preserve mock patch paths, (2) the plan claims `patch(\"...old_module._fn\")` keeps working after the move, (3) the plan cites exact line numbers for a multi-step sequential edit, (4) the plan depends on a 'frozen' allowlist/magic-number invariant, (5) the plan asserts 'no circular import' or 'unused import removable' by static reasoning rather than execution, (6) the plan borrows type/function/field names from an UNMERGED dependency issue or an epic body's prose design (not from landed source) — every such symbol is an assumption until the dependency merges, (7) the plan grounds itself on an epic/parent body's `file:line` anchors, hardcoded budgets/caps, verdict/return-tuple shapes, cross-module patch seams, or a bug-number citation for a behavior-preserving move — re-grep every anchor, move caps to DATA, record tuples verbatim, sweep the whole test tree for patch targets, and locate the ACTUAL code sites of any bug number (it won't grep)."
category: architecture
date: 2026-07-04
version: "1.2.0"
user-invocable: false
verification: unverified
history: refactor-extraction-plan-unverified-assumptions.history
tags: [refactoring, extraction, cluster-extraction, backward-compat, re-export, mock-patch-path, planning, reviewer-risks, line-number-drift, circular-import, assumptions, dependency-chain, unmerged-dependency, epic-prose-api, assumed-not-grepped, stage-extraction, test-fake-assumption, pipeline, stale-epic-anchor, budgets-as-data, verdict-tuple-shape, patch-seam-sweep, bug-number-wont-grep, delegate-vs-literal, behavior-preserving-move, state-machine]
---

# Refactor Extraction Plan — Unverified Assumptions & Reviewer Risks

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-06-15 |
| **Objective** | Capture the uncertain assumptions a verbatim-move cluster-extraction PLAN makes — extracting a 12-function repo-management cluster from `hephaestus/automation/loop_runner.py` into a new `loop_repo_manager.py` with backward-compat `import X as X` re-exports (issue #1360) — so a reviewer knows exactly what to check before approving. |
| **Outcome** | Plan produced; NOT executed. These are the assumptions a reviewer must verify and an implementer must not take on faith. |
| **Verification** | unverified — planning artifact only; no code was written or run |
| **History** | v1.2.0 (2026-07-04): adds the **stale-epic-anchor + behavior-preserving-move risk trio** from issue #1815 (re-grep every epic `file:line`; move budgets/caps to DATA; record verdict/return-tuple shapes verbatim; whole-test-tree patch-seam sweep; a cited bug number won't grep — locate the ACTUAL sites; delegate the exploration to parallel read-only agents but independently verify the highest-load-bearing anchors yourself). v1.1.0 (2026-07-04): extends the skill to the **unmerged-dependency assumption class** from issue #1814 (planning a stage extraction whose base types come from an unmerged `Depends on` chain / epic-body prose, not landed source). v1.0.0: initial capture of 5 uncertain assumptions + reviewer focus checklist from issue #1360 extraction plan. See `refactor-extraction-plan-unverified-assumptions.history`. |

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
- You are grounding a plan on an **epic/parent body as the authoritative contract**, and that body cites specific `file:line` anchors, prompt-builder line refs, or gate helpers. Epic anchors go stale exactly like an issue's "Evidence:" section — a named file may merely CALL an indirection root where the literal actually lives (a thin DELEGATE), and a cited helper may not exist at all. A passed-strict-review parent plan does NOT exempt you from re-grepping every cited symbol.
- The move is **behavior-preserving (an extraction / re-housing into per-stage state machines)** and the load-bearing risks are: budgets/caps that must move to DATA (a routing table) rather than stay hardcoded; verdict/return-tuple shapes that are easy to transcribe wrong; cross-module dispatch/patch seams that must be re-imported at the NEW module path; or a behavior realized by MULTIPLE non-obvious sites with NO literal marker (e.g. a "#1572 progress-aware extension" that has no `1572` string anywhere in code).

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

```bash
# === Grounding a behavior-preserving move on an epic/parent body (issue #1815 discipline) ===
# Run from the SOURCE repo root before writing the plan. The epic body is the contract,
# but EVERY file:line it cites is a hypothesis until re-grepped.

# A. RE-GREP EVERY EPIC ANCHOR — a named file may only DELEGATE to where the literal lives.
#    Confirm the symbol is defined (not merely called) at the cited path:
grep -nE "^\s*def <symbol>\b|^\s*class <Symbol>\b" hephaestus/automation/*.py
#    e.g. epic says "_finalize_pr :36"; grep shows implementer_phase_runner.py:1111 _finalize_pr is a
#    "Delegate to :meth:`PRCreatePhase._finalize_pr`" — the LITERAL lives in _pr_create_phase.py:36.
#    Also PROVE a cited gate helper actually exists before citing it:
grep -nE "^def is_" hephaestus/automation/state_labels.py
#    e.g. epic claimed an "is_plan_review_go" gate; grep shows only is_plan_go / is_plan_no_go /
#    is_implementation_go / is_skipped / is_epic — no such helper. The real gate is the plan-review
#    verdict check inside _ensure_plan_ready (grep it, do not cite the non-existent helper):
grep -n "def _ensure_plan_ready" hephaestus/automation/implementer_phase_runner.py

# B. BUDGETS-AS-DATA — cite the exact legacy constants the move must relocate to the routing table,
#    and require a test that monkeypatches the DATA (proving nothing is hardcoded):
grep -nE "MAX_REVIEW_ITERATIONS|HARD_CAP" hephaestus/automation/_review_phase.py
#    e.g. _review_phase.py:87 MAX_REVIEW_ITERATIONS = 3 ; :95 MAX_REVIEW_ITERATIONS_HARD_CAP = *2 (=6).

# C. VERDICT / RETURN-TUPLE SHAPES — record verbatim from source (order + element meaning + enum domain):
grep -nA2 "def _evaluate_go_verdict\|def review_pr_inline\|def validate_prior_comments_addressed" \
  hephaestus/automation/_review_phase.py hephaestus/automation/pr_reviewer.py \
  hephaestus/automation/review_validator.py
#    Read the actual `return` lines AND the docstring — the ERROR verdict may be surfaced ELSEWHERE
#    than the tuple.

# D. PATCH-SEAM SWEEP — for EVERY moved symbol, grep the WHOLE test tree for its patch target so the
#    plan can require re-importing it at the NEW module path (a whole-test-tree sweep, not just one file):
for sym in <moved_symbol_1> <moved_symbol_2>; do grep -rn "$sym" tests/ ; done

# E. BUG-NUMBER-WON'T-GREP — a plan citing a bug number must locate the ACTUAL code sites; the number
#    is not in the code. Find the behavior by its real anchors instead:
grep -rn "1572" hephaestus/automation/            # returns NOTHING — the number is not in code
grep -n "_review_thread_count_decreased" hephaestus/automation/_review_phase.py   # :155 is one real site
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

### Extra steps for grounding a behavior-preserving move on an epic/parent body (issue #1815 assumption class)

When the epic/parent body is the authoritative contract for a behavior-preserving extraction (re-housing
a fused loop into per-stage state machines), add these steps on top of 1–9.

10. **Pull the epic/parent body as the contract, but re-grep every `file:line` anchor it cites — epic
    anchors go stale exactly like an issue's "Evidence:" section.** A passed-strict-review parent plan is
    NOT a substitute for re-grepping. Two failure shapes recur:
    (a) **delegate vs literal** — a named file may merely CALL the indirection root where the literal
    lives. In #1815 the epic's "`_finalize_pr :36`" actually refers to `_pr_create_phase.py:36`; the
    `implementer_phase_runner.py:1111 _finalize_pr` is only a thin DELEGATE (`"Delegate to
    :meth:`PRCreatePhase._finalize_pr`"`, calling `self.pr_create_phase._finalize_pr(...)`). Cite the
    file where the code is DEFINED, not one that forwards to it.
    (b) **non-existent helper** — the epic said the GATE gates on "`is_plan_review_go` at-or-past," but
    NO such helper exists in `state_labels.py` (only `is_plan_go` / `is_plan_no_go` /
    `is_implementation_go` / `is_skipped` / `is_epic`). The real gate is the plan-review verdict check
    inside `_ensure_plan_ready` (`implementer_phase_runner.py:429`). `grep -nE "^def <name>"` every cited
    symbol before writing it into the plan.

11. **Move budgets/caps to DATA (the routing table), never leave them hardcoded — and cite the exact
    legacy constants + demand a monkeypatch test.** For a re-housing that promises "budgets live in the
    routing table now," name the constants the move must relocate — in #1815 `_review_phase.py:87
    MAX_REVIEW_ITERATIONS = 3` and `:95 MAX_REVIEW_ITERATIONS_HARD_CAP = MAX_REVIEW_ITERATIONS * 2` (= 6)
    — and require a test that monkeypatches the DATA and asserts the loop honors the patched value. A
    test that still passes when the cap is hardcoded proves nothing.

12. **Record verdict/return-tuple shapes VERBATIM from source — order, element meaning, and enum domain
    — and note where out-of-band results are surfaced.** These are trivially transcribed wrong. In #1815:
    `_evaluate_go_verdict -> tuple[str, bool, bool]` = `(verdict, go_blocked_by_automation, should_break)`
    where `verdict ∈ {"GO", "NOGO", "HUMAN_BLOCKED"}` (the ERROR verdict is surfaced ELSEWHERE, not in
    this tuple); `review_pr_inline -> tuple[str, list[str]]` = `(review_text, thread_ids)`;
    `validate_prior_comments_addressed -> tuple[list[str], bool, set[str]]` =
    `(reopened_thread_ids, is_clean, seen/reopened_keys)`. Read the `return` lines AND the docstring, not
    just the signature.

13. **Preserve cross-module dispatch/patch seams AND locate behaviors that have NO literal marker.**
    Two sub-checks:
    (a) **patch-seam sweep** — the moved code preserves cross-module dispatch/patch seams, so re-import
    every patched symbol at the NEW module path and require a WHOLE-TEST-TREE sweep (`grep -rn` per moved
    symbol across all of `tests/`, not just the one file you happened to read) in the PR body (Risk R3).
    (b) **bug-number-won't-grep** — a behavior realized by multiple non-obvious sites with no literal
    marker (the "#1572 progress-aware iteration extension" has NO `1572` string in code — it is
    `_review_thread_count_decreased` at `_review_phase.py:155`, the budget bump in the impl-review loop,
    and a `>=` (not `==`) exhaustion anchor). A plan that cites a bug number MUST locate the ACTUAL code
    sites, because the number won't grep.

14. **Delegate the exploration to parallel read-only agents, but ALSO independently verify the
    highest-load-bearing anchors yourself — don't block on the agents.** Run direct
    `grep -nE "^def "` checks on the prompt-builder line numbers and the re-housed function signatures in
    parallel with the agents. In #1815 all 10 prompt-builder line numbers the epic cited were confirmed
    exact by direct grep, which let the plan proceed confidently while the broader agents filled in
    return-tuple shapes and test-template details. Parallelism buys speed; your own spot-check of the
    load-bearing anchors buys correctness.

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
| Trust the epic body's `file:line` anchors verbatim without re-grepping (issue #1815) | Epic #1809 carried the full approved plan with per-stage docs + prompt-function line refs; it was tempting to transcribe each `file:line` straight into the child plan | TWO cited anchors were stale/misleading: (a) "`_finalize_pr :36`" actually refers to `_pr_create_phase.py:36` — the `implementer_phase_runner.py:1111 _finalize_pr` is only a thin DELEGATE to it (a named file can merely CALL the indirection root where the literal lives); (b) the epic said the gate gates on "`is_plan_review_go` at-or-past," but NO such helper exists in `state_labels.py` (only `is_plan_go` / `is_implementation_go` / `is_skipped`) — the real gate is the plan-review verdict check inside `_ensure_plan_ready:429`. Either wrong anchor would draw a NOGO from a strict plan reviewer | `grep -nE "^def <name>"` EVERY symbol the epic cites before writing the plan — a passed-strict-review parent plan does not exempt you from re-grepping; epic anchors go stale exactly like an issue's "Evidence:" section. Cite the file where the code is DEFINED, not one that delegates to it, and never cite a gate helper you have not confirmed exists |
| Cite a bug number as if it were greppable, or leave budgets/verdict-tuples unspecified in a behavior-preserving move (issue #1815) | Early plan draft referenced "the #1572 progress-aware extension," assumed the review caps would ride along in code, and paraphrased the reviewer verdict return instead of recording it | `grep -rn "1572"` in `hephaestus/automation/` returns NOTHING — the behavior is `_review_thread_count_decreased:155` + the impl-review budget bump + a `>=` (not `==`) exhaustion anchor; a hardcoded `MAX_REVIEW_ITERATIONS = 3` / `HARD_CAP = *2` would silently NOT move to the routing table; and a paraphrased tuple is easy to get wrong (`_evaluate_go_verdict` returns `(verdict, go_blocked_by_automation, should_break)`, ERROR surfaced elsewhere) | Locate the ACTUAL code sites of any cited bug number (the number won't grep); move budgets/caps to DATA and require a monkeypatch test proving no hardcoding; record every verdict/return-tuple shape verbatim from source; and add a whole-test-tree patch-seam sweep (`grep -rn` per moved symbol) to the PR body |

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

**Issue #1815 (implementation + pr-review stage extraction, epic #1809) got these RIGHT too:**

- **All 10 prompt-builder line numbers the epic cited were confirmed exact by direct grep** run in parallel with the exploration agents, so the plan proceeded confidently on a verified foundation instead of blocking or trusting prose.
- **Both stale epic anchors were caught by re-grepping** — the `_finalize_pr` delegate-vs-literal (`_pr_create_phase.py:36`) and the non-existent `is_plan_review_go` gate (real gate: `_ensure_plan_ready:429`) — so neither wrong anchor reached the plan a reviewer would NOGO.
- **The three reviewer/verdict return-tuple shapes were recorded verbatim from source**, and the legacy budget constants (`_review_phase.py:87` / `:95`) were cited with a monkeypatch-test requirement so "budgets-as-data" is enforceable rather than aspirational.

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
- [ ] Was EVERY epic/parent-body `file:line` anchor re-grepped (not transcribed),
      confirming the symbol is DEFINED there and not merely delegated to, and that any
      cited gate helper actually exists?
- [ ] For a behavior-preserving move: are budgets/caps moved to DATA with a monkeypatch
      test, are verdict/return-tuple shapes recorded verbatim, is there a whole-test-tree
      patch-seam sweep, and does any cited bug number resolve to REAL code sites?
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

### Issue #1815 specific findings

Plan re-houses the legacy fused review → address → re-review loop into per-stage state machines
(implementation stage + pr-review stage) for epic #1809's queue-based in-process pipeline. #1815 sits on
the UNMERGED dependency #1814, whose `pipeline/` scaffolding (`stages/base.py` + `Stage` protocol,
`routing.py` / `ROUTES`, conftest fakes) does not exist on disk yet — verified absent (`git status`
clean; glob for `**/pipeline/**` empty; `gh issue view 1814` describes the contract it delivers). The
epic #1809 body carried the full approved plan; most anchors were exact, but two were stale.

| Symbol / claim in the plan | Status | What a reviewer must do |
|----------------------------|--------|-------------------------|
| 10 prompt-builder line numbers cited by epic #1809 | VERIFIED-against-main (all 10 confirmed exact by direct grep) | Trust as-is; these are the verified foundation the plan proceeded on |
| Epic anchor "`_finalize_pr :36`" | STALE — misleading | It refers to `_pr_create_phase.py:36`; `implementer_phase_runner.py:1111 _finalize_pr` is a thin DELEGATE (`"Delegate to :meth:`PRCreatePhase._finalize_pr`"`). Cite the file where the literal is DEFINED |
| Epic gate helper "`is_plan_review_go` at-or-past" | STALE — helper does NOT exist | `state_labels.py` has only `is_plan_go` / `is_plan_no_go` / `is_implementation_go` / `is_skipped` / `is_epic`; the real gate is the plan-review verdict check inside `_ensure_plan_ready:429` |
| Review budgets `MAX_REVIEW_ITERATIONS = 3` (`_review_phase.py:87`), `MAX_REVIEW_ITERATIONS_HARD_CAP = *2` (=6, `:95`) | VERIFIED-against-main; must move to DATA | Require a test that monkeypatches the routing-table budget and asserts the loop honors the patched value — a test still passing when the cap is hardcoded proves nothing |
| `_evaluate_go_verdict -> (verdict, go_blocked_by_automation, should_break)`, verdict ∈ {GO, NOGO, HUMAN_BLOCKED}; ERROR surfaced elsewhere | VERIFIED-against-main (read `return` lines + docstring) | Record verbatim; do NOT paraphrase the tuple or fold ERROR into it |
| `review_pr_inline -> (review_text, thread_ids)`; `validate_prior_comments_addressed -> (reopened_thread_ids, is_clean, seen/reopened_keys)` | VERIFIED-against-main | Record verbatim; the reviewer verdict lives in `review_text` prose, not a JSON `summary` field |
| "#1572 progress-aware iteration extension" | NO literal marker in code | `grep -rn "1572"` returns nothing; the behavior is `_review_thread_count_decreased:155` + the impl-review budget bump + a `>=` (not `==`) exhaustion anchor. Locate the real sites; do not cite the number as if greppable |
| `Stage` protocol / `routing.py` / `ROUTES` / conftest fakes (`FakeGitHub` / `FakeWorkerPool`) | ASSUMED-from-#1814 (scaffolding absent on disk — verified) | Plan's first step = "rebase on merged #1814 and read its landed templates"; do NOT redefine those types; fall back to the `SimpleNamespace`-based `_make_ctx` pattern (`tests/unit/automation/test_stage_phases.py:28`) if the dep did not ship the fakes |

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| ProjectHephaestus | Planning phase for issue #1360 (extract 12-function repo-management cluster from `automation/loop_runner.py` into `loop_repo_manager.py` with backward-compat re-exports) | Plan produced, NOT executed; this skill records the unverified assumptions and reviewer risks. Implementation pending. |
| ProjectHephaestus | Planning phase for issue #1814 (pipeline planning + plan-review stages, epic #1809) — re-house control flow out of `planner.py` / `planner_review_loop.py` into `pipeline/stages/planning.py` + `plan_review.py`, promote `_apply_state_label` to shared `state_labels.apply_plan_verdict` | Plan produced, NOT executed. Novel finding: the extraction builds on an UNMERGED `Depends on #1813 → #1812 → #1811` chain, so every base type (`WorkItem`, `StageOutcome`, `AgentJob`, `Stage`, `ROUTES`, test fakes) is an assumption from epic-#1809 prose until the deps merge; prompt-builder reuse + `_apply_state_label` source were verified against current main. |
| ProjectHephaestus | Planning phase for issue #1815 (implementation + pr-review stages, epic #1809) — re-house the legacy fused review → address → re-review loop into per-stage state machines, sitting on the UNMERGED dependency #1814 whose `pipeline/` scaffolding is absent on disk | Plan produced, NOT executed. Novel findings (v1.2.0): the epic #1809 body is the authoritative contract but two `file:line` anchors were STALE — `_finalize_pr :36` is really `_pr_create_phase.py:36` (the `:1111` symbol is a delegate) and `is_plan_review_go` does not exist (real gate `_ensure_plan_ready:429`); budgets (`_review_phase.py:87` / `:95`) must move to DATA with a monkeypatch test; verdict/return-tuples recorded verbatim; the "#1572" behavior has no literal marker (`_review_thread_count_decreased:155` + budget bump + `>=` exhaustion anchor); all 10 prompt-builder line refs verified exact by direct grep run in parallel with the exploration agents. |
