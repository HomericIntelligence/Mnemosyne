---
name: scanner-alerts-to-github-issues-pipeline
description: "Disciplined, scanner-grounded pipeline for a cross-repo security & quality audit: collect a repo's own hosted GitHub scanner alerts (code-scanning + Dependabot), verify each on live origin/main, dedup against the existing issue backlog, cluster by rule, and file one detailed GitHub issue per verified (rule x repo) cluster. Use when: (1) asked to analyze many repos for security/quality and file a GitHub issue per distinct real finding, (2) triaging GitHub-hosted CodeQL/Semgrep/Trivy code-scanning and Dependabot alerts rather than free-form LLM code-reading, (3) filtering scanner false positives (vendored-dep CVEs, docs example keys, stale alerts) before filing, (4) needing the finding source to be the repo's own scanner alerts, not an LLM swarm's claims."
category: tooling
date: 2026-07-16
version: "1.0.0"
user-invocable: false
verification: verified-local
tags: []
---

# Scanner Alerts to GitHub Issues Pipeline

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-07-16 |
| **Objective** | Analyze all repos for security & quality and file a detailed GitHub issue per distinct issue — using the disciplined, scanner-GROUNDED approach (the repo's own hosted scanner alerts as the finding source), not free-form LLM code-reading. |
| **Outcome** | Successful cross-repo audit of 15 HomericIntelligence submodules: 11 verified, deduped issues filed after filtering scanner false positives (vendored-dep CVEs, docs example keys, stale alerts). |
| **Verification** | verified-local (11 issues were actually filed and verified to exist; this is a process skill, not CI-gated) |

## When to Use

- You are asked to "analyze all repos for security & quality and file a detailed GitHub issue per distinct issue."
- You want a scanner-GROUNDED audit — the finding SOURCE is the repo's own GitHub-hosted scanner alerts (CodeQL/Semgrep/Trivy/plugin-scanner SARIF via code-scanning, plus Dependabot), not an LLM reading code free-form.
- You are triaging hosted code-scanning + Dependabot alerts across many repos and must dedup against an existing issue backlog before filing.
- You need to filter the recurring scanner false-positive buckets (vendored-dep CVEs, docs example keys, stale-but-open alerts) before creating issues.
- You want one issue per verified (rule x repo) cluster with note-level noise rolled up, not one issue per raw alert.

This is distinct from `repo-audit-triage-fix-and-issue-workflow` (which triages `/repo-analyze-strict-full` SWARM output). There the finding source is an LLM swarm; here it is the repo's own hosted scanner alerts — a different search surface, so a different pipeline. See `[[repo-audit-triage-fix-and-issue-workflow]]` for the swarm-output variant.

## Verified Workflow

### Quick Reference

Group alerts by rule+severity to see the real clusters before filing:

```bash
gh api --paginate "repos/<o>/<r>/code-scanning/alerts?state=open&per_page=100" | jq -s add > a.json
jq -r 'group_by(.tool.name+"|"+.rule.id)[] | "\(length)x sec=\(.[0].rule.security_severity_level // "-") [\(.[0].tool.name)] \(.[0].rule.id)"' a.json | sort
```

### Pipeline

#### 1. COLLECT — pull the repo's own open scanner alerts

```bash
gh api --paginate "repos/<owner>/<repo>/code-scanning/alerts?state=open&per_page=100"
gh api --paginate "repos/<owner>/<repo>/dependabot/alerts?state=open&per_page=100"
```

- `code-scanning/alerts` covers CodeQL / Semgrep / Trivy / plugin-scanner SARIF uploads.
- A `404 "no analysis found"` from `code-scanning/alerts` means the repo has NO code scanning
  configured. That 404 IS a finding — especially for an externally-facing service.
- Secret-scanning API is often disabled; don't block on it. The token needs only `repo` scope
  for code-scanning + Dependabot.

#### 2. VERIFY on LIVE origin/main

A `path:line` in an alert is a CLAIM, not a fact. Fetch the current source and confirm the
finding still reproduces:

```bash
gh api repos/<r>/contents/<path>?ref=HEAD
```

Roughly **13%** of findings don't survive this verify step (fixed-but-not-rescanned, moved code,
or the flagged line is benign on inspection). Drop what doesn't reproduce.

#### 3. DEDUP — against the existing issue backlog

```bash
gh issue list --repo <r> --state all --search "<rule/keywords>"
```

Skip anything already filed, including anything already covered by an existing audit taxonomy
(for example `severity:*` or `audit-finding` labels). Search open AND closed.

#### 4. CLUSTER + FILE — one issue per verified (rule x repo) cluster

- File one issue per verified (rule x repo) cluster, listing every affected `path:line`.
- AGGREGATE low-severity note-level noise into ONE rollup issue per repo — do not file per-note.
- Confirm each created issue number from the `gh issue create` output. NEVER invent a `#N`.

```bash
gh issue create --repo <r> --title "..." --body "..." --label "..."
```

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Trust a HIGH `private-key` Trivy alert | Treated 5 HIGH private-key alerts in Odyssey as leaked secrets | The path was `/app/.pixi/.../site-packages/cryptography/docs/...` — example keys in the cryptography LIBRARY'S OWN DOCS inside a scanned container image, not a real secret leak | Check the path before trusting a private-key alert; example keys in a vendored library's docs are not a leak |
| File all Trivy CVE alerts as repo bugs | Planned to file ~180 CVEs across repos as issues | They were in `usr/local/lib/.../node_modules/...` and `site-packages/...` — CONTAINER BASE-IMAGE + transitive deps, not declared deps; already tracked/allowlisted | Skip mass-filing base-image and transitive CVEs; only declared-dependency CVEs are actionable repo bugs |
| File the dashboard path-injection finding | CodeQL still showed 7 open path-injection alerts, so planned to file them | The fix already landed (a closed-COMPLETED issue existed and `safe_path()` was on live main); the alerts were STALE, never re-scanned | Check close-state AND live source; distinguish a 'stale alert' from a 'live bug' before filing |
| One issue per alert | Considered filing one GitHub issue per raw scanner alert | Would flood trackers with 100s of dupes — a repo already had a 'Close duplicate audit findings' cleanup issue | Cluster by rule, roll up note-level findings, and dedup against open + closed issues first |
| Trust a sub-agent's claimed issue `#N` | Accepted a swarm agent's reported issue number to satisfy a `Closes-#N` policy | Swarm agents may fabricate issue numbers to satisfy the policy | Re-list `author:@me` and confirm each number actually exists after filing |

## Results & Parameters

### Collect / verify / dedup / file commands

See the Pipeline above. Core loop per repo:

```bash
# COLLECT
gh api --paginate "repos/<o>/<r>/code-scanning/alerts?state=open&per_page=100" | jq -s add > a.json
gh api --paginate "repos/<o>/<r>/dependabot/alerts?state=open&per_page=100"
# VERIFY
gh api repos/<r>/contents/<path>?ref=HEAD
# DEDUP
gh issue list --repo <r> --state all --search "<rule/keywords>"
# FILE (confirm the returned #N)
gh issue create --repo <r> --title "..." --body "..." --label "..."
```

### Label mapping

Map CodeQL severity to the repo's issue labels — but repos vary, so always check first:

| CodeQL security severity | Issue label |
| -------------------------- | ------------- |
| critical | `critical` |
| high | `severity:major` |
| medium | `severity:minor` |

Some repos lack a bare `security` label and use `section-8-security` instead. Run
`gh label list --repo <r>` before `gh issue create` so the `--label` values exist.

### Outcome (2026-07-16 cross-repo audit)

15 repos surveyed → **11 verified, deduped issues filed**:

| Repo | Issues |
| ------ | -------- |
| Odyssey | #5629, #5630, #5631 |
| Nestor | #130, #131 |
| Keystone | #612, #613 |
| Agamemnon | #454 |
| Hephaestus | #2255 |
| Hermes | #723 |
| Scylla | #2052 |

The vendored-`_deps` CodeQL false-criticals were handled separately — see the
`codeql-exclude-vendored-deps-false-criticals` skill.

### Authoring notes

- Escape literal `|` inside table cells as `\|`.
- Run markdownlint locally before committing: `npx --yes markdownlint-cli2 --config .markdownlint.yaml skills/scanner-alerts-to-github-issues-pipeline.md`.
</content>
</invoke>
