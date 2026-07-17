---
name: create-reusable-utilities-hephaestus-port
description: "Port project-local utilities into the shared Hephaestus automation repository. Use when: (1) project-local automation has a demonstrated cross-project use case, (2) equivalent behavior may already exist in Hephaestus and must be extended instead of duplicated, (3) a typed reusable interface must be separated from source-repository policy"
category: tooling
date: 2026-07-16
version: "1.0.0"
user-invocable: false
tags: [reuse, hephaestus, utilities, interface-design]
---

# Create Reusable Utilities (Hephaestus Port)

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-07-16 |
| **Objective** | Standard workflow for porting utilities with cross-project value into the shared Hephaestus automation repository |
| **Outcome** | Operational — migrated from the Athena `create-reusable-utilities` skill into standard knowledge |

## When to Use

- Project-local automation has a demonstrated cross-project use case and belongs in the shared Hephaestus automation repository.
- Do NOT use for one-off scripts with a single consumer — reuse must be demonstrated, not speculative.

## Required repository and authority

- Prepare Hephaestus at `$HOME/.agent_brain/automation` by following Athena's canonical dependency-resolution contract exactly (owner precedence, trust gates, checkout rules, revalidation). Report the exact repository, commit SHA, and trust basis. Any preparation or revalidation failure is blocking.
- **External-write authority checkpoint:** a direct user request to port a utility authorizes the declared branch, edit, commit, push, and PR workflow. An indirect recommendation or invocation does not. Before creating mutable state, show the resolved repository/SHA/trust basis, proposed branch, owned files, validation, and PR target, then obtain explicit approval. Read-only overlap analysis never authorizes a later write.

## Verified Workflow

### Detailed Steps

1. Read the source utility, its callers, tests, configuration, error behavior, and license.
2. Search the resolved Hephaestus checkout for equivalent or overlapping behavior. Extend an existing abstraction instead of creating a duplicate.
3. Separate reusable behavior from source-repository policy, paths, global state, and output.
4. Design a typed programmatic interface first. Make filesystem, environment, clock, network, and process dependencies injectable where useful.
5. Follow the resolved checkout's current package layout and repository instructions; never assume example paths from a prior version.
6. Write failing behavior and error-path tests in the resolved repository before implementation.
7. Add a thin CLI only when a real command-line consumer exists. Keep parsing and presentation out of the reusable core.
8. Run Hephaestus's repository-defined validation and focused/full tests.
9. Deliver the Hephaestus change through its signed, DCO-attested PR workflow. Do not edit or pin another repository as part of the same unapproved operation.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Copy-paste port | Moving the utility verbatim with source-repo paths and policy | The "reusable" code still encoded one repository's assumptions | Strip source-repository names, paths, and policy from the reusable interface |
| Assuming prior layout | Using package paths remembered from an earlier Hephaestus version | Layout had changed; the port landed in a dead location | Read the resolved checkout's current layout every time |

## Results & Parameters

### Acceptance criteria

- No source-repository names, paths, or policy remain in the reusable interface.
- Existing behavior and failures are covered by tests.
- Public types and errors are documented.
- License and attribution are compatible and preserved.
- The source repository migration is a separate, explicit follow-up after the shared change lands.

### Expected Output

Report the resolved Hephaestus repository/SHA, overlap analysis, interface decision, files changed, tests and gates run, compatibility/migration notes, and PR URL when authorized.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Athena | Shipped as the `create-reusable-utilities` plugin skill; exercised for Hephaestus ports | Migrated 2026-07-16 |

## References

- Athena dependency-resolution contract: `docs/dependency-resolution.md` in HomericIntelligence/Athena
- Related: [finish-branch-delivery-workflow.md](finish-branch-delivery-workflow.md)
