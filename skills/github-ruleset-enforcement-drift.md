---
name: github-ruleset-enforcement-drift
license: BSD-3-Clause
description: "Canonical config file says `evaluate` but live GitHub ruleset is already `active`; idempotent re-apply would silently downgrade enforcement. Use when: (1) flipping a GitHub branch ruleset from evaluate to active mode and the on-disk JSON carries `evaluate`, (2) confirming whether a canonical config file matches its live deployed state before re-applying, (3) preserving a rollback/shadow-test path after the base config file changes enforcement mode, (4) aligning variant apply-target files (e.g. `*-active.json`) that were not updated when the base file was fixed, (5) auditing required_status_checks context strings for the correct bare-name + integration_id form vs stale prefixed form, (6) retiring a duplicate CI policy check only after proving an active branch ruleset still enforces the same invariant on the default branch."
category: ci-cd
date: 2026-07-20
version: "1.1.0"
user-invocable: false
verification: verified-local
history: github-ruleset-enforcement-drift.history
tags: [github, rulesets, branch-protection, enforcement, drift, rollback, evaluate, active, integration_id, required-signatures, ci-policy-retirement, fail-closed]
---

# GitHub Ruleset Enforcement Drift

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-07-20 |
| **Objective** | Keep repository policy aligned with live GitHub rulesets and retire duplicate CI enforcement without opening a protection gap |
| **Outcome** | Existing drift remediation remains verified locally; v1.1.0 adds a fail-closed retirement workflow whose live ruleset precondition was verified locally, while the planned code and workflow changes remain unverified |
| **Verification** | verified-local — the original pre-commit/jq checks passed, and the v1.1.0 Hephaestus ruleset query confirmed an active branch ruleset covering `main` with `required_signatures`; the retirement implementation and CI were not executed |
| **History** | [changelog](./github-ruleset-enforcement-drift.history) |

## When to Use

- A GitHub branch ruleset config file has `"enforcement": "evaluate"` but the live ruleset (queried via `gh api repos/<ORG>/<REPO>/rulesets/<ID>`) reports `"enforcement": "active"` — the file is drifted and an idempotent re-apply would DOWNGRADE the live enforcing state.
- The apply script does a PUT-if-exists (idempotent) — re-applying a stale `evaluate` file when live is `active` silently removes enforcement.
- A runbook's two-phase rollout uses bare script invocation as the "shadow (evaluate) pass", but the script's bare default was changed to `active` — the documented flow is now silently active-then-active.
- A variant file (`*-active.json`, `*-evaluate.json`) was left unedited when the base file was fixed, remaining a live apply path with stale context strings.
- `required_status_checks` context entries use the stale prefixed form (`"Required Checks / lint"`) instead of the canonical bare-name + `integration_id` form (`"lint"` + `"integration_id": 15368`).
- A GitHub Actions job duplicates an invariant already enforced by a live branch ruleset, and you need to remove the duplicate without weakening merge-time policy.
- A retired workflow job name still appears in runtime filtering, documentation, test exemptions, or test-only helpers after the YAML job is removed.

## Verified Workflow

### Quick Reference

```bash
# 1. Check live enforcement vs on-disk (detect drift before re-applying)
RULESET_ID=$(gh api repos/ORG/REPO/rulesets \
  --jq '.[] | select(.name=="homeric-main-baseline") | .id')
LIVE=$(gh api repos/ORG/REPO/rulesets/$RULESET_ID --jq .enforcement)
DISK=$(jq -r .enforcement configs/github/repo-ruleset.json)
echo "live=$LIVE disk=$DISK"
# If live=active and disk=evaluate → file is stale; fix disk to match live.
# If live=evaluate and disk=active → file is ahead; re-apply will activate.

# 2. Confirm context string format from live ruleset (bare vs prefixed)
gh api repos/ORG/REPO/rulesets/$RULESET_ID \
  --jq '.rules[] | select(.type=="required_status_checks") | .parameters.required_status_checks[]'
# Correct form: {"context":"lint","integration_id":15368}
# Stale form:   {"context":"Required Checks / lint"}   ← NO integration_id, wrong prefix

# 3. After flipping base file, create a dedicated evaluate rollback file
cp configs/github/repo-ruleset.json configs/github/repo-ruleset-evaluate.json
# Edit repo-ruleset-evaluate.json to set "enforcement": "evaluate"
# Now rollback is: ./tools/github/apply-repo-rulesets.sh --evaluate

# 4. Verify both canonical files match intended enforcement
jq -e '.enforcement == "active"' configs/github/org-ruleset.json configs/github/repo-ruleset.json
jq -e '.enforcement == "evaluate"' configs/github/repo-ruleset-evaluate.json

# 5. Check all variant files for stale prefixed contexts
jq '[.rules[] | select(.type=="required_status_checks")
     | .parameters.required_status_checks[].context]' configs/github/org-ruleset-active.json
# Any "Required Checks / *" entries are stale — replace with bare names + integration_id

# 6. Verify context count and no non-canonical entries
jq '[.rules[] | select(.type=="required_status_checks")
     | .parameters.required_status_checks[]] | length' configs/github/repo-ruleset.json
# Expected: 8 (not 9 — forbid-suppressions is a workflow job, NOT a required context)

# 7. Before removing duplicate signature validation, prove the live ruleset owns it.
repo=ORG/REPO
default_branch=$(gh api "repos/$repo" --jq .default_branch)
ruleset_id=$(gh api "repos/$repo/rulesets" --paginate --jq '
  .[] | select(.name == "homeric-main-baseline"
    and .target == "branch" and .enforcement == "active") | .id' | head -n 1)
test "$default_branch" = main
test -n "$ruleset_id"
gh api "repos/$repo/rulesets/$ruleset_id" | python3 -c '
import json, sys
r = json.load(sys.stdin)
include = r.get("conditions", {}).get("ref_name", {}).get("include", [])
exclude = r.get("conditions", {}).get("ref_name", {}).get("exclude", [])
assert any(ref in include for ref in ("refs/heads/main", "~DEFAULT_BRANCH", "~ALL"))
assert not any(ref in exclude for ref in ("refs/heads/main", "~DEFAULT_BRANCH", "~ALL"))
assert any(rule.get("type") == "required_signatures" for rule in r.get("rules", []))
'
```

### Detailed Steps

1. **Detect drift before editing.** Query `gh api repos/<ORG>/<REPO>/rulesets/<ID>` to get live `enforcement` and `required_status_checks`. Compare against the on-disk canonical file. If live is `active` and disk says `evaluate`, the file is drifted — flipping the file to `active` closes the regression window; re-applying the stale evaluate file would downgrade enforcement.

2. **Confirm context string format from live state.** The live ruleset tells you the exact form GitHub reports: bare job `name:` values (`"lint"`) with `"integration_id": 15368`, NOT the prefixed `"Required Checks / lint"` form. Use whatever the live ruleset says, not what a KB note or stale file says.

3. **Flip the base canonical file** (`repo-ruleset.json`, `org-ruleset.json`) to `"enforcement": "active"`. Do NOT change context strings in `repo-ruleset.json` if they already match the live enforcing ruleset — only line 4 changes.

4. **Fix ALL variant files** that carry stale context strings or enforcement. Read the apply script to find which file each flag selects: `--active` → `*-active.json`, bare default → base file, `--evaluate` → (after this fix) evaluate file. Each selectable variant must be consistent.

5. **Create a dedicated evaluate file** (`repo-ruleset-evaluate.json`): a copy of the base file with `"enforcement": "evaluate"`. This preserves the shadow-test and rollback path after the base file flips to `active`.

6. **Add an explicit `--evaluate` flag** to the apply script pointing at the new evaluate file. The bare default should now apply the canonical (active) file. Update the usage comment in the script.

7. **Update ALL runbook two-phase rollout examples.** Any runbook section that says "bare invocation = shadow/evaluate pass" is now wrong once the bare default is `active`. Replace bare calls with `--evaluate` explicitly:
   - "Adding a new repo" step 3: use `--evaluate --repos <NewRepo>`
   - "Re-applying to all repos" shadow step: use `--evaluate`
   - Rollback section: use `--evaluate`

8. **Validate all JSON files are syntactically valid** after edits:
   ```bash
   jq empty configs/github/org-ruleset.json configs/github/repo-ruleset.json \
     configs/github/repo-ruleset-evaluate.json && echo OK
   ```

### Ruleset-backed CI policy retirement

> **Warning:** The retirement sequence below is proposed from ProjectHephaestus issue #2330.
> Its live precondition was verified locally on 2026-07-20, but the workflow/runtime edits and
> CI validation were not executed. Treat the sequence as unverified until the implementation PR
> passes CI and the post-edit ruleset query still succeeds.

1. **Name the policy owner before deleting anything.** A workflow check may be removed only when
   another active enforcement layer owns the same invariant. For cryptographic commit signing,
   verify the default branch, named ruleset, branch target, active enforcement, ref include/exclude
   conditions, and the `required_signatures` rule. A matching ruleset name alone is insufficient.
2. **Run the proof twice.** Execute the live precondition immediately before editing and again
   immediately before shipping. If the first check fails, leave the CI check intact. If the final
   check fails, restore the removed workflow query/step and its documentation attribution, then
   stop without shipping.
3. **Remove only the duplicated assertion.** If other checks still need the same fetched metadata,
   preserve that query. For example, removing signature fields from a commit query must not remove
   full commit messages still consumed by Conventional Commit or DCO validation.
4. **Retire the policy across every layer.** Search the workflow job name and checker symbol across
   workflow YAML, runtime coordinators, docs, tests, pre-commit hooks, script inventories, and code
   comments. Delete exact-name filters and policy-only success branches so a former advisory check
   cannot keep bypassing the generic failure/fix path after its job disappears.
5. **Write regression tests against the former special-case name.** A terminal poll should classify
   any failed required check as failing, and the failure handler should route that same name into
   the normal fix flow. Using the retired name in the test proves the old bypass branch is gone.
6. **Do not preserve retired YAML shape as a unit-test API.** Delete tests and test-only helpers
   whose only behavior is parsing repository-owned workflow files. Keep fixture-based tests for
   reusable parsers/helpers and use YAML/schema/security tooling to validate live workflows.
7. **Reassign documentation authority.** Every policy statement should identify the ruleset as the
   merge-time signature authority while retaining CI ownership for independent checks such as PR
   linkage, Conventional Commit subjects, and DCO trailers.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Leave `org-ruleset-active.json` untouched | Fixed `org-ruleset.json` contexts but left `org-ruleset-active.json` with 9 stale prefixed entries | `apply-org-ruleset.sh` accepts the JSON file as an argument — `org-ruleset-active.json` remains a live apply path that would push wrong contexts, re-introducing drift | When fixing context strings, grep for ALL variant files (`*-active.json`, `*-evaluate.json`) and fix every live apply path |
| Change bare default without updating runbook | Apply script bare default changed from evaluate to active, but runbook still called bare invocation as the "evaluate mode shadow pass" | Reviewer caught that the two-phase rollout was now silently active-then-active — shadow step lost | Every time a script flag default changes, audit ALL runbook examples that relied on that bare invocation and update them to use explicit flags |
| Remove `-active.json` variant files to reduce duplication | Prior plan proposed deleting `repo-ruleset-active.json` and `org-ruleset-active.json` as they were now identical to the base | Removing them broke the rollback path and the `--active` flag; the NOGO review flagged scope creep + irreversible delete | Preserve variant files even when they become temporarily identical to the base — they serve as explicit named apply paths; cleanup is a separate issue |
| Use prefixed context form in org-ruleset-active.json | Kept `"Required Checks / lint"` form from the original config | GitHub Actions reports bare job `name:` values (`"lint"`), not workflow-prefixed; contexts without `integration_id` are also unreliable | Always derive context strings from the LIVE ruleset API, not from the config file or KB assumption |
| Remove duplicate CI signature validation after checking only the ruleset name | Assumed an existing `homeric-main-baseline` object protected the default branch | A ruleset can be inactive, target another resource, exclude `main`, or omit `required_signatures`; the workflow removal would silently open a policy gap | Prove default branch, target, enforcement, ref conditions, and rule type before editing and again before shipping; fail closed and restore on final drift |
| Delete an advisory job but keep its exact-name runtime branch | Removed workflow YAML while retaining coordinator logic that treated that name as policy-only success/blocking | The dead name continued to bypass the generic CI fix flow and obscured the real state machine | Search by the exact retired job name across production code and add a regression using that former name to prove generic failure routing |
| Keep unit tests that parse the retired live workflow structure | Preserved tests and a helper whose only contract was the old YAML job inventory | The tests coupled Python code to mutable workflow layout and forced dead policy concepts to survive after deletion | Delete live-tree structural assertions with the policy; retain fixture-based helper behavior and validate live YAML through workflow-native tooling |

## Results & Parameters

**Canonical required_status_checks entry (HomericIntelligence `homeric-main-baseline`):**

```json
{ "context": "lint",                    "integration_id": 15368 }
{ "context": "unit-tests",              "integration_id": 15368 }
{ "context": "integration-tests",       "integration_id": 15368 }
{ "context": "security/dependency-scan","integration_id": 15368 }
{ "context": "security/secrets-scan",   "integration_id": 15368 }
{ "context": "build",                   "integration_id": 15368 }
{ "context": "schema-validation",       "integration_id": 15368 }
{ "context": "deps/version-sync",       "integration_id": 15368 }
```

**Count:** 8 required contexts. `forbid-suppressions` is a 9th workflow job intentionally NOT a required context. If runbook or docs say "9 contexts", they are counting workflow jobs, not required contexts — correct them against the live ruleset length.

**Apply script flag → JSON file mapping (post-fix):**

| Flag | JSON file | Enforcement |
|------|-----------|-------------|
| (none / bare) | `repo-ruleset.json` | `active` (canonical) |
| `--active` | `repo-ruleset-active.json` | `active` |
| `--evaluate` | `repo-ruleset-evaluate.json` | `evaluate` (rollback/shadow) |

**Org endpoint note:** `gh api orgs/<ORG>/rulesets` returns 404 on the GitHub free plan (requires `admin:org`). Per-repo rulesets (`repos/<org>/<repo>/rulesets`) are the enforcing path and work on the free plan. Do not designate `org-ruleset.json` as an activation path or include an org-endpoint verification command.

**Live-state comparison (verification commands):**

```bash
# On-disk vs live enforcement — must match after fix
test "$(jq -r .enforcement configs/github/repo-ruleset.json)" = \
     "$(gh api repos/ORG/REPO/rulesets/$RULESET_ID --jq .enforcement)" && echo OK

# Context count must be 8
test "$(jq '[.rules[] | select(.type=="required_status_checks")
             | .parameters.required_status_checks[]] | length' \
        configs/github/repo-ruleset.json)" = 8 && echo OK

# Rollback file must say evaluate
jq -e '.enforcement == "evaluate"' configs/github/repo-ruleset-evaluate.json
```

### Ruleset-backed signature authority evidence

| Field | ProjectHephaestus observation on 2026-07-20 |
|-------|---------------------------------------------|
| Default branch | `main` |
| Ruleset | `homeric-main-baseline` (ID `15556494`) |
| Target and enforcement | `branch`, `active` |
| Ref condition | Includes `refs/heads/main`; exclusion list empty |
| Relevant rule | `required_signatures` present |
| Retirement implementation | Unverified — the live Hephaestus tree still contained the duplicate workflow signature step, `auto-merge-policy`, runtime special cases, and the tag-coupled security hook at capture time |

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| HomericIntelligence/Odysseus | PR #307, issue #177, 2026-06-19 | Flipped `repo-ruleset.json` and `org-ruleset.json` to `active`; fixed `org-ruleset-active.json` prefixed contexts; added `repo-ruleset-evaluate.json`; added `--evaluate` flag; updated runbook two-phase rollout |
| HomericIntelligence/Hephaestus | Issue #2330 planning record, 2026-07-20 | Live precondition verified locally: default `main`, active branch ruleset `15556494`, `refs/heads/main` included, no exclusions, and `required_signatures` present. Proposed CI/runtime/test cleanup was not implemented or CI-verified. |
