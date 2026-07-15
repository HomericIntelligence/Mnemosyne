---
name: debug-external-reachability-not-local-dns
description: "Verify whether a self-hosted service is truly unreachable from outside, instead of trusting DNS/reachability checks run on a server that is itself a VPN/mesh member. Use when: (1) a client reports a self-hosted service is unreachable/timing out, (2) the server is itself on a VPN/mesh network with custom DNS (e.g. Tailscale MagicDNS, WireGuard split-DNS, corporate VPN split-horizon), (3) debugging whether a service is really down or just looked-down from the wrong vantage point."
category: debugging
date: 2026-07-13
version: "1.0.0"
user-invocable: false
verification: verified-local
tags: []
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
- DNS resolution performed on/from the server returns a private/CGNAT-range IP (e.g. Tailscale's 100.64.0.0/10) for a domain that should have a public IP
- You are tempted to blame a remote client's own VPN/tailnet connectivity (e.g. "their device is offline in `tailscale status`") without having independently verified the service's actual public reachability first

## Verified Workflow

### Quick Reference

```bash
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

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Diagnosed from server-local DNS and overlay peer status | Resolved the domain on the server, received an overlay address, and blamed an offline client peer | Split-horizon DNS changed the result for overlay members, so the observation did not represent the public path | Query a public resolver and test from an independent network before assigning a root cause |
| Assumed the client enforced its disconnected VPN | Inferred that an always-on VPN policy blocked all client traffic | Client policy was not inspected, and peer status does not reveal operating-system traffic policy | Verify client settings directly and keep the theory provisional until the public path is tested |

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
