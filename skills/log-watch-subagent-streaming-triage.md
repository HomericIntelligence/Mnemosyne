---
name: log-watch-subagent-streaming-triage
description: "Run a long-lived log-monitoring subagent that blocks cheaply on tail -F | grep, streams one triage message per incident back to the coordinating session, batches repeated signatures, and — critically — treats its own classifications as HYPOTHESES: attribution requires artifact inspection (the monitored system's own comments/state), which in the verified case REFUTED the monitor's systemic-failure hypothesis before a wrong remediation (stopping the loop / switching models) was taken. Use when: (1) watching an automation run's log for errors over hours without burning tokens on polling, (2) a monitor must report EACH incident as it happens rather than stopping at the first, (3) a monitor's plausible root-cause hypothesis is about to drive a state-changing remediation, (4) deciding what a watch agent should ignore vs batch vs escalate, (5) recalibrating a running monitor mid-flight with new classification rules."
category: tooling
date: 2026-07-17
version: "1.0.0"
user-invocable: false
verification: verified-local
tags:
  - log-monitoring
  - subagent
  - streaming-triage
  - tail-grep-blocking
  - incident-batching
  - hypothesis-vs-evidence
  - automation-loop
  - background-agent
---

# Log-Watch Subagent with Streaming Triage

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-07-17 |
| **Objective** | Watch a restarted hephaestus-automation-loop log for hours, reporting each genuine error with context while ignoring known noise |
| **Outcome** | Monitor correctly detected stalls, confirmed two fixes live (regression checks), and surfaced a 5-item pr_review park wave — whose "systemic reviewer failure" hypothesis the coordinator then REFUTED by reading the PR's own anomaly comment, avoiding a wrong loop-stop/model-switch |
| **Verification** | verified-local — live session; ~35-46k tokens per monitor turn, one blocking watch between incidents |

## When to Use

- A long-running process writes an append-only log and you need per-incident reports, not a single
  first-failure return.
- A monitoring agent's root-cause hypothesis is about to justify stopping/reconfiguring the system.
- You need to update a running monitor's classification rules without restarting it.

## Verified Workflow

### Quick Reference

```bash
# The monitor's core loop: block cheaply, never poll-read the log.
baseline=$(wc -l < "$LOG")
timeout 540 tail -n +$((baseline+1)) -F "$LOG" \
  | grep -m1 -iE 'error|critical|traceback|poisoned|rc=[1-9]|429|529|quota|fatal'
# exit 124 = no match: refresh baseline, check process liveness + log growth, loop again.
# match: wait ~15s (bounded tail, never bare sleep), extract ±30 context lines,
#        false-positive check, then send ONE triage message and resume.
```

### Detailed Steps

1. **Spawn the monitor as a background subagent** whose deliverable is messages to the coordinating
   session (one per incident), not its final return value. First message: run config, PID,
   baseline, pre-existing errors.
2. **Give it explicit three-way classification:** IGNORE (known-benign lines — enumerate them),
   BATCH (recurring same-signature events — max one message per ~30 min with cumulative counts),
   ESCALATE (new signatures, process death, regression signatures for recently shipped fixes).
   Include regression checks: the exact OLD and NEW log wordings of just-fixed bugs, so the monitor
   proves which code is running.
3. **Block, don't poll:** bounded `timeout N tail -n +K -F | grep -m1` consumes no tokens while
   waiting; on timeout, verify liveness (`pgrep`) and log growth, then re-arm. Never bare `sleep`.
4. **Treat monitor classifications as hypotheses.** A monitor sees only the log. Before any
   state-changing remediation (stopping the run, switching models), the coordinator must pull the
   system's own artifacts. Verified case: "100% pr_review parks, zero GO — reviewer contract
   mismatch, consider stopping the loop" was refuted by the PR's anomaly comment
   (`hephaestus-pr-review-zero-thread-nogo`), which carried the reviewer's real summary: "NOGO:
   ... head unchanged (4th round)" — by-design stale-PR triage, not a reviewer failure.
5. **Recalibrate mid-flight by messaging the agent.** Sending updated rules (reclassify signature X
   as by-design; escalate only if a FRESH item hits it) resumes the monitor with its context
   intact; it acknowledges and applies the delta. No restart, no lost baseline.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Return-on-first-anomaly monitor | Original watcher returned after one finding | Long runs produce many independent incidents; each respawn loses baseline and batching state | Stream per-incident messages; keep one long-lived agent |
| Trusting the monitor's root cause | "Zero GO verdicts across 5 PRs in 10 min ⇒ reviewer-side contract mismatch; stop the loop" | The 5 PRs were stale items whose heads never changed; the pipeline parks deterministic no-progress NOGOs by design (#2079) | Log-shape correlation ≠ attribution; inspect the monitored system's own artifacts before remediation |
| Foreground sleep for flush waits | `sleep 15` between match and context extraction | Bare sleep is blocked in the harness | Use a bounded `timeout 15 tail -f >/dev/null` |

## Results & Parameters

```text
Watch cadence:   timeout 540s blocking tail|grep; ~15s flush wait on match
Batching:        same signature ≤1 message/30min, cumulative counts carried forward
Cost:            ~35-46k tokens per monitor wake, near-zero while blocked
Escalation gate: fresh-item hit on a by-design signature = real defect; stale-item hit = triage
```

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| HomericIntelligence/Hephaestus | 2026-07-17 automation-loop restart | Detected 170s stall, confirmed 2 fixes live, surfaced 5-item park wave; hypothesis refuted by PR artifact before wrong remediation |
