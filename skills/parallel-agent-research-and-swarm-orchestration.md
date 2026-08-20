---
name: parallel-agent-research-and-swarm-orchestration
description: "Orchestrate dependency-aware parallel agents for research review, corpus audits, multi-phase delivery, and GitHub issue-to-PR pipelines. Use when work has independent evidence domains, explicit integration gates, and enough scale to justify coordinator overhead."
category: architecture
date: 2026-05-19
version: "2.0.0"
license: BSD-3-Clause
user-invocable: false
verification: verified-ci
history: parallel-agent-research-and-swarm-orchestration.history
tags:
  - swarm
  - parallel-agents
  - orchestration
  - research-review
  - corpus-audit
  - github-pipeline
  - worktrees
  - evidence
  - feedback-loop
---

# Parallel Agent Research and Swarm Orchestration

## Overview

Parallelism is useful only when ownership is disjoint and integration is explicit. A coordinator
defines the shared baseline, dependency graph, output contract, concurrency cap, and decision gates;
specialists gather evidence or implement bounded slices; the coordinator verifies and synthesizes.
Agents do not share a branch/index, approve destructive actions, or turn partial reports into facts.

The patterns have CI and operational evidence across research corpora and software delivery. Case
metrics and domain-specific findings are indexed in
[parallel-agent-research-and-swarm-orchestration.notes.md](parallel-agent-research-and-swarm-orchestration.notes.md),
and the full superseded version is in
[parallel-agent-research-and-swarm-orchestration.history](parallel-agent-research-and-swarm-orchestration.history).

## When to Use

- Ten or more documents need independent citation, complexity, novelty, and feasibility review.
- A corpus needs a multi-dimensional audit with file/line evidence and a synthesis grade.
- Delivery spans three or more dependent phases such as cleanup, rebase, implementation, CI, merge,
  and knowledge capture.
- Many independent issues can move through a repeatable plan/review/implement/CI pipeline.
- Post-review recommendations split into disjoint documentation, test, and code changes.
- Repository-wide work needs isolated worktrees and a bounded merge/integration sequence.

Do not use a swarm for one well-defined edit, tightly coupled files with no safe ownership split, or
work whose coordination cost exceeds execution. Run sequentially when the host cannot delegate.

## Verified Workflow

### 1. Establish the shared baseline

Before dispatch, the coordinator records:

- immutable repository/document revisions;
- authoritative external references and calculation assumptions;
- acceptance criteria and verification commands;
- task dependency graph and file/artifact ownership;
- maximum useful concurrency and resource budget;
- destructive/external-write approval boundaries;
- output schema and evidence citation format.

Every agent receives the same baseline. Do not let each reviewer independently choose model
dimensions, source versions, or grading rules; incomparable inputs make synthesis invalid.

### 2. Decompose by independent evidence or ownership

For a per-document research review, use one lead per idea and bounded specialists such as:

1. citation verifier;
2. mathematical/complexity auditor;
3. literature gap finder;
4. baseline comparison validator;
5. feasibility and implementation checker.

For a corpus audit, group dimensions that share tools and inputs, then synthesize centrally. For
software delivery, assign explicit files/modules or separate worktrees. Never ask two agents to edit
the same artifact concurrently.

### 3. Define an agent output contract

Each result includes:

| Field | Required content |
| --- | --- |
| Scope | Assigned documents/files and immutable base |
| Findings | Severity or decision plus concise rationale |
| Evidence | File/line, command output, authoritative URL, or run link |
| Verification | Executed command and observed status |
| Uncertainty | Missing access, assumptions, and unverified claims |
| Handoff | Changed files/commit or read-only artifact path |

Research reports separate quoted/source facts, derived calculations, and judgments. Derived numbers
show their formula and inputs, not “from first principles” without arithmetic.

### 4. Dispatch in dependency-aware waves

Use the maximum safe concurrency, not the maximum available slots. Typical flow:

1. read-only discovery and baseline verification;
2. independent analysis or leaf implementation;
3. coordinator synthesis and decision gate;
4. dependent implementation/integration;
5. validation and remediation;
6. publication/merge only when authorized;
7. knowledge capture after outcomes are stable.

Start later waves only when their dependency outputs are verified. If a shared base moves, rebind all
remaining work. Preserve unfinished worktrees for recovery rather than improvising cleanup.

### 5. Keep a single integration owner

The coordinator verifies every agent claim, checks file ownership, and integrates in dependency
order. For code:

- one branch/worktree per implementation unit;
- stage only owned files;
- signed, policy-compliant commits;
- focused checks before handoff;
- integration tests after composition;
- lease-protected updates after rebases.

For research, the coordinator checks contradictions, duplicate findings, baseline consistency, and
systemic errors before writing the summary.

### 6. Apply structural grade and stop rules

Define non-compensating failures before review. For example, a missing train/test split or an
incorrect system specification may cap an overall corpus grade even when prose and citations score
well. Critical correctness or provenance defects cannot be averaged away by presentation quality.

Stop or re-plan when:

- an agent reports overlapping ownership;
- the baseline or source revision changed;
- required evidence is unavailable;
- resource pressure makes concurrency unsafe;
- a destructive or external action lacks authority;
- a dependent result contradicts the approved interface.

### 7. Operate a six-phase issue-to-PR pipeline

For each repository/iteration, keep the phases explicit:

1. plan open in-scope issues and publish canonical plans;
2. review plans and record GO/NOGO evidence;
3. implement only approved plans in isolated worktrees;
4. review PRs and attach actionable inline findings;
5. address unresolved review threads using the original implementation context when available;
6. classify and drive current-head CI green, then enable merge only under repository policy.

Persist issue, plan, branch, PR, session, head SHA, review state, and check state. Pre-discovery guards
must handle issues that produced no PR. A final-loop merge action must not run during exploratory
iterations.

Inline GitHub review comments require file/path/line coordinates bound to the PR diff. After fixes,
read unresolved threads rather than assuming a new commit resolved them.

### 8. Monitor and recover without losing evidence

Poll boundedly, report meaningful state changes, and retain last known output. API rate limits,
context limits, or failed background agents do not justify fabricated results. Reduce concurrency,
resume from artifacts, or run remaining tasks sequentially.

When an agent fails after writing a partial artifact, validate the artifact before reuse. A status
such as idle or completed is not proof that its promised files, commit, or tests exist.

### 9. Verify final synthesis

Before publishing:

- reconcile every assignment with an output or explicit failure;
- verify cited files, links, commits, and run results;
- rerun aggregate tests/validators from the integrated head;
- search for missing dimensions, duplicate coverage, contradictions, and stale baselines;
- label unverified claims and residual risk;
- separate completed outcomes from recommendations.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --- | --- | --- | --- |
| 1 | Let each reviewer choose its own baseline | Calculations and comparisons became incomparable | Inject one verified baseline into every prompt |
| 2 | Assign several agents the same files | Concurrent edits conflicted and evidence ownership blurred | Use disjoint ownership and one integrator |
| 3 | Launch all phases together | Dependents consumed incomplete or stale outputs | Dispatch in dependency-aware waves |
| 4 | Average structural failures into overall score | Severe validity defects disappeared behind prose quality | Define non-compensating caps |
| 5 | Accept agent completion status as evidence | Promised artifacts or tests could be absent | Verify filesystem, commit, and command results |
| 6 | Run excessive background concurrency | Context/resource exhaustion caused lost outputs | Cap concurrency and checkpoint artifacts |
| 7 | Auto-merge during an intermediate loop | Later review/CI work had no stable target | Restrict merge to final authorized phase |
| 8 | Post only summary review comments | Fixers lacked exact coordinates and thread state | Use diff-bound inline findings and thread readback |
| 9 | Continue after baseline changed | Parallel reports referred to different revisions | Rebind or re-plan remaining work |
| 10 | Capture lessons before outcome stabilized | Recorded guidance reflected transient failures | Learn after integrated verification |

## Results & Parameters

- Research pattern: one lead plus up to five independent evidence specialists per idea.
- Corpus audit: ten dimensions may be grouped into a small first wave, followed by central
  synthesis; correctness/specification failures can cap the grade.
- Software work: one isolated worktree and explicit file ownership per implementation unit.
- GitHub automation: six ordered phases with durable issue/PR/head/review/check state.
- Concurrency: bounded by task independence, host resources, API limits, and integration capacity.
- Final acceptance: complete assignment ledger, verified artifacts, aggregate checks, contradiction
  audit, and explicit uncertainty.

## Evidence Boundary

The indexed campaigns demonstrate the orchestration structure, not universal agent counts, model
choices, or quality thresholds. Adjust concurrency and specialist roles to the workload and host;
retain immutable baselines, disjoint ownership, explicit gates, and evidence verification.
