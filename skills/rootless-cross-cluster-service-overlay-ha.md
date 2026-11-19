---
name: rootless-cross-cluster-service-overlay-ha
description: "Design rootless cross-cluster placement and on-demand artifact transfer that survives one service-host failure. Use when: (1) secure service connectivity is required without root, a TUN device, or a transparent host VPN, (2) each cluster scheduler must retain allocation authority, (3) relay or gateway redundancy could be mistaken for end-to-end availability, or (4) an artifact must remain transferable after its original provider fails."
category: architecture
date: 2026-11-19
version: "1.0.0"
user-invocable: false
verification: unverified
tags: [cross-cluster, service-overlay, rootless, high-availability, placement, artifact-replication, idempotency, failure-domain]
---

# Rootless Cross-Cluster Service Overlay Availability

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-19 |
| **Objective** | Select new-work placements across clusters and fetch artifacts on demand without root networking, a central writer, or one service-host single point of failure. |
| **Outcome** | Proposed architecture: authenticated application streams use direct paths when available and at least two independent encrypted relays otherwise. The target cluster admits and schedules durable idempotent intents. A transfer becomes HA-ready only after verified copies exist in two independent provider and storage failure domains. |
| **Verification** | Design review and public protocol documentation only. No implementation, network measurement, or live outage drill has verified this composition. Treat every availability statement as a requirement to test, not as an operational result. |

## When to Use

- Applications need encrypted communication across clusters, but arbitrary host IP networking is unnecessary.
- The environment prohibits root, `CAP_NET_ADMIN`, TUN creation, route changes, or a hosted VPN dependency.
- New work may select a target cluster, while existing jobs remain under their current cluster scheduler.
- Loss of any one gateway, relay, controller host, or artifact provider must not stop new admissions or transfers.
- Network reachability is unknown, so direct communication cannot be the only path.
- Large immutable models, datasets, snapshots, or container images must be usable after one provider fails.

This rule does not provide live job migration, whole-site disaster recovery, or reconciliation of conflicting writes after an extended partition. Those goals need additional consistency, replication, and workload-specific recovery rules. Scheduler and durable-store availability remain external prerequisites: an overlay cannot make an unavailable scheduler accept an allocation.

## Verified Workflow

### Quick Reference

Separate these four availability contracts and test each one:

```text
Connectivity: authenticated service streams + independent relay paths
Control:      redundant admission + one fenced target-local writer generation
Placement:    durable intent ID + target reconciliation after uncertain effects
Data:         immutable identity + verified copies in independent failure domains
```

A second relay does not repair a single gateway, writer, authentication authority, scheduler, or artifact copy. Declare an artifact HA-ready only when the required copies are complete and verified; do not count a planned copy or an unreachable unique source.

### 1. Establish the network boundary

Use an application-layer service overlay, not a transparent host network. Put authenticated, encrypted streams in the application or an unprivileged sidecar. A local proxy port is acceptable when an existing application cannot use the stream API. Do not create a TUN interface, change routes, or require network-administration capabilities.

Require endpoint authentication and end-to-end encryption even when traffic crosses a relay. Treat relay metadata as visible to the relay operator. Separate relay admission from authorization for the cluster, actor, domain, operation, and artifact. Stable service identities survive process replacement; compute-job transfer identities are short-lived and job-scoped.

Start with at least two private relay instances in independent host and allocation failure domains. Replicate signed service-address catalogs, or make each record independently verifiable and available through more than one catalog provider. Public discovery, public relays, automatic port opening, and a single DNS or discovery service are not private-HA dependencies.

Permit direct QUIC or another authenticated encrypted transport when measurements show that it works. Keep an outbound relay path over an allowed TCP transport, such as TLS or WebSocket, for networks that block direct UDP. A deployment-time connectivity probe can measure TCP, UDP, proxy, MTU, and throughput constraints. Do not add a preflight probe to every request; apply [connect-first fallback and uncertain-effect reconciliation](transport-fallback-connect-first-not-probe.md).

If the selected overlay cannot prove private discovery, relay authorization, revocation, packaging, connectivity, and throughput, retain the upper protocols and replace only the transport adapter. Redundant mutually authenticated HTTPS or WebSocket relays are a simpler fallback with fewer peer-to-peer optimizations.

### 2. Keep scheduler authority target-local

Do not create a global scheduler or a second production writer for a cluster. Any redundant gateway can accept a typed placement intent, but only the target cluster's fenced writer generation creates its desired state and submits work to its scheduler. Keep the active writer and its standby in different failure units. Fencing, not process count, determines the single writer.

Give each intent a globally unique identifier, a request hash, actor and authorization evidence, immutable workload and artifact revisions, resource shape and count, eligible clusters, policy constraints, and expiry. Capacity advertisements are signed, short-lived, and advisory. The target revalidates admission, capacity, architecture, artifact locality, reservations, and policy before it accepts work.

A suitable target-local lifecycle is:

```text
Received -> Admitted -> ArtifactPreparing -> ReadyForSubmission
         -> Submitted -> Running
```

Use explicit `Held`, `Refused`, and `Reconciling` outcomes. Persist the intent before acknowledgement. After an uncertain send or acknowledgement failure, query the same target by intent ID and reconcile its recorded effect. Do not submit the same mutation to another cluster merely because the first outcome is unknown. After the first request byte, repeat a mutation through another path only when the retry carries the same globally unique intent ID and request hash, and the target atomically deduplicates it before any new effect. Without that contract, reconcile the original target before any new mutation.

Keep each allocation and replica wholly inside one scheduler domain. Existing reservations and allocations remain target-local. Select targets only for new placements; do not imply live migration or automatic drain-and-resubmit.

### 3. Make artifact availability independent of one provider

Reuse immutable artifact identities, signed manifests, domain-qualified authorization, and content digests. Exclude mount-specific metadata from cross-host identity; see [cross-host identity divergence](cross-host-identity-divergence-volatile-hash-inputs.md). A signed provider record should bind the artifact ID, provider identity, failure domain, authorization scope, and expiry. Physical deduplication must never grant visibility across authorization domains.

On a target-cache miss:

1. Authorize the request and fetch a signed manifest and current provider set.
2. Coalesce concurrent fetches of the same artifact on the target.
3. Stream bounded chunks or ranges and verify their content digests.
4. Resume from verified offsets after interruption; discard or repair unverified bytes.
5. Write owner-private staging, synchronize durable bytes, verify the complete artifact, and publish atomically.
6. Admit the target-local copy through the same image, signature, receipt, and provenance checks as a local build.
7. Submit the dependent workload only after local publication and admission complete.

Use the verified staging, atomic promotion, and source-retention rules in [shared-storage artifact relocation](slurm-shared-storage-artifact-relocation.md). Compute nodes read the published target-local copy; they do not depend on runtime reads from a remote provider.

An artifact that must survive one provider or storage-host failure needs at least two complete, verified copies in independent failure domains. A copy on another process above the same storage failure domain is not independent. A unique offline source is durable evidence, not available capacity. Retention must protect active references and the minimum verified-copy count; garbage collection must not remove the last available copy or create a window below the availability target.

### 4. Remove hidden central dependencies

Inventory gateways, writer and supervisor generations, keepers, relays, discovery catalogs, authentication snapshots, transfer providers, and durable state. Give every required role a replacement in another failure unit. The allocation-move inventory in [control-plane allocation moves](control-plane-allocation-move-inventory.md) helps find roles that otherwise remain on the failed host.

Persistent services need stable execution identity and controlled replacement before walltime expiry; see [scheduler service replacement identity](scheduler-service-replacement-identity-continuity.md). Relays and gateways need current signed authorization snapshots so they do not call one central authority for every connection. Request-time authentication and authorization remain fail-closed. A peer outage after launch causes bounded retry, another path, or degraded service; it must not deliberately stop a healthy component. Apply [runtime degradation rather than component termination](runtime-component-checks-degrade-not-stop.md).

Measure recovery objectives during drills rather than inventing a constant. Surviving components must accept new work automatically, but existing streams may disconnect and reconnect. Define this distinction in service-level objectives.

### 5. Qualify the complete failure matrix

Use unprivileged representative nodes for the initial network probe. Exercise direct paths, TCP-only relay fallback, proxy behavior, MTU limits, bulk throughput, and relay failover. Then run nonproduction drills that stop one gateway, writer host, relay, transfer provider, and authentication-authority host independently. Confirm automatic recovery and no duplicate placement after an ambiguous acknowledgement.

Also test corrupted chunks, interrupted transfer resume, replayed or expired intents, revoked relay credentials, cross-domain artifact denial, retention near the minimum copy count, and scheduler or durable-store degradation. Record which external dependencies prevent recovery. Verify that no path requires TUN creation, network-administration capability, public discovery, or runtime remote artifact reads.

## Failed Attempts

These are architecture alternatives rejected during design review, not executed failure experiments.

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Transparent host VPN | Evaluated a host-wide virtual interface and routes as the connectivity boundary | It violates a rootless constraint when the implementation needs a TUN device, route changes, or network-administration capability; it also exposes more networking than service connectivity requires | Select authenticated application streams or an unprivileged local proxy and verify the candidate's actual privilege requirements |
| Redundant relays as the complete HA design | Added a second relay while leaving one writer, gateway, or artifact provider | Traffic can survive relay loss while admission, scheduling, or transfer still stops on another host | Build and test a failure-unit matrix for every required role |
| Global cross-cluster writer | Considered one federated submission authority for all schedulers | It creates a central availability and consistency dependency and conflicts with target-local scheduler authority | Accept idempotent intents redundantly, but commit them through one fenced writer generation in the target cluster |
| Retry another target after an unknown outcome | Treated a lost acknowledgement as proof that no placement occurred | The first target may have persisted or submitted the work, so a second target can duplicate it | Reconcile by intent ID before any new mutation |
| One sealed artifact copy | Equated immutable content and durable storage with provider-failure availability | Integrity does not make the only copy reachable after its provider or storage failure domain disappears | Require verified copies in independent failure domains before declaring HA-ready |

## Results & Parameters

### Configuration

```yaml
scope:
  placements: new-only
  live_migration: false
  transparent_host_network: false
  single_service_host_failure: automatic-recovery-required
  extended_partition_reconciliation: false
overlay:
  endpoint_authentication: required
  end_to_end_encryption: required
  direct_path: measured-optimization
  private_relay_minimum: 2
  relay_failure_domains: independent
  public_discovery: disabled
placement:
  target_scheduler_authority: preserved
  writer: one-fenced-generation-per-target
  intent_deduplication: globally-unique-id-and-request-hash
  unknown_effect: reconcile-before-new-mutation
artifact:
  identity: immutable-content-digest
  publication: verified-staging-then-atomic-publish
  ha_ready_verified_copy_minimum: 2
  copy_failure_domains: independent
  runtime_remote_reads: forbidden
```

The numeric minima address one failure only when each copy and service role is in a different failure domain. Increase them for stronger site-loss or partition objectives.

### Expected Output

A qualified design and implementation should provide:

- secure service connectivity without root or host route changes;
- automatic use of a surviving relay and gateway after one instance fails;
- one target-local effect for a retried or reconciled placement intent;
- no dependent workload submission before verified local artifact publication;
- continued artifact transfer from a second independent provider after the first provider fails;
- fail-closed request authorization without stopping healthy components when a peer is unavailable; and
- drill evidence with measured recovery time, duplicate-effect checks, and explicit external availability limits.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Project-neutral multi-cluster scheduler and immutable artifact-store design | Architecture review against rootless networking, new-placement-only scheduling, and one-service-host-failure requirements | Public transport documentation and existing local-control and artifact-publication contracts supported the design. No live transport, failover, integrity, or recovery test ran; frontmatter therefore remains `unverified`. |

## References

- [RFC 9000: QUIC transport](https://www.rfc-editor.org/rfc/rfc9000)
- [RFC 8446: TLS 1.3](https://www.rfc-editor.org/rfc/rfc8446)
- [Connect-first fallback, not preflight probes](transport-fallback-connect-first-not-probe.md)
- [Runtime component checks degrade rather than stop](runtime-component-checks-degrade-not-stop.md)
- [Control-plane allocation move inventory](control-plane-allocation-move-inventory.md)
- [Scheduler service replacement identity continuity](scheduler-service-replacement-identity-continuity.md)
- [Shared-storage artifact relocation](slurm-shared-storage-artifact-relocation.md)
- [Cross-host identity divergence from volatile hash inputs](cross-host-identity-divergence-volatile-hash-inputs.md)
