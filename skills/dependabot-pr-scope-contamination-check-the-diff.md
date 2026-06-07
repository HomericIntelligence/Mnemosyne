---
name: dependabot-pr-scope-contamination-check-the-diff
description: "Before reviewing a Dependabot PR, always run `gh pr diff --name-only` and inspect the commit list. Dependabot PRs frequently arrive contaminated with lockfile-format upgrades or maintainer fixup commits that the title doesn't mention. The title describes the bot's intent; the actual diff may include unrelated cascades. Use this skill when reviewing ANY bot-authored PR to avoid landing surprises. Pattern A: silent lockfile/format upgrades (e.g. pixi.lock v6→v7, 226 add/228 del on a 4-line npm bump). Pattern B: maintainer fixup commits stacked on the bot branch (12 unrelated files added by a `fix: Address CI failures for PR #N` follow-up). Mandatory phase-1 scope check before any verdict: enumerate the actual file scope, count and attribute commits, and REQUEST_CHANGES if scope doesn't match the title."
category: ci-cd
date: 2026-05-31
version: "1.0.0"
user-invocable: false
verification: verified-local
tags:
  - dependabot
  - pr-review
  - scope-bloat
  - lockfiles
  - supply-chain
  - phase-1-verification
  - bot-prs
  - srp-violation
  - pixi-lock
  - maintainer-fixup
---

# Dependabot PR Scope Contamination — Check the Diff Before Any Verdict

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-05-31 |
| **Objective** | Stop the silent failure mode where a reviewer approves a Dependabot PR based on its title (which describes the BOT'S INTENT) and accidentally lands a lockfile format upgrade or a maintainer-fixup pile-on that the title never mentioned. Prescribe a mandatory phase-1 scope check (`gh pr diff --name-only` + commit-author enumeration) BEFORE any reviewer verdict. |
| **Outcome** | Two of 11 Dependabot PRs reviewed in the 2026-05-31 HomericIntelligence/AchaeanFleet session were flagged REQUEST_CHANGES specifically because the file scope didn't match the title. Without the phase-1 scope check, both would have shipped — one carrying a silent pixi.lock format upgrade (v6→v7), the other carrying 12 unrelated files (issue templates, CI YAML, test files) stacked on a 1-line Dockerfile digest bump. |
| **Verification** | verified-local — caught 2/11 PRs in one review session (18% contamination rate). Both PRs were independently confirmed contaminated by reading the diff name list and re-walking the commit log; the contamination was not present in either PR's title. |
| **History** | New skill — no amendments yet. |

## When to Use

- Reviewing ANY bot-authored PR (Dependabot, Renovate, Lychee, Sweep, etc.) — `user.type == "Bot"` per `architecture-bot-pr-discovery-synthetic-issue-key.md`.
- About to give an `APPROVE` verdict on a "small" dependency bump where the only thing you read was the title.
- Reviewing a batch of bot PRs (e.g. dependabot weekly sweep) where pattern recognition tempts you to skip per-PR scope checks.
- A bot PR has been open >24h and you suspect a maintainer pushed a fixup commit onto the bot's branch.
- `gh pr checks N` shows a red check whose name does not relate to anything in the PR title (e.g. `pixi-check` failing on a `/dagger` npm bump).
- About to merge a Dependabot PR via auto-merge — verify the scope NOW, because once auto-merge fires the contamination ships.
- An audit / review request asks "should this dependency bump land?" — the answer requires reading the diff scope, not the title.
- A bot PR has more than 1 commit, or any commit author other than the bot itself.

## Verified Workflow

### Quick Reference

```bash
# Phase 1: scope check — MANDATORY before any verdict on a bot PR.
N=691
REPO=HomericIntelligence/AchaeanFleet

# 1. Title + commit-author enumeration.
gh pr view $N --repo $REPO --json title,baseRefOid,headRefOid,commits --jq \
  '"title: \(.title)\nbase: \(.baseRefOid[0:8]) head: \(.headRefOid[0:8])\ncommits:\n" + ([.commits[] | "  \(.oid[0:8]) by \(.authors[0].login) \(.messageHeadline)"] | join("\n"))'

# 2. Actual file scope — the ground truth.
gh pr diff $N --repo $REPO --name-only

# 3. Per-file shape — catch large adds/dels even when the file name LOOKS in-scope.
gh pr diff $N --repo $REPO | git apply --numstat -

# Decision tree:
#   - commits-list length > 1     → Pattern B candidate; check commit authors
#   - any commit author != bot    → Pattern B confirmed; REQUEST_CHANGES
#   - diff names include lockfile NOT named by the bump's natural scope → Pattern A
#   - per-file numstat shows 200+ lines on a file the title doesn't mention → Pattern A
```

### Detailed Steps

#### The trap: the title is the bot's intent, not the actual change

Dependabot writes a PR title like `chore(dagger): bump @types/node from 25.6.0 to 25.9.1 in /dagger`. That title describes one thing: "I am bumping `@types/node` inside the `/dagger` subtree". The title is the BOT'S INTENT. It is not, and cannot be, a description of the PR's actual file scope.

Between the title being written and your review happening, two things can mutate the PR:

1. **A lockfile-format cascade.** When Dependabot updates one dependency, the resolver re-writes lockfiles using whatever version of the lockfile tool is now installed on the runner. If the lockfile tool itself bumped its format version since the last solve, the lockfile gets a silent format upgrade — `pixi.lock` v6 → v7, `package-lock.json` v2 → v3, `poetry.lock` v1 → v2. The bot doesn't mention this in the title because the bot doesn't know it happened — the format upgrade was a side effect of the resolver, not of the dependency change.
2. **A maintainer fixup commit.** A repo maintainer sees the bot PR is red in CI, force-pushes a "fix CI failures" commit onto the bot's branch, and the PR now contains 12 files of unrelated work bolted onto the 1-line bump. The title is unchanged. The PR is now a multi-purpose change: dependency bump + CI fix + whatever else the maintainer threw in.

The reviewer's job in both cases is to refuse the verdict until the scope matches the title. A scope mismatch on a bot PR is a SOLID-SRP violation (Single Responsibility Principle): a "bump @types/node" PR is one responsibility, a "pixi.lock format upgrade" PR is another responsibility, a "fix CI" PR is a third. They cannot share a PR.

#### Pattern A — silent lockfile/format upgrades

**Concrete case from the 2026-05-31 session:** PR #691 (`HomericIntelligence/AchaeanFleet#691`) was titled `chore(dagger): bump @types/node from 25.6.0 to 25.9.1 in /dagger`. The npm bump itself was a 4-line devDependency change in `/dagger/package.json` and `/dagger/package-lock.json`. But the PR also modified `pixi.lock` at the repo root with **226 lines added / 228 lines deleted**. Reading the pixi.lock diff revealed:

- Format header upgraded from `version: 6` to `version: 7`.
- New `linux-64` platform declaration added (the previous file declared only `osx-64`).
- The `pypi-prerelease-mode` directive was removed.

None of those changes is explained by a `@types/node` npm bump in `/dagger`. The cause was that the Dependabot runner had a newer pixi version installed than was used at the last `pixi.lock` resolve, and the act of merely touching the lockfile triggered a re-solve under the new format. The bot's title did not mention this. The PR description did not mention this. The only place the truth lived was in `gh pr diff #691 --name-only`.

**The consequence of approving without checking:** the squash-merged commit lands `pixi.lock v7` to `main`. Every subsequent developer who pulls main now needs the matching pixi version or their local `pixi install` fails with "lockfile format unsupported". The dependency-bump PR has just become a tooling-version requirement bump for the entire team, with no advance notice.

**Detection signature:**

```bash
# The cheapest detector: does the diff touch a lockfile NOT named in the title's scope?
gh pr diff $N --repo $REPO --name-only | grep -iE 'lock|lockfile|\.lock$'

# The next-cheapest: does a CI check that's GREEN on main turn RED on the PR,
# with a name that has nothing to do with the bump's natural scope?
gh pr checks $N --repo $REPO | grep -E 'pending|failing'
# In #691, `pixi-check` was red on the PR and green on main — that's the silent
# lockfile-format upgrade tripping the version-mismatch detector.
```

#### Pattern B — maintainer-fixup commits stacked on bot branches

**Concrete case from the 2026-05-31 session:** PR #681 (`HomericIntelligence/AchaeanFleet#681`) was titled `chore(docker): bump python from 7a50012 to c845af9 in /bases`. The base commit was a 1-line digest bump in `/bases/Dockerfile`. But a follow-up commit `a2c372a4` titled `fix: Address CI failures for PR AchaeanFleet#681`, **authored by the maintainer, not the bot**, added 12 unrelated files:

- New GitHub issue templates under `.github/ISSUE_TEMPLATE/`.
- New PR template checklist items.
- A new `validate-claude-caps` CI job (~50 lines of YAML).
- `CLAUDE.md` edits.
- Nomad pattern doc updates.
- Three new test files.

None of those is in a 1-line Dockerfile digest bump's natural scope. The maintainer was being efficient — "I have a PR open, let me throw the small things on it" — but the effect is to turn a 1-line, atomic, easily revertable digest bump into a sprawling SRP-violating change. If the digest bump turns out to introduce a Python regression a week later, `git revert <merged-sha>` now reverts the CI YAML, the issue templates, the test files, and the doc updates as collateral damage.

**Detection signature:**

```bash
# How many commits? More than 1 on a Dependabot PR is suspicious.
gh pr view $N --repo $REPO --json commits --jq '.commits | length'

# Who authored each commit?
gh pr view $N --repo $REPO --json commits --jq '.commits[] | {oid, author: .authors[0].login, headline: .messageHeadline}'

# If ANY author != app/dependabot (or app/renovate, etc.), the bot's branch
# has been mutated by a human — and the title no longer describes the PR.
```

#### The mandatory phase-1 scope check

Before any verdict on a bot PR, run this exact sequence:

```bash
N=<pr-number>
REPO=<owner/repo>

# 1. Title + base/head + commit log with authors.
gh pr view $N --repo $REPO --json title,baseRefOid,headRefOid,commits --jq \
  '"title: \(.title)\nbase: \(.baseRefOid[0:8]) head: \(.headRefOid[0:8])\ncommits:\n" + ([.commits[] | "  \(.oid[0:8]) by \(.authors[0].login) \(.messageHeadline)"] | join("\n"))'

# 2. The actual file scope.
gh pr diff $N --repo $REPO --name-only

# 3. Per-file numstat (catches huge changes hidden behind innocuous filenames).
gh pr diff $N --repo $REPO | git apply --numstat -

# 4. The CI check list with status.
gh pr checks $N --repo $REPO
```

Then apply the verdict rule.

#### The verdict rule

| Condition | Verdict | Comment template |
|-----------|---------|------------------|
| Diff is title-aligned (only files mentioned by the title's scope, all commits authored by the bot, no lockfile cascade) | Proceed with normal review | n/a |
| Diff includes a lockfile format upgrade not explained by the bump | **REQUEST_CHANGES** | "The lockfile change in `<path>` upgrades the format (`<v6→v7>` / `<v1→v2>`) and is not explained by the dependency bump in the title. Revert the lockfile changes, OR scope the format upgrade to its own PR so it can be reviewed and rolled back independently." |
| Diff includes maintainer fixup commits unrelated to the title | **REQUEST_CHANGES** | "Commits `<sha1>`, `<sha2>`, ... add files (`<list>`) that are unrelated to the title's scope (`<title-scope>`). Per SRP this PR is doing more than one thing. Split the unrelated changes into separate PRs so each can be reviewed, merged, and reverted atomically." |
| Diff includes BOTH (rare but real) | **REQUEST_CHANGES** | Combine both templates. Mark the lockfile cascade first (it's the harder revert). |

The verdict rule is intentionally one-way: scope contamination is REQUEST_CHANGES, never APPROVE-with-comment. APPROVE-with-comment leaves the PR in an auto-mergeable state, and Dependabot's `@dependabot recreate` or the maintainer's next push can fire the merge before the comment is addressed.

#### Why not approve and "trust the squash to make it atomic"

A reasonable-sounding rebuttal: "We squash-merge, so all 12 files in a Pattern B PR become one squashed commit. Isn't that the same as one atomic change?"

No. The squash is an atomic ARRIVAL — the merge commit is one SHA — but it is not an atomic REVERSAL. Reverting that one SHA reverts all 12 files. A week later, when the Python digest bump turns out to have a regression, the revert also reverts the CI YAML, the issue templates, and the test files. The cost of getting back to a known-good state is now "lose 11 unrelated improvements" instead of "lose 1 digest bump". This is the SOLID-SRP violation translated into operational pain.

For lockfile cascades the cost is worse: the lockfile-format upgrade may not even BE reversible without a coordinated team-wide tooling-version downgrade. Once `pixi.lock v7` is on main, going back to v6 requires every developer to install the older pixi, which most won't notice they need until their next `pixi install` breaks.

#### Why title-trust is the default human failure mode

The trap is psychological. A reviewer sees:

- Title: `chore(deps): bump anthropic from 0.42.0 to 0.43.0`
- Author: `dependabot[bot]`
- Mental model: "this is a routine SDK bump, I've seen 50 of these, APPROVE"

The mental model substitutes the title for the diff. It is fast, it feels right, and 9 times out of 10 it IS right. The 10th time is Pattern A or Pattern B, and the cost of catching the 10th case is 30 seconds of `gh pr diff --name-only`. The cost of missing the 10th case is days of cleanup after the cascade lands on main.

Make the 30-second check non-negotiable. The verdict comes from the diff, not the title.

#### Distinguishing scope contamination from legitimate cascades

Some lockfile changes ARE in scope:

- A `package.json` change SHOULD update `package-lock.json` in the same directory. That is not a cascade, that is the same change expressed in two files.
- A `pyproject.toml` dependency change SHOULD update `pixi.lock` for the affected platform(s). That is in scope.

The contamination signature is when the lockfile change is **structurally different** from what the dependency change requires:

| Legitimate cascade | Contamination |
|--------------------|---------------|
| 1 dependency added → 5-20 lines in the lockfile under that dependency's section | 4-line npm devDep bump → 226 add/228 del across the entire pixi.lock |
| Lockfile diff scoped to one section, identifiable as the bumped dep | Lockfile diff includes format header changes (`version: 6` → `version: 7`) |
| Lockfile diff is in a subdirectory's local lockfile matching the change | Lockfile diff is at the REPO ROOT for a change scoped to a subdirectory |
| Lockfile diff matches the resolver's expected output for the bump | Lockfile diff removes/adds platform sections (`linux-64`, `osx-64`) |

The shortcut test: does the lockfile diff have a length proportional to the dependency change? A 4-line npm bump should produce roughly 4-40 lines of lockfile change. 226 lines of lockfile change for 4 lines of dependency change is a 50× signal. That is contamination.

#### Cross-link to verify-audit-findings-before-acting

This skill is the bot-PR-review analogue of `verify-audit-findings-before-acting.md`. The same principle applies: don't trust a label, check the artifact.

- Audit context (other skill): "the audit said the file is missing — `ls` the file."
- Bot-PR context (this skill): "the title said the change is a dependency bump — `gh pr diff --name-only` the change."

In both cases the failure mode is treating a prediction (audit severity tag, PR title) as a ground-truth statement about the artifact. The fix in both cases is to spend 30 seconds confirming against the artifact before acting.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Approve PR #691 based on "the npm bump in /dagger is clean" | Read the title, glanced at the `/dagger/package.json` 4-line change, prepared to APPROVE | Would have landed an unrelated `pixi.lock` format upgrade (v6→v7, linux-64 added, pypi-prerelease-mode removed) on main. Every developer who pulled main next would have failed `pixi install` until they upgraded pixi. The contamination was invisible from the title and from the `/dagger/package.json` change. | The title describes the bot's intent, not the PR's scope. `gh pr diff --name-only` is mandatory before APPROVE — even when the bump itself is obviously clean. |
| Request changes on PR #681 ONLY for the merge conflict | Re-read the CI failures, noticed the merge conflict on the maintainer's fixup commit, drafted "fix the merge conflict and I'll approve" | Would miss the scope-bloat root cause. The PR's actual problem is that 12 unrelated files were stacked on a 1-line Dockerfile digest bump (issue templates, PR template, CI YAML, doc updates, three test files). Fixing the merge conflict doesn't fix the SRP violation; the PR still can't ship cleanly because reverting the digest bump a week from now would also revert all 12 unrelated changes. | The verdict rule must be the contamination, not the symptom. A merge conflict on a contaminated PR is the symptom; the bloated scope is the cause. Reject for the cause. |
| Trust the bot author tag to mean "no human has touched this branch" | Saw `dependabot[bot]` as the PR author, assumed the commits were all bot-authored | The PR author field reflects who OPENED the PR, not who has committed to it since. A maintainer can push to `dependabot/<branch>` after the bot opens the PR, and the author field doesn't change. PR #681's `a2c372a4` was authored by the maintainer, not the bot, but the PR-level author was still `dependabot[bot]`. | Check commit-level authors, not PR-level authors. `gh pr view --json commits --jq '.commits[] \| .authors[0].login'` is the truth; the PR author field is the cover page. |
| Approve a batch of "small dependency bumps" by pattern-matching titles | Reviewed 11 Dependabot PRs in a session, used the title pattern (`chore(deps): bump X from V1 to V2`) as a heuristic for "safe to approve" | 2 of 11 (18%) had contamination. The title pattern is identical for the clean 9 and the contaminated 2; pattern-matching by title is structurally blind to the failure modes documented here. | Title pattern-matching is the failure mode this skill exists to interrupt. Run the phase-1 scope check on EVERY bot PR, no exceptions for "obviously small" bumps. The 30s/PR cost is the price of catching the 18% case. |
| Skip the scope check when the PR is "already passing CI" | Assumed green CI = scope is fine | Pattern B contamination passes CI by design — the maintainer's fixup commit is what made CI green in the first place. Green CI does not certify scope; it certifies the build and tests pass. A SRP-violating PR can be green AND still be wrong to land. | CI signals correctness of the artifact, not appropriateness of the scope. Both checks must run. |
| Defer the scope decision to auto-merge | Armed `gh pr merge --auto`, expected to revisit if anything broke | Once auto-merge fires, the contamination is on main. There is no revisit; the revert is the only recourse and it carries the costs documented in "Why not approve and trust the squash to make it atomic". | Phase-1 scope check runs BEFORE arming auto-merge. The check is a precondition for the verdict, not a post-merge audit. |

## Results & Parameters

### Detection signatures (copy-paste)

```bash
# ============================================================
# Phase 1 scope check — run BEFORE any verdict on a bot PR.
# ============================================================
N=<pr-number>
REPO=<owner/repo>

# 1. Title + commits + authors
gh pr view $N --repo $REPO --json title,baseRefOid,headRefOid,commits --jq \
  '"title: \(.title)\nbase: \(.baseRefOid[0:8]) head: \(.headRefOid[0:8])\ncommits:\n" + ([.commits[] | "  \(.oid[0:8]) by \(.authors[0].login) \(.messageHeadline)"] | join("\n"))'

# 2. File scope
gh pr diff $N --repo $REPO --name-only

# 3. Per-file numstat
gh pr diff $N --repo $REPO | git apply --numstat -

# 4. CI checks
gh pr checks $N --repo $REPO

# ============================================================
# Pattern A detector — lockfile/format cascade.
# ============================================================
# Does the diff touch a lockfile not named by the title's scope?
gh pr diff $N --repo $REPO --name-only | grep -iE 'lock$|\.lock\.|lockfile'

# Does a CI check fail on the PR that's green on main, with an unrelated name?
COMPARISON=$(gh api repos/$REPO/commits/main/check-runs --jq '.check_runs[] | select(.conclusion=="success") | .name' | sort -u)
gh api repos/$REPO/pulls/$N --jq '.head.sha' | xargs -I {} \
  gh api repos/$REPO/commits/{}/check-runs --jq '.check_runs[] | select(.conclusion=="failure") | .name' \
  | grep -vxF "$COMPARISON"

# ============================================================
# Pattern B detector — maintainer fixup stacked on bot branch.
# ============================================================
# Commit count > 1?
COMMITS=$(gh pr view $N --repo $REPO --json commits --jq '.commits | length')
echo "Commit count: $COMMITS"
[ "$COMMITS" -gt 1 ] && echo "Pattern B candidate — inspect commit authors"

# Any non-bot commit authors?
gh pr view $N --repo $REPO --json commits --jq \
  '.commits[] | select((.authors[0].login | test("\\[bot\\]$")) | not) | {oid, author: .authors[0].login, headline: .messageHeadline}'
```

### Verdict templates (copy-paste)

```markdown
<!-- Pattern A: lockfile format cascade -->
REQUEST_CHANGES

The diff modifies `<lockfile-path>` with `<N> add / <M> del`, which is not
explained by the dependency bump in the title (`<title-scope>`). Inspection
shows a format-version change: `<v6 → v7>` and `<platform/section changes>`.

Please either:
1. Revert the changes to `<lockfile-path>` so this PR is scoped to the
   dependency bump only, OR
2. Close this PR and re-open the lockfile format upgrade as its own PR so it
   can be reviewed and rolled back independently of any dependency change.
```

```markdown
<!-- Pattern B: maintainer fixup stacked on bot branch -->
REQUEST_CHANGES

Commits `<sha1>`, `<sha2>`, ... add the following files which are unrelated
to the title's scope (`<title>`):

  - `<file 1>`
  - `<file 2>`
  - ...

Per the Single Responsibility Principle this PR is doing more than one thing.
Please split the unrelated changes into separate PRs so each can be reviewed,
merged, and reverted atomically. After the split, this PR should contain ONLY
the `<bot's stated change>`.
```

### Contamination rate observed (verified-local)

In the 2026-05-31 HomericIntelligence/AchaeanFleet bot-PR review session:

- 11 Dependabot PRs reviewed in the session.
- 2 flagged REQUEST_CHANGES for scope contamination (18%):
  - PR #691: Pattern A (pixi.lock v6→v7 cascade on a `/dagger` npm bump).
  - PR #681: Pattern B (12 unrelated files in `a2c372a4` fixup commit on a 1-line Dockerfile digest bump).
- 9 reviewed clean (title-aligned, single bot-authored commit, no cascade).

Sample size is small; contamination rate likely depends on the repo's maintainer-fixup culture and the lockfile tools in use. Treat 18% as an upper-bound estimator until more sessions corroborate.

### Time cost

- Without phase-1 scope check: ~10s per PR to APPROVE on title pattern × 11 PRs = ~2 minutes total, but with 2 contaminated PRs landing on main and producing days of downstream cleanup.
- With phase-1 scope check: ~30s per PR (4 gh commands) × 11 PRs = ~5.5 minutes total, with 0 contamination landing.

The phase-1 check costs ~3.5 extra minutes per 11-PR batch and saves an indeterminate (but large) amount of downstream cleanup time per contamination caught.

### Specific commands that caught the two contaminations in this session

```bash
# Catch #1 — PR #691 (Pattern A: pixi.lock cascade)
gh pr diff 691 --repo HomericIntelligence/AchaeanFleet --name-only
# Output included `pixi.lock` — outside the title's `/dagger` scope.

gh pr diff 691 --repo HomericIntelligence/AchaeanFleet | git apply --numstat -
# Output showed `pixi.lock | 226 ++++++... 228 ------...` — 50× the npm bump size.

gh pr checks 691 --repo HomericIntelligence/AchaeanFleet
# pixi-check was red on the PR, green on main — the format-version mismatch tripping the gate.

# Catch #2 — PR #681 (Pattern B: maintainer fixup)
gh pr view 681 --repo HomericIntelligence/AchaeanFleet --json commits --jq '.commits | length'
# Output: 2 (not 1) — second commit was non-bot.

gh pr view 681 --repo HomericIntelligence/AchaeanFleet --json commits --jq \
  '.commits[] | {oid, author: .authors[0].login, headline: .messageHeadline}'
# Output showed `a2c372a4` authored by the maintainer with headline `fix: Address CI failures for PR #681`.

gh pr diff 681 --repo HomericIntelligence/AchaeanFleet --name-only
# Output included 12 files outside the `/bases/Dockerfile` scope (issue templates, CI YAML, doc updates, test files).
```

### Pre-flight script for a bot-PR batch review

```bash
#!/usr/bin/env bash
# bot-pr-scope-check.sh
# Usage: bot-pr-scope-check.sh <owner/repo> <pr-1> [<pr-2> ...]
set -euo pipefail
REPO="$1"; shift
for N in "$@"; do
  echo "=== PR #$N ==="
  gh pr view "$N" --repo "$REPO" --json title,commits --jq \
    '"title: \(.title)\ncommit count: \(.commits | length)\nauthors: " + ([.commits[].authors[0].login] | unique | join(","))'
  echo "files:"
  gh pr diff "$N" --repo "$REPO" --name-only | sed 's/^/  /'
  echo "numstat:"
  gh pr diff "$N" --repo "$REPO" | git apply --numstat - 2>/dev/null | sed 's/^/  /'
  echo "checks:"
  gh pr checks "$N" --repo "$REPO" | sed 's/^/  /'
  echo
done
```

Pipe to a file and grep for `commit count: [^1]$` (Pattern B candidates) and for lockfile filenames outside the bumped scope (Pattern A candidates) before reviewing any PR in the batch.

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| HomericIntelligence/AchaeanFleet | 2026-05-31 bot-PR review session (11 Dependabot PRs) | 2 of 11 (18%) contaminated; both caught by the phase-1 scope check. PR #691 was Pattern A: `pixi.lock` modified with 226 add/228 del (format v6→v7, linux-64 platform added, pypi-prerelease-mode removed) on a `chore(dagger): bump @types/node` PR scoped to `/dagger`. The lockfile change was at the repo root and ~50× the size of the actual npm bump. `pixi-check` was red on the PR and green on main, confirming the format-version mismatch. PR #681 was Pattern B: a maintainer-authored commit `a2c372a4` titled `fix: Address CI failures for PR #681` added 12 unrelated files (issue templates, PR template, validate-claude-caps CI job, CLAUDE.md edits, nomad pattern docs, three test files) on top of a 1-line Dockerfile digest bump in `/bases/Dockerfile`. Without the phase-1 check, both PRs would have shipped — #691 carrying a silent lockfile-format upgrade, #681 carrying a SRP-violating 12-file pile-on. Both REQUEST_CHANGES verdicts were grounded in the diff name list, not the title, per the verdict rule. |

### Related skills

- `verify-audit-findings-before-acting.md` — the parent skill for "don't trust a label, check the artifact". The audit-context analogue: audits hallucinate critical findings about absent files; verify by `ls`. This skill is the bot-PR-context analogue: PR titles misdescribe scope; verify by `gh pr diff --name-only`. Cross-link when reviewing any prediction-vs-artifact mismatch.
- `architecture-bot-pr-discovery-synthetic-issue-key.md` — the upstream discovery skill that makes bot PRs visible to issue-driven drivers. Once bot PRs are visible, THIS skill is the next step: how to actually review them safely. Read both when wiring a CI driver that processes bot PRs end-to-end.
- `tooling-pixi-lockfile-churn-self-reference.md` — the related Pixi-specific failure mode where lockfile churn is itself the change. Pattern A in this skill is the cross-tool version of that failure mode (any lockfile, not just pixi).
- `ci-cd-dependabot-pixi-lock-drift-fix.history` — historical artifact documenting the recurrence of dependabot/pixi.lock drift in the ecosystem. This skill is the proactive review counterpart to that reactive fix.
- `tooling-gh-pr-list-limit-cap-use-api-paginate.md` — the related pattern: use `gh api --paginate` when batch-enumerating PRs for a review session, so the pre-flight script above doesn't silently truncate a flooded repo's bot-PR list.
