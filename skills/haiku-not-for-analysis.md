---
name: haiku-not-for-analysis
description: "Never dispatch Haiku for analysis, triage, classification, or any judgment-required work — Haiku silently produces high-confidence false positives that look correct on the surface. Use when: (1) about to choose `model: haiku` for a sub-agent, (2) Sonnet/Opus quota is exhausted and you are tempted to substitute Haiku, (3) writing prompts for issue triage / ALREADY-DONE detection / scope classification / repo audits, (4) routing phases of an automation pipeline to model tiers."
category: tooling
date: 2026-05-07
version: "1.0.0"
user-invocable: false
verification: verified-local
tags:
  - agent-dispatch
  - model-tier
  - haiku
  - sonnet
  - opus
  - triage
  - classification
  - analysis
  - false-positive
  - already-done
  - quota-exhaustion
---

# Haiku Is for Mechanical Fixes, Never for Analysis

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-05-07 |
| **Project** | Myrmidons (`HomericIntelligence/Myrmidons`) |
| **Objective** | Stop substituting Haiku for Sonnet/Opus on analysis/triage/classification work just because the higher-tier quota is exhausted. |
| **Outcome** | Hard rule established: Haiku is only for mechanical fix work with explicit rules; analysis tasks must wait for Sonnet/Opus or ask the user before falling back. |
| **Verification** | verified-local (observed 2026-05-07 in Myrmidons issue-triage session — 4/4 ALREADY-DONE flags from a Haiku triage agent were false positives) |
| **Category** | tooling |
| **Related** | [automation-claude-model-per-phase](./automation-claude-model-per-phase.md) — phase-to-tier routing pattern; [already-done-issue-detection](./already-done-issue-detection.md) — the workflow whose accuracy Haiku destroyed; [wave-based-bulk-issue-triage](./wave-based-bulk-issue-triage.md) — already notes "Why Explore not Haiku" for classification |

## When to Use

- You are about to set `model: "haiku"` (or `claude-haiku-4-5`) on a sub-agent.
- A Sonnet or Opus quota error has just hit and you are deciding whether to retry, wait, or substitute Haiku.
- You are writing prompts for any of: GitHub issue triage, ALREADY-DONE detection, EASY/MEDIUM/HARD classification, repo audits, scope estimation, root-cause analysis, code review, planning, design decisions.
- You are routing phases of an automation pipeline to model tiers and need to decide which phase Haiku is allowed to handle.
- You are tempted by "Haiku is faster and cheaper, let's see if it can do this" — read the failure mode below before proceeding.

## Verified Workflow

### Quick Reference

```text
ANALYSIS / TRIAGE / CLASSIFICATION  →  model: sonnet  (preferred)
                                       model: opus    (acceptable)
                                       model: haiku   ❌ NEVER

MECHANICAL FIX with explicit rules   →  model: haiku   ✅
                                        (rebases with explicit conflict rules,
                                         single-issue impl with file allowlist,
                                         lint fixes ≤50 LOC, semantic merges
                                         with documented patterns)

QUOTA EXHAUSTED on Sonnet/Opus       →  Ask the user. Do NOT silently
                                        substitute Haiku for an analysis task.
```

### Decision Tree

```text
Is the agent's job to PRODUCE A JUDGMENT?
  (classify / estimate / decide / verify / triage / audit / review)
   ├─ YES → Sonnet (preferred) or Opus. NEVER Haiku.
   │        If quota exhausted → ask user, wait, or run yourself.
   │
   └─ NO  → Is the work fully specified by an explicit rule set,
            file allowlist, conflict resolution policy, or template?
             ├─ YES → Haiku is fine.
             │        (rebase fix-up, lint fix ≤50 LOC, mechanical merge
             │         with documented pattern, single-issue impl with
             │         file allowlist and explicit `Run:` commands)
             │
             └─ NO  → Sonnet. The work needs judgment even if it
                      doesn't feel like "analysis."
```

### Detailed Steps

1. **Before dispatching any sub-agent, classify the task into one of two buckets.** If you cannot articulate why the task is mechanical (i.e. you cannot list the explicit rules the agent will follow), it is an analysis task. Default to Sonnet.

2. **Make the bucket explicit in the dispatch prompt.** Mechanical fix prompts should be in imperative `Run: <shell command>` form with no judgment calls. Analysis prompts include "classify", "decide", "estimate", "verify whether X actually exists" — those go to Sonnet.

3. **When Sonnet/Opus quota is exhausted on an analysis task, do NOT silently substitute Haiku.** Surface the situation to the user with three options:
   - Wait for quota reset and resume.
   - Run the analysis manually in the orchestrator (no sub-agent).
   - Authorize Haiku with explicit acknowledgment that results will need 100% manual re-verification.

4. **For ALREADY-DONE / classification / triage tasks specifically:** Haiku conflates *discussion of a thing* with *evidence the thing exists*. It will see "the issue talks about gitleaks" and conclude "tests for gitleaks exist" without running `ls tests/integration/test_gitleaks_*.bats`. It will see "actionlint is in `.pre-commit-config.yaml`" and conclude "the hook works on Go-1.15 hosts" without checking the latest CI run. **Always use Sonnet (or Opus) for these.**

5. **If you must use Haiku for any verification-flavored work**, treat its output as suspect by default and re-verify every positive flag manually before acting. The cost of re-verification dominates any time saved by using the cheaper tier.

6. **Document the model choice in the dispatch prompt itself** so future readers (and the agent harness's logs) can audit the routing decision: a one-line rationale like `# model: sonnet — classification requires judgment` is enough.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Substituting Haiku for Sonnet on EASY/MEDIUM/HARD + ALREADY-DONE classification of ~200 GitHub issues mid-session, after Sonnet quota exhausted | Spun up a Haiku triage agent with the same prompt template that had been working on Sonnet, expecting equivalent output for less cost. | Haiku flagged 4/200 issues as ALREADY-DONE. When verified against current repo state, **all 4 were false positives**: the work hadn't actually been done; the agent confused the issue body's description of the missing thing for evidence the thing existed. Manual re-verification cost more time than waiting for quota reset would have. | For analysis/triage/classification: never substitute Haiku for Sonnet. Either wait for quota, run the analysis yourself, or ask the user before falling back. |
| Treating "Haiku saw the keyword in the codebase" as evidence the feature/file/test exists | Haiku triage agent flagged issue #517 ("Add bats test for gitleaks CHANGELOG.md allowlist") as ALREADY-DONE because it saw discussion of gitleaks in `.gitleaks.toml`. | The actual test file did not exist — `ls tests/integration/test_gitleaks_*.bats` returns nothing. Haiku conflated *config that mentions gitleaks* with *tests for gitleaks*. | ALREADY-DONE detection requires checking the EXISTENCE of the artifact (`ls`, `gh run view`, etc.), not the presence of related keywords elsewhere in the repo. Haiku does not reliably make this distinction; Sonnet does. |
| Treating "the hook ID is in `.pre-commit-config.yaml`" as evidence the hook works | Haiku flagged issue #495 ("pre-commit: actionlint hook broken on Go <1.16") as ALREADY-DONE because `actionlint` appears in `.pre-commit-config.yaml`. | The hook's brokenness is observable only in the latest CI run on Go-1.15 hosts. Mere presence of the hook ID in config tells you nothing about whether it currently runs successfully. | Verifying "does X work?" requires running X (or reading recent run logs). Haiku skips this step and infers from config existence. |
| Treating "the hook ID exists" as evidence the hook's `files:` regex covers the right paths | Haiku flagged issue #636 ("myrmidons-doc-drift pre-commit hook `files:` pattern misses docs/ subdir") as ALREADY-DONE because the hook ID was in the config. | The `files:` regex was the actual subject of the issue. Haiku didn't read it. Sonnet would have. | Issues that ask about a specific config attribute (regex, default value, ordering) require READING that attribute — not just confirming the surrounding key exists. Haiku does not zoom in to the right granularity. |
| Assuming "Haiku is fine for low-stakes batch work" generalizes to triage | Pattern from `haiku-batch-worktree-agents` (Haiku for 60-80 mechanical issue impls) was extended to triage by analogy. | Mechanical impl is bounded by an explicit per-issue workflow template; triage requires open-ended judgment about scope and existence. The two are categorically different despite both being "batch" work. | "Batch" is not a meaningful axis for model selection. The axis is **judgment required vs. mechanical execution**. Triage is judgment, even when 200 issues at a time make it feel mechanical. |

## Results & Parameters

### The rule, stated three ways

**As a one-liner:** Haiku for mechanical fixes only. Sonnet (or Opus) for everything else.

**As a quota-fallback policy:** When Sonnet/Opus is exhausted on an analysis task, ask the user. Never silently substitute Haiku.

**As a prompt-time check:** If the agent's prompt contains the words *classify*, *decide*, *estimate*, *triage*, *audit*, *review*, *verify whether*, *which of these*, or *is this already done*, the model is Sonnet (or Opus). Period.

### Tasks Haiku CAN do

| Task | Why Haiku is fine |
|------|-------------------|
| Single-issue implementation with explicit file allowlist + `Run:` commands | Workflow is fully specified; no judgment required |
| Lint fixes ≤50 LOC under a documented rule set (e.g. ruff, shellcheck) | Mechanical pattern-matching against rule list |
| Rebase fix-ups with explicit conflict-resolution policy ("prefer ours for X, prefer theirs for Y") | Conflict resolution is rule-driven, not judgment-driven |
| Bulk file renames / mechanical refactors driven by a sed-like pattern | Pure transformation; no semantic decision |
| Filling docstring templates from a defined schema | Template fill, not generation |
| Bulk `gh issue create` calls from fully-specified inputs | No design decisions in the loop |

### Tasks Haiku CANNOT do (use Sonnet/Opus)

| Task | Failure mode |
|------|--------------|
| Issue triage / EASY-MEDIUM-HARD classification | Conflates issue body wording with codebase reality |
| ALREADY-DONE detection on existing issues | Flags as done based on keyword presence; false positives are the norm |
| Repo audits / repo-analyze-strict | Misses bugs that require reading two files together and reasoning about their interaction |
| Scope estimation / "how big is this issue?" | Underestimates because it doesn't trace dependencies |
| Code review / PR review | Misses semantic issues; rubber-stamps surface-level patterns |
| Root-cause analysis / debugging | Stops at first plausible explanation rather than verifying |
| Planning / design / architecture decisions | Produces shallow, generic plans without engaging with constraints |
| "Verify whether X actually exists / works / is correct" | This is the canonical failure mode — see Failed Attempts table above |

### The 4/4 false-positive incident (2026-05-07 Myrmidons session)

| Issue | Haiku said | Reality | Why Haiku was wrong |
|-------|-----------|---------|---------------------|
| #517 (bats test for gitleaks CHANGELOG.md allowlist) | ALREADY-DONE | Test file does not exist | Saw gitleaks discussion in `.gitleaks.toml`, conflated with test existence |
| #495 (pre-commit actionlint broken on Go <1.16) | ALREADY-DONE | Hook still broken in latest CI run | Saw `actionlint` in pre-commit config, did not check CI logs |
| #636 (myrmidons-doc-drift `files:` regex misses docs/) | ALREADY-DONE | Regex still misses docs/ | Saw hook ID exists, did not read the regex |
| (4th issue, same class) | ALREADY-DONE | Not done | Same conflation pattern |

**False-positive rate:** 4/4 = 100%. Sonnet on the same prompt class would not have made any of these errors (verified by re-running the equivalent triage on Sonnet after quota reset).

### Quota-exhaustion playbook

When the orchestrator hits a Sonnet/Opus quota error mid-task:

```text
1. Identify which class of work the blocked sub-agents were doing.
   - Mechanical fix? → Substituting Haiku is fine. Document the swap.
   - Analysis / triage / classification / verification?
       → DO NOT substitute Haiku silently.

2. Surface to the user with three options:
   (a) Wait for quota reset (usually 4–6h on a session limit).
   (b) Run the analysis manually in the orchestrator with no sub-agent.
   (c) Authorize Haiku with explicit "results will need 100% manual
       re-verification" caveat. The user's call.

3. If user picks (c), record every Haiku output as suspect. Re-verify
   every positive flag (especially ALREADY-DONE) by hand before acting.
```

### Cross-references in this knowledge base

- `wave-based-bulk-issue-triage.md` line 71 already documents "Why Explore not Haiku: Classification requires reading issue context and judging scope". This skill is the **expanded, evidence-backed** version of that note, with the failure mode that motivated it.
- `automation-claude-model-per-phase.md` documents the phase-to-tier mapping for the Hephaestus pipeline. This skill is the **why** behind the planner=Opus / reviewer=Sonnet / implementer=Haiku split: the implementer is mechanical, the reviewer/planner are judgment-required.
- `haiku-batch-worktree-agents.md` documents Haiku's strengths for bounded mechanical impl work. This skill is the **boundary** of that pattern: do not extend it to triage, audit, or classification.
- `already-done-issue-detection.md` is the workflow whose accuracy Haiku destroys. Always run that workflow on Sonnet (or Opus).

## Verified On

| Project | Date | Context | Outcome |
|---------|------|---------|---------|
| Myrmidons | 2026-05-07 | Triage session over ~200 GitHub issues; Sonnet quota exhausted mid-session; Haiku triage agent substituted | 4/4 ALREADY-DONE flags from Haiku were false positives. Forced full manual re-verification. User explicitly directed: "don't ever use HAIKU for analysis, only for fixing small issues. Only use Opus/Sonnet (when its available) for analysis." |
