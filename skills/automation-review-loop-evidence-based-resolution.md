---
name: automation-review-loop-evidence-based-resolution
description: "How to build a Python implement->review loop that drives LLM sub-agents to review a PR and fix its review comments, so it converges on an EVIDENCE-BASED GO instead of a self-reported one. SHIPPED & verified-ci (ProjectHephaestus PR #1084 / issue #1083): (a) the fixer agent's address step counts as progress ONLY when `addressed AND committed` are both true -- a clean worktree with prose replies like 'documented as a limitation' must NOT resolve threads; resolution is gated on a real commit, never on the model's self-report; (b) the loop converges ONLY on an explicit `Verdict: GO` -- 'reviewer posted zero threads' regardless of verdict ends AMBIGUOUS/NO-GO too fast; (c) thread RESOLUTION is moved OUT of the fixer and INTO a fresh read-only REVIEWER/validator on the next pass that compares each prior thread against the new diff and resolves only genuinely-addressed ones, re-opening the rest -- the fixer only edits+commits+pushes and must NOT call the resolve mutation; (d) a `state:skip` label (sourced from the state_labels single-source module, auto-provisioned, honored on issue OR PR) skips all phases and is auto-applied on iteration exhaustion; (e) a `--nitpick` flag where the reviewer severity-tags every inline comment (critical/major/minor/nitpick) and SUPPRESSES nitpick by default so the loop doesn't burn iterations on cosmetics; (f) per-comment dispatch -- classify each comment's fix difficulty with a cheap sub-agent, render a `@ <file> Line <#> - <difficulty> - <desc>` todo list, dispatch ONE sub-agent per comment (serialize same-file comments), tier models simple->haiku/medium->sonnet/hard->opus. ALSO captures (UNVERIFIED, found by strict post-merge review of that very code) FOUR design defects to avoid: match threads by thread `id` not `(path, line)`; FETCH+concatenate an existing comment body before `updatePullRequestReviewComment` (it REPLACES, not appends); gate auto-`state:skip` on real iteration exhaustion not blanket non-GO; FENCE untrusted comment text in prompts. Use when: (1) building/auditing a Python loop that has an LLM sub-agent review a PR then fix the inline comments, (2) a review loop resolves threads even though no commit was produced, (3) a loop ends NO-GO/AMBIGUOUS 'too fast' before ever earning a GO, (4) deciding whether the fixer or the reviewer resolves GitHub review threads, (5) adding a skip-label or a nitpick-suppression flag to such a loop, (6) dispatching one fix sub-agent per review comment with tiered models."
category: architecture
date: 2026-06-07
version: "1.0.0"
user-invocable: false
verification: verified-ci
tags:
  - hephaestus-automation-loop
  - implement-review-loop
  - review-thread-resolution
  - evidence-based-resolution
  - commit-gated-progress
  - verdict-go-convergence
  - state-skip-label
  - nitpick-severity-suppression
  - per-comment-dispatch
  - tiered-models
  - prompt-injection
  - graphql-review-threads
  - homericintelligence
---

# Review Loop: Resolve Threads on Commit Evidence, Converge on Verdict GO

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-06-07 |
| **Objective** | Make a Python implement->review loop (an LLM sub-agent reviews a PR, another fixes the inline comments) converge on an EVIDENCE-BASED `Verdict: GO` rather than on the fixer's self-report. Stop the loop from (a) resolving review threads when no commit was produced, (b) terminating NO-GO/AMBIGUOUS before earning a GO, and (c) burning iterations on cosmetic nitpicks. Add a `state:skip` escape hatch and per-comment tiered dispatch. |
| **Outcome** | SHIPPED -- ProjectHephaestus PR #1084 (closes #1083) merged CI-green. The commit-gate, the `Verdict: GO` convergence, the reviewer-side evidence-based resolution, the `state:skip` vocabulary/gating, the `--nitpick` default-off suppression, and per-comment tiered dispatch all landed. A STRICT post-merge review then found 4 MAJOR design defects in the merged code (see Failed Attempts -- those corrections are NOT yet validated). |
| **Verification** | verified-ci for what shipped (commit-gate, `state:skip` vocabulary/gating, `--nitpick` suppression, verdict-GO convergence, reviewer-side resolution, per-comment dispatch). The 4 design corrections in Failed Attempts are `unverified` -- proposed, not yet implemented or CI-confirmed. Do NOT treat the buggy-as-merged behavior as the ideal. |

## When to Use

Trigger phrases / situations:

- "review loop resolved a thread but no commit was made"
- "the fixer agent replied 'documented as a limitation' and the thread got resolved"
- "the loop ended NO-GO / AMBIGUOUS too fast" / "it never earned a GO"
- "should the fixer or the reviewer resolve the review threads?"
- "add a skip label to the automation loop" / "honor state:skip on an issue or PR"
- "suppress nitpick comments" / "reviewer severity tags critical/major/minor/nitpick"
- "dispatch one sub-agent per review comment" / "tiered models for fix difficulty"
- You are building or auditing a Python loop where one LLM sub-agent reviews a PR and another fixes the inline review comments, and you need the contract for "what counts as progress" and "who resolves threads."
- This is the **successor** to `tooling-hephaestus-automation-loop-drive-green-broken-design` (PRs #1073/#1075/#1077/#1079) -- that skill introduced `review_validator.py` (re-raise unaddressed comments as new threads) and bot-thread resolution. PR #1084 hardens the *resolution-vs-commit* and *convergence* contract on top of it.

## Verified Workflow

### Quick Reference

```python
# 1. PROGRESS IS GATED ON A REAL COMMIT, NOT THE MODEL'S SELF-REPORT.
#    _commit_if_changes returns a bool. The address step only counts as
#    progress when BOTH the model said it addressed comments AND a commit
#    actually landed. A clean worktree -> no progress, regardless of prose.
addressed = run_fixer_agent(...)          # model self-report (untrusted alone)
committed = _commit_if_changes(worktree)  # True only if HEAD advanced
made_progress = addressed and committed   # BOTH required
# Thread resolution NEVER happens here -- the fixer does not call the resolve mutation.

# 2. CONVERGE ONLY ON AN EXPLICIT `Verdict: GO`. Zero threads != GO.
if reviewer_verdict == "GO":
    converge()
# "reviewer posted zero threads" with verdict AMBIGUOUS/NO-GO is NOT convergence.
# Require the literal GO so the loop can't end before earning it.

# 3. RESOLUTION IS EVIDENCE-BASED AND LIVES IN THE REVIEWER, NOT THE FIXER.
#    On the NEXT review pass, a fresh READ-ONLY sub-agent compares each prior
#    thread against the new diff: resolve only genuinely-addressed threads,
#    re-open (new inline thread) the rest. The fixer only edits+commits+pushes.
for thread in prior_threads:
    if validator_says_addressed_by_diff(thread, new_diff):
        resolve(thread.id)        # reviewer side only
    else:
        reopen_as_new_thread(thread)  # re-open OVERRIDES a stale GO
```

```bash
# 4. state:skip -- manual+automatic override, honored on issue OR PR.
#    The label NAME lives in the single-source state_labels module (NOT hard-coded).
#    Auto-provision it; auto-apply it when the loop exhausts iterations without GO.
#    When present on the issue OR the PR, skip ALL phases.

# 5. --nitpick flag. Reviewer severity-tags EVERY inline comment:
#    critical | major | minor | nitpick. nitpick is SUPPRESSED by default;
#    --nitpick re-enables it. Default-off keeps the loop off cosmetic threads.
review --nitpick   # opt IN to nitpick-severity comments
```

### Detailed Steps

1. **Gate "progress" on a real commit (`addressed AND committed`).**
   `_commit_if_changes` returns `True` only if HEAD advanced. The fixer's
   self-reported "addressed" list is untrusted on its own -- a clean worktree
   with prose replies (e.g., "documented as a limitation", "this is intended")
   must count as ZERO progress and must NOT resolve any thread. Resolution is
   gated on commit evidence, never on the model's self-report.

2. **Converge ONLY on an explicit `Verdict: GO`.** Do not converge on "reviewer
   posted zero threads." A zero-thread pass with verdict AMBIGUOUS or NO-GO ends
   the loop too fast -- before it ever earns a GO. Parse the verdict explicitly
   (see `llm-output-verdict-parse-last-line-not-substring`) and require the
   literal `GO` token to converge.

3. **Move thread RESOLUTION into the reviewer/validator on the next pass.**
   The fixer agent ONLY edits, commits, and pushes; it MUST NOT call the GitHub
   resolve mutation. On the next review pass, a fresh READ-ONLY sub-agent
   compares each prior thread against the new diff and:
   - resolves a thread ONLY if the diff genuinely addressed it (evidence-based);
   - re-opens (as a NEW inline thread -- GitHub has no "unresolve" mutation, and
     the unresolved-thread lister filters resolved threads out) every thread the
     diff did NOT address. A re-open OVERRIDES a stale GO so the loop keeps going.
   Respect the own-threads-only guarantee (do not touch human threads).

4. **`state:skip` label as a manual + automatic override.** Put the label NAME
   in the single-source-of-truth `state_labels` module -- do NOT hard-code the
   string at the callsite. Auto-provision the label (create it if missing).
   Honor it on EITHER the issue OR the PR: if present, skip ALL phases. Auto-apply
   it when the loop exhausts its iteration budget without a GO (but see the
   PITFALL in Failed Attempts: gate the auto-apply on TRUE exhaustion, not on a
   single iteration-0 zero-thread non-GO).

5. **`--nitpick` flag + severity tagging.** The reviewer tags every inline comment
   with a severity: `critical | major | minor | nitpick`. By DEFAULT, suppress
   nitpick-severity comments entirely; `--nitpick` re-enables them. Default-off
   suppression keeps the loop from burning iterations on cosmetic threads.

6. **Per-comment dispatch with tiered models.** Classify each review comment's
   fix difficulty with a cheap, separate sub-agent. Render a todo list of the
   form `@ <file> Line <#> - <difficulty> - <description>`. Dispatch ONE sub-agent
   per comment, but SERIALIZE same-file comments to avoid worktree write conflicts.
   Tier the model by difficulty: simple -> haiku, medium -> sonnet, hard -> opus.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Resolve threads from the fixer's self-reported "addressed" list | The loop resolved review threads whenever the fixer agent said it had addressed them -- even with a clean worktree and prose-only replies ("documented as a limitation") | Threads got resolved (with reply text) while NO commit was produced; the PR looked addressed but the diff was unchanged | Gate resolution on a real commit: `_commit_if_changes` returns a bool; count an address step as progress ONLY when `addressed AND committed`. Never trust the model's self-report alone. (SHIPPED, PR #1084.) |
| Converge when the reviewer posts zero threads | The loop terminated on "zero new threads" regardless of the verdict | It ended AMBIGUOUS/NO-GO "too fast", before ever earning a GO; a quiet reviewer pass was mistaken for success | Require an explicit `Verdict: GO` to converge. Zero threads != GO. (SHIPPED, PR #1084.) |
| Let the fixer agent resolve its own threads | The implementer/fixer agent both edited the code AND called the resolve mutation in one pass | The fixer has every incentive to declare victory; resolution co-located with fixing is not evidence-based | Move resolution to a fresh READ-ONLY reviewer/validator on the next pass that diffs each prior thread against the new code; the fixer only edits+commits+pushes and must NOT call resolve. (SHIPPED, PR #1084.) |
| Burn iterations on every cosmetic comment | Reviewer treated all inline comments equally; the loop tried to address nitpicks | Cosmetic threads consumed iterations the loop needed for real defects | Severity-tag every comment (critical/major/minor/nitpick) and SUPPRESS nitpick by default; `--nitpick` opts back in. (SHIPPED, PR #1084.) |
| **(PROPOSED / UNVERIFIED)** Match prior threads for resolution on `(path, line)` | The validator paired a prior thread to the new diff by file path + line number | Two threads can share a line (e.g., the reviewer's original + a re-open), and path normalization can drift across hunks -- so the wrong thread gets resolved/re-opened | Match on the thread `id`: include the id in the validation prompt AND the payload, and have the sub-agent echo it back. NOT YET FIXED in #1084. |
| **(PROPOSED / UNVERIFIED)** Edit an existing comment via `updatePullRequestReviewComment` using only its node id | To avoid duplicating a comment, the code fetched only the node id from the comment index and called the update mutation | `updatePullRequestReviewComment` REPLACES the body -- updating with new text silently DESTROYS the original comment. Returning only the node id is insufficient | FETCH the existing body first and CONCATENATE; the comment index must return the body, not just the id. NOT YET FIXED in #1084. |
| **(PROPOSED / UNVERIFIED)** Auto-apply `state:skip` on any `last_verdict != "GO"` | The loop labeled the issue/PR `state:skip` whenever the most recent verdict was not GO | It fired after a SINGLE iteration-0 zero-thread NO-GO, permanently stranding a fixable issue that just hadn't been worked yet | Gate auto-skip on TRUE exhaustion -- `iterations_run >= MAX_ITERATIONS` (or an explicit AMBIGUOUS terminal state), not blanket non-GO. NOT YET FIXED in #1084. |
| **(PROPOSED / UNVERIFIED)** Interpolate `thread["body"]` unfenced into the coordinator prompt | Untrusted GitHub comment text was dropped directly into the prompt's todo list (authoritative region), with only first-line truncation as "safety" | First-line truncation is not injection-safe; an attacker-controlled comment can inject instructions into the prompt's authoritative region | FENCE all untrusted comment text (or reduce it to path+line only) before interpolation. Truncation is not a sanitizer. NOT YET FIXED in #1084. |
| **(PROPOSED / UNVERIFIED, DRY)** Re-implement the read-only sub-agent invocation per sub-agent type | Each sub-agent type duplicated the `is_codex` branch -> `invoke_claude_with_session`/`run_codex_text` -> `parse_json_block` -> 3-exception catch shape | The same invocation+parse+error-handling block is copy-pasted per sub-agent, drifting over time | Factor a shared `run_read_only_session` helper that all read-only sub-agents call. NOT YET FACTORED in #1084. |

> Rows marked **(PROPOSED / UNVERIFIED)** are design defects a strict post-merge
> review found IN the merged PR #1084 code. The corrections are NOT yet
> implemented or CI-confirmed -- treat them as the next implementer's must-fix
> list, not as shipped behavior.

## Results & Parameters

### The progress / convergence contract (SHIPPED, verified-ci)

| Rule | Implementation | Why |
|------|----------------|-----|
| Progress requires a commit | `made_progress = addressed and committed`; `_commit_if_changes` returns bool (True iff HEAD advanced) | A clean worktree with prose replies is NOT progress and must not resolve threads |
| Convergence requires an explicit GO | parse reviewer output, require literal `Verdict: GO` | "zero threads" with AMBIGUOUS/NO-GO is not success |
| Fixer never resolves | fixer agent only edits+commits+pushes; resolution mutation lives in the reviewer/validator | evidence-based resolution; fixer can't self-declare victory |
| Reviewer resolution is diff-evidence-based | fresh READ-ONLY sub-agent compares each prior thread vs new diff; resolve addressed, re-open (new thread) the rest | re-open OVERRIDES a stale GO; GitHub has no unresolve mutation |

### `state:skip` label (SHIPPED, verified-ci)

| Property | Value |
|----------|-------|
| Label name source | the single-source `state_labels` module (NOT a hard-coded string at the callsite) |
| Provisioning | auto-provisioned (created if missing) |
| Scope | honored on the issue OR the PR |
| Effect when present | skip ALL phases |
| Auto-apply (shipped) | applied when the loop exhausts iterations without GO |
| Auto-apply (CORRECTION, unverified) | gate the auto-apply on `iterations_run >= MAX_ITERATIONS` or AMBIGUOUS terminal, NOT on a blanket `last_verdict != "GO"` (a single iteration-0 NO-GO must NOT strand the issue) |

### `--nitpick` severity model (SHIPPED, verified-ci)

```text
Reviewer tags every inline comment with one severity:
  critical | major | minor | nitpick

Default:    suppress nitpick-severity comments entirely.
--nitpick:  re-enable nitpick comments.

Rationale: default-off suppression keeps the loop from spending iterations
on cosmetic threads it would otherwise have to "address" to earn a GO.
```

### Per-comment dispatch + tiered models (SHIPPED, verified-ci)

```text
1. For each review comment, a cheap separate sub-agent classifies fix difficulty.
2. Render a todo list:
     @ <file> Line <#> - <difficulty> - <description>
3. Dispatch ONE sub-agent per comment.
   - SERIALIZE comments that touch the SAME file (avoid worktree write conflicts).
   - Parallelize across distinct files.
4. Tier the model by difficulty:
     simple -> haiku
     medium -> sonnet
     hard   -> opus
```

### Cross-references to companion skills

- **`tooling-hephaestus-automation-loop-drive-green-broken-design`** (PRs
  #1073/#1075/#1077/#1079) -- the PREDECESSOR. It introduced `review_validator.py`
  (re-raise unaddressed comments as NEW inline threads, since GitHub has no
  unresolve mutation) and drive-green bot-thread resolution. PR #1084 (this skill)
  hardens the resolution-vs-commit and convergence contract on top of it.
- **`llm-output-verdict-parse-last-line-not-substring`** -- how to robustly parse
  the `Verdict: GO` token from the reviewer's output (do not substring-match).
- **`ci-cd-no-commit-retry-with-review-thread-injection`** (PR #847) -- the
  no-commit-on-red-CI retry path; complements this skill's "no commit -> no
  progress, no resolution" rule.
- **`architecture-github-labels-as-state-vocabulary`** -- why `state:skip` belongs
  in a single-source label vocabulary module rather than a hard-coded string.

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| ProjectHephaestus | PR #1084 (closes #1083), merged CI-green: shipped the commit-gated progress rule, `Verdict: GO` convergence, reviewer-side evidence-based thread resolution, `state:skip` label vocabulary/gating + auto-apply, `--nitpick` default-off severity suppression, and per-comment tiered dispatch. | [PR #1084](https://github.com/HomericIntelligence/ProjectHephaestus/pull/1084) / [issue #1083](https://github.com/HomericIntelligence/ProjectHephaestus/issues/1083) |
| ProjectHephaestus | Strict post-merge review of PR #1084 found 4 MAJOR design defects (thread `(path,line)` matching, comment-body REPLACE-vs-concatenate, over-eager auto-`state:skip`, unfenced untrusted comment text) + 1 DRY note (`run_read_only_session`). Corrections captured as PROPOSED/UNVERIFIED Failed-Attempts rows. | Same PR #1084 -- corrections not yet implemented or CI-confirmed. |
