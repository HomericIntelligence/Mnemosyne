---
name: source-policy-assertion-scope
license: BSD-3-Clause
description: "Bound a source-text policy assertion to the region the policy governs. Use when a test pins a whole function or file against a forbidden token, and a correct new branch elsewhere in the same artifact adds that token; when a review proposes deleting the policy assertion to make the test pass; or when a rendered-script test must keep a fail-open form enforced. Slice from the governed invocation to its terminal line, keep the assertion, and prove the slice is not vacuous with a mutant in the governed region."
category: testing
date: 2026-11-10
version: "1.0.0"
user-invocable: false
verification: verified-ci
tags:
  - source-text-assertion
  - policy-pin
  - whole-function-assertion
  - bounded-slice
  - fail-open
  - mutation-check
  - non-vacuous-guard
  - rendered-script
  - stale-test
---

# Scope a Source-Text Policy Assertion to Its Governed Region

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-10 |
| **Objective** | Keep a source-text policy assertion enforced when a correct change adds a new branch elsewhere in the same artifact. |
| **Outcome** | Successful. The scoped assertion kept the policy, and the correct branch no longer failed the test. |

A test that pins a whole function or file against a forbidden token does not
assert one policy. It asserts that no future branch in that artifact may use the
token for any purpose. A correct new branch then fails the test even though the
governed behavior is intact. Bound the assertion to the lines that implement
the policy. Keep the policy check. Prove that the bounded slice still catches a
violation.

## When to Use

- A test asserts that a forbidden shell form, for example `|| return 1`, is absent from a whole function or file.
- A correct new branch in the same artifact adds that form for a different purpose, and the whole-artifact assertion fails.
- A review proposes deleting the policy assertion because the test is red, but the policy is still required.
- A rendered-template or shell-fragment test must prove a warn-and-continue or fail-open form.
- The exact source text is the contract, so a direct behavior test is unavailable or not the local convention.

Do not use this skill for a layout-only assertion (line numbers, offsets, or
file length). Remove those assertions, or re-anchor them to a behavior or a
value authority. Do not use this skill to excuse a real violation in the
governed region.

## Verified Workflow

### Quick Reference

```python
# Slice the governed step, not the whole function body.
body = out[out.index("recorded_removal() {") : out.index("next_function() {")]
step = body[body.index("remove") : body.index("unset ")]
assert "|| return 1" not in step
assert "warning:" in step
```

The slice starts at the invocation that performs the policy action and ends at
the line that completes it. The forbidden form must be absent. The required
warning marker must be present.

### Suggested Approach

1. State the policy in one sentence. For example: "The removal step warns and continues; it never returns failure."
2. Identify the exact region that implements the policy. Use the governed invocation as the start anchor and its terminal line as the end anchor. Do not include adoption, recording, or caller branches.
3. Slice only that region. Keep the original policy assertions inside the slice.
4. Prove that the slice is not vacuous. Add the forbidden form inside the governed region. The test must fail. Restore the source.
5. Prove that the slice is independent. Change a branch outside the governed region, for example the adoption path. The test must stay green.
6. Keep the adjacent assertions that cover other policies, such as a cleanup handler that must exit zero.

If stable anchors are absent, extract the governed step into a named helper or
a named block first. Then slice the named region. Do not weaken the assertion
to a nearby but different line.

### Decision Table

| Observation | Action |
| ------- | ------- |
| A whole-artifact pin fails after a correct change outside the policy | Bound the slice to the governed region and keep the policy. |
| The governed region violates the policy | Keep the test red and fix the product. |
| The anchors are unstable | Extract the governed step into a named helper or block first. |
| The behavior is directly testable | Prefer a behavior test. Keep the source pin only when the exact source form is the contract. |

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| ------- | ---------------- | --------------- | --------------- |
| Whole-function pin | Asserted that the forbidden token was absent from the entire function body. | A correct new branch in the same function used the token for a different purpose. The policy still held, but the test failed. | A pin over an artifact is a pin over every future branch in that artifact. |
| Delete the assertion | Removed the failing policy check to make the test pass. | The fail-open policy lost its only guard. | Keep the policy. Narrow the scope. |
| Add the branch to an allowlist | Made the forbidden token conditionally acceptable for the new branch. | The assertion became conditional and could hide a later violation in the governed step. | Slice the governed region instead of enumerating exceptions. |
| Behavior-only rewrite with no harness | Replaced the source pin with a behavior test. | The rendered shell fragment had no direct unit harness, and the new test changed the selection tier. | Keep the scoped source pin and record the behavior-coverage limit. |

## Results & Parameters

### Configuration

```yaml
slice_start: the governed invocation
slice_end: the line that completes the policy action
forbidden_form: "|| return 1"
required_text: the warning marker
outside_region_probe: a correct branch outside the policy
inside_region_mutant: the forbidden form inside the governed region
```

### Expected Output

- The scoped assertion passes with the correct new branch.
- The assertion fails when the forbidden form is in the governed region.
- The assertion ignores changes outside the governed region.
- The test shard that selects the test is green.

## Verified On

| Project | Context | Details |
| ------- | ------- | ------- |
| A service launch template | A rendered shell-script policy test in a nightly shard | The whole-function pin failed after a correct new branch added the token. The scoped slice passed, and a mutant in the governed step failed. See [notes](source-policy-assertion-scope.notes.md). |

## References

- [Test behavior instead of fixed source positions](testing-source-line-number-assertions-are-churn-engines.md)
- [Non-vacuous regression guards](testing-non-vacuous-regression-guards-behavior-unchanged.md)
- [Template render-variant review](template-render-variant-review.md)
- [Enumerated registry assertion drift](enumerated-registry-assertion-drift.md)