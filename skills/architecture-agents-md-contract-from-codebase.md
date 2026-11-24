---
name: architecture-agents-md-contract-from-codebase
license: BSD-3-Clause
description: "Plan an AGENTS.md contract from repository behavior, ownership, and host constraints; link the canonical authority policy, reuse documentation checks, and record unverified assumptions."
category: architecture
date: 2026-11-23
version: "1.2.0"
user-invocable: false
verification: unverified
tags:
  - agents-md
  - agent-behavior-contract
  - planning
  - derive-from-codebase
  - authority
  - host-permissions
  - markdownlint
  - ci-gate
  - drift-guard
  - line-number-drift
  - unverified-assumptions
history-source: "https://github.com/HomericIntelligence/Mnemosyne/blob/1956c91d76867bc2e484eaf573a57051855186f8/skills/architecture-agents-md-contract-from-codebase.history"
history-cleanup-date: "2026-09-20"
---

# Planning an AGENTS.md Agent-Behavior Contract Derived From the Codebase

> **Warning:** This workflow has not been validated end-to-end. Treat it as a hypothesis
> until CI confirms it.

Follow the [agent authority and host permissions policy](https://github.com/HomericIntelligence/Athena/blob/main/docs/policies/agent-authority.md)
for authority, host permissions, security invariants, and stop conditions.

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-06-20 |
| **Objective** | Plan an `AGENTS.md` agent-behavior contract. Ground each rule in repository behavior and policy. Keep host mechanics in the host configuration or adapter reference. |
| **Outcome** | Plan produced only. No documentation change, lint run, or CI run was executed. The durable value is the planning pattern and the risk inventory. |
| **Verification** | unverified. This is a planning artifact. Every cited line number and lint claim is an assumption, not a confirmation. |
| **Category** | architecture / planning |
| **Related Issues** | Odysseus #186 |

Base agent guidance on actual repository behavior. Distinguish host-enforced limits
from workflow suggestions, and state unresolved assumptions. Existing authorization
covers routine work; reserve permission requests for missing authority or a material
ambiguity. Link the canonical authority policy. Do not copy host permission flags or
tool names into the contract.

---

## When to Use

Use this skill when:

1. You plan or add an `AGENTS.md` agent-behavior contract to a repository. The contract
   covers scope, permitted and prohibited actions, coordination, escalation, and
   verification commands.
2. You need to derive the permitted-action set, off-limits set, and escalation path
   from repository behavior and policy. Do not derive portable authority from one
   harness invocation.
3. You want to use an existing markdownlint CI gate instead of adding a new CI job.
4. You want a drift guard for a stable behavior or configuration contract.
5. A sibling `AGENTS.md` exists in the ecosystem and you want to reuse its structure
   without letting the contracts diverge.

Do NOT use this as a record of executed work. It is a plan with open assumptions.

---

## Verified Workflow

> **Warning:** This section is a proposed workflow, not a verified one. No `AGENTS.md`
> was written, markdownlint was not run against a draft, and CI did not confirm it.
> Re-grep by content. Do not trust line numbers from an old snapshot.

### Quick Reference

```text
1. Glob **/AGENTS.md and reuse a sibling's section structure.
2. Derive each rule from its owner:
     authority and scope      <- canonical policy and task authority
     permitted actions        <- repository policy and ownership
     off-limits set           <- repository invariants and security policy
     host mechanics           <- host configuration or adapter reference
   Link the canonical policy. Do not copy permission flags or tool names.
3. Extend the existing markdownlint file list by one filename.
4. Run markdownlint on the draft.
5. Add a behavior or configuration drift guard. Do not pin prose.
6. Cross-reference the document without disturbing harness-loaded instructions.
7. Scope the new AGENTS.md to its own repository.
```

1. **Find the in-ecosystem template first.** Run `Glob **/AGENTS.md`. If a sibling
   exists, reuse its section set where it helps. Omit sections that do not apply.

2. **Give each rule an owner.** Derive authority and scope from the canonical policy
   and the task. Derive permitted actions from repository policy and ownership. Derive
   the off-limits set from repository invariants and security policy. Keep exact host
   flags, tool names, and matching rules in the host configuration or adapter reference.
   Re-grep each fact by content because line numbers drift.

3. **Use the existing enforcement gate.** CI often lints a fixed file list. Extend that
   list by the new filename. Do not add a second markdownlint job.

4. **Prove the lint result.** Confirm the markdownlint configuration covers the new
   document. Run markdownlint against the draft before you claim a pass. Configuration
   that disables some rules does not prove that the document passes.

5. **Add a behavioral drift guard.** Tie a stable behavior or configuration value to its
   source. Use a focused test or a configuration check. Do not add a test for prose
   wording or a duplicated host flag string.

6. **Make the contract discoverable.** Add a banner or link in the repository entry
   point. Do not disturb the section structure that the harness loads as authoritative
   project instructions. Check that each relative link resolves.

7. **Scope the new AGENTS.md to its own repository.** With two `AGENTS.md` files,
   explicitly scope the root contract. Do not duplicate the sibling's rules. Divergence
   is the long-term failure mode.

### Assumptions and risks to communicate

- **Unverified line numbers.** A plan can cite exact lines from grep snapshots. Line
  numbers drift. Re-grep by content.
- **Markdownlint pass is unproven until it runs.** A disabled-rules configuration is
  not a test result.
- **Project-instruction edits can collide.** `CLAUDE.md` or `AGENTS.md` can be loaded as
  authoritative instructions. A banner must not disturb their structure.
- **Multiple AGENTS.md files can diverge.** Scope each contract explicitly.
- **Relative-link resolution depends on directory depth.** Confirm each link target.

---

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| ------- | -------------- | ------------- | -------------- |
| Copying host permission values from a runner | Putting a bypass flag and a broad tool list into `AGENTS.md` as the permitted-action contract | It normalized a bypass, made host mechanics look like repository authority, and became stale when the host changed | Link the canonical authority policy. Keep host flags and tool names in the host adapter reference. |
| Trusting grep line numbers as stable | Citing exact source lines from a grep snapshot | Line numbers drift; the cited line may no longer be the right one | Re-grep by content and anchor each fact to a string match. |
| Asserting markdownlint passes from configuration alone | Concluding a draft is lint-clean because some rules are disabled | The remaining enabled rules never ran | Run markdownlint against the drafted content before claiming a pass. |
| Adding a new CI markdownlint job | Proposing a separate job for the new document | It duplicates the existing gate and the two gates drift | Extend the existing fixed file list by one filename. |

---

## Results & Parameters

The plan produces one root `AGENTS.md` whose contract is derived, not invented:

| Contract element | Derived from |
| ---------------- | ------------ |
| Section structure | A sibling `AGENTS.md`, reused where it helps |
| Authority and scope | The canonical authority policy and task authority |
| Permitted and prohibited actions | Repository policy, ownership, and security invariants |
| Host mechanics | Host configuration or adapter reference, linked rather than copied |
| Enforcement | The existing markdownlint fixed file list, extended by one line |
| Drift guard | A focused behavior or configuration check, not a prose-string test |
| Discoverability | A banner or link in `CLAUDE.md`, `README.md`, or `docs/README.md` |

All items are proposed. No file was written, and no lint or CI ran. The line numbers
and the markdownlint result are assumptions.

---

## Verified On

| Project | Context | Details |
| ------- | ------- | ------- |
| Odysseus | Issue #186 planning ("add a root AGENTS.md") | Planning only. **Unverified.** No `AGENTS.md` was written. Markdownlint and CI never ran. All cited line numbers and the lint pass are assumptions. |

## References

- [Agent authority and host permissions policy](https://github.com/HomericIntelligence/Athena/blob/main/docs/policies/agent-authority.md)
- `automation-agent-tool-scopes-least-privilege.md` for the version-scoped Claude adapter reference