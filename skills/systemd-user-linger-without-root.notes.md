# Notes: systemd-user-linger-without-root

Supporting evidence, generalized from a live verification in October 2026 on a
login node of a managed multi-login compute cluster. Site-identifying details
are replaced; the commands and outputs are otherwise exact.

## Evidence captures

Policy (stock rule present, no local override observed):

```text
$ grep -A4 'set-self-linger' /usr/share/polkit-1/actions/org.freedesktop.login1.policy | grep allow
    <allow_any>yes</allow_any>
    <allow_inactive>yes</allow_inactive>
    <allow_active>yes</allow_active>
```

Failure from the automation context (no logind session for the invoking PID):

```text
$ loginctl enable-linger
Could not enable linger: No such device or address
```

Enablement through the manager API with the explicit UID and no interaction:

```text
$ gdbus call --system --dest org.freedesktop.login1 \
    --object-path /org/freedesktop/login1 \
    --method org.freedesktop.login1.Manager.SetUserLinger 4695 true false
()

$ loginctl show-user $USER -p Linger
Linger=yes

$ ps -u $USER -o pid,cmd | grep 'systemd --user'
... /lib/systemd/systemd --user
```

Residual limit observed in the same context: `/run/user/<uid>` appeared after
enablement, and a user manager ran, but `systemctl --user` from the automation
context still failed with `Operation not permitted`. Unit management should be
verified from a real login session during rollout.

## Ladder values observed on the same host

- `sudo`: password required; treated as unavailable.
- crontab: denied by an administrator-controlled allowlist.
- `KillUserProcesses`: stock default `no`, so detached processes survive
  logout even without linger.
- self-linger: allowed, as shown above.

## Provenance

Learned during placement planning for a per-login-node reverse proxy for one
shared inference service. The planning record stays in that project; this
entry keeps only the reusable Linux decision rule.
