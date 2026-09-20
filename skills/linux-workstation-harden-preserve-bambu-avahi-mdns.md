---
name: linux-workstation-harden-preserve-bambu-avahi-mdns
license: BSD-3-Clause
description: "Preserve mDNS printer discovery during Linux workstation hardening when Bambu Studio or OrcaSlicer uses LAN printers."
category: architecture
date: 2026-07-07
version: "1.1.0"
user-invocable: false
verification: verified-local
tags:
  - hardening
  - workstation
  - systemd
  - service-disable
  - avahi
  - avahi-daemon
  - mdns
  - bonjour
  - bambu
  - bambu-lab
  - bambu-studio
  - orcaslicer
  - 3d-printer
  - cups
  - ipp
  - linux-mint
  - ubuntu
history-source: "https://github.com/HomericIntelligence/Mnemosyne/blob/1956c91d76867bc2e484eaf573a57051855186f8/skills/linux-workstation-harden-preserve-bambu-avahi-mdns.history"
history-cleanup-date: "2026-09-20"
---

# Linux Workstation Hardening: Preserve Bambu Lab mDNS Discovery via avahi

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-07-07 |
| **Objective** | Preserve Bambu Lab LAN printer discovery through an template-host-a-style workstation hardening pass |
| **Outcome** | workstation hardened with avahi kept, cups disabled — Bambu Studio still auto-discovers printers on LAN; private infrastructure change (reference withheld) |
| **Verification** | verified-local |

## When to Use

- You're about to apply template-host-a's or template-host-b's `wpa_supplicant / ModemManager / avahi-daemon / bluetooth / cups / openvpn` service-disable block to a workstation that has Bambu Lab printers on the LAN.
- Bambu Studio or OrcaSlicer's "Devices" tab stopped auto-discovering LAN printers after a hardening pass or fresh install.
- A hardened box's `systemctl is-active avahi-daemon` says `inactive` and you need to decide whether to re-enable it.
- Deciding whether CUPS is required for LAN 3D printers (spoiler: no, not for Bambu).

## Verified Workflow

### Quick Reference

```bash
# template-host-a/template-host-b service-disable list MINUS avahi (Bambu mDNS discovery needs it).
# CUPS stays disabled — Bambu Lab printers do NOT use CUPS.
SERVICES=(wpa_supplicant ModemManager bluetooth blueman-mechanism
          cups cups-browsed cups.socket cups.path openvpn)
for svc in "${SERVICES[@]}"; do
  if systemctl list-unit-files "$svc" &>/dev/null; then
    sudo systemctl disable --now "$svc" 2>/dev/null || true
  fi
done
# Confirm avahi is still up so Bambu Studio can discover printers:
systemctl is-active avahi-daemon avahi-daemon.socket   # expect: active active
```

### Detailed Steps

1. **Identify that the target host has Bambu Lab printers on the LAN.**
   Prove that mDNS is what the slicer relies on before pruning anything:

   ```bash
   avahi-browse -at | grep -iE 'bambu|_octoprint|_ipp'
   ```

   If Bambu-branded services appear, the host is a Bambu-adjacent workstation and the carve-out
   below applies. If not, inspect available printer and slicer configuration; generic service names
   can hide the dependency. Preserve discovery while uncertain, continue other authorized changes,
   and ask only if removing the service requires a decision that the evidence cannot resolve.

2. **Build the service-disable list by REMOVING `avahi-daemon` and `avahi-daemon.socket`** from
   the template-host-a/template-host-b template list. Keep everything else. The template is:
   `wpa_supplicant ModemManager avahi-daemon avahi-daemon.socket bluetooth blueman-mechanism cups cups-browsed cups.socket cups.path openvpn` — carve avahi out, keep the rest.

3. **Run the loop.** `systemctl list-unit-files <svc>` returns success only if the unit exists
   on this host, so absent units are silently skipped — no manual pruning per distro is needed.

4. **Understand the CUPS-on-Ubuntu-24.04 quirk.** On Ubuntu 24.04 / Mint 22.1, `cups.service`
   is socket-activated: disabling `cups.socket` and `cups.path` prevents CUPS from ever
   starting, even though `cups.service` itself may not appear in `list-unit-files` output. This
   is expected — don't chase the missing `cups` echo. `ss -tulnp | grep ':631'` after the run
   should be empty; that's the real evidence CUPS is off.

5. **Verify the outcome.**
   - `systemctl is-active avahi-daemon` → `active`
   - `systemctl is-active cups.socket` → `inactive`
   - Open Bambu Studio → Devices → confirm the printer appears within ~10s of the tab opening.
   - `ss -tulnp | grep -E ':(631|5353)'` → UDP 5353 (mDNS) still listed by avahi; TCP 631
     (CUPS/IPP) gone.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|-----------------|
| Copy template-host-a's full disable list verbatim onto a Bambu-adjacent workstation | Ran the template-host-a SERVICES loop including `avahi-daemon avahi-daemon.socket` | Bambu Studio's "Devices" tab stopped auto-discovering the printer on the LAN. Bambu Studio + OrcaSlicer use mDNS/Bonjour discovery, which needs avahi. Manually typing the printer's IP + access code works but auto-discovery is gone until avahi comes back. | Carve `avahi-daemon` + `avahi-daemon.socket` out of any workstation-hardening service-disable list on hosts that talk to Bambu Lab printers |
| Keep CUPS "to be safe" for printing | Left `cups cups-browsed cups.socket cups.path` in the enabled set on the assumption a slicer/printer stack needs it | Bambu Lab printers do NOT use CUPS/IPP — they speak proprietary MQTT + HTTPS on their own ports. CUPS was pure attack surface (open port 631/IPP) with zero benefit. | Bambu is a fully out-of-band print stack; CUPS can be disabled on a Bambu-only workstation without losing any Bambu functionality |
| Use static IP + access code and forget mDNS | Configured each Bambu printer with a static DHCP reservation and its LAN-mode access code, planning to disable avahi | Works for the first configuration but breaks whenever DHCP re-hands the printer a new address (router reboot, printer power-cycle, network re-jigger) — the slicer's saved IP goes stale silently. Also requires re-configuring the slicer's device entry per printer. | mDNS discovery via avahi is the durable, low-maintenance path; disabling it trades a static-IP maintenance burden for a tiny reduction in attack surface (mDNS is Tailscale/LAN-local, ufw-scoped) |

## Results & Parameters

**Modified SERVICES array (copy-paste):**

```bash
SERVICES=(wpa_supplicant ModemManager bluetooth blueman-mechanism
          cups cups-browsed cups.socket cups.path openvpn)
for svc in "${SERVICES[@]}"; do
  if systemctl list-unit-files "$svc" &>/dev/null; then
    sudo systemctl disable --now "$svc" 2>/dev/null || true
  fi
done
```

**Verification block:**

```bash
# What SHOULD be on: avahi (mDNS for Bambu), the mesh essentials, plus the box's other daemons.
systemctl is-active avahi-daemon avahi-daemon.socket   # active active
ss -tulnp | grep ':5353'                               # avahi's mDNS listener on UDP 5353

# What SHOULD be off:
systemctl is-active cups cups-browsed cups.socket cups.path  # inactive * 4 (or 'unknown' where the unit doesn't exist on this distro)
ss -tulnp | grep ':631'                                # empty — no CUPS/IPP listener
```

**Reference deployment:** applied on `workstation` (Linux Mint 22.1 "Xia" / Ubuntu 24.04 base,
kernel 6.8.0-134-generic) via a private infrastructure change (reference withheld)
on 2026-07-07. See `workstation/scripts/harden.sh` step [3/6] in that PR. After the run:
`systemctl --failed` reports zero units in a failed state; avahi remained `active`; Bambu Studio's
Devices tab discovered the printer within seconds of opening.

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| local-infra | Onboarding host `workstation` (Mint 22.1) to the mesh hardening standard while preserving Bambu Lab printer discovery | Private change (reference withheld) — `workstation/scripts/harden.sh` step [3/6]; post-run `systemctl is-active avahi-daemon` → `active`, `systemctl is-active cups.socket` → `inactive`, Bambu Studio auto-discovered the LAN printer within ~10s |
