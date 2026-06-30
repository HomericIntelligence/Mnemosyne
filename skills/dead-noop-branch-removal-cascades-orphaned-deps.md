---
name: dead-noop-branch-removal-cascades-orphaned-deps
description: "Plan the removal of a provably-dead no-op branch (an `elif <cond>: pass` that recognises a pattern then does nothing while control always falls through to an independent arm) and follow the orphan cascade: deleting the branch orphans the sole-use module-level constant it referenced (e.g. a compiled-regex `CVSS_PATTERN`), and deleting that constant orphans the import that defined it (`import re`). All three must be removed in the SAME change or ruff F401 (unused import) / F841 (unused local) fails. Use when: (1) an audit flags a `bare pass` / no-op `elif` branch and offers 'comment OR remove'; (2) the branch references a module-level constant or import used nowhere else; (3) you must prove the cascade terminates cleanly before planning (grep the symbol repo-wide AND grep `\\bre\\.` in-file); (4) a passing existing test already encodes the fall-through as a tested contract; (5) you are tempted to add a clarifying comment, remove only the branch, or add a test for removed dead code."
category: architecture
date: 2026-06-30
version: "1.0.0"
user-invocable: false
verification: unverified
tags: []
---

# Dead No-Op Branch Removal Cascades to Orphaned Deps

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-06-30 |
| **Objective** | Plan the clean removal of a provably-dead `elif <cond>: pass` branch and the orphan cascade it triggers (sole-use constant → its defining import) without leaving a lint failure or a half-fix |
| **Context** | ProjectHephaestus issue #1466 — `[audit][S4] validation/audit.py:78 bare pass in CVSS elif branch` |
| **Outcome** | PLAN ONLY — decided REMOVE (not comment); identified the 3-symbol cascade (branch → `CVSS_PATTERN` → `import re`); proved single-use by grep; confirmed the existing test is the regression guard |
| **Language** | Python (ruff F401/F841 lint semantics) |
| **Build required** | No code was executed — plan only |
| **Verification** | unverified (no pytest / ruff / mypy / CI run this session) |

> **Warning:** This workflow has not been validated end-to-end. Treat as a hypothesis until CI confirms.

## When to Use

- An audit flags a `bare pass` inside an `elif` branch that recognises a condition (e.g. `elif isinstance(score_str, str) and CVSS_PATTERN.match(score_str): pass`) but does nothing — control always falls through to an independent arm, so the branch cannot mutate the accumulator and is provably dead.
- The audit offers "add a clarifying comment OR remove the branch" and you must decide.
- The dead branch is the **sole** consumer of a module-level constant (a compiled regex, a lookup table) which is itself the sole consumer of a top-level import.
- A passing existing test already asserts the fall-through behaviour (the contract the dead branch was supposed to — but does not — affect).
- You want to avoid the half-fix that leaves a ruff F401 (unused import) / F841 (unused local) failure, or that wrongly deletes a still-used import.

## Verified Workflow

> **Note:** Despite the validator-required `## Verified Workflow` heading, this is a **Proposed Workflow** — it is `unverified` (plan only, no CI). Treat every claim below as a hypothesis until CI confirms.

### Quick Reference

```bash
# 1. PROVE the constant is single-use (def + the one use you are removing) repo-wide.
#    Expect: only the target file, at the def line and the dead-branch use.
grep -rn "CVSS_PATTERN" hephaestus/ tests/

# 2. PROVE the import is single-use WITHIN the file that defines the constant.
#    Expect: only the def line `CVSS_PATTERN = re.compile(...)` references `re.`.
grep -n '\bre\.' hephaestus/validation/audit.py

# 3. Run the EXISTING test UNCHANGED — it is the regression guard. It must stay green.
pixi run pytest tests/unit/validation/test_audit.py -k test_no_score_returns_none -q

# 4. Lint must be clean AFTER removing all 3 symbols together (catches a half-fix).
pixi run ruff check hephaestus/validation/audit.py
```

### Detailed Steps

#### Step 1 — Confirm the branch is provably dead

The branch matches a pattern then does nothing. Because the bare `pass` cannot mutate the accumulator (`scores`), and control always continues to an independent numeric-lookup arm, the branch's only observable effect is **none**. It is dead — removing it cannot change behaviour.

#### Step 2 — Decide REMOVE, not COMMENT (KISS/DRY)

The audit's "comment OR remove" is not a coin flip. A comment **documents why dead code exists**; removal **eliminates it**. When the branch is provably a no-op, removal is strictly better — there is no behaviour to preserve and nothing for a comment to usefully explain.

#### Step 3 — Map the orphan cascade BEFORE editing

Removing the only use of a sole-use symbol orphans it:

```text
delete  elif ... CVSS_PATTERN.match(...): pass   (the dead branch)
  └─ orphans  CVSS_PATTERN = re.compile(...)      (module-level constant — now unused)
       └─ orphans  import re                      (now unused)
```

All three must be removed in the **same change**. Leaving the constant → ruff F841 (assigned-but-unused) is actually module-level so it surfaces as a dead definition; leaving `import re` → ruff F401 (imported-but-unused). A half-fix fails lint.

#### Step 4 — Prove the cascade terminates cleanly (the planning step that prevents a half-fix)

```bash
grep -rn "CVSS_PATTERN" hephaestus/ tests/   # only audit.py: def + the dead use
grep -n '\bre\.' hephaestus/validation/audit.py   # only the `re.compile` def line
```

If `CVSS_PATTERN` appears anywhere else, you may NOT remove it. If `re.` is used elsewhere in the file, you may NOT remove `import re`. The grep is what distinguishes "safe full cascade" from "wrongly deleting a still-used import."

#### Step 5 — Treat the existing test as the regression guard (do not touch it)

`tests/unit/validation/test_audit.py::test_no_score_returns_none` asserts a pure CVSS-vector entry returns `None`. After removal the same input still hits neither numeric arm → still `None`. The test must pass **unchanged**. Removing dead code should never require a test change — if it does, the branch was not actually dead.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| ------- | -------------- | ------------- | -------------- |
| Comment instead of remove | Add a clarifying comment explaining the no-op branch rather than deleting it | Leaves dead code in place and merely documents why a no-op exists | Prefer removal when the branch is provably a no-op — KISS: eliminate dead code, don't annotate it |
| Remove only the branch | Delete the `elif` branch but leave `CVSS_PATTERN` and `import re` | Orphaned constant + unused import → ruff F401/F841 failure | Removing a sole-use symbol must cascade to its dependents in the SAME change |
| Assume the cascade terminates | Plan the cascade removal without grepping the symbols first | Could leave a lint failure (a missed consumer) OR wrongly delete a still-used import | Grep the constant repo-wide AND grep `\bre\.` in-file BEFORE planning to prove single-use |
| Add/change a test for the removed branch | Author a new test (or edit one) "to cover" the deleted branch | The fall-through is already a tested contract (`test_no_score_returns_none`); the branch had no effect to cover | Removing dead code needs no test change — if it does, the branch was not actually dead |

## Results & Parameters

**Verification status: `unverified`.** No pytest, ruff, mypy, or CI was run this session — the entire analysis is a reasoned implementation plan for ProjectHephaestus issue #1466.

### Cascade-proving greps (copy-paste)

```bash
# Constant is single-use across the whole repo (def + the one dead use):
grep -rn "CVSS_PATTERN" hephaestus/ tests/

# Import is single-use within the defining file (only the `re.compile` def line):
grep -n '\bre\.' hephaestus/validation/audit.py
```

### Before / after loop-body diff

```diff
-import re
-
-CVSS_PATTERN = re.compile(r"CVSS:3\.[01]/...")   # module-level constant (line ~28)
-
 def extract_cvss_score(...):
     ...
     for score_str in candidates:
         if <numeric arm A>:
             scores.append(...)
-        elif isinstance(score_str, str) and CVSS_PATTERN.match(score_str):
-            pass                                  # dead no-op (line ~78) — recognises, does nothing
         elif <numeric arm B>:
             scores.append(...)
     return min(scores) if scores else None
```

After removal, a pure CVSS-vector input still matches neither numeric arm and falls through to `return None` — identical to before. `test_no_score_returns_none` stays green unchanged.

### Most uncertain assumptions / risks for the reviewer (honest)

1. **UNVERIFIED — plan only.** No pytest/ruff/mypy was run. The "F401/F841 would fire if you leave the orphans" claim is reasoned from ruff defaults, **not** observed against this repo's exact ruff config.
2. **Grep not exhaustive for dynamic refs.** The single-use proof scoped `\bre\.` to `audit.py` and `CVSS_PATTERN` repo-wide (files-with-matches); it did **not** rule out a dynamic / `getattr` / string reference to `re` or `CVSS_PATTERN` elsewhere (low risk, unverified).
3. **Blank-line reflow when deleting the constant.** Removing the `CVSS_PATTERN` constant (line ~28) must not leave a double-blank that `ruff format` would re-flow. The plan asserts the surrounding blanks are correct but this was **not** run through `ruff format`.

## Verified On

- **Verification level:** `unverified` — plan only, no execution.
- **Source:** ProjectHephaestus issue #1466 (`[audit][S4] validation/audit.py:78 bare pass in CVSS elif branch`), planning session 2026-06-30.
- **Not run:** pytest, ruff check, ruff format, mypy, CI.
- **Regression guard (would-be):** `tests/unit/validation/test_audit.py::test_no_score_returns_none` — asserted to pass unchanged, but not executed this session.
