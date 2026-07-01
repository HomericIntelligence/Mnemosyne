---
name: documentation-vague-convention-anchor-and-presence-guard
description: "Plan the right-sized fix for an audit finding that flags a VAGUE PROSE CONVENTION (a hand-wavy cadence/threshold/frequency such as 'reviewed... typically monthly' with no defined trigger, driver, or owner) as a modularity / predictability / POLA finding. The doc-prose sibling of architecture-executable-convention-guard-pattern: there the guarded invariant is an EXECUTABLE code contract; here it is PHRASE-MEMBERSHIP in a doc. The three-part fix: (1) ANCHOR the vague value to an EXISTING concrete mechanism already documented in the repo (e.g. tie a review cadence to the existing `Auto Tag Release` workflow) instead of inventing a brand-new process; (2) make the prose EXPLICIT about TRIGGER + DRIVER + OWNER (feature/fix-driven NOT date-driven; 'the maintainer cutting the release'); (3) add a doc-CONTENT presence guard that asserts ONLY the HARD invariant — required phrases present, vague phrasing absent — and NEVER the inferred value itself (never assert a 'monthly' rhythm). Reuse the repo's existing doc-guard test pattern (e.g. tests/unit/docs/test_version_currency.py) and ride the already-wired `pytest tests/unit` gate — do NOT add a new CI workflow. Use when: (1) an audit/NITPICK cites a doc line with a fuzzy cadence/frequency and no trigger/driver/owner; (2) you are tempted to invent a new scheduled process — anchor to an existing mechanism instead; (3) you are tempted to assert the inferred cadence value in a test — assert only phrase presence/absence; (4) you are adding a doc-content regression test and want to copy a sibling tests/unit/docs guard rather than wire new CI; (5) you must decide between an executable convention guard and a doc-prose presence guard — pick this one when the value is INFERRED/unverifiable and only phrase-membership is a hard invariant."
category: documentation
date: 2026-07-01
version: "1.0.0"
user-invocable: false
verification: unverified
tags:
  - planning
  - documentation
  - audit-remediation
  - vague-convention
  - prose-cadence
  - anchor-to-existing-mechanism
  - trigger-driver-owner
  - doc-content-presence-guard
  - phrase-membership-invariant
  - never-assert-inferred-value
  - reuse-existing-test-gate
  - no-new-ci-workflow
  - roadmap
  - release-driven-cadence
  - modularity-finding
  - pola
---

# Documentation Vague-Convention: Anchor to an Existing Mechanism + Doc-Content Presence Guard

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-07-01 |
| **Objective** | Plan the right-sized fix for ProjectHephaestus issue #1493 — an audit flagged `docs/ROADMAP.md:53` ("reviewed and updated at the end of each release cycle (typically monthly)") as a vague cadence with no defined trigger, driver, or owner (an S10 Planning / modularity / predictability finding). |
| **Outcome** | A documentation-only plan: rewrite the "Updating This Roadmap" prose to define cadence as RELEASE-DRIVEN (anchored to the existing `Auto Tag Release` workflow), FEATURE/FIX-DRIVEN NOT DATE-DRIVEN, owned by "the maintainer cutting the release"; add `tests/unit/docs/test_roadmap_cadence.py` asserting required phrases present + "typically monthly" absent; reuse the wired `pytest tests/unit` gate — no new CI. |
| **Verification** | unverified — this is a PLAN. No prose was applied, no test was written or run, no linter/CI was executed. |
| **History** | (none — initial version) |

## When to Use

- An audit / NITPICK / repo review cites a documentation line containing a **fuzzy cadence, frequency, or threshold** ("typically monthly", "periodically", "as needed", "roughly quarterly") with **no defined trigger, driver, or owner**, and files it as a modularity / predictability / POLA finding.
- You are tempted to **invent a brand-new scheduled process** to fix the vagueness — stop and anchor the value to an **existing mechanism already documented in the repo** instead.
- You are tempted to **assert the inferred cadence value in a test** (e.g. "the doc must say monthly") — assert only the **hard invariant** (required phrases present, vague phrasing absent), never the unverifiable rhythm.
- You are adding a **doc-content regression test** and want to copy a sibling `tests/unit/docs/` guard and ride the already-wired `pytest tests/unit` gate rather than wiring a new CI workflow.
- You must choose between an **executable convention guard** (see `architecture-executable-convention-guard-pattern`) and this **doc-prose presence guard** — pick this one when the flagged value is an **inferred / unverifiable** quantity and only **phrase-membership** is a hard, assertable invariant.

## Proposed Workflow

> **Warning:** This workflow has not been validated end-to-end. Treat as a hypothesis until CI confirms.

### Quick Reference

```bash
# 1. Locate the vague prose by STABLE CONTENT SUBSTRING, not by the audit's (possibly drifted) line number.
grep -n "typically monthly" docs/ROADMAP.md

# 2. Find the EXISTING mechanism to anchor to (do NOT invent a new process).
#    Here: the release workflow the repo already documents.
grep -rn "Auto Tag Release" docs/RELEASING.md .github/workflows/

# 3. CRITICAL — verify the anchor's real trigger BEFORE writing "not date-driven".
#    Reading the prose is NOT enough. Open the workflow file and confirm no schedule/cron.
grep -nE "schedule:|cron:" .github/workflows/auto-tag.yml || echo "no cron -> feature/fix-driven OK"

# 4. Copy the SIBLING doc-guard test pattern; do NOT wire a new CI job.
ls tests/unit/docs/                       # e.g. test_version_currency.py, test_pi_private_provider_docs.py
# The new test rides the already-wired gate:
pixi run pytest tests/unit/docs/test_roadmap_cadence.py
```

```python
# tests/unit/docs/test_roadmap_cadence.py  (doc-CONTENT presence guard — asserts ONLY the hard invariant)
from pathlib import Path

# parents[3] resolves to repo root for a file at tests/unit/docs/<file>.py
# (mirror the sibling guard's depth; CONFIRM independently — see Failed Attempts).
ROADMAP = Path(__file__).resolve().parents[3] / "docs" / "ROADMAP.md"


def test_roadmap_cadence_is_release_driven_not_date_driven() -> None:
    text = ROADMAP.read_text(encoding="utf-8").lower()
    # HARD invariant: required trigger + driver + owner phrases present.
    assert "auto tag release" in text        # anchored to the EXISTING mechanism
    assert "not date-driven" in text         # explicit driver
    assert "maintainer" in text              # named owner
    # HARD invariant: the vague phrasing is gone.
    assert "typically monthly" not in text
    # DO NOT assert an inferred cadence value (e.g. a "monthly" rhythm) — it is unverifiable.
```

### Detailed Steps

1. **Re-locate the vague prose on disk by content substring.** Audit `file:line` coordinates drift; `grep -n "typically monthly" docs/ROADMAP.md` before quoting or editing. (Overlaps `audit-doc-consistency-fix-verify-coordinates-on-disk`.)

2. **Find an EXISTING mechanism to anchor to — do NOT invent a new process.** The vagueness is fixed by tying the value to something concrete the repo already documents. Here: the `Auto Tag Release` workflow in `docs/RELEASING.md`. Anchoring beats inventing because a new scheduled process would itself be un-owned and un-enforced — you would recreate the finding one level up.

3. **VERIFY the anchor's real behavior before asserting a property of it.** This is the load-bearing risk. Do not write "not date-driven" from the anchor's *prose* alone — open `.github/workflows/auto-tag.yml` and confirm it has no `schedule:`/`cron:` trigger. If the workflow IS cron-scheduled, "not date-driven" is factually wrong and the whole framing collapses.

4. **Rewrite the prose to be explicit about TRIGGER + DRIVER + OWNER.** Trigger: a release is cut. Driver: features/fixes landing (NOT the calendar). Owner: "the maintainer cutting the release." Describe how to propose changes. Bump the doc's `Last updated:` line.

5. **Add a doc-CONTENT presence guard that asserts ONLY the hard invariant.** Required phrases present (`auto tag release`, `not date-driven`, `maintainer`) and vague phrasing absent (`typically monthly`). NEVER assert the inferred cadence value itself — a "monthly" rhythm is unverifiable and would be a fabricated assertion.

6. **Reuse the repo's existing doc-guard pattern and ride the wired test gate.** Copy the structure of a sibling `tests/unit/docs/` test (`test_version_currency.py`, `test_pi_private_provider_docs.py`); it runs under the already-wired `pixi run pytest tests/unit`. Do NOT add a new CI workflow for a one-invariant doc guard (disproportionate; see `audit-doc-consistency-fix-verify-coordinates-on-disk` §4).

7. **Explicitly REJECT an executable "cadence" guard.** Release frequency is inferred/unverifiable, so there is no executable value to assert. Only phrase-membership is a hard invariant — that is the whole reason this is the doc-prose sibling of, not the same as, `architecture-executable-convention-guard-pattern`.

## Verified Workflow

_Not applicable._ This skill was captured from a planning session and is `unverified`: no prose edit was applied, no test was written or executed, and no linter/CI ran, so there is no verified workflow. The actionable, hypothesis-level methodology lives under **Proposed Workflow** above and must be treated as unvalidated until CI confirms it. (This placeholder section exists only because `scripts/validate_plugins.py` requires the literal `## Verified Workflow` heading; it makes no verification claim.)

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Invent a new scheduled process | Fix "typically monthly" by defining a brand-new formal review cadence/process from scratch | A newly-invented process is itself un-owned and un-enforced — it recreates the same modularity finding one level up; and it is more change than the finding warrants (KISS/YAGNI) | Anchor the vague value to an EXISTING documented mechanism instead of inventing a new one |
| Assert the inferred cadence value | Write a test asserting the doc states a "monthly" (or any specific) rhythm | Release frequency is inferred and unverifiable; asserting it fabricates a value the repo cannot guarantee, making the guard both wrong and brittle | Assert ONLY the hard invariant — required phrases present / vague phrasing absent — never the inferred value |
| Build an executable cadence guard | Reach for `architecture-executable-convention-guard-pattern` and write a `scripts/check_*.py` enforcing cadence | There is no executable, verifiable value to enforce here — only phrase-membership in a doc is a hard invariant; an executable guard would have nothing sound to check | This is the DOC-PROSE sibling: the guarded invariant is phrase-membership, so use a `tests/unit/docs/` presence test, not an executable CLI guard |
| Add a new CI workflow for the guard | Wire a dedicated CI job/workflow to run the new doc-content test | Disproportionate for a single-invariant doc guard; the repo already has a wired `pytest tests/unit` gate that picks up `tests/unit/docs/*` automatically | Ride the already-wired test gate; reserve new CI workflows for genuinely new enforcement surfaces |
| Assert "not date-driven" from prose only | Read `docs/RELEASING.md` (which says "the only manual step") and conclude the anchor workflow is feature-driven | The prose was never cross-checked against `.github/workflows/auto-tag.yml`; if that workflow has a `schedule:`/`cron:` trigger, "not date-driven" is factually wrong | Verify the anchor's REAL trigger in the workflow file itself before asserting a property of it (UNVERIFIED in the source session — see risks) |
| Edit ROADMAP.md prose without checking markdownlint | Plan multi-paragraph bold-lead-in formatting in the rewritten section | The linter was never run against the new formatting; markdownlint may reject the bold-lead-in / multi-paragraph structure | Run the repo's markdown linter against the edited doc before claiming the fix is complete |

## Results & Parameters

Concrete instantiation used in the source planning session (ProjectHephaestus issue #1493):

- **Target doc / line:** `docs/ROADMAP.md:53` — "reviewed and updated at the end of each release cycle (typically monthly)".
- **Existing mechanism anchored to:** the `Auto Tag Release` workflow, documented in `docs/RELEASING.md` (workflow file: `.github/workflows/auto-tag.yml`).
- **New prose framing:** RELEASE-DRIVEN; FEATURE/FIX-DRIVEN, **not date-driven**; owner = "the maintainer cutting the release"; plus how to propose changes; bump `Last updated:`.
- **Regression guard:** `tests/unit/docs/test_roadmap_cadence.py` — required substrings present (`auto tag release`, `not date-driven`, `maintainer`), vague substring absent (`typically monthly`). Rides `pixi run pytest tests/unit`. No new CI job.
- **Sibling patterns copied:** `tests/unit/docs/test_version_currency.py`, `tests/unit/docs/test_pi_private_provider_docs.py` (repo-root resolution via `Path(__file__).resolve().parents[3]`).

**Unverified assumptions / risks (from the source session — a reviewer MUST check these):**

1. **UNVERIFIED:** that `Auto Tag Release` is genuinely manual / feature-driven. The plan read `docs/RELEASING.md` prose ("the only manual step") but did NOT open `.github/workflows/auto-tag.yml` to confirm the absence of a `schedule:`/cron trigger. If it IS cron-scheduled, "not date-driven" is factually wrong.
2. **UNVERIFIED:** that markdownlint accepts the new multi-paragraph bold-lead-in formatting in `ROADMAP.md` — the linter was never run.
3. **ASSUMPTION:** `parents[3]` resolves to repo root for a file at `tests/unit/docs/`. It matches the sibling `test_version_currency.py`, but was NOT independently confirmed for this path depth.
4. **BRITTLENESS:** the required-phrase set is coupled to the exact prose wording; if the prose is reworded during review, the substring asserts can break. Keep phrase set minimal and re-check after any wording change.

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| ProjectHephaestus | Planning-only session for issue #1493 ([audit][S10 Planning] vague iteration cadence). No code applied; no CI run. | Related skills: `architecture-executable-convention-guard-pattern` (executable sibling), `audit-stale-version-comment-version-agnostic-fix` (don't embed a fabricated specific value), `audit-doc-consistency-fix-verify-coordinates-on-disk` (re-locate coordinates; avoid disproportionate drift-guard CI). |
