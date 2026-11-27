---
name: minecraft-lan-discovery-udp-4445-firewall
description: "Minecraft 'Open to LAN' worlds do not appear in the Multiplayer list when the firewall default-denies inbound. Add a UFW rule for UDP 4445 from the LAN subnet so multicast world announcements reach clients. Use when: (1) a Minecraft LAN world is visible by direct IP:port but not in the Multiplayer list, (2) setting up a new host's firewall baseline for a gaming or homelab mesh, (3) auditing firewall rules for Minecraft LAN play."
category: tooling
date: "2026-11-26"
version: "1.0.0"
user-invocable: false
tags: [minecraft, lan-discovery, firewall, ufw, udp-4445, multicast, homelab]
---

# Minecraft LAN Discovery: UDP 4445 Firewall Rule

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-11-26 |
| **Objective** | Ensure Minecraft "Open to LAN" worlds appear in the Multiplayer list on LAN clients. |
| **Outcome** | Operational — rule added to the mesh-wide firewall baseline. |

## When to Use

- A Minecraft LAN world is joinable by direct IP:port but does not appear in the Multiplayer list.
- You are setting up or auditing a firewall baseline for a host that participates in Minecraft LAN play.
- You are troubleshooting why Minecraft clients on the same LAN cannot discover each other's worlds.

## Verified Workflow

### Quick Reference

```bash
# Add the rule (UFW):
ufw allow from <LAN_SUBNET> to any port 4445 proto udp comment 'Minecraft LAN discovery (224.0.2.60:4445)'

# Verify:
ufw status | grep 4445
```

### How Minecraft LAN Discovery Works

1. A player opens a single-player world to LAN ("Open to LAN").
2. The host starts a temporary server on a **random high TCP port**.
3. The host multicasts a world announcement to `224.0.2.60:4445/udp` roughly every 20 seconds.
4. Clients listening on that multicast address receive the announcement and display the world in the Multiplayer list.
5. When a client joins, it connects to the host's random TCP port.

### The Problem

A default-deny inbound firewall (UFW with `default deny incoming`) silently drops the multicast UDP 4445 packets. Direct IP:port joins still work because the client initiates the TCP connection (stateful conntrack allows the return traffic). But the multicast discovery never reaches clients, so worlds never appear in the Multiplayer list.

### The Fix

Add one UFW rule to the firewall baseline:

```bash
ufw allow from <LAN_SUBNET> to any port 4445 proto udp comment 'Minecraft LAN discovery (224.0.2.60:4445)'
```

Where `<LAN_SUBNET>` is the LAN CIDR (e.g., `192.168.2.0/24`).

### Important Notes

- **The game port is separate.** The temporary server listens on a random high TCP port that changes each session. The UDP 4445 rule only enables *discovery*. To allow joining, either open the specific port shown in the "Open to LAN" message, or use a dedicated server with a fixed port.
- **Multicast vs. unicast.** The `224.0.2.60` address is a multicast group. UFW's `from <LAN_SUBNET>` matches the source IP of the packet, not the destination. The rule allows any UDP 4445 packet originating from the LAN subnet, which covers the multicast announcements.
- **Tailscale mesh.** If players are on different subnets (e.g., via Tailscale), multicast does not cross subnet boundaries. Players on the tailnet must join by direct IP:port or use a dedicated server.
- **fail2ban.** The UDP 4445 rule is in the firewall baseline, not in fail2ban. fail2ban does not need to be configured for this port.

### Integration with Host-Agnostic Scripts

In a multi-host setup, put the rule in the shared firewall baseline so every host gets it:

```bash
# shared/scripts/setup-firewall.sh
ufw allow from "$LAN" to any port 4445 proto udp comment 'Minecraft LAN discovery (224.0.2.60:4445)'
```

Host wrappers export `LAN_SUBNET` and call the shared script. The rule is verified in the script's self-check:

```bash
grep -q '4445' <<<"$status" || { echo "ERROR: Minecraft LAN discovery rule missing"; exit 1; }
```

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Direct IP:port join only | Open the specific TCP port shown in "Open to LAN" message | Works for joining but worlds never appear in the Multiplayer list; users must manually enter IP:port each time | Add UDP 4445 rule for discovery; open the game port separately for joining |
| Allow all multicast | `ufw allow to 224.0.0.0/4` | Too broad; allows all multicast traffic, not just Minecraft discovery | Scope the rule to port 4445 from the LAN subnet |
| Rely on default allow outgoing | Assume outbound multicast is allowed | UFW default deny incoming drops the *incoming* multicast announcement on clients, even though the host's outbound is allowed | The rule must be on the *receiving* (client) side, not just the hosting side |

## Results & Parameters

### Configuration

| Parameter | Value | Notes |
|-----------|-------|-------|
| Multicast group | `224.0.2.60` | Minecraft LAN discovery address |
| Discovery port | `4445/udp` | Multicast announcement port |
| Game port | Random high TCP | Changes per session; open separately |
| Announcement interval | ~20 seconds | Host re-announces periodically |
| Firewall rule | `ufw allow from <LAN> to any port 4445 proto udp` | In the mesh-wide baseline |

### Verification

```bash
# On the client, check if the rule exists:
ufw status | grep 4445

# Test discovery: open a world to LAN on one host, check Multiplayer list on another
# within 20-30 seconds.
```