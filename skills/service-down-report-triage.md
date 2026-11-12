---
name: service-down-report-triage
license: BSD-3-Clause
description: "Classify a 'the service is down' report before deep diagnosis: a broken status tool, a degraded-but-serving component, or a capacity shortfall. Use when: (1) a user or ticket reports the service down, (2) a summary status command prints a healthy verdict for the whole service, (3) the status command exits with a schema-validation error on a record the service now publishes, or (4) replicas are missing against a desired count and you must decide whether this is an outage."
category: debugging
date: 2026-11-12
version: "1.0.0"
user-invocable: false
verification: verified-local
tags: [incident-triage, service-down, degraded, health-route, status-cli, schema-mismatch, last-good-snapshot, capacity-shortfall, read-only, serving]
---

# Service-Down Report Triage

## Overview

| Field | Value |
| ----- | ----- |
| **Date** | 2026-11-12 |
| **Objective** | Answer a "why is the service down" report with one correct classification: tool failure, degraded-but-serving, or capacity shortfall, before any deep diagnosis. |
| **Outcome** | Operational. One reported outage resolved to "up, with one degraded sub-component that self-healed", a second symptom resolved to a scheduler capacity limit, and a broken status CLI was classified as a client version mismatch. Every step was read-only. |

## When to Use

- A user, ticket, or operator asks why the service is down, and no diagnosis exists yet.
- A summary status command prints a healthy verdict for the whole service.
- The status command fails with a schema-validation error instead of printing status.
- A serving pool shows zero live replicas against a nonzero desired count or floor.
- You must decide whether to open an incident or to report a degraded state.

## Verified Workflow

### Quick Reference

Each step is read-only. Do not restart anything before the classification is complete, because a restart destroys evidence.

```bash
# 1. The health route answers before any CLI check. A 200 with ok=true refutes "down".
curl -sS -m 10 http://<gateway-host>:<port>/healthz | python3 -m json.tool

# 2. Read the component-level degrade fields in that response, not only the
#    top-level verdict: sync or cache state, last error category, degraded
#    flags, heartbeat ages, and peer health.

# 3. When the status CLI cannot parse the record, read the raw published record.
python3 - <<'PY'
import json, time
record = json.load(open("<public-status-record>"))
print("record_age_s", round(time.time() - record["published_at"], 1))
print("available", record.get("gateway_available", record.get("available")))
PY

# 4. Missing replicas: read the queue reason before any capacity hypothesis.
squeue -u <service-user> -o "%.10i %.9P %.55j %.8T %.10M %R"
```

### Suggested Approach

1. **Probe the health route first.** A direct HTTP probe refutes or confirms "down" before any CLI can mislead. A 200 response with a top-level ok flag means the front door and request path are alive; an unauthenticated request that returns 401 with an invalid-key error is a correct rejection and also proves the front door works.
2. **Treat the summary verdict as insufficient component proof.** A summary status command can print a healthy service verdict while the health route shows a degraded sub-component. Read the component-level fields of the health response before you answer the report. A summary that omits the degrade is the common presentation, not a rare one.
3. **Classify degraded-but-serving as a distinct state.** A health response can carry ok=true while one sub-component reports a degraded state with a fixed error category. When the service serves from its last good snapshot, serving continues fail-safe and the bounded consequence is narrow: lifecycle changes such as new or revoked credentials or refreshed configuration do not propagate until the sync recovers. Report "degraded, not down", name the consequence, and re-probe before you open an incident; the state can self-heal without intervention.
4. **Classify a schema-validation exit as tool failure.** A status CLI that exits with a validation error (for example "Extra inputs are not permitted" for a field the service now publishes) is a client/server version mismatch. Find the matching client build, or read the raw status record and the health route. The service can be fully up while its status tool is broken. The live-probe entry below owns this branch.
5. **Classify a replica shortfall as a scheduler question.** Desired replicas above live, with jobs pending behind a scheduler limit reason such as a group node or GRES cap, is a capacity matter. Read the queue reason, cite it, and route to the QOS group-cap entry below. Do not restart components, and do not lower desired counts to hide the divergence.
6. **Do not probe what the status output does not list.** A request against a model or route absent from the status record proves nothing about service health; its failure is uninformative in both directions.
7. **Complete with one classification per report.** Deliver: the classification (up, degraded-but-serving, tool failure, or capacity shortfall), the evidence (health-route fields, record age, queue reason), and for a degraded state the bounded consequence and a self-heal check on the next observation. Record owner decisions you did not take, such as raising a scheduler cap, as explicit requests.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| ------- | -------------- | ------------- | -------------- |
| Trust the summary CLI | Answered "the service is up" from the summary status command alone. | The health route showed one sub-component degraded for about a day; the summary did not surface it. | Read component-level degrade fields on the health route before any verdict. |
| Read the CLI error as the outage | Treated a schema-validation exit from the status CLI as proof of the reported outage. | The CLI build could not parse a new record field; the raw record and the health route showed the service up. | A tool that cannot parse the record has a version mismatch, not a service failure. |
| Attribute missing replicas to the service | Treated a pool with zero live replicas as an outage symptom. | Every replica job was pending behind a scheduler group cap, and the account's running nodes stood at that cap. | Read the queue reason before a capacity hypothesis; a capacity shortfall is not an outage. |

## Results & Parameters

### Configuration

Classify from the health route and the queue, in this order:

```text
health 200 + ok=true + no degraded flags           -> up
health 200 + ok=true + sub-component degraded flag -> degraded-but-serving
                                                      name the bounded consequence;
                                                      re-probe for self-heal
health route unreachable, no HTTP response         -> front-door or network problem
status CLI schema-validation error                 -> tool failure (client version mismatch)
replicas pending behind a scheduler limit reason   -> capacity shortfall (scheduler cap)
```

### Expected Output

- One classification per report: up, degraded-but-serving, tool failure, or capacity shortfall.
- The evidence: health-route component fields, status record age, and the queue reason when capacity is involved.
- For a degraded state: the bounded consequence, and whether the state self-healed on the next probe.
- For an owner decision you did not take (for example a cap raise): an explicit request with the measured numbers.

## Verified On

| Project | Context | Details |
| ------- | ------- | ------- |
| A tracked multi-model inference service on a shared GPU cluster | A "why is it down" report from a user | The health route answered 200 with ok=true and a healthy supervisor while one sub-component reported a degraded sync state with a fixed error category; the summary CLI printed only a healthy service verdict. The degrade self-healed by the next day with no intervention. A second symptom, missing replicas, came from a scheduler group node cap. See the [notes](service-down-report-triage.notes.md). |

## References

- [Inference gateway backlog with low engine load](inference-gateway-backlog-low-engine-load-diagnosis.md) — when the report is rejects or queueing, not "down".
- [Serving-pool simultaneous replica outage diagnosis](serving-pool-replica-outage-diagnosis.md) — when replicas die after starting rather than never start.
- [Slurm QOS group-cap regression diagnosis](slurm-qos-group-cap-regression-diagnosis.md) — owns the scheduler-cap branch and the limit-ownership rule.
- [Comet live read-only release status probe](comet-live-readonly-release-status-probe.md) — owns the client-version-mismatch branch and selector separation.
- [Runtime component checks degrade, they do not stop](runtime-component-checks-degrade-not-stop.md) — the design rule that makes degraded-but-serving possible.
