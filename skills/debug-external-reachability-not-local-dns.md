---
name: debug-external-reachability-not-local-dns
license: BSD-3-Clause
description: "Investigate reported service timeouts or 'the component is down' verdicts when the observation vantage point differs from the service: VPN or split DNS makes server-local reachability differ from the external client path, and a host-local probe on one node of a shared multi-node cluster cannot observe a component on another node. Use when: (1) a client reports a self-hosted service unreachable, (2) a socket-table or loopback probe on your own node returns nothing for a component that lives elsewhere in a shared cluster, or (3) a published state record can confirm liveness by its timestamp."
category: debugging
date: 2026-07-13
version: "1.1.0"
user-invocable: false
verification: verified-local
tags: []
history-source: "https://github.com/HomericIntelligence/Mnemosyne/blob/1956c91d76867bc2e484eaf573a57051855186f8/skills/debug-external-reachability-not-local-dns.history"
history-cleanup-date: "2026-09-20"
---

# Debug External Reachability, Not Local DNS

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-07-13 |
| **Objective** | Determine whether a reported timeout reflects a public reachability failure or misleading server-local DNS and overlay-network evidence |
| **Outcome** | An independent network vantage point and live access-log correlation replaced an incorrect local-network diagnosis with evidence of the service's actual state |

## When to Use

- A client reports a self-hosted service is unreachable or timing out
- The server hosting the service is itself a member of a VPN/mesh network with DNS features (Tailscale MagicDNS, WireGuard with custom DNS, corporate VPN split-DNS, etc.)
- You are debugging whether a service is really down, or only *looks* down because you checked from the wrong vantage point (the server itself, or another machine on the same private network)
- You work in an agent session on one node of a shared multi-node cluster, and you must decide whether a component on a different node is alive; a host-local probe cannot observe it
- DNS resolution performed on/from the server returns a private/CGNAT-range IP (e.g. Tailscale's 100.64.0.0/10) for a domain that should have a public IP
- You are tempted to blame a remote client's own VPN/tailnet connectivity (e.g. "their device is offline in `tailscale status`") without having independently verified the service's actual public reachability first

## Verified Workflow

### Quick Reference

```bash
# 0. Shared multi-node cluster: check the published record's freshness FIRST.
# A node-local probe cannot observe another node's process.
python3 - <<'PY'
import json, time
record = json.load(open("<shared-record-path>"))
age = time.time() - record["written_at"]
print("record_age_s", round(age, 1))
# age below the publish interval -> alive, stop here
PY

# 1. Never trust DNS resolved on/from the server (or same private network) as external truth.
# Explicitly query a known-public resolver instead of the default:
dig @8.8.8.8 <domain> +short
dig @1.1.1.1 <domain> +short

# 2. Test TRUE external reachability from a genuinely independent network vantage point
# (not the server's loopback, not the LAN, not anything on the same tailnet/mesh) --
# use a remote fetch tool/service running on unrelated infrastructure to hit the real
# public endpoints end-to-end (DNS -> internet routing -> port-forward -> firewall ->
# reverse proxy -> app):
#   GET https://<domain>/<health-path>          -> expect the documented healthy status
#   GET https://<domain>/<authenticated-path>   -> expect an authentication challenge

# 3. Correlate a live user retry against server-side access logs -- the most decisive check.
# Ask the user to retry right now, note the timestamp, then filter the reverse proxy's
# access log to that exact window:
tail -F /path/to/reverse-proxy/access.log | grep --line-buffered '<domain>'
# or, after the fact:
grep '<domain>' /path/to/reverse-proxy/access.log | awk -v t="<HH:MM>" '$0 ~ t'
```

### Detailed Steps

1. Do not trust DNS resolution performed on, or from, the server itself (or anything on
   the same private network as the server) as representative of what an external client
   sees, whenever the server participates in ANY VPN/mesh network with DNS features
   (Tailscale MagicDNS, WireGuard custom DNS, corporate split-DNS, etc.). Those resolvers
   may silently override the domain to a private overlay IP for tailnet/mesh members only.
2. Explicitly query a known-public DNS resolver instead of the system default:
   `dig @8.8.8.8 <domain> +short` or `dig @1.1.1.1 <domain> +short`. Compare the result to
   what the server's own/default resolver returns — a mismatch (private CGNAT range like
   100.64.0.0/10 vs. a real public IP) is the signature of a mesh-network DNS override, not
   proof the service is actually unreachable from outside.
3. Test true external reachability from a genuinely independent network vantage point — not
   curl on the server's own loopback, not a device on the same LAN or tailnet. A remote
   fetch tool/service running on infrastructure unrelated to the server's own network
   exercises the FULL real path a real external client experiences: public DNS -> internet
   routing -> router port-forward -> firewall -> reverse proxy -> application.
4. When possible, correlate directly with the reporting user's own live action: ask them to
   retry the failing action right now, and immediately check server-side access logs (e.g.
   a reverse proxy's `access.log`) filtered to that exact time window. This is the single
   most decisive diagnostic step — it observes ground truth (did the request even arrive?
   did it succeed or error?) instead of reasoning abstractly about DNS/routing/firewalls.
   If the request shows up succeeding at the exact moment of the retry, the "connectivity
   problem" theory is likely wrong and something else (client-side caching, a since-fixed
   outage, a transient issue) explains the original report.
5. Before committing to a root-cause theory and presenting it to the user as a fix,
   sanity-check it against evidence gathered from an independent vantage point — especially
   when the suspected culprit is itself a private/overlay network that the diagnosing host
   is also a member of. That is exactly the situation where local evidence is most likely to
   mislead, because the private network "helpfully" changes name resolution behavior for its
   own members.
6. Check whether the client enforces an always-on VPN or blocks traffic when its VPN is
   disconnected. This can produce the same timeout symptom as a server-side reachability
   failure, so verify the setting instead of inferring it from overlay peer status.
7. In a shared multi-node cluster, a host-local observation instrument is bound to its own
   node. A local socket-table read (`ss -x`), a loopback connect, or a local process list
   returns "absent" for a service that lives on a different node, even when the shared
   filesystem shows the service's files. Treat "my node cannot see it" as "I used the
   wrong vantage point", not "the component is down". Before you declare a remote
   component down, read its published state record (endpoint, heartbeat, or telemetry
   file on the shared filesystem) and compare its written-at timestamp to the current
   time. A record seconds old is decisive proof of liveness; only a stale timestamp
   (age above the component's publish interval) supports a down verdict, and even then
   confirm from the component's node or its network endpoint before you act.
8. Name the vantage point in the verdict. Record which node each probe ran on, so a
   later reader does not reuse a node-local absence as evidence of an outage.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Diagnosed from server-local DNS and overlay peer status | Resolved the domain on the server, received an overlay address, and blamed an offline client peer | Split-horizon DNS changed the result for overlay members, so the observation did not represent the public path | Query a public resolver and test from an independent network before assigning a root cause |
| Assumed the client enforced its disconnected VPN | Inferred that an always-on VPN policy blocked all client traffic | Client policy was not inspected, and peer status does not reveal operating-system traffic policy | Verify client settings directly and keep the theory provisional until the public path is tested |
| Declared a cluster component down from a node-local socket probe | Ran `ss -x` and a loopback connect on the session's own node, saw nothing, and concluded the operator was down | The component lived on a different node; a host-local instrument cannot observe it across nodes | Read the published state record's written-at timestamp; a record seconds old refutes "down" decisively |
| Concluded "down" for hours from repeated wrong-vantage probes | Re-ran the node-local probe on a schedule and treated each absence as fresh evidence | Each run reproduced the same instrument mismatch, so the absence carried no new information | One record-freshness read replaces any number of repeated node-local absences |

## Results & Parameters

### Configuration

```yaml
# Vantage points to check, in order of trustworthiness for "is this externally reachable":
vantage_points:
  - name: server_local_dns
    trust: low
  - name: lan_or_same_mesh_client
    trust: low
  - name: public_resolver_query
    command: "dig @8.8.8.8 <domain> +short"
    trust: high
  - name: independent_external_fetch
    target: "https://<domain>/<health-path>"
    trust: high
  - name: live_user_retry_plus_access_log_correlation
    trust: decisive
```

### Expected Output

- `dig @8.8.8.8 <domain> +short` returns the server's real public WAN IP, not a private
  overlay/CGNAT range (e.g. NOT in 100.64.0.0/10 for Tailscale)
- An independent external fetch to the service's documented health endpoint returns its
  expected healthy status
- An independent external fetch to an authenticated endpoint returns the documented
  authentication challenge rather than a network timeout
- Reverse-proxy access log shows the user's retry request arriving and succeeding within
  seconds of the timestamp they report retrying, confirming the service was reachable at
  that moment regardless of what server-local DNS or tailnet peer status suggested

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Self-hosted HTTPS service | Reported client timeout while the server participated in an overlay network with split-horizon DNS | Diagnosis corrected through a public-resolver query, an independent external fetch, and reverse-proxy access-log correlation |
