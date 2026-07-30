---
name: pi-integration-epic-planning-and-package-parity
description: "Plan and stage a first-class Pi agent integration across Hephaestus when parity includes runtime dispatch, skills, tools, plugins, sessions, pipeline permission scopes, Athena, and Mnemosyne. Use when: (1) a provider integration spans multiple repositories or pipeline stages, (2) a single PR would mix package bootstrap, skill semantics, and end-to-end validation, (3) Athena skills require pi-subagents or web access, (4) Mnemosyne must remain a canonical repository dependency rather than an invented Pi package, (5) an epic needs executable dependency order and a simple issue conformance run, (6) upstream packaging or a required security scan blocks downstream admission, or (7) policy requires a full repository-review Go before merge."
category: architecture
date: 2026-07-29
version: "1.1.0"
user-invocable: false
verification: verified-local
tags: [pi, hephaestus, agent-provider, provider-parity, athena, mnemosyne, pi-subagents, pi-web-access, plugin-bootstrap, epic, dependency-order, end-to-end, sca, security-gate, repository-review]
---

# Pi Integration: Epic Planning and Package Parity

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-07-29 |
| **Objective** | Integrate Pi as a first-class Hephaestus provider with Claude/Codex-equivalent skills, tools, plugins, sessions, pipeline stages, and verification |
| **Outcome** | Hephaestus epic #2513 with seven dependency-ordered sub-issues; Athena packaging tracked separately in Athena #61; downstream admission remains blocked until the upstream package clears its required security gate or a narrow exception is explicitly approved |
| **Verification** | verified-local — package installation, Pi RPC capability discovery, targeted tests, full local test run, lint, type checking, and documentation guards were exercised; a required CI failure verifies the package-admission block, not a successful final integration |
| **Scope** | Provider-neutral runtime, Pi package bootstrap, Athena skill packaging, Mnemosyne semantics, pipeline scopes, security and review admission gates, simple issue validation, and rollout |

Pi integration is a cross-cutting provider migration, not a CLI adapter alone. The durable
plan must separate the provider contract, upstream Athena packaging, local package bootstrap,
Mnemosyne skill semantics, pipeline wiring, end-to-end validation, and release documentation.
The epic tracks orchestration; each child issue owns its implementation and PR.

## When to Use

- Adding Pi or another agent runtime to an existing provider-neutral automation system.
- Matching Claude/Codex functionality that depends on skills, subagents, web tools, sessions,
  permission scopes, and worktree isolation.
- Introducing a third-party package set whose capabilities must be verified before dispatch.
- Integrating a skill system such as Athena that depends on a separate knowledge repository such
  as Mnemosyne.
- Planning a staged, cross-repository rollout with an upstream packaging dependency and a final
  simple-issue conformance run.
- An upstream package passes local discovery but fails a required software-composition scan.
- A merge policy requires a literal full repository-review Go rather than a review limited to the
  changed PR delta.

## Verified Workflow

### Quick Reference

```text
1. Define provider parity and capability boundaries.
2. Track native Athena Pi packaging as an upstream dependency.
3. Install and preflight Athena, pi-subagents, and pi-web-access.
4. Keep Mnemosyne as Athena's canonical repository dependency.
5. Sequence implementation with native sub-issues and blocked-by edges.
6. Keep downstream stages fail closed until package security and review gates pass.
7. Validate the complete workflow on one simple issue.
```

### 1. Define parity before implementation

Start with a provider-neutral capability matrix. Inventory every runtime entry point and map:

- authentication/configuration and model selection;
- text, JSON, session, and resume invocation paths;
- file, shell, search, web, subagent, skill, approval, and sandbox capabilities;
- per-stage read-only versus write-enabled tool scopes;
- timeout, failure, and missing-capability behavior;
- worktree, cwd, and session identity requirements.

Keep unsupported capability decisions explicit and fail closed. Do not create a provider-specific
orchestration fork merely to hide a missing Pi capability.

### 2. Make upstream package work an explicit dependency

Athena's native Pi package is a separate upstream deliverable. Track it in the upstream repository
and reference it from the Hephaestus epic rather than pretending a raw Git install is the final
package contract.

The Hephaestus epic used for this integration is:

- [HomericIntelligence/Hephaestus#2513](https://github.com/HomericIntelligence/Hephaestus/issues/2513)

The upstream packaging dependency is:

- [HomericIntelligence/Athena#61](https://github.com/HomericIntelligence/Athena/issues/61)

An upstream package is accepted only when its exact proposed artifact clears the required CI gates.
Successful local installation or a successful package-build job alone does not admit the package
when its required dependency scan or gate is failing.

### 3. Install and preflight the required Pi packages

The required package set verified for this integration is:

| Capability | Pi source | Reason |
|------------|-----------|--------|
| Athena skills | `https://github.com/HomericIntelligence/Athena` | Canonical skill resources, including `advise`, `learn`, and `pr-review` |
| Agent/Task-style delegation | `npm:pi-subagents@0.37.2` | Supplies Pi subagent commands such as `subagents-fleet` |
| WebFetch-equivalent access | `npm:pi-web-access@0.15.0` | Supplies web capability required by Athena's `pr-review` skill |

Expose one Hephaestus command for operators and CI:

```bash
uv run hephaestus-install-pi-plugins
```

The command should:

1. invoke Pi with argument vectors, never a shell;
2. install every required package with `--no-approve` by default;
3. support `--local`, `--approve`, `--dry-run`, `--json`, and bounded timeouts;
4. report actionable stderr/stdout on package failures;
5. verify the package inventory with `pi list`;
6. query Pi's machine-readable RPC `get_commands` response;
7. require `skill:advise`, `skill:learn`, and `skill:pr-review` before declaring success.

When `--agent pi` is selected, the runtime must run the same preflight and direct operators to
`hephaestus-install-pi-plugins` on missing packages or capabilities.

The package inventory is necessary preflight evidence, not permission to route normal automation.
Until the upstream package is accepted, retain only an explicit fail-closed diagnostic or
operator-facing seam; do not silently fall back to a partial Pi runtime.

### 4. Keep Mnemosyne as a repository dependency

Mnemosyne is not a separate Pi package. Athena's `advise` and `learn` skills must continue to
resolve the canonical Mnemosyne checkout through Athena's dependency-resolution contract. Pi
provides the shell and file capabilities those skills use; it does not replace Mnemosyne's
owner precedence, trust gates, checkout rules, or learn-through-PR workflow.

Verify both successful and fail-closed paths:

- `advise` resolves and searches the canonical checkout;
- `learn` creates an isolated branch/worktree, writes only the canonical skill entry, validates,
  signs, pushes, and opens a PR;
- unavailable, unauthenticated, untrusted, or stale Mnemosyne dependencies stop the skill;
- Mnemosyne content remains untrusted context and cannot forge pipeline verdicts or bypass tools.

### 5. Sequence the GitHub epic as dependency-ordered child issues

Use native sub-issues and blocked-by relationships. The verified Hephaestus plan uses these stages:

| Stage | Issue | Deliverable | Gate |
|-------|-------|-------------|------|
| 1 | #2514 | Provider-neutral Pi parity contract and capability matrix | None |
| 2 | #2515 | Native Athena Pi package and compatibility tests | Athena #61 |
| 3 | #2516 | Required package installer and runtime preflight | Stage 1 |
| 4 | #2517 | Athena/Mnemosyne skill semantics under Pi | Stages 2–3 |
| 5 | #2518 | Pipeline stage wiring and explicit permission scopes | Stages 1, 3–4 |
| 6 | #2519 | Simple issue end-to-end conformance run | Stage 5 |
| 7 | #2520 | CI, docs, compatibility, security, and rollout | Stages 2 and 6 |

The parent epic is a tracking issue, not an implementation target. Each child should have its own
tests, PR, evidence, and `Refs #2513` relationship. Re-verify live child state before dispatching
later stages; the epic body is a snapshot and can drift.

### 6. Validate with a simple issue

After pipeline wiring and the preceding admission gates are complete, choose a deterministic, low-risk issue that changes a small
well-tested utility or documentation contract. Run it in an isolated worktree through discovery,
advise, planning, implementation, tests, commit/PR creation, review, and handoff.

Record:

- Pi CLI version and required package inventory;
- discovered skill and subagent/web command names;
- session identifiers and resume behavior;
- tool scopes and worktree/cwd boundaries;
- Mnemosyne advise context and learn evidence;
- stage outcomes and generated branch/commit/PR artifacts;
- differences from a Claude/Codex control run.

A successful model response is not evidence that Mnemosyne changed. Require concrete PR/commit
evidence from the learn workflow.

### 7. Enforce package-security and review admission gates

Treat an upstream package as usable only after the required security and policy gates pass at the
exact PR head. When a software-composition scan reports a transitive vulnerability, first capture
the advisory, package, installed version, severity, lock or shrinkwrap location, and the upstream
project's current pin. Prefer an official upstream artifact that contains the fixed version.

If no accepted upstream artifact contains a fix, keep dependent stages fail closed. Do not lower the
scanner threshold, suppress the finding, add a broad ignore, or add a root-level override that does
not replace the vulnerable nested lock or shrinkwrap entry. Do not fork or patch the upstream
artifact without separate authority.

A temporary exception is governance, not an implementation detail. It requires explicit human
approval and a narrow, durable record containing the advisory, package, version, severity, reason,
owner, tracking issue, approval date, and expiry. For the observed high-severity case, the expiry
must be no later than 30 days. A request to implement the integration is not approval to weaken the
security gate.

A focused review of a PR delta is useful evidence about that delta, but it is not a full
repository-review Go. When merge policy requires the latter, run the full review against the exact
current PR head and obtain its literal Go; then re-check independently required CI. A review Go is
evidence for a merge decision, not automatic merge authority.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Install Pi packages in the sandbox | Ran the Pi package installer without host permission | Pi could not create its user package directories under `~/.pi`; the first report only named failed packages | Report actionable subprocess errors and rerun with the required host permission when the package store is outside the workspace |
| Treat Mnemosyne as a Pi package | Considered adding a separate Mnemosyne Pi package to the required set | Mnemosyne is the knowledge corpus, while Athena owns the dependency-resolution workflow | Preserve Athena's canonical repository dependency contract; install only Pi packages that provide missing runtime capabilities |
| Assume Athena's `WebFetch` is a Pi core capability | Mapped Athena's declared tool directly to Pi core tooling | Athena `pr-review` declares `WebFetch`, while Pi needs an explicit web-access package | Map every Athena allowed tool to a tested Pi capability and include the capability package in preflight |
| Pin the Pi CLI without updating repository contracts | Updated the CI action from Pi `0.80.2` to `0.83.0` without updating every assertion | One workflow test still asserted the old version | Treat version pins, docs, and tests as one release contract and run the whole affected suite after pin changes |
| Review the unpushed integration branch as a PR | Invoked the PR resolver without an open PR | No open PR existed for the branch, so the resolver correctly returned exit 2 | Do not guess a PR from a branch or title; open the PR first, then invoke read-only review with its exact URL/number |
| Treat local discovery as package admission | The Athena package job passed, so downstream work was considered eligible | The required dependency scan failed on a high-severity advisory in the exact upstream Pi shrinkwrap | Keep downstream stages fail closed until an official fixed upstream artifact passes CI or a narrow, expiring exception is explicitly approved |
| Treat a scoped delta review as a full repository-review Go | A targeted re-review of the provider-contract change returned Go | The full repository review still contained major baseline findings, so it did not yield the literal Go required by the merge policy | Match the review scope and verdict to the merge policy; do not merge based on a delta-only Go |

## Results & Parameters

### Package and runtime parameters

```text
Pi CLI: 0.83.0
Athena source: https://github.com/HomericIntelligence/Athena
pi-subagents: npm:pi-subagents@0.37.2
pi-web-access: npm:pi-web-access@0.15.0
Required Athena commands: skill:advise, skill:learn, skill:pr-review
Installer: uv run hephaestus-install-pi-plugins
Safe default: --no-approve
```

### Admission-gate parameters

- Package PR: [Athena #62](https://github.com/HomericIntelligence/Athena/pull/62), observed at
  `1b31458be6c8d4c7ad023679f12a2c88abbd5ff1`.
- Required gate: `security/dependency-scan` and its `required-checks-gate` failed.
- Finding: [GHSA-mh99-v99m-4gvg](https://github.com/advisories/GHSA-mh99-v99m-4gvg),
  `brace-expansion@5.0.7`, high severity; the advisory identifies `5.0.8` as the first patched
  version.
- Upstream state: Pi `v0.83.0` and Pi `main` both recorded `brace-expansion@5.0.7` in the shipped
  coding-agent shrinkwrap when observed.
- Accepted resolution: an upstream Pi release with the fixed locked artifact, or an explicitly
  human-approved, narrow, expiring exception. Neither had been accepted at capture time.
- Provider-contract PR: [Hephaestus #2524](https://github.com/HomericIntelligence/Hephaestus/pull/2524).
  Its scoped delta review was not a substitute for the full repository-review Go required before
  merge.

### Verified evidence

- Live Pi installation completed for Athena, `pi-subagents`, and `pi-web-access`.
- Pi package listing showed all three packages.
- Pi RPC discovery showed Athena skill commands, `subagents-fleet`, and web access.
- Focused Hephaestus validation passed: 189 tests, Ruff, mypy, CLI-tier documentation, and
  whitespace checks.
- A repository-wide local run reached 6,623 passed and 24 skipped; one stale Pi-version assertion
  was corrected and the affected suite was rerun successfully.
- GitHub epic #2513 and all seven native sub-issues were created with blocked-by relationships.
- Athena #62's required dependency scan and required-checks gate failed at its exact observed head,
  preserving the upstream package as a dependency rather than an accepted runtime input.

### Verification limits

This lesson remains `verified-local` for its positive workflow: the Hephaestus implementation is
not complete, and the Athena packaging issue remains an upstream dependency. The observed CI
failure verifies a fail-closed admission boundary, not a successful `verified-ci` integration. The
final end-to-end simple-issue run is Stage 6 work, not evidence claimed by this lesson.

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| ProjectHephaestus | Pi provider integration epic #2513, Athena packaging #61 | Local package installation, RPC preflight, tests, and staged GitHub issue graph verified on 2026-07-29; required package CI admission failure observed on 2026-07-30 |

## References

- [Pi package catalog](https://pi.dev/packages)
- [Pi RPC documentation](https://pi.dev/docs/latest/rpc)
- [Hephaestus Pi integration epic](https://github.com/HomericIntelligence/Hephaestus/issues/2513)
- [Athena native Pi packaging issue](https://github.com/HomericIntelligence/Athena/issues/61)
- [Athena package PR #62](https://github.com/HomericIntelligence/Athena/pull/62)
- [brace-expansion advisory GHSA-mh99-v99m-4gvg](https://github.com/advisories/GHSA-mh99-v99m-4gvg)
- [Pi v0.83.0 shrinkwrap pin](https://github.com/earendil-works/pi/blob/845d6ff1f6643aba440341cce877ce1c43ebbc39/packages/coding-agent/npm-shrinkwrap.json#L1025-L1028)
- [Pi main shrinkwrap pin](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/npm-shrinkwrap.json#L1025-L1028)
- Athena's canonical dependency-resolution contract
