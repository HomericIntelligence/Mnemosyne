---
name: audit-remediation-verify-evidence-before-planning
description: "Before planning a fix for an audit/remediation issue, verify the audit's cited evidence (file:line) against the live tree — audit findings go stale once the target is independently remediated, and an audit that names SEVERAL targets can have a SUBSET already fixed. Re-read EVERY cited file:line before planning, fix ONLY the issue-named targets (a repo-wide survey will surface more non-compliant siblings — note them out-of-scope, do not expand the PR), and do not invent a unit test for a doc/UX field that has no test contract. When a doc-table column is genuinely UN-RECOVERABLE from the repo (e.g. a semantic-version 'Added' anchor), INFER it but LABEL the provenance honestly as best-effort, and design any drift-guard to validate ONLY the verifiable invariant (table membership vs live __all__), never the inferred value. Use when: (1) planning a fix for an audit-filed issue with file:line evidence, (2) the issue spans multiple repos or submodules, (3) the issue recommends doc/field-name/frontmatter changes that may already be done, (4) the audit names multiple targets and any subset may already be remediated, (5) you must author a doc table that mixes a verifiable column (symbol membership) and an unverifiable column (which version first shipped it)."
category: architecture
date: 2026-06-26
version: "1.3.0"
user-invocable: false
verification: verified-local
history: audit-remediation-verify-evidence-before-planning.history
tags: []
---

# Audit Remediation: Verify Evidence Before Planning

**History:** [changelog](./audit-remediation-verify-evidence-before-planning.history)

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-06-19 |
| **Objective** | Plan a fix for a cross-repo audit-remediation GitHub issue without trusting stale audit evidence |
| **Outcome** | Discovered the audit was stale — target submodule already remediated; scoped the plan to only the genuinely-actionable owned-repo work + a drift guard |
| **Verification** | verified-local |

> **Verification note:** The evidence-verification steps below (grep against the live tree, confirming canonical names in the Pydantic source of truth) were genuinely RUN this session and confirmed the target docs were already remediated — that is what `verified-local` attests to. The downstream implementation (the architecture.md section + the drift-guard script wired into `just ci`) was **planned only**, not executed or CI-validated. Do not read this as `verified-ci`.
>
> **v1.1.0 note:** The canonical mapping (`subject`/`assign_to`/`blocked_by` model fields serialized as `subject`/`assigneeAgentId`/`blockedBy`) was verified this session by reading BOTH `models.py` AND `agamemnon_client.py` against the live tree. The corresponding architecture.md table edit itself was **planned only**, not executed or CI-validated.
>
> **v1.3.0 note (UNVERIFIED — plan only; inferred-version-anchor case):** Planning ProjectHephaestus issue #1506 (audit finding: three Stable subpackages — `hephaestus.cli`, `hephaestus.system`, `hephaestus.version` — lack per-symbol API tables in `COMPATIBILITY.md`). **No code was executed, no tests run, no CI** — this addition is `unverified`, NOT `verified-local` or `verified-ci`. The durable learning: when an audit asks you to author a doc table whose "Added" semantic-version column is genuinely UN-RECOVERABLE (the subpackages predate the existing tables; there is no authoritative record of which version first shipped each symbol), you must INFER those values — and label them honestly as "best-effort historical anchors" so the reviewer does not treat them as authoritative. Anchors were inferred by: reusing a version already documented for the symbol in a sibling table; `git log -S <symbol>` to find the introducing commit/PR and mapping its era to a minor; and defaulting pre-1.0 infrastructure to `0.1.0`. The accompanying drift-guard deliberately validates ONLY the recoverable invariant (table membership cross-checked against live `__all__`, both directions) and deliberately does NOT assert the inferred "Added" string — guarding an inferred field would lend false authority to fabricated data. Also: re-reading the live `__all__` caught the audit's symbol count as stale AND under-counted (issue claimed 12 for `hephaestus.cli`; live `__init__.py` had 16).
>
> **v1.2.0 note (single-repo, multi-target frontmatter case):** Planning ProjectHephaestus issue #1553 ("Skills missing `argument-hint` frontmatter field"), which named TWO targets — `skills/brainstorm/SKILL.md` and `skills/python-repo-modernization/SKILL.md`. Reading `skills/brainstorm/SKILL.md:1-6` showed `argument-hint: <idea or feature description>` **already present at line 4** — the audit snapshot (2026-06-16) was stale for that target; only `python-repo-modernization` genuinely lacked the field. Re-reading every cited file:line before planning (not trusting the issue text) is what `verified-local` attests to here; the PR/CI for #1553 had **not landed at capture time** — state honestly, this is `verified-local`, not `verified-ci`. A repo-wide `awk` survey over all `skills/*/SKILL.md` both confirmed `brainstorm` was already compliant AND surfaced ~10 OTHER skills missing the field — deliberately EXCLUDED to respect one-issue-per-PR scope. The field is unenforced: `grep -rl "argument-hint" tests/` returned nothing and `ls tests/unit/ | grep -i skill` was empty, so verification is a YAML-frontmatter parse (`yaml.safe_load_all`), NOT a unit test — do not invent a test where no contract exists.

## When to Use

- Planning a fix for an issue filed by an automated/ecosystem audit that cites specific `file:line` evidence.
- The issue spans multiple repos, especially when some are git submodules owned by other repos.
- The recommendation is a doc/field-name/role-description change that another team may have already fixed.
- Any "documentation drift" or "X docs show deprecated Y" issue.
- Authoring a doc/table that CLAIMS canonical names or values — every cell must be code-traceable.
- The audit names MULTIPLE targets (e.g. "these 2 skills are missing field Z"). Any subset may already be remediated — verify EACH named target independently; never plan for all of them on the strength of the issue title.
- The recommendation is a config/frontmatter/UX field change (e.g. a Claude Code plugin `argument-hint`) that may be unenforced — confirm whether a test/validator contract exists before scoping any verification step.
- You must author a doc table (e.g. an API/COMPATIBILITY table) that mixes a VERIFIABLE column (symbol membership, derivable from live `__all__`) and an UNVERIFIABLE column (which version first shipped each symbol). The latter is often un-recoverable for packages that predate the table — you will have to INFER it and must label the provenance honestly.
- The audit cites a symbol/item COUNT (e.g. "`__all__` has 12 symbols"). Counts go stale and are frequently under-counted — re-derive the FULL set from the live source, never transcribe the audit's enumeration.

**Related:** `agent-config-validation-and-integrity` covers HOW to validate YAML frontmatter structurally (`yaml.safe_load_all`, required fields). This skill is distinct: it is about VERIFYING AUDIT FINDINGS before planning — re-reading every cited target on disk, detecting stale/partially-fixed multi-target audits, and resisting scope creep. Reach for that skill once you know what to validate; reach for this one to decide whether the audit's claim is even still true.

## Verified Workflow

The evidence-verification phase (steps 1-3) was actually executed against the live tree and is the basis for the `verified-local` claim. Steps 4-6 (scoping and the drift guard) were the resulting plan, which was not itself executed in CI.

1. **Read the issue's cited evidence FIRST and diff it against the live tree.** For every `file:line` the issue names, open the live file at those coordinates and confirm the claimed text is actually there. Do not assume the evidence is current — an audit captures a snapshot at filing time, and the target may have moved on.
2. **Identify the source of truth and confirm canonical values there.** For a field-name/schema issue, the source of truth is the code (Pydantic models / enums / REST contract), not the prose. Confirm the canonical values in code, and treat docs as the thing aligned TO code, never the reverse.
3. **Distinguish real hits from false positives — grep, then eyeball each in context.** A token like `title:` inside a generated JSON-Schema is a display label, and a method name like `test_unknown_depends_on_raises` is describing behavior — neither is a documented schema field. A raw grep count is not a violation count; inspect every hit.
4. **Scope by ownership.** Do NOT edit files inside git submodules from the meta-repo — they are owned by their own repo and must be PR'd there (or a referencing issue filed). One PR per owned repo.
5. **If the cited target is already remediated, say so explicitly.** State it in the plan and in the PR body, then pivot the plan to (a) the still-actionable owned-repo recommendation and (b) a drift-prevention guard so the deprecated form cannot silently return.
6. **Match the repo's EXISTING check pattern for the guard.** Here that meant a bash script under `scripts/` plus a `just` recipe wired into `just ci` — not a new framework. A meta-repo with "no application code" should not get a pytest harness just for a doc check.
7. **When you author a canonical-names/values table, read EACH cell from the source of truth, and distinguish the model/field layer from the serialization/wire layer** (e.g. Pydantic `assign_to` vs JSON `assigneeAgentId` in the REST client). Never invent a "deprecated/legacy" variant for a field that is current. A drift guard that only matches the OLD tokens will not catch a wrong NEW canonical name — so add a positive check (table cell == code) and a negative check (guessed-wrong name is absent).
8. **Verify EACH named target separately when the audit names several.** An audit that says "targets A and B are missing field Z" is two independent claims — open A and B at their cited coordinates and confirm Z is absent in EACH. A partially-stale audit (A already fixed, B genuinely missing) is the norm, not the exception; planning a no-op edit on the already-fixed target earns a reviewer NOGO.
9. **Run a repo-wide survey to learn the convention AND the true scope — then fix ONLY the issue-named targets.** A one-liner (`awk`/`grep` over the whole population) both confirms which named targets are genuinely non-compliant and reveals the convention to follow (field position, quoting). It will usually surface MORE non-compliant siblings than the issue named. Resist fixing them: note them explicitly as out-of-scope (they belong to the broader audit bundle), keep the PR to one issue's targets.
10. **Don't invent a test where no contract exists.** For a pure doc/UX/frontmatter field, check whether any test or validator actually asserts it (`grep -rl "<field>" tests/`, `ls tests/unit/ | grep -i <area>`). If nothing does, the verification is a structural parse (`yaml.safe_load_all` over the frontmatter), not a new unit test. Adding a bespoke test for an unenforced field is scope creep and a false-rigor signal.
11. **Derive the field VALUE from the artifact's actual behavior, and place it per the dominant convention.** For `argument-hint`, read what the skill operates on (it modernizes a target repo -> `<path to Python repo to modernize>`) rather than copying a generic placeholder, and position it where sibling skills put it (immediately after `description`) confirmed by reading siblings, not by guessing.

### Proposed Workflow (v1.3.0 — UNVERIFIED, plan only)

> **⚠️ Warning:** The steps below come from a PLAN for ProjectHephaestus issue #1506 that was **never executed** — no code ran, no tests, no CI. They are reasoning patterns, not a validated procedure. Treat as `unverified`.

12. **Re-derive any cited COUNT from the live source; never transcribe the audit's enumeration.** The audit claimed `hephaestus.cli.__all__` had 12 symbols; the live `hephaestus/cli/__init__.py:22-39` had 16 (it omitted `DRY_RUN_HELP_CAVEAT`, `add_dry_run_arg`, `add_github_throttle_args`, `configure_github_throttle_from_args`). An audit that lists N items can be BOTH stale AND under-counted — read the full `__all__` yourself.
13. **For an un-recoverable provenance column (the "Added" semantic-version), INFER honestly and LABEL the provenance.** These subpackages predate the existing tables; nothing authoritatively records which version first shipped each symbol. Anchor by, in priority order: (a) reuse a version already documented for the same symbol in a sibling table (e.g. `system.get_system_info` was `0.3.0` in the top-level table -> reuse `0.3.0` for `format_system_info`); (b) `git log -S <symbol>` to find the introducing commit/PR and map its era to a minor (e.g. `emit_json_status`/`add_json_arg` from PR #603 -> `0.6.0`; throttle args from #1520 -> `0.9.0`); (c) default pre-1.0 infrastructure to `0.1.0`. In the plan, explicitly call these "best-effort historical anchors" so the reviewer knows they are inferences, not facts.
14. **Design the drift-guard to validate ONLY the recoverable invariant — deliberately NOT the inferred column.** Cross-check table membership against live `__all__` in BOTH directions (symbol-missing-from-docs and symbol-missing-from-`__all__`) — a hard, verifiable invariant. Do NOT assert the "Added" version string; a guard that asserts an inferred value asserts fiction and lends false authority to fabricated data. General trick: when a doc artifact mixes a verifiable column and an unverifiable column, guard only the verifiable one.
15. **Mirror the nearest existing executable-convention guard instead of inventing one.** Found `hephaestus/validation/cli_tier_docs.py` (cross-checks `[project.scripts]` <-> `COMPATIBILITY.md`, wired into `.pre-commit-config.yaml:166` and `pyproject.toml:141`); mirror its structure, console-script registration, and pre-commit wiring exactly rather than building a bespoke CI job.
16. **Account for the second-order cost: a new gate can trip an OLDER gate.** Registering `hephaestus-check-api-table-docs` in `[project.scripts]` means the EXISTING `cli_tier_docs` guard will fail unless a "Console-Script Stability Tiers" row is also added for it. Plan the reciprocal edit so the new console script satisfies the sibling guard.

### Quick Reference

```bash
# 1. Re-verify audit evidence against live tree (expect: stale audit => no hits)
grep -nE '^[[:space:]]*-?[[:space:]]*(title|depends_on):' <cited-docs>
# 2. Confirm canonical names in the source of truth (Pydantic model)
grep -nE 'subject:|blocked_by:' src/<pkg>/models.py
# 3. Check ownership before editing — submodules are off-limits from the meta-repo
git submodule status
# 4. When authoring a canonical table: verify BOTH layers cell-by-cell
#    model/field layer (Pydantic / YAML)
grep -nE 'assign_to|subject|blocked_by' src/<pkg>/models.py
#    serialization/wire layer (JSON keys in the REST client) — these can DIFFER
grep -nE 'assigneeAgentId|blockedBy|"subject"' src/<pkg>/<rest_client>.py
# 5. Negative check — the guessed-wrong canonical name must be ABSENT from the doc
! grep -nE '<guessed-wrong-name>' <doc>   # e.g. ! grep -nE 'assignee_agent_id' docs/architecture.md

# --- multi-target frontmatter audit (e.g. ProjectHephaestus #1553 argument-hint) ---
# 6. Verify EACH named target's frontmatter separately (expect: a subset already has it)
sed -n '1,8p' skills/brainstorm/SKILL.md                 # already has argument-hint => STALE claim
sed -n '1,8p' skills/python-repo-modernization/SKILL.md  # genuinely missing => actionable
# 7. Survey the WHOLE population for convention + true scope (fix only the named targets)
for f in skills/*/SKILL.md; do printf '%s: ' "$f"; awk -F': ' '/^argument-hint:/{print $2; found=1} END{if(!found)print "MISSING"}' "$f"; done
# 8. Confirm there is NO test contract before scoping a test (expect: no output)
grep -rl "argument-hint" tests/ ; ls tests/unit/ | grep -i skill
# 9. Verification IS a frontmatter parse, not a unit test
python3 -c "import yaml,sys; list(yaml.safe_load_all(open(sys.argv[1]).read().split('---')[1]))" skills/python-repo-modernization/SKILL.md

# --- inferred-version-anchor doc table (e.g. ProjectHephaestus #1506 API tables) [UNVERIFIED plan] ---
# 10. Re-derive the FULL symbol set from live __all__; do NOT trust the audit's count
python3 -c "import hephaestus.cli as m; print(len(m.__all__)); print(m.__all__)"   # audit said 12; live had 16
# 11. Infer the un-recoverable "Added" version via git archaeology (best-effort anchor, NOT a fact)
git log -S 'emit_json_status' --oneline -- hephaestus/cli/ | tail -1   # find introducing commit/PR -> map era to minor
# 12. Guard the VERIFIABLE invariant only: table membership vs live __all__, both directions
#     (deliberately do NOT assert the inferred "Added" version string)
# 13. Mirror the nearest existing executable-convention guard, don't invent one
grep -n 'cli_tier_docs' .pre-commit-config.yaml pyproject.toml
# 14. A new console script trips the SIBLING guard — add the reciprocal Console-Script Tiers row
```

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| ------- | -------------- | ------------- | -------------- |
| Trusting the audit's file:line evidence as current | Issue cited `CLAUDE.md:55-58` / `README.md:62-69` as showing `title`/`depends_on` | The submodule had already been remediated independently; those lines now use `subject`/`blocked_by` | Always re-read cited evidence against the live tree before planning |
| Grepping for `title`/`depends_on` and treating every hit as a violation | Raw grep flagged JSON-Schema `"title":` labels and a `test_unknown_depends_on_raises` method name | These are not documented workflow fields — false positives | Anchor the pattern to field-key syntax and eyeball each hit in context |
| Assuming the meta-repo can fix the submodule's docs in this PR | Planned to edit `provisioning/ProjectTelemachy` docs from Odysseus | Submodules are owned by their own repos; editing their working tree from the meta-repo is wrong scope | Scope edits by ownership; PR the owning repo or file a referencing issue |
| Filling a canonical-names table from memory/issue text | Wrote canonical=`assignee_agent_id`, deprecated=`assigned_to (legacy)` | Source of truth has `assign_to` (model) serialized as `assigneeAgentId`; the guessed names existed nowhere | Read every table cell verbatim from code before writing it |
| Assuming the model field name equals the wire/JSON key | Conflated Pydantic `assign_to` with the REST payload key | They differ: the client maps `spec.assign_to` -> `assigneeAgentId` | Always check the serialization layer (REST client) separately from the model |
| Trusting a drift guard to catch a wrong canonical name | Guard only greps deprecated `title`/`depends_on` | A fabricated canonical name passes the guard silently | Verify the canonical table with a positive (cell==code) AND negative (guessed-wrong absent) check, not just the deprecated-token guard |
| Trusting a multi-target audit issue verbatim | #1553 named `brainstorm` + `python-repo-modernization` as missing `argument-hint`; planned to add the field to both | `skills/brainstorm/SKILL.md:4` ALREADY had `argument-hint` — the audit snapshot (2026-06-16) was stale for that target; the edit would be a no-op (or a confusing "add field that already exists") | Re-read EVERY cited file:line before planning; verify each named target independently — a subset is usually already remediated |
| Expanding the fix to all skills missing the field | A repo-wide `awk` survey surfaced ~10 OTHER skills also missing `argument-hint`; tempting to fix them all in one PR | Scope creep — violates one-issue-per-PR; those skills belong to the broader audit bundle, not #1553 | Fix ONLY the issue-named targets; note the additional non-compliant siblings as explicitly out-of-scope |
| Inventing a unit test for the frontmatter field | Considered adding a `tests/unit/` test asserting `argument-hint` is present | No test contract exists: `grep -rl "argument-hint" tests/` is empty and there are no skill tests under `tests/unit/`; the field is unenforced | Verification is a YAML-frontmatter parse (`yaml.safe_load_all`), not a unit test — don't add false-rigor tests for an unenforced doc/UX field |
| Copying a generic placeholder for the field VALUE | Almost used a vague `<argument>` hint | The value must describe what the artifact actually operates on, positioned per the dominant convention | Derive the value from behavior (`<path to Python repo to modernize>`), place it after `description` as confirmed by reading sibling skills |
| Transcribing the audit's symbol count (v1.3.0, UNVERIFIED) | Audit said `hephaestus.cli.__all__` had 12 symbols; nearly planned 12 table rows | Live `hephaestus/cli/__init__.py:22-39` had 16 — the audit omitted `DRY_RUN_HELP_CAVEAT`, `add_dry_run_arg`, `add_github_throttle_args`, `configure_github_throttle_from_args` | Re-derive the FULL set from live `__all__`; an audit's enumeration can be both stale AND under-counted |
| Treating the inferred "Added" version as an authoritative fact (v1.3.0, UNVERIFIED) | Wanted to fill the "Added" semantic-version column with confident values | Those subpackages predate the existing tables; nothing records which version first shipped each symbol — every value is an inference | Label them "best-effort historical anchors" in the plan; anchor via sibling-table reuse, `git log -S`, and a `0.1.0` pre-1.0 default — and say so |
| Designing the drift-guard to assert the "Added" version (v1.3.0, UNVERIFIED) | Considered a guard that checks both the symbol AND its documented version | The version is inferred/unverifiable; a guard asserting it would assert fiction and lend false authority to fabricated data | Guard ONLY the recoverable invariant (table membership vs live `__all__`, both directions); never guard an inferred column |
| Inventing a bespoke CI job for the new guard (v1.3.0, UNVERIFIED) | Almost wrote a custom workflow for the API-table check | An existing executable-convention guard (`hephaestus/validation/cli_tier_docs.py`, wired into `.pre-commit-config.yaml:166` + `pyproject.toml:141`) already models the pattern | Mirror the nearest existing guard's structure, registration, and pre-commit wiring exactly |
| Forgetting the new console script trips the OLDER guard (v1.3.0, UNVERIFIED) | Planned to register `hephaestus-check-api-table-docs` in `[project.scripts]` only | The existing `cli_tier_docs` guard fails unless a "Console-Script Stability Tiers" row is also added for the new script | A new gate can trip an older gate — plan the reciprocal edit |

## Results & Parameters

- **Canonical field names — TWO layers (verified by reading `models.py` AND `agamemnon_client.py` this session):**
  - Model / YAML field (Pydantic source of truth): `subject` (models.py:38), `assign_to` (models.py:40), `blocked_by` (models.py:41).
  - JSON wire key (REST client serialization): `subject` (agamemnon_client.py:207), `assigneeAgentId` (agamemnon_client.py:211,214), `blockedBy` (agamemnon_client.py:216).
  - The model field `assign_to` is serialized as `assigneeAgentId`; **the two layers differ and must be read separately**. There is NO `assignee_agent_id` field anywhere.
  - Deprecated forms (the only ones that exist): `title` (-> `subject`) and `depends_on` (-> `blocked_by`). There is NO `assigned_to (legacy)` deprecated form — that was a fabricated guess caught by a reviewer.
- **Drift-guard pattern:** first-party-only file list via
  `git ls-files -- '*.md' | awk '!/^(infrastructure|control|provisioning|ci-cd|research|shared|testing)\//'`;
  field-key regex `^[[:space:]]*-?[[:space:]]*(title|depends_on):`;
  exit `0` clean / `1` drift / `2` usage; wire into `just ci`.
- **Submodule dirs in this ecosystem to exclude from first-party scans:** `infrastructure/` `control/` `provisioning/` `ci-cd/` `research/` `shared/` `testing/`.
- **ProjectHephaestus #1553 (`argument-hint` frontmatter, v1.2.0 case):**
  - Named targets: `skills/brainstorm/SKILL.md` (ALREADY compliant — `argument-hint: <idea or feature description>` at line 4; stale audit) and `skills/python-repo-modernization/SKILL.md` (genuinely missing — the only actionable target).
  - Convention (confirmed by reading siblings): `argument-hint` placed immediately after `description`; value describes what the skill operates on. For `python-repo-modernization`: `<path to Python repo to modernize>`.
  - Enforcement: NONE. `grep -rl "argument-hint" tests/` -> no matches; no skill tests under `tests/unit/`. Verification = structural YAML-frontmatter parse (`yaml.safe_load_all`), not a unit test. `argument-hint` is optional/advisory in the Claude Code plugin format (inferred from the absence of any validator, not confirmed against upstream plugin-spec docs).
  - Out-of-scope (deliberately NOT fixed in #1553): ~10 other `skills/*/SKILL.md` also missing `argument-hint`, surfaced by the survey — they belong to the broader audit bundle (split from #1518), one issue per PR.
  - Provenance taken at face value (low risk): the audit timestamp (2026-06-16) and the split-from-#1518 origin.
- **ProjectHephaestus #1506 (per-symbol API tables for Stable subpackages, v1.3.0 case — UNVERIFIED, plan only):**
  - Targets: `hephaestus.cli`, `hephaestus.system`, `hephaestus.version` lack per-symbol API tables in `COMPATIBILITY.md`. **No code executed, no tests, no CI** — verification = `unverified`.
  - Stale/under-counted audit: audit claimed `hephaestus.cli.__all__` had 12 symbols; live `hephaestus/cli/__init__.py:22-39` had 16 (audit omitted `DRY_RUN_HELP_CAVEAT`, `add_dry_run_arg`, `add_github_throttle_args`, `configure_github_throttle_from_args`).
  - "Added" version anchors are INFERRED, not verified — labeled "best-effort historical anchors" in the plan. Anchoring method, in priority order: (a) reuse a version already documented for the same symbol in a sibling table (`system.get_system_info` documented `0.3.0` in the top-level table -> reuse `0.3.0` for `format_system_info`); (b) `git log -S <symbol>` to find the introducing commit/PR and map its era to a minor (`emit_json_status`/`add_json_arg` from PR #603 -> `0.6.0`; throttle args from #1520 -> `0.9.0`); (c) default pre-1.0 infrastructure to `0.1.0`. These are the dominant uncertain assumption in the plan.
  - Drift-guard (`api_table_docs.py`, planned): cross-checks table membership against live `__all__` in BOTH directions (missing-from-docs and missing-from-`__all__`) — a hard verifiable invariant. Deliberately does NOT validate the "Added" string. Mirrors `hephaestus/validation/cli_tier_docs.py` (which cross-checks `[project.scripts]` <-> `COMPATIBILITY.md`, wired into `.pre-commit-config.yaml:166` + `pyproject.toml:141`), including console-script registration (`hephaestus-check-api-table-docs`) and pre-commit wiring. Pre-commit `entry` pins `--environment default` because the guard imports the packages via `importlib.import_module` and needs an env where they import cleanly.
  - Reciprocal edit required: registering the new console script means the existing `cli_tier_docs` guard fails unless a "Console-Script Stability Tiers" row is added for it.
  - Reviewer risk areas (do NOT treat the inferred values as authoritative): (1) the "Added" versions are inferred — only the membership invariant is verified; (2) the table-parsing regex (`_TABLE_ROW_RE`, the ``### `package` `` header match) is hand-rolled and may mis-parse if `COMPATIBILITY.md` formatting drifts (backtick style, separator rows) — the live-tree alignment test is the safety net; (3) `test_missing_from_docs_detected` must assert MEMBERSHIP of the expected kind in a result set that ALSO contains many `table-not-found` findings (the tmp doc only has the system table), not equality.
