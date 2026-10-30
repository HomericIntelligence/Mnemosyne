---
name: mnemosyne-skill-pr-ci-gate-first-pass-green
license: BSD-3-Clause
description: "Prepare Mnemosyne skill changes for existing validation and Markdown checks. Use for required sections, table pipes, overlapping amendments, and pre-existing corpus failures."
category: tooling
date: 2026-06-13
version: "1.2.1"
user-invocable: false
verification: verified-ci
tags:
  - ci-cd
  - markdownlint
  - skills
  - mnemosyne
history-source: "https://github.com/HomericIntelligence/Mnemosyne/blob/1956c91d76867bc2e484eaf573a57051855186f8/skills/mnemosyne-skill-pr-ci-gate-first-pass-green.history"
history-cleanup-date: "2026-09-20"
---

# Mnemosyne: Author a /learn Skill PR That Passes CI on the First Pass

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-06-13 |
| **Objective** | Author a Mnemosyne `/learn` skill PR (`skills/*.md` plus optional notes) that passes the required CI gate on the FIRST push, instead of discovering a red `markdownlint` or `validate` check after the PR is open |
| **Required gate** | Observed 2026-10-30: the active ruleset `homeric-main-baseline` on `main` requires one context, `required-checks-gate`; its required pipeline runs the `validate` job (ruff + `python3 scripts/validate_plugins.py` over the WHOLE `skills/` dir + mypy + pytest) and the `markdownlint` job (markdownlint-cli2 with `.markdownlint.yaml`), both SUCCESS on PR #3628. At capture time the required contexts were literally `["validate","markdownlint"]` |
| **Outcome** | A four-step local validation order (section self-check, markdownlint-cli2, validate\_plugins.py, pre-commit) plus an open-PR amend-lock that prevents the mutually-DIRTY duplicate-PR cluster seen across 117 open Mnemosyne skill PRs |
| **Verification** | verified-ci — local markdownlint + `validate_plugins.py` + the section self-check pass on this file. The carrier ProjectHephaestus PR #1323 merged 2026-06-14 with its gate green, and Mnemosyne PR #3628 (merged 2026-10-29) ran the four-step local order below and passed the required gate on the first push |
| **Verified On** | ProjectHephaestus PR #1323 (origin carrier; merged green 2026-06-14) and Mnemosyne PR #3628 (a consumer `/learn` skill PR that ran this four-step order and merged green 2026-10-29). The dedup query reproduced the duplicate-PR cluster, and the section self-check flagged the exact 4 missing sections in PR #2417's real file |

## When to Use

- You are about to commit a new or amended Mnemosyne `skills/*.md` from a `/learn` run and want it green on the first push.
- A markdown table cell in your skill contains an inline pipe (a regex like `a|b`, a shell pipe, a column of alternatives) and you need to know why `markdownlint` MD056 rejects it even though `validate_plugins.py` passed.
- `/learn` emitted a skill that is missing one of the five required `##` sections and you want to catch it before the `validate` gate does.
- Parallel `/learn` runs each forked a fresh `origin/main` branch against the SAME skill and the resulting PRs are mutually DIRTY — you need the open-PR amend-lock.
- The `validate` gate is red on files you never touched and you need to tell pre-existing main breakage apart from a regression you introduced.
- A full-suite `pytest` run before your first commit fails `tests/test_writing_policy.py::test_active_guidance_inventory_is_closed` with the set difference listing exactly your new skill files, and you need to tell this not-yet-committed artifact apart from breakage.
- `scripts/check-symlinks.sh` flags interpreter symlinks under an untracked `.venv/` that a package runner (for example `uv run`) created in the worktree.
- You are about to label a skill `verified-ci` and want to confirm the gate is actually observed green first.

## Verified Workflow

> **Verification note:** The four-step local order below passes on this skill file. The end-to-end CI behavior is verified: carrier ProjectHephaestus PR #1323 merged with its gate green (2026-06-14) and consumer Mnemosyne PR #3628 passed the required gate on the first push after running the same local order (2026-10-29).

### Quick Reference

```text
LOCAL VALIDATION ORDER (run all four from the worktree root BEFORE committing):

  0) SECTION SELF-CHECK — the validate gate fails on your OWN new file if it
     is missing any of the five required ## sections. grep each header first:
       for sec in "## Overview" "## When to Use" "## Verified Workflow" \
                  "## Failed Attempts" "## Results & Parameters"; do
         grep -qF "$sec" skills/<name>.md || echo "MISSING: $sec"
       done
     (validate_plugins.py accepts ONLY "## Verified Workflow"; for an
      unverified skill keep that exact header and add a "> Proposed Workflow"
      warning subtitle under it — do NOT rename the header.)

  1) MARKDOWNLINT — exactly as CI runs it. Fix EVERY MDxxx, not just MD056:
       npx --yes markdownlint-cli2 --config .markdownlint.yaml \
         "skills/<name>.md"
     MD056/table-column-count is the #1 failure: an unescaped literal pipe in a
     table cell is parsed as a column separator, so the row has more cells than
     the header. Escape inline pipes as backslash-pipe, or balance the row.
     MD012/no-multiple-blanks (two or more consecutive blank lines) also shows
     up on real PRs — markdownlint flags ALL rules, not only MD056.

  2) PLUGIN VALIDATOR — lints the ENTIRE skills/ dir (SKILLS_DIR = "skills"):
       python3 scripts/validate_plugins.py
     It does NOT catch MD056 — that is markdownlint's job (step 1).

  3) PRE-COMMIT — only your file:
       pre-commit run --files skills/<name>.md

AMEND-LOCK (run BEFORE forking origin/main, to avoid the DIRTY duplicate cluster):
   gh pr list --repo HomericIntelligence/Mnemosyne --state open \
     --search "<name> in:title" --json number,headRefName,title
   If an OPEN PR already amends this skill, STACK on its branch (push to it or
   branch FROM its headRefName) — do NOT fork main into a competing branch.

VERIFIED-CI HONESTY:
   Only claim verified-ci AFTER the PR gate is observed green:
     gh pr view <PR> --json mergeStateStatus,statusCheckRollup
   Passing markdownlint + validate_plugins.py LOCALLY is verified-local.
```

1. **Amend-lock first.** Before forking `origin/main`, run the `gh pr list ... --search "<name> in:title"` query and a files-based check. If an open PR already amends the skill, stack on its `headRefName` instead of forking a competing branch. ~35 of 117 open PRs were mutually DIRTY because parallel `/learn` runs each forked fresh main against the same skill.
2. **Section self-check (step 0).** `grep -qF` each of the five required headers; any miss means the `validate` gate will fail on your own new file. Keep the literal header `## Verified Workflow`; for an unverified skill add a `> Proposed Workflow` warning subtitle under it rather than renaming the header.
3. **markdownlint (step 1).** Run `markdownlint-cli2 --config .markdownlint.yaml` over the changed main and notes files. Fix EVERY rule it reports, with MD056 and MD012 the most common.
4. **validate_plugins.py (step 2).** It lints the whole `skills/` dir. If errors appear only in files you did not touch, that is pre-existing main breakage — surface it as a separate fix PR, do not misattribute it to your change, and do not claim verified-ci off the back of it.
5. **pre-commit (step 3).** `pre-commit run --files skills/<name>.md`.
6. **Full-suite pytest ordering (new-file runs).** `tests/test_writing_policy.py::test_active_guidance_inventory_is_closed` discovers active skills from the FILESYSTEM but closes the inventory over `git ls-files`. A new, not-yet-committed skill file appears in the discovery set only, so the test fails with the difference listing exactly your new files. This is a third attribution class — a commit-ordering artifact, neither pre-existing breakage nor a regression. Run steps 0–3 before committing; run the full `pytest` suite again AFTER committing the new files, when it passes. Steps 0–3 are state-independent and stay green pre-commit.
7. **Symlink check sees environment artifacts.** `scripts/check-symlinks.sh` walks the whole tree, including untracked directories, and reports "symlink escapes repo" for interpreter links under a `.venv/` that `uv run` created. Classify these as environment artifacts: remove the runner-created environment directory before the check (or expect the report); they are not a repository defect and CI does not see them.
8. **verified-ci honesty.** Only after the PR's required gate (`validate` + `markdownlint`) is observed green via `gh pr view <PR> --json mergeStateStatus,statusCheckRollup` may you label the skill `verified-ci`. Local green is `verified-local`.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| ------- | -------------- | ------------- | -------------- |
| Ran only `validate_plugins.py` before pushing | Treated the plugin validator as the whole CI gate and pushed once it passed | `validate_plugins.py` does NOT parse markdown tables, so MD056/table-column-count reached the `markdownlint` gate and blocked the PR (7 PRs) | The required gate is TWO checks; an inline pipe in a table cell is only caught by `markdownlint-cli2` — run step 1 locally, not just step 2 |
| Forked fresh `origin/main` while other PRs amended the same skill | Each parallel `/learn` run branched from `origin/main` against the SAME skill file | All competing branches modified the same `.md`/`.history`, so they became mutually modify/modify DIRTY (~35 of 117 PRs; e.g. ~9 amending python-module-decomposition, ~14 stale-documentation-audit) | Run the open-PR amend-lock query BEFORE forking; if one exists, STACK on its `headRefName` instead of forking main |
| Generated a skill missing four required sections | Let `/learn` emit a skill and committed without a section self-check | The `validate` gate reported "Missing required section" on the PR's OWN new file (#2417 / #2420) | grep each of the five `##` headers before commit; a missing header is a guaranteed `validate` failure |
| Labeled a skill verified-ci while its own gate was red | Set `verification: verified-ci` based on a passing local run | The PR's `validate`/`markdownlint` gate was still red, so the verification level was untrustworthy | Only claim verified-ci after `gh pr view <PR> --json statusCheckRollup` shows the gate green; local-only is verified-local |
| Blamed validate errors on my own change | Saw red `validate` and assumed my new file broke it | The errors were in files I never touched — a single broken file already on main reddens EVERY PR's whole-dir `validate` | When validate errors point at untouched files, it is pre-existing main breakage; surface a separate fix PR and do not misattribute |
| Ran full-suite pytest with new files uncommitted | Ran `pytest tests/` in a new-skill worktree before the first commit (per "run all four BEFORE committing") | `test_active_guidance_inventory_is_closed` failed; the set difference listed exactly the new skill files. Filesystem discovery counts them, the `git ls-files` closure does not | The inventory-closure failure on a pre-commit new-file run is a commit-ordering artifact: commit the new files and re-run the suite; it passes. Do not misclassify it as pre-existing breakage or a regression |
| Ran the symlink check with a runner-created `.venv` | Ran `scripts/check-symlinks.sh` after `uv run` created `.venv/` in the worktree | The check reported "symlink escapes repo" for three interpreter symlinks under the untracked `.venv/` | The check walks untracked directories too; remove the runner-created environment directory (or expect the report) — an environment artifact, not a repository defect, and not visible to CI |

## Results & Parameters

### Quick Reference

- **The gate: two checks, observed inside one required context.** At capture time `main` protection required `["validate","markdownlint"]`; observed 2026-10-30 the active ruleset `homeric-main-baseline` requires one context, `required-checks-gate`, and its required pipeline runs both checks. `validate` = ruff + `python3 scripts/validate_plugins.py` (whole `skills/` dir) + mypy + pytest. `markdownlint` = `markdownlint-cli2 --config .markdownlint.yaml`. Use the authorized validation process to cover both checks and report any coverage gap.
- **MD056 is the #1 failure and `validate_plugins.py` cannot catch it.** An unescaped literal pipe inside a table cell (a regex, a shell pipe, an `a|b` alternative) is parsed as a column separator, so the data row has more cells than the header. Escape inline pipes as backslash-pipe, or balance the row. Only `markdownlint` flags this.
- **markdownlint flags ALL rules.** MD012/no-multiple-blanks (two or more consecutive blank lines) was also seen on real PRs. Do not assume MD056 is the only rule that can redden the gate.
- **The required `##` section set is five headers.** `## Overview`, `## When to Use`, `## Verified Workflow`, `## Failed Attempts`, `## Results & Parameters`. `validate_plugins.py` accepts ONLY `## Verified Workflow` — for an unverified/verified-local skill keep that exact header and add a `> Proposed Workflow` warning subtitle under it. A missing header fails `validate` on the PR's own new file.
- **Whole-repo validate.** `validate_plugins.py` sets `SKILLS_DIR = Path("skills")` and lints the ENTIRE dir, so a single broken file already on main reddens every PR's `validate`. Errors in files you did not touch are pre-existing breakage — fix-PR them separately, never claim verified-ci off them.
- **Amend-lock query.** `gh pr list --repo HomericIntelligence/Mnemosyne --state open --search "<name> in:title" --json number,headRefName,title` plus a files-based check. If an open PR already amends the skill, stack on its branch — do not fork main. This is what prevents the ~35-PR DIRTY duplicate cluster.
- **Three attribution classes for a red check.** (a) Your regression: the failure names your change. (b) Pre-existing main breakage: whole-dir tools (`validate_plugins.py`, repo-wide markdownlint) fail in files you did not touch. (c) Commit-ordering artifact: `test_active_guidance_inventory_is_closed` fails with the difference listing exactly your new, uncommitted skill files, because discovery reads the filesystem while the closure side reads `git ls-files`. Class (c) resolves by committing the new files and re-running.
- **Symlink-check noise from environment directories.** `scripts/check-symlinks.sh` scans untracked directories as well; interpreter links under a runner-created `.venv/` (for example from `uv run`) report "symlink escapes repo". Remove the environment directory before the check; CI never sees it.
- **Local validation order (canonical).** (0) section self-check, (1) `markdownlint-cli2 --config .markdownlint.yaml`, (2) `python3 scripts/validate_plugins.py`, (3) `pre-commit run --files <the file>`.
- **verified-ci is observed, not assumed.** Only `gh pr view <PR> --json mergeStateStatus,statusCheckRollup` showing the gate green earns `verified-ci`. A passing local run is `verified-local`.

### Uncertain assumptions / risks (re-check before relying on this)

- **Verified in CI.** Verification level is `verified-ci`: carrier ProjectHephaestus PR #1323 merged 2026-06-14 with its gate green, and Mnemosyne PR #3628 merged 2026-10-29 with the required gate (`required-checks-gate`, `validate` and `markdownlint` jobs SUCCESS) green on the first push of a change authored with the four-step local order. Future upgrades still follow the honesty rule: a claimed gate must be observed green, not inferred.
- **Branch-protection contexts did drift.** `["validate","markdownlint"]` was read at capture time; observed 2026-10-30, the active ruleset `homeric-main-baseline` on `~DEFAULT_BRANCH` requires one context, `required-checks-gate`, whose pipeline contains the `validate` and `markdownlint` jobs (classic branch protection is not configured). Re-confirm with `gh api repos/HomericIntelligence/Mnemosyne/rulesets` before assuming the gate structure; prefer results from the configured `markdownlint-cli2` through the authorized validation process over an inferred pass.
- **markdownlint rule set is config-driven.** `.markdownlint.yaml` disables many rules (MD013, MD022, MD031, MD032, etc.) but NOT MD056 or MD012. If the config changes, re-derive which rules can redden the gate; prefer results from the configured `markdownlint-cli2` through the authorized validation process over an inferred pass.
- **The duplicate-cluster counts (117 PRs, ~35 DIRTY, ~9 / ~14 per skill) were a point-in-time scan.** They illustrate the failure mode, not a stable metric; re-run the amend-lock query for the current open-PR state.

### Related skills

- `ci-markdownlint-all-files-repo-wide-blocks-prs` — the repo-wide markdownlint blast radius (a broken file anywhere reddens unrelated PRs), the analogue of the whole-dir `validate` behavior described here.
- `tooling-stage-only-your-own-files-in-shared-worktree` — staging discipline that keeps a `/learn` commit scoped to your own skill file, complementing the amend-lock.
- `pr-ci-failure-triage-preexisting-vs-introduced` — telling pre-existing main breakage apart from a regression you introduced, the triage step referenced in lesson 5.

## References

- [markdownlint MD056 / table-column-count rule](https://github.com/DavidAnson/markdownlint/blob/main/doc/Rules.md#md056)
- [markdownlint MD012 / no-multiple-blanks rule](https://github.com/DavidAnson/markdownlint/blob/main/doc/Rules.md#md012)
- [markdownlint-cli2 usage and `--config`](https://github.com/DavidAnson/markdownlint-cli2)
- [GitHub: Managing rulesets and required status checks](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets)
