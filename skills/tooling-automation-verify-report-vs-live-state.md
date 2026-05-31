---
name: tooling-automation-verify-report-vs-live-state
description: "Automation tools' headline summaries are observation reports, not ground truth: a `Driven: 8 / Failed: 4` banner can be technically true (the driver was invoked) AND operationally misleading (the driver was architecturally blind to the work that actually needed doing). NEVER conclude a run succeeded just because the script's `_summary.json` says so. Always cross-check live GitHub state per repo (`gh pr list --state open ...`, `gh pr view <pr> --json state,mergedAt,commits`) BEFORE reporting success. The script reports what it observed; what it observed may have been gated by a `Closes #<open-issue>` filter, an `@me` author scope, a `--limit` cap, or a done-gate that fires on noise. Use when: (1) consuming output from `drive-prs-green-ecosystem.sh` / any ecosystem-wide driver / loop runner, (2) about to tell a user 'all repos are green', (3) the run summary disagrees with what you can see in the GitHub UI, (4) a 'Failed' classification feels suspicious (the most-successful repo can be marked failed because of a done-gate firing on Dependabot noise), (5) building or reviewing the verification protocol for any automation that reports per-repo rc codes."
category: tooling
date: 2026-05-31
user-invocable: false
verification: verified-ci
version: "1.0.0"
tags:
  - automation-honesty
  - trust-but-verify
  - cross-check-live-state
  - drive-prs-green
  - audit-automation-report
  - ground-truth-check
  - architecturally-blind
  - dependabot-flood
  - done-gate
  - reality-vs-claim
  - headline-summary
---

# Verify Automation Tool Reports Against Live GitHub State Before Reporting Success

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-05-31 |
| **Objective** | Stop treating an automation tool's headline summary (`Driven: 8`, `Failed: 4`, `_summary.json`) as ground truth. Force a per-repo cross-check against live GitHub state (`gh pr list`, `gh pr view --json state,mergedAt,commits`) BEFORE reporting success, so architecturally-blind reporting and false-failure noise are caught before the user is told the run succeeded. |
| **Outcome** | Caught a `drive-prs-green-ecosystem.sh` run that reported `Driven: 8 / Failed: 4` while 7 of the 8 "Driven" repos had 0 in-scope PRs (16+ open Dependabot PRs ignored) and 3 of the 4 "Failed" were honest done-gate firings (with one of the "failed" repos having actually shipped a merged fix 29 seconds after the run window ended). The verification protocol itself was the workflow used to find the honesty gaps that became merged PR #849 in ProjectHephaestus. |
| **Verification** | verified-ci — the verification procedure itself was applied live (run `20260531T190615Z`) and surfaced the gaps that became merged PR #849. |

## When to Use

Trigger phrases that should hit this skill:

- "verify automation report"
- "trust but verify"
- "cross-check live state"
- "script lied about success"
- "drive-prs-green not actually driving"
- "audit automation report"
- "honest automation"
- "ground-truth check"
- "reality vs claim"
- "the report says Driven but nothing happened"
- "Failed repo actually merged a fix"
- "automation summary is misleading"

Trigger situations:

- A user or operator just ran `drive-prs-green-ecosystem.sh`, the loop runner, or any ecosystem-wide automation and you are about to report back what happened. Do NOT report from `_summary.json` alone.
- The run summary says `Driven: N` but you have not yet verified that any of those N repos had in-scope PRs. The driver may have been invoked against an empty filter.
- The run summary says `Failed: M` and you are about to escalate. Verify that the failure is real (an agent crashed, a push failed, an unrecoverable conflict) and not a done-gate firing on Dependabot noise.
- The script's own header comment documents a scope restriction (e.g. "issue-driven discovery only: PRs without `Closes #<open-issue>` are invisible"). The summary will hide everything outside that scope; you must surface it.
- You are reviewing the design of any automation that reports rc codes per unit (repo, PR, issue). Ask: "what could be true that this rc=0 / rc=1 would hide?"
- A repo's `gh pr list --state open` output (live) and the run log's per-repo summary disagree on what PRs exist. The live state is correct; the log is observing through a filter.

## Verified Workflow

### Quick Reference

The single bash snippet below runs the full cross-check across the repos a run touched and prints a Reality vs Claim table. Run it AFTER any ecosystem-wide automation invocation, BEFORE reporting success.

```bash
#!/bin/bash
# Reality-vs-Claim cross-check for an automation run.
# Inputs:
#   RUN_LOG_DIR — directory containing _summary.json + per-repo logs
#   ORG         — GitHub org (e.g. HomericIntelligence)
#   DRIVEN_REPOS, FAILED_REPOS — space-separated lists from the summary banner
set -euo pipefail

RUN_LOG_DIR="${1:-/tmp/drive-green-runs/$(ls -1t /tmp/drive-green-runs | head -1)}"
ORG="${ORG:-HomericIntelligence}"

# 1. Trust nothing. Pull the summary the script claims.
echo "=== Headline summary ==="
cat "${RUN_LOG_DIR}/_summary.json" 2>/dev/null || echo "(no _summary.json)"

# 2. For EVERY repo the script claims "Driven", query live state.
echo ""
echo "=== Reality vs Claim (Driven repos) ==="
printf "%-28s %-10s %-10s %s\n" "REPO" "CLAIM" "OPEN_PRS" "VERDICT"
for r in ${DRIVEN_REPOS:-}; do
  open_count=$(gh pr list --repo "${ORG}/${r}" --state open \
                 --json number -L 100 --jq 'length' 2>/dev/null || echo "?")
  if [ "${open_count}" = "0" ]; then
    verdict="HONEST (idle)"
  else
    # Check if the open PRs are Dependabot (architecturally blind to issue-driven discovery)
    deps=$(gh pr list --repo "${ORG}/${r}" --state open \
             --json author -L 100 --jq '[.[] | select(.author.login | test("dependabot"; "i"))] | length' 2>/dev/null || echo 0)
    if [ "${deps}" = "${open_count}" ] && [ "${deps}" -gt 0 ]; then
      verdict="MISLEADING (${deps} Dependabot PRs unseen)"
    else
      verdict="REVIEW (${open_count} open, ${deps} Dependabot)"
    fi
  fi
  printf "%-28s %-10s %-10s %s\n" "${r}" "Driven" "${open_count}" "${verdict}"
done

# 3. For EVERY repo the script claims "Failed", classify the failure mode.
echo ""
echo "=== Reality vs Claim (Failed repos) ==="
for r in ${FAILED_REPOS:-}; do
  log="${RUN_LOG_DIR}/${r}.log"
  if [ ! -f "${log}" ]; then echo "${r}: (no per-repo log)"; continue; fi
  cat <<EOF
--- ${r} ---
$(grep -nE "Found .* PR.*drive|pushed CI fixes|agent session produced no new commit|open PR.s. remain|Repo not done" "${log}" | head -10)
EOF
  # If the log shows "pushed CI fixes", verify the push actually landed.
  pushed_pr=$(grep -oE "PR #[0-9]+" "${log}" | head -1 | tr -d 'PR #')
  if [ -n "${pushed_pr}" ]; then
    echo "  Verifying claimed-pushed PR #${pushed_pr}:"
    gh pr view "${pushed_pr}" --repo "${ORG}/${r}" \
      --json state,mergedAt,closedAt 2>/dev/null \
      | jq -r '"    state=\(.state) mergedAt=\(.mergedAt) closedAt=\(.closedAt)"'
  fi
done
```

### Detailed Steps

The four queries that, together, reduce an automation summary to ground truth.

#### Step 1 — Pull the summary the script wrote

```bash
cat <run-log-dir>/_summary.json
```

The summary is the script's self-report. Read it, then suspect every field. Banner fields are derived from rc codes per unit, and rc=0 / rc=1 can be set by gates that fire on noise.

#### Step 2 — For EVERY "Driven" repo, query live open PRs

```bash
for r in $DRIVEN_REPOS; do
  gh pr list --repo HomericIntelligence/$r --state open \
    --json number,title,headRefName,author,mergeStateStatus -L 100
done
```

"Driven" means the driver was invoked. It does NOT mean it had work in scope. If the live count of open PRs is non-zero but the per-repo log shows `No open PRs found for the specified issues — nothing to drive`, the driver was architecturally blind. The most common blindness: PRs without `Closes #<open-issue>` are invisible to issue-driven discovery (Dependabot is the canonical example).

For very large open-PR sets, `--limit 100` itself is a hard cap; use `gh api --paginate /repos/$ORG/$r/pulls?state=open&per_page=100` for an unbounded enumeration. See the related skill `tooling-gh-pr-list-limit-cap-use-api-paginate`.

#### Step 3 — For every PR the log claims was "pushed", verify the head commit

```bash
gh pr view <pr> --repo <repo> --json headRefOid,commits --jq \
  '.commits[-3:] | .[] | "\(.oid[:10]) \(.authoredDate) \(.messageHeadline)"'
```

"Pushed CI fixes" in a log line does not guarantee the commit landed on the PR head. Read the last few commits and confirm the timestamp falls inside the run window AND the messageHeadline matches what the agent claimed it pushed.

#### Step 4 — For every PR that disappeared from open-PRs since the run, verify it merged

```bash
gh pr view <pr> --repo <repo> --json state,mergedAt,closedAt
```

A PR can disappear from the open-PR set during a run for three reasons: it merged, it was closed without merge, or it was renamed/moved (rare). Distinguish these. A repo marked `Failed` can still have shipped a merged fix — the failure was the done-gate firing on remaining unrelated noise (e.g. one Dependabot PR), not the agent's actually-driven PR.

Example, verbatim, from the session that produced this skill:

```text
$ gh pr view 246 --repo HomericIntelligence/ProjectTelemachy \
    --json state,mergedAt,closedAt,number
{"closedAt":"2026-05-31T19:11:39Z","mergedAt":"2026-05-31T19:11:39Z","number":246,"state":"MERGED"}
```

The repo was in the `Failed` list. The PR was MERGED 29 seconds after the run reported the failure. The "failure" was a `#839`-class done-gate firing because 1 Dependabot PR remained.

#### Step 5 — For every "Failed" repo, classify the failure mode from its log

```bash
grep -nE "Found .* PR.*drive|pushed CI fixes|agent session produced no new commit|open PR.s. remain|Repo not done" <repo-log>
```

There are at least four failure-mode categories, and they look the same in the summary banner. Decompose:

| Category | Log signature | Real failure? |
|----------|---------------|---------------|
| Done-gate fired on noise | `open PR(s) remain` / `Repo not done` after a successful drive | NO — repo shipped, just not "clean" |
| Driver had nothing in scope | `Found 0 PR(s) to drive` while `gh pr list` is non-empty | NO — architecturally blind |
| Agent session produced no new commit | `agent session produced no new commit` | MAYBE — could be honest noop or genuine bug |
| Push failed / agent crashed | exit code != 0 from the agent itself, no `pushed CI fixes` line | YES — real failure |

Only the last (and sometimes the third) row is a real failure. The first two are reporting noise that the banner cannot distinguish.

#### Step 6 — Produce the Reality vs Claim table and report THAT, not the banner

The deliverable to the user is the table from Step 2 + the classification from Step 5, not `_summary.json`. The headline summary belongs in an appendix, labelled "raw script output", not in the lede.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Trust the summary banner | Read `Summary: Driven 8 / Failed 4` from `_summary.json` and reported success | "Driven" only means "the driver was invoked", not "PRs reached green". 7 of 8 "Driven" repos had 0 in-scope PRs (16+ open Dependabot PRs the driver could not see). The headline hid the architectural blindness. | Always decompose "Driven" by joining the per-repo log with live `gh pr list` state. Banner counts are observation reports, not ground truth. |
| Trust per-repo `rc=0` | Trusted `exit 0` from each per-repo invocation to mean "done" | `rc=0` means "nothing to drive given the filter". That is honest when the repo is genuinely idle (0 open PRs) and misleading when the filter is blind (16 Dependabot PRs invisible to issue-driven discovery). Same rc, opposite reality. | `rc=0` + non-empty live `gh pr list --state open` = misleading "done". Always pair the rc with a live PR count. |
| Trust the per-repo "Successful: N" count in the log | Saw `Successful: 1` in a per-repo log and reported that as the truth for the repo | A 1-issue success can be honest (the issue's PR actually pushed CI fixes and merged) but the repo can still have N unrelated open PRs the script never even tried to touch. The "Successful: 1" is a count of in-scope work completed, not a count of repo health. | Cross-reference each log-claimed `pushed CI fixes` against `gh pr view <pr> --json commits` to verify the pushed commit actually landed AND against `gh pr list --state open` to surface unrelated open PRs. |
| Believe the "Failed" classification at face value | Read `Failed: ProjectTelemachy` and assumed something broke | The "failure" was a `#839`-class done-gate firing because 1 Dependabot PR remained. The actually-driven PR #246 had already MERGED 29 seconds earlier (`mergedAt: 2026-05-31T19:11:39Z`). The "failed" repo was the most successful repo in the run. ProjectOdyssey PRs #5468 and #5473 also merged after the run ended. | A repo can be simultaneously `rc=1 from the done-gate` AND `actually shipped a merged fix in this run`. Classify each "Failed" by failure mode (table in Step 5) before reporting. |

## Results & Parameters

### Verification matrix — the session that produced this skill

Run: `drive-prs-green-ecosystem.sh` invocation `20260531T190615Z`.

Banner: `Driven: ProjectHephaestus Odysseus AchaeanFleet ProjectAgamemnon ProjectProteus ProjectArgus ProjectCharybdis ProjectHermes` (8 repos) / `Failed: 4 repos`.

Decomposed Reality vs Claim:

| Repo | Banner | Open PRs (live) | Dependabot PRs ignored | Verdict |
|------|--------|-----------------|------------------------|---------|
| ProjectHephaestus | Driven | 0 | 0 | HONEST (genuinely idle) |
| Odysseus | Driven | 5 | 5 | MISLEADING (architecturally blind) |
| ProjectAchaeanFleet | Driven | 11 | 11 | MISLEADING (architecturally blind) |
| ProjectAgamemnon | Driven | 1 | 1 | MISLEADING (architecturally blind) |
| ProjectProteus | Driven | 4 | 4 | MISLEADING (architecturally blind) |
| ProjectArgus | Driven | 3 | 3 | MISLEADING (architecturally blind) |
| ProjectCharybdis | Driven | 5 | 5 | MISLEADING (architecturally blind) |
| ProjectHermes | Driven | 5 | 5 | MISLEADING (architecturally blind) |
| ProjectTelemachy | Failed | (post-run: open) | n/a | FALSE FAILURE (PR #246 merged 19:11:39Z, 29s after the run) |
| ProjectOdyssey | Failed | (post-run: open) | n/a | FALSE FAILURE (PRs #5468 and #5473 merged after run) |
| (3rd Failed) | Failed | n/a | n/a | FALSE FAILURE (done-gate noise) |
| ProjectNestor | Failed | n/a | n/a | REAL FAILURE (4 no-commit issues — genuine agent bug) |

Summary: 7 of 8 "Driven" were misleading, 3 of 4 "Failed" were false failures, 1 of 4 "Failed" was a real agent bug. The headline `Driven: 8 / Failed: 4` mapped to ground truth `1 honest-idle + 7 architecturally-blind / 1 real-bug + 3 false-failures`. The honesty gaps surfaced by this audit became merged PR #849 in ProjectHephaestus.

### Why "Driven" can hide everything — the script's own header comment

The driver's own header documents the architectural blindness:

```bash
# drive-prs-green-ecosystem.sh, line 12:
#   issue-driven discovery only: PRs without `Closes #<open-issue>` are invisible.
```

Dependabot PRs do not carry `Closes #<issue>` lines. They are therefore invisible to issue-driven discovery by design. The banner `Driven: 8` is consistent with this design; it just does not mean what a reader of the banner would naturally think it means.

### Why "Failed" can hide success — the `#839` done-gate

The `is_repo_done` check is the gate that lets the automation loop exit. It returns `rc=1` if ANY open PR remains, including Dependabot PRs the driver was never going to touch. So a repo that:

1. Drove its in-scope PR successfully (e.g. `Telemachy #246` pushed at 19:11:10Z),
2. The PR merged (e.g. `Telemachy #246` merged at 19:11:39Z),
3. But had 1 Dependabot PR remaining at the moment the done-gate ran,

will be reported `Failed` in the banner despite being the most-successful repo in the run.

### Failure-mode classification table (use in Step 5)

| Failure mode | Banner | Real failure? | Action |
|--------------|--------|---------------|--------|
| Done-gate fired on noise (`open PR(s) remain` / `Repo not done`) | Failed | No | Report as `done-gate-noise`, link to `#839` |
| Driver had nothing in scope (`Found 0 PR(s) to drive`) | Driven or Failed | No | Report as `architecturally-blind`, surface ignored PR count |
| Agent session produced no new commit | Failed | Maybe | Inspect the agent log; could be honest no-op or real bug |
| Push failed / agent crashed (no `pushed CI fixes` line, exit != 0) | Failed | Yes | Escalate; this is the only category that warrants escalation |

### Cost comparison — verification time vs wasted-trust cost

| Approach | Time | Risk |
|----------|------|------|
| Trust the banner | ~5s (read `_summary.json`) | HIGH — user is told a misleading story; downstream decisions are wrong |
| Step 1 only (banner + classify rc codes) | ~30s | HIGH — same banner blindness |
| Step 1 + Step 2 (cross-check open PRs per repo) | ~2 min for 12 repos | LOW — catches architectural blindness |
| Full Step 1–5 | ~5 min for 12 repos | NEGLIGIBLE — catches false failures and verifies pushed commits |

5 minutes of verification saves the reporting-back-a-lie failure mode entirely.

### Related skills

- `tooling-gh-pr-list-limit-cap-use-api-paginate` — same shape of "the report you read is not the truth": `gh pr list --limit N` is a hard cap, not a page size, so a "no remaining PRs" check can silently pass with N+ items still open. Use `gh api --paginate /repos/.../pulls?state=open&per_page=100` for unbounded enumeration when Step 2 above has to enumerate every PR.
- `verify-audit-findings-before-acting` — the audit-finding analogue of this skill: strict-mode audit reports also lie (3 of 11 majors hallucinated in one session). Same discipline (verify each finding against the filesystem) at the consume-an-audit-report layer.
- `tooling-hephaestus-automation-loop-drive-green-broken-design` — documents the FOUR design bugs in `drive-green` that produce the `SKIP no open issues` blindness this skill cross-checks against. Read for the WHY behind the architectural blindness; read THIS skill for the verification protocol.
- `ci-cd-verify-merged-prs-end-to-end` — the merged-PR analogue: closing an umbrella issue requires actually running the composed artifacts, not assuming N green PRs compose. Same "merged ≠ verified" discipline at the umbrella-issue layer.

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| ProjectHephaestus | Live `drive-prs-green-ecosystem.sh` run `20260531T190615Z` against 12 repos in HomericIntelligence org | Banner `Driven: 8 / Failed: 4` decomposed via the protocol above into `1 honest-idle + 7 architecturally-blind / 1 real-bug + 3 false-failures`. Verified `Telemachy PR #246` merged at `2026-05-31T19:11:39Z` (29s after the run reported the repo failed) via `gh pr view 246 --repo HomericIntelligence/ProjectTelemachy --json state,mergedAt,closedAt`. The honesty gaps surfaced became merged PR #849 in ProjectHephaestus. |
