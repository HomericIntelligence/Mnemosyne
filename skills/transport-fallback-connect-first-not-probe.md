---
name: transport-fallback-connect-first-not-probe
license: BSD-3-Clause
description: "Select a fallback transport by the failure of the primary attempt, never by a pre-flight probe. Use when: (1) designing route selection between a primary and a standby transport for requests whose effects must not run twice, (2) a client probes the primary service before each request and genuine requests then reset near a bounded accept budget, (3) ghost rejected-request audit rows or broken-pipe warnings appear on a healthy service, or (4) deciding which transport failures are safe to fail over and which require reconciliation."
category: architecture
date: 2026-11-13
version: "1.0.0"
user-invocable: false
verification: verified-live
tags:
  - transport
  - fallback-routing
  - connect-phase
  - probe
  - connection-budget
  - uncertain-effect
  - reconciliation
  - exception-taxonomy
---

# Choose the Fallback Transport by the Failure, Never by a Pre-Flight Probe

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-13 |
| **Objective** | Route effect-bearing requests across a primary and a standby transport without silently duplicating an effect and without exhausting the primary's connection budget. |
| **Outcome** | Operational. Removing one per-request probe repaired every reset request. The primary attempt's own connect-phase failure became the failover signal. Post-connect failures stayed terminal and keyed to a read-only status reconciliation. |
| **Verification** | verified-live. A forced removal experiment isolated the probe as the sole cause of `ECONNRESET` on live mutation requests. The corrected routing passed the repository's complete required CI surface. The boundaries in this file come from that shipped transport. See [notes](transport-fallback-connect-first-not-probe.notes.md). |

## When to Use

- You design a client that has a primary and a standby transport, for example a host-local Unix socket and a remote TLS endpoint, and requests have effects that must not run twice.
- Each logical operation can open more than one connection to the same service, for example a context exchange plus the effect request.
- A client does a pre-flight probe against the primary service to select the route, and genuine requests then fail with `ECONNRESET` or `ECONNREFUSED` near a bounded accept or handler budget.
- A healthy service writes rejected-request audit rows or broken-pipe warnings that no operator can attribute to real calls.
- You must decide which transport failures can retry on the standby and which make the effect uncertain.

## Verified Workflow

### Quick Reference

- Never select a route with a pre-flight probe. Send every request to the primary. Let the failure of that attempt select the fallback.
- A connect-phase failure is the only failover signal: the error provably occurred before one request byte left the client. Connect, refused, accept timeout, and handshake failures are in this class.
- A failure after the first byte is terminal. No-reply, reset, or parse failure after connect means the service can have the effect in flight. Do not redirect the request. Reconcile through the read-only status endpoint.
- Classify connect-phase errors as a subclass of the generic client error. Existing error categories keep matching. The failover decision reads the subclass.

```python
def submit(request):
    try:
        return send_primary(request)          # connect or refused -> OperatorConnectError
    except (OperatorConnectError, OperatorUnreachableError):
        route = published_standby_route()
        if route is None:
            raise                             # the primary refusal stands, unchanged
        return send_standby(route, request)   # safe: no request byte ever left the client
```

### Suggested Approach

1. **Count the connections one logical operation opens.** A probe costs one connection. If one operation opens a context exchange, an effect request, and a probe for each, the server accepts three connections per operation. A bounded accept or handler budget sizes for real work, not for doubles.
2. **Treat a probe as a full request.** The service accepts, often authenticates, and parses a probed connection. A probe that closes without a complete request produces server-side evidence: rejected-request rows and broken-pipe warnings. These pollute audits, alarms, and health signals, and real operators investigate them as attackers or defects.
3. **Fail over on the attempt, not on evidence before it.** The primary attempt's own connect-phase failure proves the request never reached a listener, so the standby is safe. Do not read health records, heartbeats, or cached states to decide: they are stale by construction when the listener dies between the read and the send.
4. **Draw the failover line at the first request byte.** Everything provably before it (connect, refused, timeout while waiting for accept, TLS handshake failure) is in the failover class. Everything after it (no reply, reset, truncated or malformed reply) is terminal: the effect can be in flight and only reconciliation answers it. Keep handshake failures in the pre-byte class: handshake bytes moved, but no request byte did.
5. **Keep the primary's failure contract unchanged.** Fallout text, exit codes, and refusal wording on the unchanged path must be byte-identical, and tests must pin them. A routing refactor that silently edits refusal wording breaks every operator runbook.
6. **When a failure appears, isolate the route-selection layer by removal.** Force the primary-only path temporarily. If the failures stop, the selection layer was the cause; investigate the removed logic, not the service.

### Boundaries

| Failure class | Example causes | Safe action | Unsafe action |
| -------- | -------- | --------- | -------- |
| Before any request byte | connect refused, accept timeout, DNS failure, handshake abort, wrong-owner refusal before send | Fail over to the standby | none |
| After the first request byte | no reply, reset, truncated or malformed reply, deadline while reading | Stop. Mark the effect uncertain. Reconcile on the read-only status endpoint | A second attempt on any transport |

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Per-request probe to select the route | The client probed the primary's socket before every request and fell back only when the probe failed | Each probe opened and drove a bounded handler drop. With a context exchange, request, and probe per call, the accept budget closed after a few operations and later mutation requests reset with `ECONNRESET` before one byte was read. The same probes wrote five rejected-request rows plus broken-pipe warnings per command into the service audit | A probe is a complete request to the server. Only the caller believes it is free |
| Probe only on paths that looked suspect | Probes ran on the healthy path too | The common case paid the same budget and audit cost as the failing case | Every route-selection check that touches the primary penalizes the fast path, and the fast path is most of the traffic |
| Redirect resets to the standby | On a reset after connect, send the same request on the standby transport | A reset reply happens after the service read the request. The effect can be running. A second attempt duplicates it with no ded key honored | Only pre-byte failures fail over. Post-connect failures reconcile on the read-only status endpoint |
| Health-record check to select the route | Read heartbeat or liveness records before deciding | The record ages between the read and the send, so the decision uses staleness as truth; the health layer is not the connection layer | Send the request and take the answer the transport gives you |

## Results & Parameters

### Configuration

| Parameter | Values seen | Decision it changes |
| --------- | ----------- | ------------------- |
| Accept or handler budget | small fixture-style values (for example 10) through production values | How many wasted connections kill the backlog |
| Connections per logical operation | 1 through 3 in the reference stack | The multiplier the budget must absorb |
| Failover exception class | subclass of the generic client error | Existing `except` categories keep matching; the fallback decision reads the subclass |

### Verification

- Force the primary path with the selection layer removed; every failing request that reset now completes.
- The primary-path refusal wording is byte-identical before and after the change.
- No new connection opens for routing evidence; one logical operation uses exactly the connections its protocol requires.
- The service audit shows no routing evidence rows: no rejected rows or broken-pipe warnings that a client generator cannot attribute.
- A kill-the-listener test proves the failover fires only for the pre-byte class, and a post-connect failure stays terminal.
