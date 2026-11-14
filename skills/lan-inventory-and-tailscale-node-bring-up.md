---
name: lan-inventory-and-tailscale-node-bring-up
description: "Enumerate devices on an owned LAN, reconcile them with a tailnet, classify each host by how an owner can act on it, and bring tailnet-eligible nodes online under their authorization boundary. Use when asked to list machines on the LAN, list machines on the tailnet, find LAN hosts missing from the tailnet, count passwordless-key SSH access on the LAN, or bring an owned LAN node onto the tailnet."
category: tooling
date: 2026-11-14
version: "1.0.0"
user-invocable: false
tags:
  - lan
  - tailscale
  - inventory
  - ssh
  - homelab
---

# LAN Inventory and Tailscale Node Bring-Up

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-14 |
| **Objective** | Produce a verified, two-sided inventory: which machines are on the owned LAN and which are on the tailnet; then safely bring tailnet-eligible, LAN-reachable nodes online. |
| **Outcome** | Operational |

Use this entry after you have the shared facts a session owns: the owned CIDR,
the owner account, and the tailnet membership. Stay inside that area. Do not scan
ranges the owner did not name, and do not use credentials that you were not given.

## When to Use

- List all machines on an owned LAN, or all machines on an owned tailnet.
- Answer which LAN hosts are not on the tailnet (or were on it but are logged out
  or offline).
- Count the LAN hosts that accept passwordless-key SSH from the owner's account.
- Bring an owned LAN node onto the tailnet that an installer or a gateway expects.
- Do not use this entry to replace an installer-focused walk-through for one host
  (see [tailscale-maestro-setup](./tailscale-maestro-setup.md)) or a known-fleet
  fan-out runbook (see
  [multi-repo-governance-and-ecosystem-setup](./multi-repo-governance-and-ecosystem-setup.md));
  use this entry when the host list is unknown and the first task is to build it.

## Verified Workflow

### Quick Reference

```bash
tailscale status                              # identity map of the tailnet
# LAN pass 1: ICMP (misses silent devices)
for i in $(seq 1 254); do ping -c 1 -W 1 <prefix>.$i >/dev/null 2>&1 & done; wait
# LAN pass 2: neighbor table (devices that answered at some point)
ip neigh show
# LAN pass 3: TCP 22 only (catches ICMP-silent SSH hosts)
for i in $(seq 1 254); do timeout 1 bash -c "echo > /dev/tcp/<prefix>.$i/22" 2>/dev/null && printf 'open-22-%s\n' "$i"; done
# LAN pass 4: local names for the responders, best effort
python3 -c "import socket,sys; [print(a, socket.gethostbyaddr(a)[0]) for a in sys.argv[1:]]" <addrs>
# Key-only SSH admission probe (no passwords)
ssh -o ConnectTimeout=4 -o BatchMode=yes <user>@<host> 'hostname; uname -sr'
```

### Suggested Approach

1. Build the tailnet map first with `tailscale status`. It is the identity map you
   join later. Record each peer as online or offline, and as LAN-reachable or not.
2. Enumerate the LAN with three passes: ICMP ping, the ARP/IPv6 neighbor table, and
   a TCP port-22 sweep of the owned CIDR. Ping alone misses devices that filter
   ICMP; the neighbor table alone misses fresh silent devices; the port-22 sweep
   catches SSH hosts that answer neither. Keep the sweep inside the owned CIDR.
3. Resolve names best effort with the local resolver the LAN already serves for
   DHCP clients (`getent hosts <ip>` or `socket.gethostbyaddr`). Some devices give
   no name, and randomized MACs carry no vendor. Do not treat a missing name as a
   failure; report it as a limit.
4. Classify every discovered address into five groups, then report them to the
   owner as two lists plus a cross-reference:
   - **A** — on the tailnet and online. Nothing to do.
   - **B** — LAN-reachable, SSH open, tailnet logged out or offline, key access
     works. Tailnet-eligible; go to step 5.
   - **C** — LAN-reachable, SSH open, key access denied (publickey). Requires the
     owner's credentials; hand over the exact command, do not attempt passwords.
   - **D** — SSH open but the presented host key does not match the remembered
     key. Halt for that host; go to step 6.
   - **E** — no SSH, or IoT/infrastructure appliances. Not actionable; report.
   One physical box can appear on two addresses with the same MAC (secondary
   interface or alias); record both and treat it as one device.
5. Bring-up of group B requires interactive authorization by the owner:
   - Confirm the daemon is running and the node is logged out (`tailscale status`
     prints a login URL, `tailscaled` reported active while logged out is normal).
   - Re-running `tailscale up` with a plain user often fails with an access-denied
     error; run `sudo tailscale up` interactively as the owner. Neither this entry
     nor any agent grants that authorization.
   - If the node previously stored non-default settings, repeat them explicitly
     in the same command (for example, `--accept-dns=false`), or choose `--reset`
     deliberately. Without either, the daemon refuses to change settings silently.
   - The owner opens the printed one-time login URL in a browser and authorizes
     the node. One-time URLs are secrets for that session; never store, commit,
     or print them into artifacts beyond the immediate hand-off message.
   - Verify success afterwards: `tailscale status` shows the node online and the
     owner can reach it at its 100.x/fd7a: address or by name. Do not claim
     bring-up succeeded before this check.
6. Host-key mismatch (group D) is a stop condition, not a setup step:
   - Never bypass verification (`StrictHostKeyChecking=no`) and never append a
     freshly scanned key over a changed remembered key — appending defeats
     verification entirely.
   - A previously-added remembered entry may be stale (reimaged node, swapped
     NIC, or name reuse). Only the owner can confirm which. Report the mismatch,
     the verification time, and that no connection was made.
   - If the owner confirms the node is legitimate, the fix is to have the owner
     (or its explicit instruction) remove the stale remembered entry, then
     reconnect and verify the fingerprint again against an out-of-band source
     (owner console, client list on the access point).
7. Close with the full inventory: two lists (LAN, tailnet), the LAN↔tailnet
   cross-reference, and the explicit limits — ICMP-silent hosts that also lack
   port 22 were not seen; the count of responders; randomized MACs with no name;
   and whether the owner already authorized each group-B bring-up.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Ping-only sweep | Enumerated the LAN with ICMP one packet per host | Devices that filter ICMP were missing from the list | Add ARP/neighbor and TCP-22 passes before declaring the list complete |
| One address = one device assumption | Counted each responding address as a separate machine | One host answered on two addresses with one MAC (secondary interface/alias) | Group addresses by MAC before reporting counts |
| `ssh-keyscan … >> known_hosts` for a changed key | Appended freshly scanned keys to the remembered store to "refresh" | Appending defeats host key verification; it silences the exact alarm a mismatch should raise | Halt on any changed key; resolve out of band with owner confirmation |
| `tailscale up` as a plain user | Started the login flow without elevation on a logged-out node | Denied by the daemon: operator privileges or `sudo tailscale up` are required | Gate bring-up on interactive owner sudo; never claim success before `tailscale status` shows online |
| Re-run `tailscale up` without previously set non-default flags | Repeated the command as stored in history, with defaults | The daemon refuses to apply changed settings silently and prints an access message that names the required explicit flags | Repeat the node's prior non-default flags or pass `--reset` deliberately |
| Assume the login completed | Treated "owner clicked the link" as bring-up complete | No verification was run; the node can stay logged out | Re-check `tailscale status`; report it as pending until the check passes |

## Results & Parameters

### Configuration

No persistent configuration is required. The only durable inputs are the owner's
owned CIDR and the owner account that holds the group-B nodes' keys.

### Expected Output

- List 1: every discovered LAN device — address, name or "(no name)", MAC, group
  (A/B/C/D/E), and how access was verified.
- List 2: every tailnet peer — name, address, online/offline, and LAN mapping when
  one exists.
- Cross-reference table and the verification limits, including which passes were
  skipped and why.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Single-owner LAN with a tailnet mesh | Local host session, 2026-11-14 | Inventory of 19+ addresses, 3 passwordless-key SSH hosts, 2 logged-out nodes identified; one host-key mismatch left unresolved pending owner confirmation |

## References

- [Multi-repo governance and ecosystem setup](./multi-repo-governance-and-ecosystem-setup.md) — fleet fan-out after you know the host list and host keys are pinned.
- [Tailscale Maestro setup](./tailscale-maestro-setup.md) — install and first-login walk-through for one host.
- [Homeric cross-host deployment and mesh topology](./homeric-crosshost-deployment-and-mesh-topology.md) — service topology after the nodes are online.
- [Notes](./lan-inventory-and-tailscale-node-bring-up.notes.md) — evidence and failure signatures behind this entry.
