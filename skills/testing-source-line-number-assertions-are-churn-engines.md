---
name: testing-source-line-number-assertions-are-churn-engines
license: BSD-3-Clause
description: "When an unrelated edit moves source lines and makes a test fail, use this skill. Also use it when a review requests source-offset maintenance or a test enforces stored citations. Remove layout-dependent assertions. Keep behavior checks and nonempty validation."
category: testing
date: 2026-07-16
version: "1.2.0"
user-invocable: false
verification: verified-ci
tags:
  - line-number-assertion
  - behavior-testing
  - regression-test
  - review
  - nonempty-validation
---

# Test behavior instead of fixed source positions

## Overview

| Field | Value |
| ------- | ------- |
| Date | 2026-07-16 |
| Objective | Remove test failures caused only by changes to source layout. |
| Outcome | Layout-dependent tests removed while functional checks remained. |

## When to Use

- An unrelated import, comment, or format change moves a source line and makes a test fail.
- A test uses a stored source citation to select an expression or check file length.
- A review asks an author to update numeric source offsets.
- An automation loop repeatedly changes line references without a behavior change.
- A test-selection gate still selects a test that an approved change removed.

## Verified Workflow

### Quick Reference

Identify the product contract. Remove the layout-dependent assertion.
Run a current, nonempty selection of applicable behavior tests.
Do not report an empty selection as a pass.

### Distinguish the contracts

A fixed position in an implementation file is not usually a product contract.
An exception applies when line position is itself a documented product output.
For example, a parser can report the line of invalid input.

Line numbers in tracebacks, failure messages, review annotations, and historical
citations are diagnostic data. Their presence alone is not a defect.
Do not ban all source-location APIs or all numeric citations.

### Remove the incorrect dependency

1. Find the assertion that depends on source layout.
2. Trace its inputs, including stored citations and intermediate variables.
3. Identify the behavior that the test claims to protect.
4. Remove the layout assertion if it protects no required behavior.
5. Otherwise, test that behavior through its applicable public interface.
6. Preserve existing permission, ownership, state, and failure-path checks.
7. Remove imports and test data that no remaining test uses.

Do not replace the assertion with a source-text search that has the same
purpose. A symbol-presence check is sufficient only when symbol availability
is the actual public contract. It does not prove runtime behavior.

Do not update a line offset only to satisfy the removed layout assertion.
Keep useful navigation references when they do not impose a test invariant.
Generate navigation references only if the repository requires that feature.
Do not rewrite historical records to make their citations match current code.

### Keep validation meaningful

After a test is removed, resolve the test selection again against the current
source. Remove obsolete node IDs from the selection, not failure evidence
from the report. Run the applicable remaining suite.

A deleted test can be inapplicable. That does not make an empty test run
successful. Pytest exit code 5 means that no tests were collected.
Report that selection gap and choose applicable tests before claiming a pass.

If parameter names changed, select the complete current test function when
all its cases are applicable. Do not silently skip missing cases or treat
collection errors as success.

### Review prevention

Review the assertion and its data flow, not only its syntax.
Variable indirection can hide a dependency on a fixed source position.
Stored citation bounds and file-length checks can impose the same dependency.

Require a behavior-level correction or removal of the invalid assertion.
Do not require an automated scanner unless the task includes that scanner.
If a scanner is required, test rejection of layout invariants and acceptance
of legitimate diagnostic locations. Keep the existing review and CI gates.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Offset maintenance | Update the expected line after an unrelated edit. | Another edit moves the line again without changing behavior. | Remove the layout invariant. |
| Source-text replacement | Search for an equivalent expression instead of its line number. | The test can still depend on implementation layout rather than behavior. | Exercise the required public contract. |
| Symbol-only replacement | Check that a function exists instead of testing its effects. | Availability alone does not prove the original behavior. | Use symbol checks only for an availability contract. |
| Empty-run success | Treat a removed test and pytest exit code 5 as a pass. | No applicable test executed. | Resolve the selection and run applicable tests. |
| Blanket location ban | Reject every source-location API or numeric citation. | Diagnostic and parser-location contracts can require these values. | Classify the asserted contract before rejection. |

## Results & Parameters

- Expected regression result: an unrelated source-layout change does not fail a behavior test.
- Expected safety result: existing functional protection remains tested.
- Expected validation result: applicable tests execute and their actual results are recorded.
- Empty selection: not a passing validation result.
- Automated review enforcement: separate implementation and evidence are required.

## Verified On

| Context | Evidence | Limit |
| ------- | ------- | ------- |
| Layout-dependent test removal | The removal passed repository checks and merged. | This does not prove that an automated review guard exists. |

Supporting evidence is in the companion notes.
