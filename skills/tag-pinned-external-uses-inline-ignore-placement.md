---
name: tag-pinned-external-uses-inline-ignore-placement
description: "Suppress an unpinned-action scan finding on a reusable workflow pinned to a protected signed tag, and place the ignore comment on the reported `uses:` line. Use when a security scanner reports an unpinned action reference that policy accepts, when a new reusable-workflow call adds such a finding, or when you add inline suppressions during a change and the scan gate still fails."
category: ci-cd
date: "2026-11-01"
version: "1.0.0"
user-invocable: false
verification: verified-local
tags: [zizmor, unpinned-uses, reusable-workflow, tag-pin, inline-suppression, ignore-comment, gha-security-scanning-supply-chain, permissions-scope, ownership, gate-verification]
---

# Place an Inline Ignore on the Reported Line for a Tag-Pinned External Workflow

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-01 |
| **Objective** | Accept an unpinned-action finding for one policy-approved tag-pinned workflow, without widening suppression to sibling jobs, and keep the security scan gate green. |
| **Outcome** | Operational. A scan gate reported nine high findings in a change that added seven tag-pinned reusable-workflow calls and one workflow-level permission grant. A rationale comment above the job did not suppress the finding. Moving one `# ignore[...]` comment onto the reported `uses:` line removed all nine findings. No further scanner rule required rework. |

## When to Use

- A security scanner reports an unpinned action reference for a reusable workflow that policy pins to a protected signed tag with an immutable release.
- A change adds new external reusable-workflow calls, and the scan gate then fails.
- A repository accepts a permission grant that a scanner reports as too broad, and the repository needs a recorded rationale.
- You added an inline suppression and the gate result did not change.

## Verified Workflow

### Quick Reference

Put the ignore comment on the same line as the reported `uses:` value:

```yaml
  contract-check:
    uses: <user>/<repo>/.github/workflows/<name>.yml@<protected-tag>  # zizmor: ignore[unpinned-uses]
    permissions:
      contents: read
```

Run the gate command that the repository enforces, and read its exit status. Do not read the
finding count alone.

### Suggested Approach

1. Run the enforced scan command with no filter, and keep its exit status. A suppressed finding
   often stays in the ignored count. Only the exit status shows whether the gate passes.
2. Read the reported line and column. A scanner attaches an inline ignore to the line that it
   reports. A comment above the job, above the `uses:` key, or on the job identifier does not
   suppress the finding.
3. Record the policy basis in a comment near the call: the protected tag, the immutable release,
   and why a content hash does not apply. Keep this rationale next to the suppression so a reviewer
   can audit the exception.
4. Suppress only the reported rule. Do not add a scanner-wide configuration exemption, a severity
   remap, or a job identifier that suppresses more rules. A single-line ignore for one rule keeps
   the exemption bounded to that call.
5. Check the permission scope of a new call. A read-only job declares its own `permissions` block.
   A job-level declaration does not inherit the write grants of the workflow. Add an ignore only to
   the workflow-level grant that the scanner reports for the job that needs it, and keep a comment
   that names the job that needs it.
6. Re-run the enforced command and confirm a zero exit status and no unignored finding. Then re-run
   the tests that read the workflow file. A structural test that compares a job's keys can fail
   after a comment-only edit if the parser reads comments as data.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| 1 | Put the ignore comment and the rationale on the lines above the job identifier | The finding persisted with nine unignored high findings; the scanner attaches an inline ignore to the reported line, not to the block that contains it | Place the ignore on the exact line that the scanner reports, and keep the rationale beside it |
| 2 | Confirm success from a counts line that read "no unignored findings" | The command still exited with a failure status because suppression did not take effect | Verify with the exit status of the enforced command, not the counts text |

## Results & Parameters

### Configuration

| Parameter | Value | Note |
| ----------- | ------- | ------ |
| Scan mode | Offline, medium severity and above, over the workflow and action roots | Matches the repository pre-commit gate |
| Suppression syntax | `# zizmor: ignore[rule]` on the reported line | One rule per comment |
| Rule for a tag-based reusable-workflow pin | `unpinned-uses` | Applies only to the policy-approved tag pin |
| Rule for a workflow-level write grant | `excessive-permissions` | Applies only to the grant that the tag-push job needs |

### Expected Output

- The scan command exits with status 0.
- The suppressed finding moves to the ignored count with no unignored finding.
- The structural workflow tests still pass.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Governance-adoption change in a shared tooling repository | Seven new read-only reusable-workflow calls pinned to a protected signed tag, plus one pre-existing workflow-level write grant | Nine high findings before the comment move; zero unignored findings and exit status 0 after it; the read-only job declarations were unchanged. See [notes](tag-pinned-external-uses-inline-ignore-placement.notes.md) |

## References

- [GitHub Actions security scanning and supply-chain checks](gha-security-scanning-supply-chain.md)
- [Generated artifacts go stale after input changes](generated-artifacts-stale-after-input-change-pinned-regeneration.md)
- zizmor audit documentation: <https://docs.zizmor.sh/audits/#unpinned-uses>