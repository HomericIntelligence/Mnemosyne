---
name: comet-cli-offline-review-evidence-reporting
license: BSD-3-Clause
description: "Review Comet CLI behavior without cluster access and report bounded evidence for offline defects or user-observed dashboard incidents. Use when: (1) reviewing comet or comet-admin commands in a workstation-only environment, (2) a CLI issue must be filed without exercising Slurm, gateways, or databases, (3) users report several dashboard views failing with the same validation error, (4) local validation is complete but the full test suite has no reliable terminal result."
category: testing
date: 2026-08-05
version: "1.1.0"
user-invocable: false
verification: verified-local
history: comet-cli-offline-review-evidence-reporting.history
tags: [comet, cli, dashboard, incident, offline, code-review, no-cluster, issue-reporting, pytest]
---

# Offline Comet Review and Incident Evidence Reporting

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-08-05 |
| **Objective** | Review Comet's CLI surfaces without issuing cluster, database, or gateway operations, and turn bounded user-supplied dashboard evidence into actionable incident tracking. |
| **Outcome** | Four confirmed CLI defects were reported individually after local review, and one multi-view dashboard incident was consolidated into a single issue without speculative reproduction. |
| **Verification** | verified-local — CLI help, focused tests, lint, formatting, and type checks passed; GitHub issue creation/comment succeeded; CI, a completed full suite, and dashboard-endpoint validation were not observed. |
| **History** | [changelog](./comet-cli-offline-review-evidence-reporting.history) |

## When to Use

- Reviewing `comet` or `comet-admin` while Slurm, a Comet gateway, or a production database is intentionally out of scope.
- Validating the help tree and CLI handlers with `typer.testing.CliRunner` or tests explicitly labelled offline, no-DB, and no-Slurm.
- Investigating command construction, backend-selection logic, transport-error presentation, or filesystem-derived identifiers without starting a service.
- Filing a small set of independently actionable CLI bugs and needing each issue to contain reproducible local evidence and a concrete remedy.
- A full test invocation starts or collects successfully but does not produce a reliable final result; partial evidence must not become a full-suite claim.
- A user reports multiple Comet dashboard views failing with the same query parameters and validation payload, but direct dashboard or cluster access is outside the task boundary.
- You need to decide whether new affected views belong in an existing incident issue or need a separate issue.

## Verified Workflow

> **Verification:** verified locally only; CI validation is pending. The review ran no cluster commands and did not start, submit to, or query Slurm, a gateway, or a database.

### Quick Reference

```bash
# Work from the Comet checkout. These help paths were exercised locally.
uv run comet --help
uv run comet-admin --help
uv run comet logs --help
uv run comet-admin keys --help

# The dedicated CLI test module documents its offline contract at its header.
uv run pytest tests/test_cli.py -q

# Local static quality gates.
uv run ruff check .
uv run ruff format --check .
uv run ty check

# Collection proves test discovery only; it does not prove the full suite passed.
uv run pytest --collect-only -q

# Fallback when the GitHub connector cannot create an issue. Search first.
gh issue list --repo LLM360/comet --state open --search "dashboard from to int parsing"
gh issue comment 540 --repo LLM360/comet --body-file /tmp/comet-dashboard-affected-views.md
```

### Detailed Steps

1. **Set an explicit non-live boundary.** Do not invoke lifecycle, allocation, submit, gateway, deployment, or operational subcommands. Restrict execution to help output, source inspection, and tests whose fixtures mock external effects. Keep database and gateway credentials out of the review environment.
2. **Map the command surface before testing behavior.** Inspect the Typer application registrations and group callbacks in `src/comet/cli/main.py` and `src/comet/cli/admin.py`. Exercise root and relevant group `--help` paths so missing registrations and malformed option declarations are caught without making a live request.
3. **Find the local contract.** Prefer `tests/test_cli.py`, whose module docstring explicitly identifies offline, no-DB, no-Slurm coverage. Inspect fixtures to confirm that filesystem roots, Slurm lookups, and HTTP calls are supplied by temporary paths or mocks before relying on a test as non-live.
4. **Review side-effect boundaries statically.** Trace each suspect command from argument parsing through command construction and backend selection. Check subprocess argv lists, environment-variable branches, local snapshot fallbacks, HTTP exception boundaries, and record-file naming instead of executing the corresponding operational command.
5. **Use deterministic local failures for error paths.** When a command should handle a transport failure, test it with a `CliRunner`, a mocked client, or an unreachable loopback endpoint. Assert the exit code and concise user-facing message. Never depend on a real gateway just to see an error path.
6. **Run the focused CLI suite and record the exact result.** In this review, `tests/test_cli.py` passed with 41 tests. Preserve the command and count in the report; do not extrapolate this result to unrelated integration paths.
7. **Run static gates separately.** Run Ruff lint, Ruff format-check, and Ty. In this review all three passed. A formatter check and a linter check answer different questions, so report both rather than shortening the result to “Ruff passed.”
8. **Separate collection from execution.** The full test suite collected 831 tests, but its run did not yield a reliable final result. Report collection as discovery evidence only and label full-suite status unknown or incomplete. Do not write “all tests pass.”
9. **Confirm each finding twice before filing.** Pair the responsible source path and exact faulty branch with a local behavioral reproduction or a collision pair. For a candidate issue, state the affected command, expected versus observed behavior, user impact, minimal safe reproduction, recommended fix, and a regression-test target.
10. **Search for duplicates before creating issues.** Search the repository issue tracker by command name, source symbol, and symptom. If no existing issue owns the defect, create one issue per independent fix. Do not bundle unrelated commands merely because they were found in one review; separate ownership, tests, and closure criteria make remediation tractable.
11. **Record user-supplied dashboard evidence faithfully.** Preserve the exact URLs, parameters, response payload, and which views the user reports as affected. Label those URLs as user-provided unless they were independently fetched; do not claim browser, API, or cluster reproduction from a report alone.
12. **Find the shared failure shape.** If several views have the same query shape and the same validation error, file one incident after a duplicate search. Enumerate every known affected view in that issue so ownership, triage, and a regression test cover the shared navigation/query contract.
13. **Bound the root-cause statement.** An error that reports `int_parsing` for relative time strings is evidence of a likely client/backend query-contract mismatch, not source-level proof of which side is wrong. State the hypothesis and compatible remedies, such as emitting integer timestamps in the frontend or accepting documented relative-time expressions in the backend, until code or endpoint validation confirms the cause.
14. **Update the same incident as scope grows.** When a user identifies an additional view that fails with the identical parameters and payload, add a comment to the existing incident rather than creating a duplicate. Include the new URL and explicitly say why it belongs to the same issue.
15. **Prefer the GitHub connector for tracker operations.** Use the connector for duplicate searches and comments when available. If it lacks issue creation, use the GitHub CLI as a fallback; preserve the returned issue URL and comment identifier as local verification evidence.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Treating help output as functional proof | Loaded the command help tree and assumed every handler was sound | Help validates registration and parsing, not downstream argv construction, state selection, or exception handling | Combine help smoke coverage with focused behavioral tests and source-level path tracing |
| Calling the full suite passing after collection | The suite collected 831 tests, but no reliable final execution result returned | Collection does not execute assertions, and an interrupted or unreported run is not a pass | Report `831 collected` and leave full-suite status unknown or incomplete |
| Using live infrastructure for integration confidence | Considered exercising gateway, database, and Slurm-backed commands directly | That would violate the no-cluster scope and make failures depend on external state | Use offline fixtures, mocks, temporary files, and deterministic loopback failures instead |
| Treating user-provided links as independently reproduced | The dashboard URLs and FastAPI payload were supplied by the user, but no dashboard request was made during the task | A report is valuable incident evidence but does not establish that the agent fetched the endpoint or observed current production state | Attribute exact URLs and responses to the user, and state the verification boundary explicitly |
| Declaring a dashboard root cause from validation text | The `int_parsing` error pointed to relative `from` and `to` values | The response identifies a type-contract failure, but not whether the frontend, backend, routing layer, or API compatibility changed | Describe the query-contract mismatch as likely and give solution paths as hypotheses pending source or endpoint validation |
| Opening a new issue for each failed view | GPU, history, and gateway pages used the same `from=now-24h&to=now&timezone=browser` shape and the same validation failure | Separate issues would split one probable cross-view regression and make a shared fix harder to track | Search duplicates first; consolidate identical query-shape failures and comment newly discovered views on the existing issue |
| Assuming endpoint text makes a unique filename | Replaced URL punctuation with dashes for external-worker protection records | Distinct URLs such as `http://gpu-1:30000` and `http://gpu-1-30000` collapse to the same path | Include a stable digest of the complete endpoint in the filename and test collision pairs |
| Letting raw HTTP client failures escape | Exercised a local unreachable endpoint through `smoke` and `whoami` | Users receive a library traceback rather than an actionable CLI error | Catch transport exceptions at the command boundary and print a concise nonzero failure message |

## Results & Parameters

### Local validation evidence

| Check | Observed result | Interpretation |
|-------|-----------------|----------------|
| `comet` and `comet-admin` help tree | Loaded locally, including relevant command groups | CLI registration and help rendering work for the reviewed surface |
| Focused offline CLI suite | `41 passed` | Strong local evidence for `tests/test_cli.py`; not a repository-wide pass |
| Ruff lint and format check | Passed | Source linting and formatting were clean in the review environment |
| Ty type check | Passed | Static type checking was clean in the review environment |
| Full-suite collection | `831 collected` | Test discovery succeeded; execution outcome was not established |
| Cluster operations | None run | Slurm, gateway, and database state were deliberately not touched |

### Dashboard incident evidence

The following evidence was supplied by the user and was not independently fetched:

| Affected view | User-supplied URL | Observed response |
|---------------|-------------------|-------------------|
| GPU | `https://dashboard.llm360.ai/comet/gpu?from=now-24h&to=now&timezone=browser` | FastAPI `int_parsing` errors for `query.from` (`now-24h`) and `query.to` (`now`) |
| History | `https://dashboard.llm360.ai/comet/?from=now-24h&to=now&timezone=browser` | Reported to fail with the same query shape |
| Gateway | `https://dashboard.llm360.ai/comet/gateway?from=now-24h&to=now&timezone=browser` | Reported to fail with the same query shape and validation failure |

Duplicate search found no matching open issue. The report was filed as [LLM360/comet#540](https://github.com/LLM360/comet/issues/540), then the gateway view was appended to that incident in comment `5197651491` rather than opened as a separate issue.

Treat the likely cause as a dashboard/API query-contract mismatch: the client sends relative time expressions while the receiving endpoint validates those fields as integers. Until code or endpoint validation is available, carry both remediation paths in the issue:

1. Convert the dashboard's relative range selection to the API's required integer timestamp format before navigation/request construction.
2. Or extend the backend's documented contract to parse relative expressions such as `now` and `now-24h` consistently.

Acceptance criteria should cover GPU, history, and gateway links generated with a relative range; make the expected time unit and timezone behavior explicit; preserve valid integer timestamp requests; and add cross-view regression coverage for the shared query builder or backend parser.

### Confirmed findings and recommended fixes

| Issue | Evidence and impact | Recommended solution |
|-------|---------------------|----------------------|
| LLM360/comet#512 — `comet logs --follow` | The follow path builds `tail -f 100 <file>`, so `100` is interpreted as a filename rather than a line count. Follow mode is unusable. | Build argv with an explicit count option, for example `tail -n 100 -f <file>`, and add a regression test asserting the exact argv. |
| LLM360/comet#513 — `comet-admin keys list` ignores DB mode | Listing always reads the local key snapshot, even when `COMET_DB_DSN` selects the database backend. Database-created or revoked keys can be absent or stale. | Choose the database-backed list path when the DSN is configured; retain the snapshot only as the explicit offline fallback and test both modes. |
| LLM360/comet#514 — `smoke` and `whoami` leak transport tracebacks | A local connection failure lets raw `httpx` details reach the terminal rather than a CLI-level diagnostic. | Catch the appropriate HTTP transport exception at each command boundary, emit a concise actionable error, return nonzero, and test the unreachable-client path. |
| LLM360/comet#515 — external-worker records can collide | URL sanitization maps distinct endpoints to the same record filename, allowing one worker's protection state to overwrite another's and making supervisor pruning unsafe. | Derive the record name from a readable prefix plus a stable full-URL digest; test known collision pairs and preserve or migrate existing records deliberately. |

### Issue-reporting template

Use this minimum structure for each independently actionable defect:

1. **Scope:** command, source symbol, and source path.
2. **Observed behavior:** a short local reproduction or static argv/state trace.
3. **Expected behavior and impact:** why the current behavior breaks an operator or risks an unsafe action.
4. **Recommended remediation:** the smallest coherent code change, including compatibility considerations.
5. **Acceptance criteria:** a focused regression test plus the relevant offline quality checks.
6. **Validation boundary:** name what was run and explicitly name omitted live systems and incomplete suites.

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| LLM360/Comet | Local CLI review on 2026-08-05 | No cluster commands; 41 focused CLI tests passed; Ruff and Ty passed; 831 tests collected but no full-suite pass was claimed; issues #512 through #515 were filed separately. |
| LLM360/Comet | User-observed dashboard incident on 2026-08-05 | No dashboard endpoint or cluster command was run. User-supplied GPU and history URLs, validation payload, and later gateway URL were consolidated into issue #540; issue creation/comment returned #540 and comment id `5197651491`. |
