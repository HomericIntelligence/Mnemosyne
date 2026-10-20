---
name: durable-export-overwrite-guard
license: BSD-3-Clause
description: "Guard re-runnable exports so a rerender never destroys verified-good prior content. Use when a dump, export, or sync job overwrites an existing artifact and a partial or divergent rerun would silently shrink it."
category: tooling
date: 2026-10-19
version: "1.0.0"
user-invocable: false
verification: verified-live
tags:
  - overwrite-guard
  - export
  - dump
  - non-shrinking
  - prefix-check
  - diverge
  - clobber
  - regression-guard
  - exception-policy
  - atomic-write
---
# Guard Exports Against Destructive Overwrites

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-19 |
| **Objective** | Let a scheduled export refresh its artifacts while proving it never replaces good existing content with smaller or divergent content. |
| **Outcome** | Operational. An hourly session-transcript export gained a non-shrinking-prefix guard with an explicit bypass. In its first days the guard blocked several bad overwrites, including one genuinely divergent source that a plain size comparison would have trusted. |
| **Verification** | verified-live: the guard ran in production across hourly executions; blocked overwrites were enumerated from the run log and each blocked case was reproduced in tests. See [notes](durable-export-overwrite-guard.notes.md). |

## When to Use

- A re-runnable export, dump, or sync writes over an artifact a previous run produced.
- A rerun can legitimately produce less content after an upstream retention trim, yet that output must still not destroy the fuller artifact.
- Two writers can produce content for the same destination, and divergence matters more than freshness.
- You review a destructive path protected by an exception tuple, and one missing tuple arm would turn the guard itself into the failure.

## Verified Workflow

### Quick Reference

```text
Guard rule: the staged content must extend the existing content, never shrink it.
  - Parse both sides into comparable units with stable identities.
  - Identical units: existing sequence must be a non-shrinking prefix of the staged one.
  - Unparseable or legacy existing content: replaceable (never wedge on old formats).
  - Divergence (same slot, different identity): block and log, always.
  - Human override: an explicit flag, named after destruction (--clobber), never the default.
```

### Suggested Approach

1. **Compare structure, not bytes.** Byte or size comparisons miss content that rewrote earlier slots. Parse both artifacts into their natural unit sequence and compare unit identities in order.
2. **Require a non-shrinking prefix.** The existing unit sequence must appear unchanged at the head of the staged sequence; longer staged content passes, shorter or altered content blocks.
3. **Fail open only for unreadable history.** Existing content that predates the identity scheme or fails to parse is replaceable; otherwise the guard wedges every legacy artifact forever.
4. **Enumerate every exception arm in the guard's exception tuple, and test each arm.** A guard that catches `OSError` and `ValueError` but not `UnicodeDecodeError` (or the local equivalents) crashes on the first corrupt legacy file and converts a protective check into a hard outage of the export. Independently re-read the tuple against the decode and parse stack before approving it.
5. **Write atomically.** Stage to a temporary sibling and rename onto the destination so a killed run never leaves a torn artifact that later guard reads must classify.
6. **Log every block with its divergence evidence.** Each blocked overwrite needs the destination, the blocking reason, and the first divergent unit identity, so an operator can tell a retention trim from true source corruption.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Overwriting unconditionally | Each run replaced the artifact with the freshest render | One upstream trim destroyed days of accumulated good content in a single scheduled run | Fresh output is not authority; compare before replacing |
| Guarding on size or line count alone | Blocked only when the staged file was smaller | A divergent rewrite of the same approximate length sailed through the heuristic | Identity-ordered comparison catches same-size divergence |
| Guarding with an incomplete exception policy | The parse failures the author expected were caught | A decode error from an unexpected character escaped the tuple and hard-failed the export on a legacy file | Every arm of the exception tuple needs its own replayed failure test |
| Wedge-on-unparseable | Treating an unreadable existing artifact as a block | Old-format artifacts became permanently unrefreshable | Unreadable history is replaceable history; divergence is not |

## Results & Parameters

### Configuration

```yaml
export_guard:
  comparison: ordered-unit-identities
  rule: existing-must-be-a-non-shrinking-prefix-of-staged
  unparseable_existing: replaceable
  divergent_slot: block-and-log
  bypass: explicit-flag-required
  write: stage-temp-then-rename
  exception_policy: enumerate-every-arm-with-a-test
```

### Expected Output

- Refreshes that only ever extend good artifacts, with a run log line per blocked overwrite.
- A test suite that replays each failure arm: truncation, divergence, corrupt encoding, legacy format, bypass.
- An operator-visible divergence record precise enough to locate the first altered unit.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Agent session-transcript export | Hourly scheduled refresh of per-session artifacts on shared storage | Guard blocked truncation and divergence overwrites in production; one initially missing exception-tuple arm was found by review and fixed with a replayed-corruption test. See [notes](durable-export-overwrite-guard.notes.md). |

## References

- [Warn before overwriting an existing destination](warn-on-existing-dest-subdir.md)
