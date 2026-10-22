---
name: systemd-user-linger-without-root
license: BSD-3-Clause
description: "Enable systemd user lingering for an unprivileged account without sudo, including from automation contexts where loginctl fails with ENXIO. Use when user units must survive logout and start at boot."
category: tooling
date: 2026-10-22
version: "1.0.0"
user-invocable: false
verification: verified-live
tags:
  - systemd
  - loginctl
  - linger
  - polkit
  - dbus
  - user-units
  - no-sudo
  - daemon-supervision
  - logout-survival
  - boot-persistence
  - service-account
  - managed-cluster
---
# Enable systemd User Lingering Without Root

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-22 |
| **Objective** | Make user-level systemd services durable (survive logout, start at boot) for an account that has no sudo and possibly no login session. |
| **Outcome** | Operational. Lingering was self-enabled through polkit with no administrator action; a user manager started; units survived logout and boot without tmux or cron. |
| **Verification** | verified-live: policy file read, enablement call succeeded, `Linger=yes` and a running `systemd --user` confirmed on a managed multi-login cluster login node, October 2026. See [notes](systemd-user-linger-without-root.notes.md). |

## When to Use

- User units must survive logout and start at boot, and the account has no sudo.
- `loginctl enable-linger` fails with `Could not enable linger: No such device or address` (ENXIO) from an automation, agent, or `su` context.
- Before you conclude "no user systemd here" and design a fallback (scheduler chains, supervisord, tmux keep-alive): not enabled is not the same as not enablable.
- Planning durable per-user services on managed multi-login or otherwise restricted hosts.

## Verified Workflow

### Quick Reference

```bash
# 1. Read the policy first. Stock systemd allows self-service linger.
grep -A4 'set-self-linger' /usr/share/polkit-1/actions/org.freedesktop.login1.policy | grep allow

# 2. Enable, skipping loginctl's session resolution (safe from automation).
gdbus call --system --dest org.freedesktop.login1 \
  --object-path /org/freedesktop/login1 \
  --method org.freedesktop.login1.Manager.SetUserLinger "$(id -u)" true false

# 3. Verify state, manager, and runtime directory.
loginctl show-user "$USER" -p Linger          # expect: Linger=yes
pgrep -u "$(id -u)" -f 'systemd --user'       # expect: a pid
ls -ld "/run/user/$(id -u)"                   # expect: directory exists
```

### Suggested Approach

1. **Classify the failure before you recover.** ENXIO means the caller has no resolvable logind session; it is not a policy denial. A polkit denial says "not authorized". The recoveries differ: an alternate call path for the first, an administrator request for the second.
2. **Read the policy before you ask for privilege.** Stock systemd ships `org.freedesktop.login1.set-self-linger` with `allow_any`, `allow_inactive`, and `allow_active` set to yes. Local rules can override it. When stock applies, linger needs no sudo, although common practice runs it as an administrator.
3. **Prefer the D-Bus call under automation.** `loginctl enable-linger` for the invoking user resolves the caller's session and fails with ENXIO when none exists (agent harnesses, `su`, some remote execution). `SetUserLinger(uid, true, false)` takes an explicit UID and, with interactive flag false, needs neither a session nor a polkit agent.
4. **Probe the full durability ladder before you design supervision.** Record: sudo rights (`sudo -n -l`), crontab usability (cron.allow/cron.deny can deny unprivileged users), effective `KillUserProcesses` in `logind.conf` (with the stock `no`, plain detached processes survive logout even without linger), and the self-linger policy. Then choose the highest available rung: user units, then a detached restart-loop daemon, then a profile-hook or manual restart.
5. **Accept that boot persistence always needs one privileged mechanism.** Lingering, a cron.allow entry, or a root-owned unit each need at most one administrator action, and only lingering is self-service under the stock policy. No purely unprivileged boot-time registration exists on a standard host; if every rung is denied, document a restart step and design clients to degrade rather than fail.
6. **Use the plain command from a real session.** From a PAM login session (SSH, console), `loginctl enable-linger` for the invoking user works under the same policy and is simpler to read in a runbook.
7. **Verify the bus from the context that will operate the units.** After enablement, `systemctl --user` from a non-session context may still fail to connect even with `XDG_RUNTIME_DIR` set. Confirm unit operations from the actual operating context (usually a real login session) during rollout, not from a one-off probe shell.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Linger from an automation context | `loginctl enable-linger` as the service account from an agent shell with no logind session | `Could not enable linger: No such device or address` | ENXIO is a session-resolution failure, not a policy denial; do not redesign around an assumed denial |
| Assuming sudo is required | Planned an administrator enablement step | Unnecessary: the stock polkit rule allows self-service | Read `set-self-linger` policy before you schedule administrator work |
| User bus from the same context | `systemctl --user` with `XDG_RUNTIME_DIR` set after linger was enabled | Connection refused with `Operation not permitted` | Linger plus a running manager does not guarantee bus reachability from every context; verify unit operations from the real operating context |
| Capability conclusion from one failure | `systemctl --user` failed, so the plan assumed no user systemd existed | The failure was absence of enablement, not absence of capability | Probe enablement before you conclude a primitive is denied; the conclusion changes the whole design |

## Results & Parameters

### Configuration

```yaml
linger_self_enable:
  policy_probe: "grep -A4 set-self-linger /usr/share/polkit-1/actions/org.freedesktop.login1.policy"
  enable_call: "org.freedesktop.login1.Manager.SetUserLinger(uid, true, false)"
  interactive_flag: false   # no polkit agent prompting from automation
  verify:
    - "loginctl show-user <user> -p Linger   # yes"
    - "pgrep -u <uid> -f 'systemd --user'"
    - "ls -ld /run/user/<uid>"
  revert: "loginctl disable-linger <user>"
ladder_probes:
  sudo: "sudo -n -l"
  cron: "crontab -l        # watch for cron.allow denial"
  logout_survival: "grep KillUserProcesses /etc/systemd/logind.conf"
  self_linger: "policy_probe above"
```

### Expected Output

- `Linger=yes` on the account, a `systemd --user` manager process, and an existing runtime directory.
- User units with `Restart=always` and `WantedBy=default.target` that survive logout and start at boot with no tmux, cron, or administrator action.
- A recorded ladder table per host, so the design chooses rungs by evidence rather than assumption.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Managed multi-login compute cluster | Unprivileged service account on a login node; enablement driven from an automation context | Self-linger policy allowed; D-Bus enablement succeeded; `Linger=yes` and user manager confirmed; October 2026. See [notes](systemd-user-linger-without-root.notes.md). |

## References

- [freedesktop logind D-Bus API (SetUserLinger)](https://www.freedesktop.org/software/systemd/man/latest/org.freedesktop.login1.html)
- [Periodic-task scheduler fallback chain](periodic-task-scheduler-fallback-chain.md) — the alternative when user systemd is truly denied
- [E2E cross-host doctor prerequisite checker](e2e-crosshost-doctor-prerequisite-checker.md) — session-bus environment for `systemctl --user` over SSH, and linger as a prerequisite pattern
