---
name: planning-validator-false-assurance-flatten-duplicate-guard
description: "Planning lesson for fixing a validator that gives false assurance because its parser flattens repeated entries into a dict (last-write-wins), making it structurally unable to detect duplicate/conflicting rows it is supposed to forbid. The fix must preserve ALL occurrences before the flatten, then add an explicit duplicate/conflict check. Captures the planning risks: a breaking return-type API change with un-grepped blast radius, stale plan line numbers, an unverified doc-promise claim, a verify-clean-day-one gate risk, a scope-policy assumption about exact-duplicates, and the need for a RED test that reproduces the exact false-OK. Use when: (1) planning a fix for a markdown/config/table parser that builds dict[key]=value from repeated rows and a validator over it never reports duplicates; (2) a self-contradiction guard reports OK on a self-contradictory document; (3) a plan changes a loader's return type and you must bound the caller blast radius; (4) strengthening a validator that gates CI and you must avoid a day-one merge failure."
category: tooling
date: 2026-06-12
version: "1.0.0"
user-invocable: false
verification: unverified
tags:
  - planning
  - validator
  - parser
  - last-write-wins
  - flatten
  - duplicate-detection
  - conflict-detection
  - false-assurance
  - self-contradiction-guard
  - breaking-api-change
  - doc-drift
  - red-test
  - planning-risk
---

# Planning a Fix for a Validator That Cannot See Its Own Contradiction

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-06-12 |
| **Objective** | Capture the durable PLANNING lesson from an implementation-plan for ProjectHephaestus issue #1213: a validator reported OK on a self-contradictory doc because its parser flattened repeated rows into `dict[key]=value` (last-write-wins), so the duplicate/conflict it was meant to catch was erased before any check ran. |
| **Outcome** | Plan written, not yet implemented. The durable value is the failure-class diagnosis plus a checklist of the plan's riskiest unverified assumptions a reviewer must check. |
| **Verification** | unverified — the plan was never executed end-to-end; treat every step as a hypothesis. |
| **Source issue** | ProjectHephaestus #1213 (`hephaestus/validation/cli_tier_docs.py`) |

### The failure class: "self-contradiction guard that can't see its own contradiction"

A validator is supposed to forbid duplicate or conflicting entries in a document.
But the parser it relies on builds a flat `dict[key] = value` from repeated rows.
When a key appears twice, the second write silently clobbers the first
(**last-write-wins**), so by the time the validator runs, the contradiction has
already been collapsed into a single consistent-looking entry. The validator then
checks only set-membership and value-validity — never "did this key appear more
than once?" — and reports OK on a document that openly contradicts itself.

**The structural fix is ordering, not logic:** you cannot bolt a duplicate check
onto the flattened dict, because the duplicates are gone. You must **preserve all
occurrences BEFORE the flatten** (parse into `dict[key, list[value]]` or a list of
`(key, value)` pairs), then add an explicit duplicate/conflict pass over the
preserved occurrences.

### The concrete instance (issue #1213)

- `load_documented_tiers` parsed every `## Console-Script Stability Tiers` table
  row into `tiers[cli] = tier`, so a CLI documented twice collapsed last-write-wins.
- `find_violations` checked only set-membership + valid-tier-value — never
  duplicate/conflicting keys — so it reported OK on a self-contradictory
  COMPATIBILITY.md.
- **Planned fix:** parse into `dict[cli, list[tier]]` (preserve occurrences); add
  `find_duplicate_tiers()` emitting `conflicting-tier` (distinct values for one key)
  vs `duplicate-tier` (same value repeated); thread results through a new optional
  3rd param `duplicates=None` on `find_violations` so existing 2-arg callers keep
  working; change `load_documented_tiers` to return a tuple `(tiers, occurrences)`.

## When to Use

Reach for this skill when **planning** (not yet implementing) a fix and any of these hold:

- A markdown/config/table parser builds `dict[key] = value` from repeated rows, and a
  validator over the result never reports duplicate or conflicting keys.
- A "self-contradiction guard" reports OK on a document that visibly contradicts itself
  (the same key mapped to two different values, or a value the doc says is forbidden).
- The plan changes a loader/parser's **return type** (e.g., `dict` -> `tuple[dict, dict]`)
  and you must bound the caller blast radius before trusting the change is safe.
- You are **strengthening a validator that gates CI** and need to avoid a day-one merge
  failure if the live artifact already contains a newly-detected violation.

### The six planning risks a reviewer MUST check (the heart of this skill)

These are the riskiest unverified assumptions baked into a plan of this shape. They are
where reviews of these plans should spend their attention.

1. **Return-type change is a breaking API change with unknown blast radius.**
   Changing `load_documented_tiers` from `dict` to `tuple[dict, dict]` breaks every
   caller that does a bare assignment or unpack. The plan only grepped the *test* file
   for callers (`grep -n "find_violations(" tests/...`) plus the module's own `main`.
   It did **not** grep the whole repo for external callers of `load_documented_tiers`
   (pre-commit hooks, other validation modules, `scripts/`). **A reviewer must run
   `grep -rn "load_documented_tiers" hephaestus/ scripts/ tests/`** before trusting the
   tuple-unpack is safe. This is the single biggest unverified assumption.

2. **Line numbers cited in the plan may be stale.** The plan cites exact lines
   (71-94, 120-146, 42-45, 171-176) read at plan time. Implementation must re-read the
   file; never trust line numbers carried over from a plan.

3. **The doc-promise claim was read once, not re-verified.** The objective leans on
   `COMPATIBILITY.md:104-107` "advertising it prevents drift." That wording was read
   once and not re-checked against the exact text. A reviewer should confirm the doc
   actually makes that promise before justifying the fix by it.

4. **Verify-clean-day-one is a real gate risk.** Strengthening a validator can make a
   previously-green CI gate fail the moment it merges, if the live doc already contains a
   (newly-detected) duplicate. The plan added a step to run `main` against the real
   COMPATIBILITY.md first — but **that step was never actually run during planning**; it
   is an *assumption* that the live doc is clean today. The implementer MUST execute the
   strengthened check against the live artifact before turning it on.

5. **Scope-policy assumption: is an exact-duplicate (same value twice) actually a
   violation?** The plan decided BOTH same-value duplication (`duplicate-tier`) and
   different-value conflict (`conflicting-tier`) are violations, justified by "the doc
   forbids duplication." The second half — flagging harmless exact-duplicates — is an
   *interpretation*, not something the issue explicitly required; the issue only names
   the *conflicting* case. A reviewer should confirm flagging exact-duplicates is
   desired, or it could break a legitimately-duplicated-but-consistent row.

6. **General pattern for "guard gives false assurance" issues:** the plan's verification
   section MUST include a RED test that reproduces the *exact* false-OK the issue
   describes — here, `test_find_violations_surfaces_duplicates_when_aligned`: the
   contradiction is reported even when scripts/tiers otherwise align. Without that test,
   the fix can pass narrower unit tests yet still leave the reported hole open.

## Verified Workflow

> **Warning:** This workflow was NEVER validated end-to-end. It is the proposed plan for
> issue #1213, not an executed-and-confirmed procedure. Treat every step as a hypothesis
> until CI confirms it. (Section header kept as "Verified Workflow" only to satisfy the
> skill validator; verification status is `unverified`.)

### Quick Reference

```bash
# RISK 1 — bound the blast radius BEFORE changing a loader's return type.
# Do NOT grep only the test file; grep the whole repo for the changed function.
grep -rn "load_documented_tiers" hephaestus/ scripts/ tests/

# RISK 4 — before turning a strengthened CI-gating validator on, run it against the
# LIVE artifact to confirm it is clean TODAY (avoid a day-one merge failure).
python3 -m hephaestus.validation.cli_tier_docs   # or the module's `main` entry point
```

### Detailed Steps (proposed)

1. **Diagnose the ordering bug, not the check logic.** Confirm the parser flattens
   repeated rows into `dict[key]=value` and that the validator runs *after* the flatten.
   The duplicates are erased before any check; no amount of extra checking on the dict
   recovers them.
2. **Preserve occurrences before the flatten.** Parse into `dict[key, list[value]]`
   (or a list of `(key, value)` pairs). Keep the flattened `dict` too if existing logic
   needs it — return both, e.g. `(tiers, occurrences)`.
3. **Add an explicit duplicate/conflict pass** over the preserved occurrences. Emit
   distinct codes: `conflicting-<thing>` when a key maps to >1 distinct value;
   `duplicate-<thing>` when the same value repeats. (See RISK 5 before deciding the
   latter is a violation.)
4. **Thread results without breaking callers.** Add the new data as an *optional*
   parameter with a safe default (`duplicates=None`) so existing 2-arg callers keep
   working without edits.
5. **Bound the return-type blast radius (RISK 1).** Run
   `grep -rn "<loader_fn>" hephaestus/ scripts/ tests/`; update every caller that
   assumes the old return type. Do not rely on a test-file-only grep.
6. **Re-read the file at implementation time (RISK 2).** Discard plan line numbers.
7. **Re-verify the doc-promise claim (RISK 3).** Confirm the doc actually advertises the
   guarantee the fix is justified by.
8. **Write the RED test first (RISK 6).** Reproduce the exact false-OK: a
   self-contradictory document for which the *old* validator returned clean. The test
   must fail before the fix and pass after.
9. **Run the strengthened validator against the live artifact (RISK 4)** before enabling
   the stricter gate, to confirm the live doc is clean day-one.
10. **Confirm scope policy (RISK 5)** with the issue/owner: is an exact-duplicate row a
    violation, or only a conflicting one?

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Bolt a duplicate check onto the flattened dict | Add a "are there duplicates?" check after `dict[key]=value` was built | The duplicates were already erased by last-write-wins; nothing left to detect | Fix the ORDERING — preserve all occurrences BEFORE the flatten; a check downstream of the flatten is structurally blind |
| Grep only the test file for callers of the changed-return-type function | `grep -n "find_violations(" tests/...` plus the module's own `main` | Missed potential external callers (pre-commit hooks, other validation modules, `scripts/`) of `load_documented_tiers`, whose return type changed | Always grep the WHOLE repo for any function whose signature/return type changes: `grep -rn "<fn>" hephaestus/ scripts/ tests/` |
| Trust the line numbers cited in the plan | Plan referenced lines 71-94, 120-146, 42-45, 171-176 | Plans go stale; the file shifts before implementation | Re-read the file at implementation time; never act on plan-time line numbers |
| Justify the fix by a doc promise read once | Relied on "COMPATIBILITY.md:104-107 advertises it prevents drift" | The exact wording was never re-verified | Re-read and confirm the doc actually makes the promise the fix leans on |
| Assume the live doc is clean for the strengthened gate | Planned a step to run `main` against the real doc but never ran it | Strengthening a validator can fail CI the day it merges if the live artifact already violates the new rule | Run the strengthened check against the LIVE artifact before turning the gate on |
| Decide exact-duplicates are violations without confirming scope | Flagged both `duplicate-tier` (same value twice) and `conflicting-tier` | The issue only named the *conflicting* case; forbidding harmless exact-duplicates is an interpretation that could break legitimate rows | Confirm scope with the issue/owner before flagging exact-duplicates |
| Verify the fix only with narrow unit tests | Tested duplicate detection in isolation | Could pass without reproducing the *reported* false-OK (contradiction reported even when keys otherwise align) | Add a RED test that reproduces the exact false-OK the issue describes, then make it pass |

## Results & Parameters

**Status:** plan only, unverified. No code was changed; no tests were run.

**Failure-class signature to recognize in future plans:**

- Parser: `out[key] = value` inside a loop over repeated rows -> last-write-wins.
- Validator: checks membership / value-validity, never "appeared more than once".
- Symptom: validator returns clean on a document that maps one key to two values.

**Reviewer checklist (paste into a plan review of this shape):**

```text
[ ] R1 Blast radius: grep -rn "<loader_fn>" hephaestus/ scripts/ tests/  (NOT test-only)
[ ] R2 Line numbers re-read at implementation time, not trusted from the plan
[ ] R3 Doc-promise wording re-verified against the actual file
[ ] R4 Strengthened validator run against the LIVE artifact (clean day-one?)
[ ] R5 Scope: is an exact-duplicate (same value twice) actually a violation?
[ ] R6 RED test reproduces the EXACT false-OK from the issue (not just a narrow unit)
```

**Proposed code shape (issue #1213, unverified):**

```python
# Preserve occurrences BEFORE flattening (the structural fix).
# load_documented_tiers returns (tiers, occurrences):
#   tiers:       dict[str, str]          # flattened, last-write-wins (kept for back-compat)
#   occurrences: dict[str, list[str]]    # every value seen per key (enables duplicate check)

def find_duplicate_tiers(occurrences: dict[str, list[str]]) -> list[Violation]:
    out: list[Violation] = []
    for cli, tiers in occurrences.items():
        if len(tiers) < 2:
            continue
        if len(set(tiers)) > 1:
            out.append(Violation("conflicting-tier", cli, tiers))   # distinct values
        else:
            out.append(Violation("duplicate-tier", cli, tiers))     # RISK 5: confirm scope
    return out

# Thread via an OPTIONAL param so existing 2-arg callers keep working unchanged.
def find_violations(documented, expected, duplicates=None): ...
```
