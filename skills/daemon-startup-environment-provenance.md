---
name: daemon-startup-environment-provenance
license: BSD-3-Clause
description: "Diagnose and prevent a long-running service that inherits connection settings from the shell that started it. Use when a service silently fails its external connections while a sibling component on the same host succeeds, when its errors contain a loopback address that the component documentation does not name, or when you review how a service receives its connection configuration."
category: debugging
date: 2026-11-26
version: "1.0.0"
user-invocable: false
verification: verified-local
tags: [daemon, startup, environment-inheritance, connection-route, configuration-provenance, diagnostics]
---

# Daemon Startup Environment Provenance

## Overview

| Field | Value |
| ------- | --------------- |
| **Date** | 2026-11-26 |
| **Objective** | Find and remove connection settings that a long-running service inherited from the interactive session that started it. |
| **Outcome** | Operational. The rule and the diagnostic found an inherited loopback dial host that silently failed every connection of one service while a sibling component with its own route worked. |

## When to Use

- A service fails its external connections while a sibling component on the same host reaches the same target.
- The service's error records name a loopback address, a tunnel port, or another node's local forward, and the component documentation names a remote target.
- The service swallows per-request failures into counters, so the cause is invisible.
- You review or design how a service receives its connection configuration.

Do not use this skill for a network fault that affects every process on the host. Check one healthy sibling process first; a fault that spares one component is a per-process configuration difference.

## Verified Workflow

### Quick Reference

```text
Rule:      a long-running service must receive explicit configuration, not an
           inherited interactive-session environment.
Read:      the running process's own view: its environ, its cmdline, and its
           first connection error record.
Do not:    accept "another component reaches the target" as proof that this
           process can.
Diagnose:  a failing dial host equal to loopback or a local tunnel port, while
           the document names a remote host = inherited session setting.
```

### Suggested Approach

1. Read the effective configuration of the actual process. Inspect its environment and command line, not the component page and not a working neighbor. A value in the live process wins over every document.
2. Compare the dial target in the failure record with the target in the component document. A loopback address or a local forward port in the failure, where the document names a remote host, is evidence of inheritance, not of a network fault.
3. Check where the value came from. Interactive sessions commonly export a dial host, a tunnel port, or a proxy that is valid only on that node. A service started from that shell keeps it, and a restart from the same shell keeps it again.
4. Prefer explicit inputs. Give the service its connection settings as typed arguments, flags, or an owner-only runtime record. Scrub node-local session settings from the start context. An environment allowlist for children is not sufficient if the service itself starts in the operator session.
5. Log the effective target class once at startup, without credential material. A startup line that names the host class (loopback, tunnel, direct) turns the next incident into one read.
6. Verify the repair by behavior. Send one request through the real path and read the result. A successful start is not evidence that the route is correct.
7. Use one owner for the route. When two components serve the same purpose with different routes, decide which one owns it, and stop or fence the other. See `daemon-request-loop-failure-visibility`.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Trust the working sibling component | Used one component's successful connection as proof of a valid route | Each process carries its own environment; the failing service inherited a session setting the other did not | Read the failing process's own configuration |
| Read the failure as a swallowed exception only | Fixed the error visibility first | Visibility made the counts readable but named no target | Visibility is a prerequisite, not a diagnosis; read the error content next |
| Restart the service from the same shell | Restarted after the first failure | The same interactive session exported the same wrong dial host | A restart from the same context repeats the cause |

## Results & Parameters

### Configuration

```yaml
diagnostic_order:
  - read_process_environ
  - read_process_cmdline
  - read_first_error_record
  - compare_with_documented_target
inheritance_signs:
  - loopback_dial_host
  - local_forward_port
  - node_local_proxy
repair:
  - pass_explicit_configuration
  - scrub_session_settings_from_start_context
  - log_effective_target_class_at_startup
```

### Expected Output

- The failing process's configuration names the same target class as the component document.
- The startup log shows the effective target class once.
- One request through the real path returns success.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Private multi-component deployment (identifiers withheld) | A background service inherited a loopback tunnel setting from the operator session and failed every database connection while key synchronization in a sibling component worked | See [notes](daemon-startup-environment-provenance.notes.md). |

## References

- Related: `daemon-request-loop-failure-visibility` (make the failures visible; one processor per queue)
- Related: `debugging-absence-of-evidence-verify-with-authority` (absence in a log is not proof)