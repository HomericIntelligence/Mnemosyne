---
name: host-agnostic-shared-scripts-required-params
description: 'Shared infrastructure scripts must not silently default host-specific values (LAN subnet, ports, paths). Require them with ${VAR:?} and have host wrappers export the value. Use when: (1) a shared script is called by multiple hosts with different parameters, (2) a script currently defaults to a specific host value, (3) adding a new host to a mesh and its parameters differ from existing hosts.'
category: architecture
date: "2026-11-26"
version: "1.0.0"
user-invocable: false
tags: [host-agnostic, shared-scripts, required-params, fail-loud, wrappers, infrastructure]
---

# Host-Agnostic Shared Scripts with Required Parameters

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-11-26 |
| **Objective** | Ensure shared infrastructure scripts work correctly across all hosts without leaking one host's configuration to another. |
| **Outcome** | Operational — pattern applied to firewall, fail2ban, and verification scripts. |

## When to Use

- A shared script is called by multiple hosts that have different parameters (LAN subnet, allowed ports, host directory).
- A shared script currently defaults to a specific host's value (e.g., `LAN="${LAN_SUBNET:-192.168.2.0/24}"`).
- You are adding a new host to a mesh and its parameters differ from existing hosts.
- You are auditing shared scripts for host-specific literals.

## Verified Workflow

### Quick Reference

```bash
# Shared script: require the parameter, fail loud if missing
LAN="${LAN_SUBNET:?set LAN_SUBNET to this host's LAN CIDR, e.g. 192.168.2.0/24}"

# Host wrapper: export the value before calling the shared script
export LAN_SUBNET=192.168.2.0/24
bash shared/scripts/setup-firewall.sh
```

### The Problem

When a shared script defaults to a specific host's value, two things go wrong:

1. **Silent wrong-target**: If a new host forgets to pass its parameter, the script silently uses the old host's value. The firewall allows the wrong subnet, fail2ban ignores the wrong network, and verification passes against the wrong configuration.
2. **Copy-paste drift**: Host wrappers copy the shared script's default into their own code, creating duplicate logic that diverges over time.

### The Pattern

**Shared script** (host-agnostic, no defaults):
```bash
#!/usr/bin/env bash
set -euo pipefail

# Require LAN_SUBNET — fail loud if missing
LAN="${LAN_SUBNET:?set LAN_SUBNET to this host's LAN CIDR}"

# Validate format
if [[ ! "$LAN" =~ ^([0-9]{1,3}\.){3}[0-9]{1,3}/([0-9]|[12][0-9]|3[0-2])$ ]]; then
  echo "ERROR: LAN_SUBNET must be an IPv4 CIDR (got: $LAN)" >&2
  exit 1
fi

# Use $LAN throughout — never hardcode a subnet
ufw allow from "$LAN" to any port 22 proto tcp
```

**Host wrapper** (thin, exports the value):
```bash
#!/usr/bin/env bash
set -euo pipefail
export LAN_SUBNET=192.168.2.0/24   # this host's LAN

REPO_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
bash "$REPO_DIR/shared/scripts/setup-firewall.sh"
```

### Decision Rules

1. **Shared scripts never contain host literals.** No IP addresses, hostnames, or paths that belong to one host. Use parameters.
2. **Required parameters use `${VAR:?}`.** This fails immediately with a clear message instead of silently defaulting.
3. **Optional parameters use `${VAR:-default}`** only when a sensible default exists for all hosts (e.g., `RELOAD_SSH="${RELOAD_SSH:-reload}"`).
4. **Host wrappers are the only place host-specific values appear.** They export the values and call the shared script.
5. **Validate parameters in the shared script.** Check format (CIDR, port number, path existence) and fail loud on invalid input.
6. **Verify the result.** The shared script should check that the applied configuration matches the requested parameters.

### What to Check for Host Literals

```bash
# Search for common host-specific patterns in shared scripts
grep -rn '192\.168\.' shared/scripts/     # LAN subnets
grep -rn '100\.[0-9]*\.' shared/scripts/  # Tailscale IPs
grep -rn 'localhost\|127\.0\.0\.1' shared/scripts/  # loopback (may be intentional)
```

### Migration Checklist

When converting a shared script from host-specific to host-agnostic:

1. Identify all host-specific values (IPs, ports, paths, hostnames).
2. Replace each with a parameter using `${VAR:?}` or `${VAR:-default}`.
3. Add validation for each required parameter.
4. Update all host wrappers to export the parameter.
5. Update the shared README to document the new parameter.
6. Run `bash -n` on all scripts.
7. Search for remaining host literals: `grep -rn '192.168\.' shared/scripts/`

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Default to first host's subnet | `LAN="${LAN_SUBNET:-192.168.2.0/24}"` | New hosts silently used the old subnet; firewall allowed wrong network; fail2ban ignored real threats | Require the parameter with `${LAN_SUBNET:?}`; fail loud |
| Copy shared script per host | Duplicate the script in each host's directory with host-specific values | Drift: updates to one copy didn't propagate; bugs fixed in one host reappeared in others | One shared script, host wrappers export values |
| Use a config file | Read `LAN_SUBNET` from a shared config file | Config file itself becomes host-specific; another layer of indirection | Environment variables passed by wrappers are simpler and explicit |

## Results & Parameters

### Configuration

| Parameter | Required | Default | Validation |
|-----------|----------|---------|------------|
| `LAN_SUBNET` | Yes | None | IPv4 CIDR regex |
| `ALLOW_LAN_PORTS` | No | Empty | Space-separated port numbers |
| `HOST_DIR` | Yes | None | Directory existence check |
| `HARDENING_CONF` | Yes | None | File path |
| `JAIL_LOCAL` | Yes | None | File path |
| `PRINTER_URI` | No | None | IPP URI format |

### Verification

```bash
# Check for host literals in shared scripts
grep -rn '192\.168\.' shared/scripts/ && echo "FAIL: host literal found" || echo "OK: no host literals"

# Verify all wrappers export required params
for f in */scripts/harden.sh */scripts/tune.sh; do
  grep -q 'export LAN_SUBNET' "$f" || echo "MISSING: $f"
done
```