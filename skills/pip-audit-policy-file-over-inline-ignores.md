---
name: pip-audit-policy-file-over-inline-ignores
license: BSD-3-Clause
description: "Enforce one uv-only, fail-closed pip-audit path whose sole suppression authority is an exact repository-root ledger. Use when: (1) CI, hooks, or task runners invoke pip-audit differently, (2) native --ignore-vuln flags or alternate ledgers bypass review, (3) scanner status can contradict JSON evidence, or (4) stale suppressions must fail rather than disappear silently."
category: ci-cd
date: 2026-08-07
version: "2.0.0"
user-invocable: false
verification: unverified
history: pip-audit-policy-file-over-inline-ignores.history
tags: [pip-audit, uv, suppression-ledger, fail-closed, dependency-scanning, ci-policy, structural-tests]
---

# Enforce One Fail-Closed pip-audit Path

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-08-07 |
| **Objective** | Replace raw, piped, and caller-configurable dependency-audit paths with one uv command, one exact repository-root ledger, and one evidence-verifying wrapper. |
| **Outcome** | Proposed policy contract for ProjectHephaestus issue #2566: canonical scan execution, structured suppression records, exact matching, operational exit code 2, and repository-wide drift guards. |
| **Verification** | unverified — acceptance tests and implementation were specified but not executed in this learning session. |
| **History** | [changelog](./pip-audit-policy-file-over-inline-ignores.history) |

## When to Use

- Required CI, scheduled CI, pre-commit, and task-runner recipes do not execute the same dependency-audit command.
- A repository still pipes raw scanner JSON into a filter and relies on shell pipeline status.
- Native scanner ignore flags, bare advisory IDs, caller-selected ignore files, or public suppression parameters can bypass the reviewed ledger.
- The wrapper trusts only the subprocess return code or only the JSON body, allowing contradictory or incomplete evidence.
- Suppression records can outlive the finding they approved, match several duplicate findings, or silently broaden across package versions.
- A guard checks only known configuration files and could miss Python subprocesses, shell scripts, Dockerfiles, Makefiles, package scripts, or shebang-marked files.

## Proposed Workflow

> **Warning:** This workflow has not been validated end-to-end. Treat it as a proposed contract until implementation tests and CI confirm it.

## Verified Workflow

> **Warning:** The repository validator requires this heading, but the workflow below is unverified. ProjectHephaestus issue #2566 supplied an acceptance-mapped design; no code or CI result was produced during this learn run.

### Quick Reference

~~~bash
# Every active audit surface invokes exactly this command.
uv run hephaestus-filter-audit --scan

# Stdin remains an unsuppressed evidence-classification seam.
pip-audit --format json | hephaestus-filter-audit
~~~

Canonical ledger record:

~~~text
advisory=GHSA-abcd-2345-6789 | package=example-package | version=1.2.3 | owner=@security-owner | review=issue:#2566 | expires=2099-12-31 | rationale=Temporary upstream compatibility
~~~

### Detailed Steps

1. **Make the wrapper own scanner execution.** Add one explicit scan mode. Launch the fixed vector consisting of the current interpreter, module pip_audit, JSON format, and disabled progress spinner. Capture stdout/stderr, disable check-on-nonzero, and apply one fixed timeout. External callers still enter through uv, while the scanner runs in that uv-managed interpreter.

2. **Resolve one ledger internally.** Compute the repository root and require exactly its .pip-audit-ignore.txt. Before launching the scanner, require that path to exist, be a regular non-symlink file, and resolve strictly to the expected path. Do not accept an ignore-file option or environment override.

3. **Use a closed record grammar.** Split each nonblank, non-comment physical line on the literal delimiter space-pipe-space and require exactly these ordered fields: advisory, package, version, owner, review, expires, rationale. Reject inline comments, escaping, unknown or repeated fields, control characters, value whitespace, duplicate advisory/package/version triples, expired records, and noncanonical identifiers.

4. **Normalize evidence before policy.** Require a top-level object containing dependencies and fixes lists. Each dependency needs a canonicalizable nonempty name, a valid PEP 440 version, and a vulnerabilities list. Each vulnerability needs a canonical advisory ID and an optional list of severity objects. Allow unconsumed scanner fields; reject skipped or incomplete dependencies.

5. **Cross-check status and evidence.** Scanner status 0 is valid only with zero vulnerabilities; status 1 is valid only with one or more. Empty, malformed, or incomplete JSON, launch failure, timeout, contradictory status/evidence, and every other status are operational error 2.

6. **Apply suppressions only after validation.** Match normalized advisory/package/version triples. Each ledger record must consume exactly one current finding. An unmatched stale record or ambiguous duplicate evidence is operational error 2. Report matched approvals separately from below-threshold warnings.

7. **Keep the public filter unsuppressed.** The reusable filter API should accept evidence and a severity threshold only. Suppression loading belongs exclusively to the private canonical scan path. Stdin classification therefore cannot acquire a hidden caller-controlled bypass.

8. **Keep verdict semantics independent of rendering.** HIGH, CRITICAL, and UNKNOWN findings block with status 1; LOW and MEDIUM findings warn with status 0; approved exact matches are reported separately. Human and JSON modes must return identical 0, 1, or 2 statuses.

9. **Replace every active surface atomically.** Required workflow, scheduled/manual workflow, manual pre-commit hook, and task-runner recipe each contain exactly one canonical command. Update summaries so an operational scanner failure is not reported as merely a vulnerability finding.

10. **Discover bypasses repository-wide.** Recursively inspect production Python, shell, YAML, TOML, JSON, INI/config, Dockerfile, Makefile, Just, and extensionless shebang files. Exclude only deliberate non-production trees such as .git, generated environments/caches, build, docs, and tests. Permit audit tokens only in the canonical module, package declaration/entry point, and approved configured surfaces.

11. **Test adversarial trees and boundaries.** Synthetic trees must prove discovery catches raw subprocess calls, underscore spellings, scanner Actions, native ignore flags, alternate wrapper or ledger paths, Docker/Make/Just/package/workflow commands, shell files, and extensionless scripts. Runtime tests must cover ledger grammar, expiry dates, exact matching, stale/ambiguous records, ledger path attacks, subprocess argv/timeout, malformed evidence, and output-mode parity.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| ------- | -------------- | ------------- | -------------- |
| Raw scanner piped into a policy filter | Shell pipeline behavior and scanner invocation were split between two processes and multiple call sites. | Scanner status, evidence completeness, and policy could drift or be lost through shell semantics. | Let one wrapper launch the fixed scanner command and validate both status and JSON. |
| Bare advisory-ID ledger | One ID suppressed every matching package/version occurrence and carried no owner, review, expiry, or rationale. | The exception could silently broaden and persist after its justification expired. | Bind approval to an exact normalized triple plus lifecycle metadata. |
| Caller-selected ignore file or public ignore_ids parameter | Tests and callers could choose a different ledger or inject suppressions directly. | The repository-root ledger was not the sole authority. | Keep suppression loading private to canonical scan mode and reject alternate CLI flags. |
| Trust scanner exit code alone | Status 0 could accompany malformed, empty, skipped, or contradictory evidence. | An operational failure could be mistaken for a clean scan. | Require the expected JSON shape and status/evidence consistency. |
| Trust JSON alone | Valid vulnerability evidence could arrive with an unexpected operational status. | The wrapper could normalize a scanner failure into a policy verdict. | Treat all status/evidence contradictions as operational error 2. |
| Ignore stale ledger records | Removed or version-changed findings left approvals in place indefinitely. | Policy debt accumulated invisibly and could match a future unrelated recurrence. | Require every record to consume exactly one current finding. |
| Guard only four known files | An alternate command could be added in Python, packaging metadata, Docker, or a shebang script. | The structural test froze current locations, not the repository invariant. | Discover all eligible production executable/configuration surfaces and test synthetic bypasses. |

## Results & Parameters

### Canonical Contract

| Parameter | Required value |
| ------- | ------- |
| External command | uv run hephaestus-filter-audit --scan |
| Scanner vector | current Python interpreter, -m pip_audit, --format json, --progress-spinner off |
| Timeout | 300 seconds |
| Ledger | repository-root .pip-audit-ignore.txt only |
| Match key | normalized advisory, package, version |
| Blocking severities | HIGH, CRITICAL, UNKNOWN |
| Operational failure | exit 2 |
| Policy block | exit 1 |
| Clean, warning-only, or fully approved evidence | exit 0 |

### Ledger Validators

~~~text
advisory: [A-Z][A-Z0-9]*(?:-[A-Z0-9][A-Z0-9._]*)+
package:  PEP 503 canonical name
version:  valid PEP 440 with canonical rendering
owner:    @[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?
review:   issue:#[1-9][0-9]* or pr:#[1-9][0-9]*
expires:  ISO date active through current UTC date
rationale: trimmed, control-free, 1-200 characters
~~~

### Acceptance-Mapped Verification

~~~bash
uv run pytest tests/unit/validation/test_audit.py tests/unit/ci/test_pip_audit_policy.py tests/unit/docs/test_security_policy.py -v
just test-shell
uv run ruff check hephaestus/ tests/
uv run mypy hephaestus/ scripts/ tests/
~~~

Expected structural result: every configured surface contains exactly one canonical command, and no other production surface can invoke pip-audit, pip_audit, a pip-audit Action, native ignore options, or the wrapper.

## Verified On

| Project | Context | Details |
| ------- | ------- | ------- |
| ProjectHephaestus | Issue #2566 implementation design | Proposed only; implementation and CI verification remain pending. |

## References

- [Validate vulnerability-scanner evidence before filtering](vulnerability-scanner-evidence-fail-closed-validation.md)
- [General vulnerability exception governance](scan-vulnerabilities.md)
- ProjectHephaestus ADR-0007 (required dependency-scan gate)
- ProjectHephaestus ADR-0008 (uv-only execution)
