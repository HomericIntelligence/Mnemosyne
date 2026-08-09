---
name: documentation-agent-provider-data-boundaries
description: "Document direct model-provider processing without making false local-only or universal-retention claims. Use when: (1) local automation dispatches repository prompts through provider CLIs, (2) several providers have different authentication and retention controls, (3) an optional adapter exposes only a bounded smoke path, or (4) privacy docs need closed inventory and processor tables with tested lifecycle ownership."
category: documentation
date: 2026-08-07
version: "1.0.0"
user-invocable: false
verification: unverified
tags: [privacy, data-inventory, external-processors, claude, codex, pi, retention, deletion, no-proxy]
---

# Document Direct Agent-Provider Data Boundaries

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-08-07 |
| **Objective** | Make privacy documentation accurately describe which selected repository material leaves a locally operated automation tool, who receives it, who controls retention, and how deletion works. |
| **Outcome** | Proposed closed-inventory and processor-matrix pattern from ProjectHephaestus issue #2566, including direct Claude/Codex transport, bounded Pi smoke processing, operator-managed credentials, and no project proxy. |
| **Verification** | unverified — official provider guidance was checked, but the documentation and semantic regression tests were not implemented in this learn run. |

## When to Use

- A project says it runs locally and readers could infer that all processed data stays on the operator's machine.
- Automation constructs prompts from issues, pull requests, diffs, repository files, plans, reviews, or comments and dispatches them through a provider CLI.
- Claude, Codex, GitHub, and an operator-selected adapter receive different data and use different account terms.
- A provider integration is generally blocked but exposes a narrow smoke-test seam that must not be described as full automation.
- Privacy documentation lists data categories without naming local location, external recipient, retention owner, and deletion route.
- Tests assert links or nonempty table cells but do not freeze the complete inventory or row-specific lifecycle claims.

## Proposed Workflow

> **Warning:** This workflow has not been validated end-to-end. Treat it as a documentation and test contract until the target repository's tests and CI pass.

## Verified Workflow

> **Warning:** The repository validator requires this heading, but the workflow is unverified. Only the underlying source inspection and official-provider guidance lookup were performed.

### Quick Reference

~~~text
Local operation != local-only processing.

For every data category record:
  local/project location
  external recipient
  retention owner
  deletion path

For every external processor record:
  data received
  direct transport/authentication
  retention/terms authority
  deletion route
  whether the project operates a proxy
~~~

### Detailed Steps

1. **Trace the real dispatch boundary from code.** Locate prompt construction and provider dispatch, then enumerate the material selected into each prompt. Do not infer privacy behavior from the repository's local installation model. A local coordinator can still send issue, PR, diff, review, plan, comment, and repository content directly to a remote service.

2. **State the transport model plainly.** Say that the selected provider CLI connects directly using operator-managed authentication and that project infrastructure does not proxy, inspect, retain, or delete the provider-side copy. Keep local credential storage and issuer-side OAuth/token/API-key revocation separate.

3. **Separate providers by actual scope.** Document Claude and Codex as normal selected automation providers. Document Pi or another optional adapter separately when normal automation is fail-closed and only a fixed, tool-free smoke prompt/result crosses the boundary. Say explicitly that the smoke path does not automatically include GitHub content, repository files, diffs, or automation state.

4. **Create a closed data inventory.** Define the expected category names as a test constant, not an open-ended prose list. For the Hephaestus design, the seven categories were repository/GitHub content; selected prompts, responses, and session metadata; credentials/account metadata; automation state/worktrees/logs; Pi smoke artifacts; crash bundles; and observability metrics.

5. **Assign lifecycle ownership per row.** Each inventory row names local location, external recipient, retention owner, and actionable deletion path. Distinguish deleting local build state, provider CLI state, GitHub content, provider-side prompts, credentials, crash bundles, and downstream metric copies.

6. **Create a closed processor matrix.** Replace claims such as “sub-processors: none” with exact rows for GitHub, Anthropic/Claude, OpenAI/Codex, and the operator-selected Pi provider. Each row states data received, direct transport/authentication, retention and terms authority, deletion route, and “No” for a project proxy.

7. **Do not promise a universal provider retention period.** Claude Code and Codex behavior depends on the consumer, commercial, API, enterprise, organization, and account controls selected by the operator. Link current official provider guidance and tell operators to review the terms that apply to their account before sending sensitive content.

8. **Keep one authoritative privacy document.** Operational service inventories and provider-specific guides should link to the authoritative processor matrix and restate only their narrower runtime boundary. Preserve intentional historical service rows when architecture records and tests require them; remove retired tools only from active-control language.

9. **Test semantics, not just Markdown presence.** Parse tables by heading and freeze exact row sets and headers. Add row-specific assertions for provider deletion, CLI storage, credential revocation, build cleanup, private smoke-artifact deletion, crash-bundle deletion, and process-lifetime metrics. Freeze the processor set, direct transport, operator credentials, provider-controlled retention, deletion routes, smoke-only boundary, and no-proxy values.

10. **Ban misleading absolutes.** Regression tests should reject unconditional “all data stays local,” “sub-processors: none,” fixed provider-wide retention promises, and “credentials are never persisted anywhere.” Resolve local Markdown targets so a filename-shaped but broken link cannot pass.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| ------- | -------------- | ------------- | -------------- |
| Equate locally operated with local-only | The policy described installation topology, not outbound provider calls. | Readers could reasonably believe selected repository data never left the machine. | Trace prompt dispatch and disclose direct remote processing explicitly. |
| Claim no subprocessors | GitHub and selected model providers receive project or prompt data directly. | The processor inventory contradicted actual runtime behavior. | Use a closed processor table and distinguish “no project proxy” from “no external processor.” |
| Promise one provider retention period | Product tier, account type, organization controls, legal exceptions, and current terms vary. | A fixed statement becomes inaccurate for another authentication mode or after provider policy changes. | Assign retention authority to the selected provider/product/account and link current official controls. |
| Treat credentials as absent locally | Provider CLIs and environments can store tokens, OAuth grants, account state, or API keys outside project state. | Deleting build output would not revoke access or clear CLI credentials. | Document logout/local removal and issuer-side revocation separately. |
| Describe bounded smoke as full provider integration | The optional adapter sent only an explicit smoke prompt while normal automation remained blocked. | The policy overstated both data exposure and product capability. | Give the smoke seam its own row and explicitly exclude automatic repository/GitHub context. |
| Check only links and nonempty cells | Generic text could satisfy tests while losing a category, processor, or lifecycle responsibility. | Documentation drift remained semantically invisible. | Parse tables, freeze closed sets, and assert row-specific facts and forbidden claims. |

## Results & Parameters

### Closed Inventory Contract

| Set | Required members |
| ------- | ------- |
| Data categories | Repository/GitHub content; prompts/responses/session metadata; credentials/account metadata; automation state/worktrees/logs; Pi smoke artifacts; crash bundles; observability metrics |
| External processors | GitHub; Anthropic (Claude); OpenAI (Codex); operator-selected Pi provider |
| Inventory columns | Data category; local/project location; external recipient; retention owner; deletion path |
| Processor columns | Service; data received; transport and authentication; retention/terms authority; deletion route; project proxy |

### Provider Boundary

| Provider path | Automatic scope | Authentication | Retention and deletion authority |
| ------- | ------- | ------- | ------- |
| Claude automation | Selected prompt and included issue/PR/diff/repository/review material | Operator-managed Claude/provider credentials | Selected Anthropic product, account, organization settings, and current terms |
| Codex automation | Selected prompt, included repository material, and generated output | Operator-managed Codex/OpenAI credentials | Selected OpenAI product, account, organization settings, and current controls |
| Pi smoke | Explicit smoke prompt and result only; normal automation remains blocked | Operator-selected adapter configuration | Operator-selected provider terms and controls |
| GitHub | Repository, issue, PR, comment, diff, and workflow data used by the repository | Operator-managed GitHub credentials | GitHub account/repository settings and terms |

### Structural Test Pattern

~~~python
EXPECTED_DATA_CATEGORIES = {
    "Repository and GitHub content",
    "Selected agent prompts, responses, and session metadata",
    "Credentials and account metadata",
    "Automation queues, worktrees, and logs",
    "Pi smoke prompt and result",
    "Crash bundles",
    "Observability metrics",
}

EXPECTED_PROCESSORS = {
    "GitHub",
    "Anthropic (Claude)",
    "OpenAI (Codex)",
    "Operator-selected Pi provider",
}
~~~

Expected behavior: table parsing fails if a row is added, removed, renamed, left generic, loses a deletion route, moves retention responsibility to the project, or claims a project proxy exists.

## Verified On

| Project | Context | Details |
| ------- | ------- | ------- |
| ProjectHephaestus | Issue #2566 privacy-policy design | Runtime source boundaries and current official provider guidance inspected; documentation implementation and CI remain pending. |

## References

- [Anthropic organization data retention guidance](https://privacy.anthropic.com/en/articles/7996866-how-long-do-you-store-my-organization-s-data)
- [Anthropic consumer deletion guidance](https://privacy.anthropic.com/en/articles/7996878-can-you-delete-data-sent-via-claude-ai)
- [OpenAI API data controls](https://platform.openai.com/docs/models/default-usage-policies-by-endpoint)
- [Codex CLI authentication guidance](https://help.openai.com/en/articles/11381614-api-codex-cli-and-sign-in-with-chatgpt)
- ProjectHephaestus ADR-0005 (provider ownership)
