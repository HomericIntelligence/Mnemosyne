---
name: live-cli-sweep-invariants
description: "Keep a bounded live CLI acceptance sweep trustworthy: closed case inventory, one verdict per case on hang, mutating cases behind an explicit flag, and negative controls that prove the assertions can fail. Use when writing or reviewing a PASS/FAIL/SKIP sweep that runs real commands against a live deployment, and when a review of such a sweep finds wrong verdicts."
category: testing
date: 2026-11-16
version: "1.0.0"
user-invocable: false
tags:
  - acceptance-testing
  - cli
  - shell
  - sweep
  - timeout
  - negative-control
  - mutation-gate
  - case-inventory
---

# Live CLI Sweep Invariants

<!-- Use [ASD-STE100](../docs/asd-ste100.md) for prose. Keep the headings and table
columns below so that the entry stays compatible with corpus retrieval. -->

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-16 |
| **Objective** | Make a per-case PASS/FAIL/SKIP sweep over live commands report the truth: every command exercised once, one verdict per case, no state change without a flag, and assertions that can fail. |
| **Outcome** | Operational. Four defects found and fixed in one 46-case sweep, all caught by these four invariants or the review they enable; the repaired sweep passed two independent review rounds and its CI. |

## When to Use

- You write a shell or Python sweep that runs one real command per case against a live deployment and prints `PASS`, `FAIL`, or `SKIP` per case.
- You review such a sweep and must decide whether its verdicts can be trusted.
- A sweep reports surprising passes: cases pass while the deployment is degraded, or a hang prints two verdict lines for one case.
- A sweep can change live state and you must decide which cases run by default.

## Verified Workflow

### Quick Reference

Keep these four invariants. Each one has a distinct failure mode; check all four on every change to the sweep.

| Invariant | Rule | Failure mode it prevents |
| --------- | ---- | ------------------------ |
| Closed inventory | The case listing and the executed case bodies are set-equal: every listed id has exactly one body, and no body is missing from the listing. An unknown selector is a usage error. | A case that never runs, or a selector that matches zero cases and exits zero — a false green. |
| One verdict per hang | The runner reports a timeout once. Every case body that does not use a shared expect helper starts with the already-reported guard before it reads the exit code. | Two FAIL lines and a doubled fail count for one case. |
| Mutation gate | Cases that can change live state run only behind an explicit flag, and the listing marks them. An invocation without the flag must be a provably bounded refusal. | A read-only run that cancels jobs, retries requests, or rotates credentials. |
| Negative control | At least one case uses input that must fail a text assertion. Run it after every assertion-helper change. | Vacuous assertions: a helper bug makes every check match, and the sweep reports passes that prove nothing. |

### Suggested Approach

1. Derive the case list from the command surface, not from memory. One leaf command or one bounded behaviour per case.
2. Keep one shared runner that records the exit code, captures output to a per-case file, and enforces a timeout. Keep shared verdict helpers that read that file.
3. Give every case body the same shape: run, then verdict. When a body needs custom logic instead of a shared helper, start its first condition with the already-reported guard for timeouts.
4. Split groups by the first component of the case id, and make selectors match that component or the full id. A selector that matches nothing must exit with the usage code, not zero.
5. Count the listing against the bodies in review. A one-line script that compares the two sets finds the drift that eyeballs miss.
6. Add the negative control last: run one case with input that cannot satisfy its expected text. If it reports PASS, an assertion helper is vacuous.
7. Treat expected refusals as passes, but bound them: a bounded HTTP status or a usage exit proves the command reached its boundary. It does not prove the deployment works — say so in the header.

When a sweep cannot run against the live deployment (review context, no credential), verify the invariants statically: compare the listing to the bodies, check each raw body for the timeout guard, and check each mutating invocation for its gate.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| ------- | -------------- | ------------- | --------------- |
| 1 | Text assertions through a helper that read the pattern from the wrong positional argument. | Every `contains` call matched every file, so all text assertions passed vacuously; only exit-code checks had meaning. | Add the negative control: one case whose input must fail its expected text. If it passes, an assertion is vacuous. |
| 2 | Raw case bodies that read the exit code after a shared runner that already reported the timeout. | A hang produced two FAIL lines for one case and a doubled fail count. | The already-reported guard must be the first condition of every case body that does not use a shared verdict helper. |
| 3 | Mutating invocations left outside the mutation gate because the expected deployment state made them refusals. | A reviewer found five unguarded mutating invocations; the refusal depended on deployment state, not on the sweep. | Gate on the flag what the command can do, not on the state you expect. A provably bounded refusal shape can stay read-only. |
| 4 | A case group name that matched zero case ids, and a case body missing from the listing. | `--list` looked complete, one selector exited zero with an empty summary, and one case never ran. | Derive group names from case-id prefixes, and compare listing to bodies mechanically. |

## Results & Parameters

### Configuration

Run shape that carried these invariants:

```bash
sweep.sh --client=PATH --models=MODEL --timeout=N --long-timeout=N \
  --artifact-dir=DIR [--only=GROUP_OR_CASE] [--mutate]
```

- Long flags only; no environment configuration; the run prints a config marker block and writes it to the artifact directory.
- Exit codes: 0 when no case fails, 1 when a case fails, 2 on a usage error or unknown selector.
- Expected output per case: one line, `PASS` or `FAIL` with seconds and a detail, or `SKIP` with a reason. A detail must never carry credential material: key identifiers and bounded statuses only.

### Expected Output

- A hang prints exactly one `FAIL <case> ... [timeout]` line.
- The negative control reports `FAIL missing expected text '...'` while the helper bug exists.
- The summary line counts match the per-case lines exactly.

## Verified On

| Project | Context | Details |
| ------- | ------- | ------- |
| An inference-service CLI (private deployment) | 46-case live acceptance sweep, two independent review rounds | The four defects above were found and fixed; see [notes](live-cli-sweep-invariants.notes.md). |

## References

- [Enumerated Registry Assertion Drift](enumerated-registry-assertion-drift.md) — exact-list assertions over registries that parallel merges extend.
- [Negative Scan Coverage Attestation](negative-scan-coverage-attestation.md) — prove a negative result covered its inputs before recording it.
