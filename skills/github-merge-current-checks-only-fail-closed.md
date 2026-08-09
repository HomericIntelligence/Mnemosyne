---
name: github-merge-current-checks-only-fail-closed
description: "Authorize a manual GitHub PR merge only from current Checks API evidence. Use when: (1) a merge helper falls back to legacy combined commit statuses, (2) missing or unreadable check runs can become mergeable, (3) a tri-state check helper delegates authorization to a second evidence source, or (4) CLI regressions must prove no merge mutation occurs without trustworthy current checks."
category: ci-cd
date: 2026-08-06
version: "1.0.0"
user-invocable: false
verification: unverified
tags:
  - github
  - pull-requests
  - checks-api
  - check-runs
  - commit-status
  - merge-authorization
  - fail-closed
  - regression-testing
---

# Authorize Manual PR Merges Only From Current Checks

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-08-06 |
| **Objective** | Prevent an out-of-band manual PR merger from treating absent, malformed, or unreadable current check-run evidence as merge authorization. |
| **Outcome** | Proposed one Boolean Checks API boundary, removal of every legacy combined-status fallback, precise operator-facing failure logs, and CLI-level regressions that prove the legacy endpoint and merge mutation are never called on unavailable evidence. |
| **Verification** | unverified — the source, planned change, and acceptance criteria were supplied and reviewed, but the implementation, tests, and CI were not executed in this learning session. |

This pattern is deliberately scoped to a manual merge command. It does not change an automation
pipeline's independent review authority, exact-head receipt, or merge-wait contract.

## When to Use

- A manual merger queries `gh pr checks` or GitHub check runs, then falls back to
  `/commits/<sha>/status` when no current checks are available.
- A check helper returns `True | False | None`, and `None` dispatches to a weaker or legacy
  authorization source.
- A GitHub CLI error such as `no checks reported` is interpreted as “try another source” rather
  than “refuse to merge.”
- JSON decode failures, wrong top-level shapes, empty check lists, or non-object entries can escape
  without a clear operator diagnostic.
- Unit tests exercise parsing helpers but do not run the CLI far enough to prove that unavailable
  evidence prevents branch pushing and the merge API call.
- A repository is removing an obsolete authorization path and needs a static assertion that its
  endpoint, helpers, and dispatcher are gone.

## Proposed Workflow

> **Warning:** This workflow has not been validated end-to-end. Treat it as a hypothesis until the
> focused regressions, affected suites, static checks, and CI pass.

### Quick Reference

```python
import json
import logging
import subprocess

logger = logging.getLogger(__name__)


def _checks_pass_and_log(repo: str, pr_number: int) -> bool:
    """Return whether current GitHub check-run evidence permits a merge."""
    try:
        checks = _gh_json(
            [
                "pr",
                "checks",
                str(pr_number),
                "--repo",
                repo,
                "--json",
                "name,state,bucket,workflow",
            ]
        )
    except subprocess.CalledProcessError as exc:
        diagnostic = (exc.stderr or "") + (exc.stdout or "")
        if "no checks reported" in diagnostic.lower():
            logger.error(
                "No check runs reported for PR #%d; refusing merge",
                pr_number,
            )
        else:
            logger.error(
                "Error getting check runs for PR #%d: %s",
                pr_number,
                diagnostic.strip() or exc,
            )
        return False
    except (RuntimeError, json.JSONDecodeError) as exc:
        logger.error("Error getting check runs for PR #%d: %s", pr_number, exc)
        return False

    if not isinstance(checks, list):
        logger.error(
            "Invalid check-run response for PR #%d; refusing merge",
            pr_number,
        )
        return False
    if not checks:
        logger.error("No check runs reported for PR #%d; refusing merge", pr_number)
        return False

    any_success = False
    for check in checks:
        if not isinstance(check, dict):
            logger.error(
                "Invalid check-run entry for PR #%d; refusing merge",
                pr_number,
            )
            return False
        name = check.get("name", "")
        state = check.get("state", "")
        bucket = str(check.get("bucket", "")).lower()
        logger.info("    - %s: state=%s, bucket=%s", name, state, bucket)
        if bucket in CHECK_BAD_BUCKETS or bucket == "pending":
            return False
        if bucket == "pass":
            any_success = True
    return any_success
```

```bash
# Prove obsolete authorizers are absent from the manual merger.
! rg -n \
  'legacy_status|get_combined_status|commits/.*/status|checks_pass_or_legacy' \
  <manual-merge-module>

# Run the two authorization-boundary regressions first.
<project-test-command> \
  <test-file>::<test-class>::test_no_checks_block_legacy_success \
  <test-file>::<test-class>::test_check_error_blocks_merge \
  -v --log-cli-level=ERROR
```

### Detailed Steps

1. **Name the authority before editing.** For this command, only current check-run evidence may
   answer whether CI/CD permits the merge. A legacy combined commit status is not a recovery path;
   it is a second authorizer with different semantics. Keep automation-loop review and merge-wait
   rules explicitly out of scope when the command is out-of-band.

2. **Collapse eligibility into one Boolean helper.** Replace `True | False | None` with `bool`.
   `True` means the current Checks API response is present, structurally usable, has no known bad
   or pending bucket, and contains at least one passing check. Every unavailable-evidence path
   returns `False`; there is no sentinel that can trigger fallback authorization.

3. **Distinguish unavailable-evidence failures in logs.** Catch the CLI process exception and
   combine its captured stderr and stdout only for the diagnostic. Emit a dedicated
   `No check runs reported ...; refusing merge` message for GitHub's no-checks response. For other
   command errors, log the stripped tool diagnostic or the exception. Catch JSON/runtime errors
   separately so operators can distinguish missing evidence from unreadable evidence.

4. **Validate the response before classification.** Require a nonempty list and require each entry
   to be a mapping. Reject a wrong top-level response, an empty list, or any malformed entry before
   inspecting fields. Log each usable check's name, state, and normalized bucket to preserve the
   operator's existing visibility.

5. **Keep the bucket rule explicit.** Return `False` immediately for every configured bad bucket
   and for `pending`. Record whether at least one `pass` bucket exists and return that Boolean only
   after the complete list is inspected. This prevents a nonempty but non-success response from
   authorizing the merge.

6. **Delete alternate authorizers completely.** Remove the legacy REST helper, the fallback
   dispatcher, imports used only by those paths, and object-style compatibility wrappers that keep
   the obsolete behavior callable. Do not leave a dormant helper “for compatibility” when it can
   still answer the authorization question.

7. **Block before any mutation.** The orchestration seam should log that it is checking the current
   Checks API, call the one helper, and immediately return a blocked outcome when it returns
   `False`. Branch push and merge requests must remain downstream of this guard.

8. **Test through the CLI boundary.** In the missing-check regression, configure the legacy status
   endpoint to return success if called, then assert all of the following: CLI exit is nonzero, the
   legacy endpoint was not queried, no merge request was issued, and the explicit refusal message
   was logged. In a separate test, make the check query raise an unreadable-evidence error and
   assert a nonzero exit, exactly the expected pre-merge call count, no push, and the error text.

9. **Preserve adjacent behavior.** Retarget passing, failed, pending, dry-run, push-all, batch, and
   merge-queue tests to the consolidated helper rather than weakening or deleting them. Remove only
   tests whose sole purpose was compatibility with the deleted authorizer.

10. **Add a source-level absence check.** Use `rg` to prove the legacy helper names, combined-status
    API method, and commit-status endpoint are absent from the manual merge module. Behavioral tests
    prove runtime safety; the source assertion prevents an unused legacy path from quietly returning.

## Verified Workflow

_Not applicable yet._ The actionable methodology is under **Proposed Workflow**. This placeholder
exists for corpus validation and makes no verification claim. Promote the workflow only after the
implementation tests pass; use `verified-local` for local evidence or `verified-ci` after CI confirms
the final branch.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| ------- | -------------- | ------------- | -------------- |
| Fall back to the combined commit-status endpoint | Missing current check runs triggered a query whose configured legacy result could be `success` | Absence of the chosen authority became permission to consult a semantically different authority, so missing evidence could authorize a merge | Missing current evidence is a blocking result; delete the fallback rather than reorder it |
| Return `None` from the check helper | `None` represented unavailable check-run evidence and a dispatcher decided what to query next | The helper did not own a closed authorization contract, and the caller could reinterpret uncertainty as permission | Use one Boolean helper where every unavailable or unreadable path is `False` |
| Keep object-style compatibility helpers | Older wrappers and their isolated unit tests remained after internal code moved to CLI JSON parsing | The obsolete authorization behavior stayed callable and expanded the maintenance surface without a package export contract | Remove private, unexported compatibility paths and their duplicate tests when their consumers are test-only |
| Test only the helper result | Parser tests asserted `False` for selected inputs but did not execute the command's push and merge branches | A future dispatcher or fallback could still convert the helper's failure into a merge | Drive the public CLI and assert both forbidden calls: no legacy status query and no merge mutation |
| Emit one generic “checks failed” message | Missing, malformed, and command-error evidence shared one vague log | Operators could not tell a normal CI failure from an unavailable authority source | Preserve a precise refusal reason for no checks, invalid shape, invalid entry, and query/decode error |

## Results & Parameters

### Authorization Matrix

| Current check-run result | Helper result | Legacy status queried? | Merge mutation allowed? |
| ------- | ------- | ------- | ------- |
| Nonempty valid list; at least one `pass`; no bad or pending bucket | `True` | No | May continue to the command's remaining guards |
| Any known bad bucket | `False` | No | No |
| Any `pending` bucket | `False` | No | No |
| Valid nonempty list with no `pass` bucket | `False` | No | No |
| Empty list or GitHub “no checks reported” error | `False` with explicit refusal log | No | No |
| Wrong top-level type or non-mapping entry | `False` with invalid-response log | No | No |
| CLI failure, runtime error, or JSON decode error | `False` with diagnostic log | No | No |

### Regression Assertions

```python
assert cli_main() == 1
assert legacy_status_request not in github_calls
assert not any(call_is_merge_request(call) for call in github_calls)
assert "refusing merge" in captured_logs
```

Use an error-specific assertion for unreadable evidence:

```python
assert "Error getting check runs for PR #1: checks unavailable" in captured_logs
```

### Acceptance Sequence

```bash
# 1. Focused authorization regressions.
<project-test-command> <missing-check-test> <check-error-test> -v

# 2. Static removal proof.
! rg -n \
  'def (checks_success_and_log|legacy_status_and_log|_legacy_status_and_log|_checks_pass_or_legacy)\\b|get_combined_status|commits/.*/status' \
  <manual-merge-module>

# 3. Complete affected unit suites.
<project-test-command> <manual-merge-tests> <github-helper-tests> -v

# 4. Static quality checks for every changed source and test file.
<project-lint-command> <manual-merge-module> <manual-merge-tests> <github-helper-tests>
```

## Verified On

| Project | Context | Details |
| ------- | ------- | ------- |
| ProjectHephaestus | Proposed hardening of the out-of-band `hephaestus-merge-prs` command | The implementation plan identified one current-check parser, two legacy status paths, test-only compatibility wrappers, and CLI regression criteria. No Hephaestus source was changed and no test or CI result was produced by this learning session. |

## Related Skills

- [GitHub Auto-Merge: CI Gating, Branch Protection, and Merge Method](github-auto-merge-ci-gating-merge-method.md) covers GitHub auto-merge operations, required contexts, stale runs, and merge-method selection.
- [Automation Review Authorization: CI Boundary](automation-review-authorization-ci-boundary.md) covers the queue pipeline's distinct review authority, exact-head proof, and conditional merge contract.
- [Fail-Closed JSON Result Validation for External Tools](tooling-subprocess-json-fail-closed-result-validation.md) covers the generic subprocess and JSON trust boundary used by external-tool validators.
