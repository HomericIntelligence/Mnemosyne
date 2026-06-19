---
name: ci-cd-load-bearing-filename-nitpick-document-dont-rename
description: "Use when: (1) an audit/lint/review NITPICK proposes renaming a file or symbol 'for discoverability/clarity' — first check whether the name is a load-bearing CROSS-REPO convention before planning the rename, (2) the candidate name is wired into branch-protection rulesets, CI status-check contexts, runbooks, canonical-checks docs, or sibling/fleet repos — the right fix is to make the name self-documenting (header comment + rationale at the source-of-truth doc), NOT to rename, (3) you must SCOPE the blast radius of a rename and need to distinguish a FILENAME change (cosmetic: breaks docs/runbook references + fleet uniformity) from a JOB-NAME change (load-bearing: breaks ruleset status-check contexts, which key off the BARE JOB NAME, not the workflow filename), (4) you are about to claim N files are 'identical across the fleet' from a single-line grep match — matching a workflow NAME or a header line is NOT byte-identity; the convention is the job-name CONTRACT, not literal file equality. Headline: a discoverability rename against a cross-repo convention has disproportionate blast radius and can deadlock ruleset rollout — DOCUMENT the rationale instead of renaming."
category: ci-cd
date: 2026-06-19
version: "1.0.0"
user-invocable: false
verification: unverified
tags:
  - ci-cd
  - planning-quality
  - audit-nitpick
  - discoverability-rename
  - load-bearing-convention
  - cross-repo-convention
  - branch-protection
  - required-status-checks
  - ruleset-context
  - bare-job-name
  - blast-radius-scoping
  - filename-vs-job-name
  - document-dont-rename
  - self-documenting-name
  - fleet-uniformity
  - grep-identity-fallacy
---

# CI/CD: Load-Bearing Filename NITPICK — Document, Don't Rename

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-06-19 |
| **Objective** | Resolve a "rename `.github/workflows/_required.yml` for discoverability" NITPICK (issue #215, sole open child of Epic #174) in the Odysseus meta-repo, where `_required.yml` is a deliberate org-wide convention shared across ~15 repos |
| **Outcome** | Plan WRITTEN but NOT executed/merged. Recommendation: DOCUMENT the rationale (in-file header comment + source-of-truth canonical-checks doc) rather than rename. The plan itself contained an overstatement of blast radius that this skill records as the key lesson. |
| **Verification** | `unverified` — planning learning; plan never executed, and self-review (assumption #2) found the plan overstated the rename's impact on ruleset contexts |
| **History** | n/a (initial version) |

## When to Use

- An **audit/lint/review NITPICK** says "rename file X / symbol Y **for discoverability** (or clarity)" and X/Y looks arbitrary — STOP and check whether the name is a load-bearing convention before you plan the rename.
- The candidate name appears in **branch-protection rulesets, CI status-check contexts, runbooks, canonical-checks docs, or sibling/fleet repos**. If so, prefer making the name self-documenting (header comment + rationale doc) over renaming.
- You need to **scope the blast radius** of a rename and must separate FILENAME impact (cosmetic) from JOB-NAME impact (load-bearing) — they are NOT the same in GitHub Actions branch protection.
- You are about to assert "these N files are identical across the fleet" from a **single grep line match** (workflow `name:`, a header line) — that is a NAME/CONTRACT match, not byte identity.
- You see a "low-effort cleanup" framed nitpick that, if executed, would touch many repos and could **deadlock a ruleset rollout**.

## Verified Workflow

> **Warning (Proposed Workflow):** This workflow has not been validated end-to-end. Treat as a hypothesis until CI confirms. Verification level: `unverified` — this is a planning learning. The plan was written but never executed or merged, AND a self-review found the plan itself overstated the rename's blast radius (see Failed Attempt #2 — the filename-vs-job-name distinction is the key correction). Reason the recommendation, do not trust it blindly.

### Quick Reference

```bash
# === DECISION RULE for a "rename X for discoverability" NITPICK ===
# 1. Is the name a load-bearing CROSS-REPO convention? Check ALL of these:

ORG=HomericIntelligence; REPO=Odysseus
NAME="_required.yml"   # the file the nitpick wants to rename

# (a) Is it referenced by branch-protection RULESETS / required status-check contexts?
#     NOTE: ruleset contexts key off the BARE JOB NAME (e.g. `lint`), NOT the filename.
#     So renaming the FILE alone does NOT change ruleset contexts — but the file is
#     still the canonical CARRIER of the convention. Grep the ruleset JSONs to confirm
#     which contexts exist and whether any reference the filename or the job names.
grep -RnE "required_status_checks|context|\"lint\"|\"test\"|\"build\"" \
  org-ruleset*.json repo-ruleset*.json 2>/dev/null

# (b) Is the name referenced in runbooks / canonical-checks docs / onboarding?
grep -RnF "$NAME" docs/ .github/ 2>/dev/null

# (c) Does the SAME name exist across sibling/fleet repos (a fleet convention)?
#     Matching the workflow `name:` line proves the CONTRACT, NOT byte-identity.
#     Do NOT claim "identical files" from one grep line — `name:` may sit at a
#     different line number per repo (e.g. line 1 here, line 7 in Scylla/Odyssey).
for d in */*/; do
  [ -f "$d/.github/workflows/$NAME" ] && \
    grep -nE "^\s*name:\s*Required Checks" "$d/.github/workflows/$NAME" \
      | sed "s|^|$d: |"
done

# 2. If ANY of (a)/(b)/(c) is true => DO NOT RENAME. Instead DOCUMENT:
#    - Add a self-documenting header comment to the file explaining WHY the name
#      is canonical and load-bearing (and that renaming has cross-repo blast radius).
#    - Add/strengthen the rationale at the SOURCE-OF-TRUTH doc (canonical-checks
#      / branch-protection runbook) so discoverability is solved without a rename.

# 3. SCOPE the blast radius precisely (do not overstate):
#    - Renaming the FILENAME  => breaks docs/runbook references + fleet uniformity
#                                (COSMETIC w.r.t. enforcement; ruleset contexts unaffected).
#    - Renaming the JOB NAMES => breaks ruleset required-status-check CONTEXTS
#                                (LOAD-BEARING; can deadlock ruleset enforcement).
#    State this distinction explicitly in the plan.

# 4. Verify your runner commands are REAL tasks before citing them in the plan:
grep -nE "markdownlint|yamllint" pixi.toml   # confirm the exact task names exist
```

### Detailed Steps

1. **Pause on the word "discoverability."** A rename-for-clarity nitpick against an
   inscrutable-looking name is a trap: the name is often inscrutable *because* it is a
   terse, load-bearing convention. Treat "rename for discoverability" as a prompt to
   *investigate the name's role*, not as an approved task.
2. **Establish whether the name is a cross-repo convention.** Check the three carriers:
   (a) branch-protection rulesets / required status-check contexts, (b) runbooks +
   canonical-checks / onboarding docs, (c) sibling repos in the fleet. Any hit means the
   name is part of a contract.
3. **If it is a convention → DOCUMENT, do not rename.** The correct resolution of a
   discoverability nitpick against a cross-repo convention is to make the name
   *self-documenting*: a header comment in the file explaining why the name is canonical
   and load-bearing, plus a rationale paragraph at the source-of-truth doc. This delivers
   the discoverability the nitpick wanted, at near-zero blast radius.
4. **Scope blast radius precisely — separate filename from job names.** In GitHub Actions
   branch protection, required status-check **contexts key off the bare JOB NAME**
   (e.g. `lint`), NOT the workflow filename or any `Required Checks / lint` display prefix.
   Therefore: renaming the **file** breaks docs/runbook references and fleet uniformity but
   does **NOT** alter ruleset contexts; renaming the **jobs** breaks the ruleset contexts
   and can deadlock enforcement rollout. A plan that says "renaming the file breaks the
   rulesets" is **wrong** — say "renaming the file breaks docs/uniformity; renaming jobs
   breaks ruleset enforcement."
5. **Do not claim fleet-wide file identity from a single grep line.** Matching the workflow
   `name:` (or any header line) proves the **job-name contract**, not byte-identical files.
   The same `name:` can appear at different line numbers across repos. State "the
   convention is the job-name contract" rather than "the files are identical."
6. **Verify every runner command you cite.** Before writing `pixi run markdownlint` /
   `pixi run yamllint` (or any task) into a plan, confirm the exact task name exists in the
   repo's `pixi.toml` / `justfile`. Don't assume task names from convention.
7. **Diff ALL source-of-truth artifacts you rely on**, don't read one and assume the rest
   match (e.g. `org-ruleset.json` vs `org-ruleset-active.json` vs `repo-ruleset*.json` —
   diff all four for the status-check contexts rather than trusting one).

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| 1 | Took the NITPICK at face value and scoped a plan to rename `_required.yml` "for discoverability." | The name is NOT arbitrary — it is a deliberate, org-wide, load-bearing convention wired into branch-protection enforcement and runbooks across ~15 repos. A rename has disproportionate blast radius and can deadlock ruleset rollout. | For a "rename for clarity" nitpick against a cross-repo convention, the correct fix is to make the name self-documenting (header comment + rationale doc), NOT to rename. |
| 2 (KEY) | Asserted "renaming the file would break the ruleset rollout." | Ruleset required-status-check **contexts key off the BARE JOB NAME** (e.g. `lint`), not the workflow filename or a `Required Checks / lint` prefix. Renaming the **file alone** does NOT change the contexts — only renaming the **jobs** would. The plan overstated the file rename's blast radius. | Distinguish FILENAME (cosmetic: breaks docs/runbook refs + fleet uniformity) from JOB NAMES (load-bearing: breaks ruleset contexts). The real risk of a file rename is broken docs/uniformity, not broken enforcement. State this split explicitly. |
| 3 | Claimed the file is "identical across 14 submodules" based on `grep "name: Required Checks"` matching line 1 in each. | Matched the workflow NAME (a single header line), not byte-identical contents. Scylla/Odyssey had `name:` at line 7, not line 1 — the files are NOT byte-identical. | A single grep line match proves the job-name CONTRACT, not literal file equality. Never claim fleet-wide file identity from one matched line. |
| 4 | Cited `pixi run markdownlint` and `pixi run yamllint` as the repo's verification runners. | Never verified those exact pixi task names exist in Odysseus's `pixi.toml`. | Confirm the exact task name in `pixi.toml`/`justfile` before writing any runner command into a plan. |
| 5 | Read `org-ruleset.json` (9 status-check contexts) and `.pre-commit-config.yaml:63` via grep preview, then assumed sibling ruleset files and the full pre-commit config matched. | Did not diff `org-ruleset-active.json` / `repo-ruleset*.json` against `org-ruleset.json`, and read the pre-commit exclude line via grep preview only, not the full file. | Diff ALL source-of-truth artifacts you depend on; a single read + an assumption of parity is an unverified claim, not evidence. |

## Results & Parameters

**Decision rule (copy-paste into a plan):**

```text
NITPICK: "rename <X> for discoverability/clarity"
  └─ Is <X> a load-bearing cross-repo convention?
       Carriers to check:
         (a) branch-protection rulesets / required status-check contexts
         (b) runbooks / canonical-checks / onboarding docs
         (c) sibling/fleet repos using the same name
     ├─ NO  → a local rename may be fine (still verify references).
     └─ YES → DO NOT RENAME. Make the name self-documenting:
                • header comment in the file (why it's canonical + blast radius)
                • rationale paragraph at the source-of-truth doc
              This delivers the discoverability with near-zero blast radius.
```

**Blast-radius table (GitHub Actions branch protection):**

| You rename… | Breaks… | Severity | Why |
|-------------|---------|----------|-----|
| the **workflow FILENAME** (`_required.yml`) | docs/runbook references + fleet uniformity | Cosmetic w.r.t. enforcement | Ruleset contexts key off job names, NOT the filename — enforcement is unaffected |
| the **JOB NAMES** (`lint`, `test`, …) | ruleset required-status-check CONTEXTS | Load-bearing | Contexts ARE the bare job names — renaming them deadlocks enforcement until rulesets are updated |

**Case context:** Odysseus meta-repo, GitHub issue #215 (sole open child of Epic #174),
file `.github/workflows/_required.yml`. Recommended resolution: document the rationale
in-file + at the canonical-checks source-of-truth doc; do NOT rename.

**Related skill (CI mechanics):** `gha-required-checks-branch-protection` covers the
underlying mechanics — bare-job-name = context, job key vs `name:` field disambiguation,
the reusable-workflow `_required.yml` aggregator pattern. This skill is the *planning
decision* layer on top of it (when NOT to rename, and how to scope the blast radius).

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| Odysseus | Implementation plan for issue #215 / Epic #174 (`_required.yml` rename NITPICK) — plan written, NOT executed; self-review found a blast-radius overstatement | unverified — planning learning |
