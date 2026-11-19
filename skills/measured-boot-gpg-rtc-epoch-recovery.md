---
name: measured-boot-gpg-rtc-epoch-recovery
license: BSD-3-Clause
description: "Diagnose and recover a Heads/PureBoot-style measured-boot machine whose GPG key is reported unusable and whose kexec boot params fail signature verification, most often after power loss reset the RTC to the Unix epoch. Use when boot fails with \"unusable public key\", \"gpg: verify signature failed: Unknown system error\", or \"Invalid signature on kexec boot params\", or when the recovery shell shows Jan 1 1970."
category: debugging
date: 2026-11-17
version: "1.0.0"
user-invocable: false
verification: verified-local
tags: []
---
# Measured-Boot GPG Signature Failure After RTC Reset

## Overview

| Attribute | Value |
| ----------- | ------ |
| **Date** | 2026-11-17 |
| **Objective** | Restore boot on a measured-boot machine (Heads/PureBoot family) that refuses to load the installed operating system after an OS update or power loss, with GPG reporting the key unusable and the kexec boot params rejected |
| **Outcome** | Successful: boot restored by correcting the RTC and re-signing the boot partition; verification passed on subsequent boot |

## When to Use

Use this skill when all or most of these hold:

- The machine uses a Heads/PureBoot-style measured boot chain and fails before the OS starts.
- The firmware screen shows one or more of: an OS-update-triggered `/boot` mismatch, `gpg: no default secret key: unusable public key`, `gpg: signing failed: unusable public key`, `gpg: verify signature failed: Unknown system error`, `Unable to sign kexec hashes`, `Invalid signature on kexec boot params`, or `Failed default boot`.
- The failure appeared after an OS update that touched `/boot` (kernel, initramfs, bootloader config), or after an unexplained power interruption.
- The security key (OpenPGP-capable USB dongle) is detected, and the key has no expiry set.
- The recovery shell reports `date` as `Thu Jan 1 1970` (or another stale date).

Do NOT use this skill for:

- A machine whose only symptom is an unexpected reboot with correct boot verification — see `linux-diagnose-unclean-reboot-dead-cmos.md` for that diagnosis.
- Suspected key compromise or tampering — treat that as a security incident; do not re-sign to make the error go away.
- Expired keys: extend the expiry, export the updated public key, re-import it into the firmware keyring, then sign — no clock fix is required.

## Verified Workflow

### Quick Reference

```bash
# Role: recovery shell (in-firmware rescue environment)
date                              # If this prints Jan 1 1970, stop fixing signatures and fix time
date -s "2026-11-17 12:34:00"     # busybox date; use true UTC time
hwclock --systohc                 # persist to the RTC (busybox: hwclock -w)
date && hwclock                   # both must agree and show true time
# Then: reboot into the firmware menu (or keep the session and navigate there)
#       Options -> Update checksums and sign all files in /boot
#       insert BOTH the security key and the vault (gold USB) when prompted
```

### Suggested Approach

1. **Do not factory-reset yet.** A measured-boot firmware keeps only public keys and relies on GPG validity windows. The most common cause of "unusable key" with a non-expired key is a reset RTC: the real-time clock lost battery-backed power (unplug, breaker, PSU hiccup, dead coin cell) and now reads the Unix epoch, so GPG sees the key as "created in the future".
2. **Check the clock before the keys.** In the recovery shell run `date` and `hwclock`. If either shows 1970 or a stale fixed date, set it (`date -s`), persist it (`hwclock --systohc`), and confirm both agree.
3. **Re-sign `/boot` only after the clock is correct.** In the firmware Options menu choose `Update checksums and sign all files in /boot`. Insert both the security key and the vault. Success is reported as an operation success message. Verification then passes on the next boot.
4. **Fix the root cause.** Replace the CMOS/RTC coin cell. The RTC resets only on total loss of standby power, so a recurring 1970 date means the battery is exhausted or the machine loses standby power.
5. **Keep the procedure for every future update.** Each OS update that rewrites `/boot` triggers the same signature check. Expect to re-sign at next boot with both devices inserted. This is the designed control, not an error.
6. **Kernel panic on `exit` from the recovery shell is harmless.** The shell is ephemeral; a panic there does not touch disk state. Power-cycle and return to the menu or the shell.
7. **If signing succeeds but verification still fails** after the clock is correct and the keys match, suspect a public/secret key-pair mismatch (for example, an interrupted initial provisioning due to power loss). Compare the fingerprint in the firmware GPG key list with `gpg --card-status` on the security key. A persistent mismatch requires full re-provisioning (factory reset/re-ownership) with the original vault and backups. Do not attempt this casually.
8. **A firmware reflash alone does not repair this.** It can restore a broken firmware image; it cannot give GPG a valid time window or repair a mismatched key pair. Flash does not substitute for the steps above.

### Ordering notes

- A dead-vs-present TPM (e.g., a `TOTP: No TPM` line) is an independent signal; HOTP can still succeed. Record the TPM state, but do not let it block the signature repair.
- Verify the time persists across a reboot before concluding the repair (`date` again after reboot). If the RTC is battery-dead, every cold boot re-triggers the epoch and the signatures fail again until the cell is replaced.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Re-signing at the default 1970 clock | Ran the firmware update-checksums-and-sign flow with an RTC reset to epoch 0 | GPG rejected the key as not valid at that time; signing and verification both failed with "unusable public key" / "verify signature failed: Unknown system error" | Correct and persist the RTC first; sign only after `date` and `hwclock` agree on true time |
| Assuming key expiry or a key mismatch | Spent effort comparing keys and considering re-enrollment before checking the clock | Keys were fine and fingerprints matched; the GPG validity window was the blocker | Check `date` and `hwclock` before any key operation on a measured-boot machine |
| Firmware reflash as a fix | Flashed updated firmware and re-signed HOTP with the vault | Boot still stopped at "Invalid signature on kexec boot params" because the verification ran against a broken time base and stale signed config | Reflash does not repair RTC-gated GPG validity; correct time and re-sign `/boot` |
| Typing `exit` in the recovery shell | Tried to return to the menu GUI via `exit` | The in-firmware shell kernel-panicked | Recovery-shell `exit` may panic; it is ephemeral and safe — power-cycle instead |
| Treating the first "Unknown system error" as firmware corruption | Considered re-flash and factory reset immediately | The environment was fine; the signature config was stale because of the clock | Rule out the RTC and the re-sign step before any destructive or re-provisioning action |

## Results & Parameters

### Commands that recovered the machine

```bash
# In the recovery shell:
date                                     # observed: Thu Jan 1 1970
date -s "2026-11-17 12:34:00"            # true UTC time; busybox-compatible
hwclock --systohc                        # persist into the RTC; survives reboot only if the cell holds charge
date && hwclock                          # both must agree
# Firmware menu: Options -> Update checksums and sign all files in /boot
#                 insert security key + vault; confirm GPG card
```

### Expected output

- `date` and `hwclock` print the true date, identical to each other, and the value survives a reboot.
- The update-and-sign operation reports success with both the security key and the vault inserted.
- The next boot passes HOTP and shows the true time; the "Invalid signature on kexec boot params" message is gone and the OS loads.

### Recurrence prevention

- Replace the CMOS coin cell; expect the failure on every cold boot until it is replaced.
- After any OS update that rewrites `/boot`, re-sign at next boot before assuming tampering.
- Keep vault and GPG backups offline; a factory reset is unrecoverable without them.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Measured-boot OS deployment (Heads/PureBoot class) | 2026-11-17 recovery incident: OS update followed by power-loss-induced RTC reset to epoch 0 | Verified: correcting and persisting the RTC, then re-signing `/boot` with key and vault, restored normal boot; fingerprints matched throughout |

## References

- Related: skills/linux-diagnose-unclean-reboot-dead-cmos.md (dead CMOS as a cause of unclean reboot; this skill covers the measured-boot signature failure it can trigger)
