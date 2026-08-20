---
name: nats-server-auth-authz-hardening
description: "Use when hardening NATS client, leafnode, or cluster-route listeners; choosing token versus mTLS certificate mapping versus operator/NKey/JWT; validating nested NATS configuration; or proving authentication fails closed. Protect each listener separately, map leaf remotes to port 7422 and routes to 6222, extract nested blocks by brace depth with word-boundary anchors, wire validator tests into both local and CI gates, enumerate clients before rollout, and preserve unverified certificate/account assumptions until parse and functional tests run."
category: architecture
date: 2026-06-20
version: "2.0.0"
user-invocable: false
license: BSD-3-Clause
verification: mixed
history: nats-server-auth-authz-hardening.history
tags: [nats, authentication, authorization, tls, token, leafnode, cluster-route, config-validation, fail-closed, adr]
---

# NATS Server Authentication and Authorization Hardening

## Overview

NATS exposes separate security boundaries for clients (4222), cluster routes (6222), and leafnodes
(7422). Protecting one does not protect the others. Configuration presence is not enforcement proof:
parse with required environment, prove missing credentials fail, and run authorized/unauthorized
connections on every active listener.

Verification is `mixed`: dual-listener token hardening was CI-verified; cluster-route token hardening
and its six validator tests were verified locally with CI pending; earlier `verify_and_map`, accounts,
and certificate-role planning retained unresolved syntax and mapping risks. Details are in
[the notes](./nats-server-auth-authz-hardening.notes.md); exact prior content is in
[history](./nats-server-auth-authz-hardening.history).

## When to Use

- TLS exists but application-layer NATS authentication/authorization does not.
- Client auth was added but leafnode or route listeners still accept anonymous peers.
- Leaf remotes use 4222 instead of the leafnode port 7422.
- Cluster peers on 6222 need protection from unauthorized joins.
- A validator uses simple range matching on blocks containing nested `tls {}` sections.
- An unset environment variable may make configuration fail open or fail parse.
- A justfile recipe exists but CI never invokes it.
- A config test file exists but neither local nor CI gates call it.
- An issue cites stale config lines or an ADR number that may already exist.
- A certificate-mapping plan assumes bare CN matching or unverified `accounts {}` syntax.
- Fail-closed rollout may break plaintext clients that were never inventoried.

## Verified Workflow

### 1. Audit current listeners, identity, and clients

Read actual configuration and ADRs before editing:

```bash
rg -n 'authorization|verify_and_map|accounts|leafnodes|cluster|routes|listen' configs/nats/
rg -n 'nats://|NATS_URL|4222|6222|7422' --glob '!**/vendor/**' .
ls docs/adr/
```

Record which listeners are active, their ports, TLS state, current credentials, and every client or
peer. Separate clients that already support credential environment variables from clients needing a
code/config change. Tailnet isolation is defense in depth, not a substitute for broker identity.

### 2. Choose one supported identity model deliberately

- **Tokens:** simplest shared-secret rollout; independent credential per listener. Rotation and
  least privilege are limited, so keep values in secret storage and never commit them.
- **mTLS `verify_and_map`:** client certificate identity can map to users. Mapping order and exact
  names must be verified against the deployed NATS version; prior planning assumed SAN email, then
  SAN DNS, then RFC-2253 DN, never a bare CN.
- **Operator/NKey/JWT:** stronger decentralized tenancy but higher operational complexity. Confirm
  compatibility separately for clients, leafnodes, and cluster routes.

Do not combine proposed account/subject syntax with verified token deployment and call the whole
design verified. Preserve per-mechanism evidence boundaries.

### 3. Protect all active listeners independently

Token shape, with secret values supplied by the runtime:

```text
# top level: client listener, port 4222
authorization { token: <NATS_CLIENT_TOKEN> }

leafnodes {
  port: 7422
  authorization { token: <NATS_LEAF_TOKEN> }
}

cluster {
  port: 6222
  authorization { token: <NATS_CLUSTER_TOKEN> }
}
```

Leaf remote URLs target 7422 and provide the leaf credential. Cluster route credentials belong in
the cluster authentication contract, not a leaf-only NKey/JWT mechanism. When no routes exist, an
otherwise valid cluster authorization block is inert; tests must preserve that single-host case.

For certificate mapping, require client certs with the exact verified SAN identity and keep cluster
and leaf mutual verification distinct. `accounts {}` subject permissions must mirror the current
subject-schema ADR (the cited mesh used `hi.*`) and be parse/behavior tested before rollout.

### 4. Validate nested blocks by brace depth

Simple `awk '/leafnodes *{/,/^}/'` stops at the first nested close brace. Implement a `block(keyword)`
extractor that increments/decrements brace counts and begins only at a word-boundary match:

```awk
$0 ~ "(^|[[:space:]])" kw "[[:space:]]*\\{" { active=1 }
active { print; depth += gsub(/\{/, "{"); depth -= gsub(/\}/, "}") }
active && depth == 0 { exit }
```

Require the client authorization at top level, leaf authorization inside `leafnodes {}`, and cluster
authorization inside `cluster {}` when the block exists. A similarly named `subcluster {}` must not
satisfy the cluster check. Auth text outside the target block must not satisfy it either.

### 5. Prove fail-closed behavior

Run `nats-server -t -c <config>` with all required environment variables and expect zero. Unset each
required credential independently and expect nonzero; do not grep for an empty expansion or rely on
presence checks. If the binary is unavailable locally, a container with the exact production NATS
version is acceptable, but the command and mounts must mirror the deployed config.

Then run functional cases against a temporary broker:

1. authorized client/leaf/route connects and performs the allowed operation;
2. missing or wrong credential is rejected on each active listener;
3. allowed subjects succeed and denied publish/subscribe subjects fail;
4. TLS identity mismatch fails where certificate mapping is used;
5. single-host config without routes remains valid.

### 6. Wire tests into both gates

Test fixtures must cover nested braces, auth outside the target, misleading keyword prefixes,
authenticated listener, unauthenticated listener, and no-cluster single-host behavior. A test file
does not self-run: invoke it from the local task and a dedicated CI step. Grep both files to prove
the wiring, then run the repository required gate.

### 7. Roll out and document safely

Check ADR inventory before creating a number. Accepted ADRs are append-only; if the requested ADR
already owns this decision, amend only when repository policy permits an in-progress record,
otherwise create a superseding ADR. Document ports, listener-specific secrets, rotation, client
migration, rollback, and unverified certificate/account assumptions.

Stage rollout so credentials reach clients before the broker becomes fail-closed. Verify logs contain
no credential values, only listener and rejection classification.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --- | --- | --- | --- |
| Rely on network isolation | Trusted the tailnet as authentication | Any reachable compromised peer could join | Enforce broker-layer identity too |
| Protect client listener only | Added top-level auth | Leafnode listener remained anonymous | Configure every active listener separately |
| Use port 4222 for leaf remote | Connected to client port | Leaf protocol/auth contract lives on 7422 | Use listener-specific ports |
| Range-match nested config | Stopped at first closing brace | Nested TLS blocks truncated extraction | Track brace depth |
| Match `cluster` as substring | Accepted `subcluster {}` | Wrong block satisfied the guard | Anchor keyword boundaries |
| Grep token presence | Found text in the file | Did not prove nesting, parse, or enforcement | Parse and run negative connections |
| Treat unset variable as empty | Expected config to parse | NATS exits nonzero for missing required value | Assert nonzero as fail-closed behavior |
| Add only a just recipe | Assumed CI would discover it | Workflow never invoked the recipe | Add an explicit CI step |
| Create an unwired test | Added fixture script | No gate executed it | Wire local and CI commands |
| Map bare certificate CN | Assumed `verify_and_map` behavior | Mapping uses SAN/DN semantics, not bare CN | Verify exact deployed mapping and certificate SAN |
| Create requested ADR number blindly | Trusted issue prose | The number already existed | Inspect ADR inventory and policy first |

## Results & Parameters

| Boundary | Port | Required proof |
| --- | ---: | --- |
| Client | 4222 | Own auth block; allowed/denied client tests |
| Cluster route | 6222 | Auth inside `cluster {}`; peer success/failure; no-route pass |
| Leafnode | 7422 | Auth inside `leafnodes {}` and matching remote credential |
| Nested validator | N/A | Brace depth plus word-boundary keyword match |
| Missing credential | N/A | `nats-server -t` exits nonzero |
| Test wiring | N/A | Explicit invocation in local task and CI workflow |
| Certificate mapping | N/A | Exact SAN/DN mapping verified on deployed NATS version |
| Subject permissions | N/A | Functional allowed and denied publish/subscribe tests |

## Verified On

- Dual client/leaf token implementation: verified in CI.
- Cluster route token and validator suite: verified locally; CI was pending in the source case.
- Certificate mapping/accounts planning: unverified until parse and functional tests execute.

## Companions

- [Case notes](./nats-server-auth-authz-hardening.notes.md)
- [Version history and exact superseded snapshot](./nats-server-auth-authz-hardening.history)
