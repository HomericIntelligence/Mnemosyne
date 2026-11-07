---
name: extension-visibility-field-must-be-the-gating-field
license: BSD-3-Clause
description: "Make the field that a host gates on, not a descriptive field, carry the state in a plugin entry that an extension publishes. Use when: (1) an extension sets an enabled-style switch to make an entry selectable, (2) the host still hides the entry from its picker or list, (3) an entry must show a degraded state but stay selectable, or (4) a review claims a config flag defeats a host filter without host evidence."
category: tooling
date: 2026-11-06
version: "1.0.0"
user-invocable: false
verification: verified-live
tags:
  - plugin
  - extension
  - host-runtime
  - model-picker
  - visibility
  - status-field
  - config-flag
  - host-evidence
  - review-evidence
---

# Extension Visibility: Gate on the Field the Host Reads

## Overview

| Field | Value |
| -------- | ------- |
| **Date** | 2026-11-06 |
| **Objective** | Keep an entry that an extension publishes selectable in the host after a temporary outage, and prove which host field decides visibility. |
| **Outcome** | Successful. The `enabled` flag was set to true, but the host picker still hid the entry. The host gates on `status`. An isolated-host run proved the cause. The change kept `status` at the healthy value and put the degraded word in the display name. |

## When to Use

- An extension publishes entries, such as models, tools, or providers, with both a config switch, such as `enabled`, and a status or state word, such as `status`.
- The host picker or list still omits an entry after you set its config switch to true.
- An entry must stay selectable while its backing service is down, restarted, or degraded.
- A review or a plan says that a config flag defeats a host filter, and the claim has no host evidence.
- A string-keyed registry already holds the state word, so a change to the state word alone does not refresh the host list.

## Verified Workflow

### Quick Reference

```bash
# 1. Find the gate in the installed host, not in the extension source.
grep -ao 'status!=="deprecated"[^,)]\{0,20\}' "$(command -v <host-binary>)"

# 2. Prove the gate by execution in an isolated host home. Do not infer it.
R=<scratch>/hosttest; mkdir -p "$R/home/.config/<host>"
# Write a minimal provider with two entries:
#   status=<healthy>, enabled=true   -> appears
#   status=<hidden-word>, enabled=true -> must be absent
env -i HOME="$R/home" XDG_CONFIG_HOME="$R/home/.config" PATH=/usr/bin:/bin \
  TERM=dumb timeout 120 <host-binary> <list-command>
```

### Detailed Steps

1. Find the field that the host reads. Search the installed host binary or its
   package for the filter that selects list entries. A filter that compares a
   state word, such as `status`, does not read a config switch such as
   `enabled`. The switch can be true and the entry stays hidden.
2. Prove it by execution, not by inspection. Use an isolated home so that the
   user configuration cannot mask the result. Start the host with a minimal
   configuration that holds two entries. The two entries differ only in the
   state word. The hidden word must not appear.
3. Isolate the host fully. Many hosts read a managed service port from their
   own state directory, not from the configuration file. A port that is
   already in use stops the run and looks like a host failure. Set a free port
   with the host command for it, for example `<host> service set port <n>`.
4. Repair the field that gates visibility. If the host hides one state word,
   set the published entry to the visible word for every state. A service that
   is down must not set the hidden word, because that removes the entry and
   defeats a selectable-anyway goal.
5. Keep the user informed in the display string. Put the degraded word in the
   name, such as a `down · retry` token. The name is not a gate, so the entry
   stays selectable.
6. Check that state changes refresh the host list. A registration key that only
   contains the state word does not change when the state word does not change.
   Confirm that the key includes the observed value, such as the live count.
7. Write the documentation to the host behavior. State what the host does with
   a refused request. Do not promise a retry that the extension does not make.
   If the host returns a retryable refusal, give the user that refusal text and
   the action to take.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --- | --- | --- | --- |
| Set the config switch only | Set `enabled: true` on every entry and kept the degraded state word to show the state | The host picker filtered on the state word, so the degraded entry was absent from the picker and from the session list. The unit test passed because it checked the extension output, not the host filter | Test visibility through the host. The config switch is not the gate |
| Infer the gate from minified strings alone | Read the host bundle and concluded from the filter text that the switch was ignored | Minified helper names repeat with different bodies, so reading one call site is not proof | Prove the gate by execution in an isolated host home |
| Run the host with the real user configuration | Ran the host list command to compare entries | The real configuration supplied the real provider, so the stub entries were hidden by the user config, not by the field under test | Use an isolated home and an isolated port for the run |
| Dismiss a review finding that the filter was real | Accepted an earlier review verdict that the switch fixed the problem | The finding was correct. A second independent review and an execution run showed the entry was hidden, and a later change set the state word to the visible value | Check a filter claim against host evidence before you dismiss it |
| Promise a retry in the docs | Wrote that a request to a degraded entry is tried again instead of rejected | The extension only publishes the entry. The host refused the request with a retryable error, and the user had to try again | State what the extension does and what the user must do |
| Ignore reload on recovery | Expected the host list to refresh when the entry recovered | The registration key carried only the state word, which did not change | Confirm the registration key includes the observed value |

## Results & Parameters

### Configuration

```yaml
host_visibility_probe:
  isolated_home: <scratch>/hosttest/home
  isolated_port: host service set port <free-port>
  entries:
    - status: <visible-word>, enabled: true   # must appear
    - status: <hidden-word>,  enabled: true   # must not appear
  timeout_seconds: 120
published_entry:
  status: <visible-word>            # keeps the entry selectable
  config_switch: true               # not the gate
  display_name: "<name> — <state> · <observed value>"
registration_key: [endpoint, credential, entries_with_observed_value]
```

### Expected Output

- The isolated run lists only the entry with the visible state word. The
  hidden-word entry is absent, even with the config switch true.
- After the fix, every entry appears in the host list. A degraded entry states
  its state and the observed value in its name.
- A state change in the entry refreshes the host list.

## Verified On

| Project | Context | Details |
| --- | --- | --- |
| Self-hosted model gateway and its agent-host provider extension | A gateway model was hidden from the agent-host picker after a server restart, although the extension set the config switch to true | [notes](extension-visibility-field-must-be-the-gating-field.notes.md) |

## References

- [tooling-opencode-v2-plugin-install-compat](tooling-opencode-v2-plugin-install-compat.md) — plugin loading and version compatibility; this skill adds the field that gates entry visibility.
- [ci-gate-verify-artifact-is-consumed-before-guarding](ci-gate-verify-artifact-is-consumed-before-guarding.md) — confirm that the consumer reads an artifact before you guard it.