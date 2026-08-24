---
name: architecture-container-secret-cmdline-leak-fix
license: BSD-3-Clause
description: "Prevent containerized services from exposing credentials through launch argv, child-process argv, effective-configuration dumps, startup logs, exceptions, crash artifacts, or retained files. Use when: (1) moving a secret from a command-line flag into an environment variable, file, or stdin, (2) a runtime or framework serializes its parsed configuration, (3) a cmdline-only regression test passes but a credential still appears in logs, (4) responding to a credential exposure that requires containment, rotation, and historical-log remediation."
category: architecture
date: 2026-06-19
version: "2.0.0"
user-invocable: false
verification: verified-local
history: architecture-container-secret-cmdline-leak-fix.history
tags:
  - containers
  - secrets
  - command-line
  - effective-configuration
  - logging
  - redaction
  - credential-rotation
  - security-boundary
---

# Container Secret Exposure Surface Audit

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-06-19; broadened 2026-08-24 |
| **Objective** | Keep a service credential out of every observable and retained surface, not only the launcher command line. |
| **Outcome** | Model the complete secret flow, choose the least-exposed transport each consumer supports, redact at serialization boundaries, restrict retained artifacts, and prove absence using a sentinel through the real launch path. |
| **Verification** | verified-local — a container launch kept a credential out of its constructed command line, but inspection of actual runtime output found that the framework serialized the parsed configuration, including the credential, into retained startup logs. |
| **History** | [changelog](./architecture-container-secret-cmdline-leak-fix.history) |

## When to Use

- A container command includes a secret-bearing flag, an inline environment assignment, or a token-bearing URL.
- A launcher is being changed from `--credential <value>` to an environment variable, mounted file, secret descriptor, or stdin.
- The launched application, framework, or child process logs its parsed arguments or effective configuration.
- A test asserts that a secret is absent from a constructed command but does not inspect emitted logs or retained artifacts.
- Logs, tracebacks, support bundles, crash dumps, or generated configuration files have a broader audience or longer lifetime than the credential should have.
- A credential was exposed and the response must address both future launches and historical copies.

## Verified Workflow

### Quick Reference

```text
1. Map: source -> launcher -> container -> child -> parsed config -> diagnostics -> retention.
2. Minimize: use the least-observable transport supported by each consumer.
3. Redact: serialize only an allowlist of safe diagnostic fields.
4. Restrict: create logs and artifacts for the intended audience, with bounded retention.
5. Prove: inject a sentinel through the real launch path and scan every observable surface.
6. Respond: contain historical copies and rotate the credential after any exposure.
```

### 1. Inventory the complete secret flow

Do not stop at the wrapper command. Trace the value through every transformation and consumer:

```text
secret store
  -> launcher argument / environment / file descriptor / mounted file / stdin
  -> container runtime metadata
  -> entrypoint and child-process argv or environment
  -> parsed application configuration
  -> startup summaries, exception text, tracebacks, metrics, and health output
  -> log files, collectors, support bundles, crash dumps, and backups
```

For each edge, record who can observe it and how long it persists. Process listings, runtime inspection APIs, scheduler metadata, logs, and backups are separate trust boundaries even when they originate from one launch.

### 2. Choose transport per consumer, not once per service

Prefer a secret manager or runtime-native secret descriptor. When the application supports it, a mode-restricted mounted file or inherited file descriptor usually exposes less than argv or a literal environment assignment. Environment variables can be an improvement over argv, but they remain visible through process inspection, debug dumps, child inheritance, and configuration serialization.

Keep asymmetric paths explicit. A control-plane client, worker, and health probe may require different authentication mechanisms. Moving one path off argv does not prove the others are safe.

### 3. Treat effective configuration as a publication boundary

Many runtimes log a dataclass, namespace, settings object, or reconstructed command at startup. If that object contains the parsed secret, changing the injection mechanism does not prevent the value from being logged.

Use an allowlisted diagnostic projection instead of serializing the authoritative configuration:

```python
def diagnostic_config(config: object) -> dict[str, object]:
    return {
        "bind_address": config.bind_address,
        "worker_count": config.worker_count,
        "auth_enabled": bool(config.api_key),
    }
```

Prefer `auth_enabled: true` or a non-reversible credential identifier over a masked value. Masking can still leak length or prefixes and is easy to apply inconsistently. Ensure exception formatting and object `repr` implementations follow the same rule.

### 4. Protect retained diagnostics at creation time

Redaction is the primary boundary; permissions are defense in depth. Create sensitive diagnostic directories with access limited to their intended operators, set a restrictive umask before file creation, and define rotation and deletion. Do not write broadly readable logs and plan to fix their mode later.

If a diagnostic genuinely needs a secret-bearing payload, isolate it from routine logs, mark it sensitive, bound its lifetime, and make access explicit. A normal startup log should never require the credential itself.

### 5. Test the real emitted surfaces with a sentinel

Use a unique non-production sentinel and exercise the same launch/configuration path as production. Assert both authentication behavior and secret absence:

```text
positive: authenticated operation succeeds with the sentinel credential
negative: sentinel is absent from
  - constructed launcher command and runtime metadata
  - live parent and child process argv
  - emitted stdout/stderr and startup logs
  - serialized health or diagnostic output
  - generated config, support bundles, and failure artifacts
permission: retained sensitive artifacts match the declared audience
```

Include a failure-path case because exceptions and crash reporting often bypass normal redaction. A unit test of the command builder is useful, but it is not sufficient evidence for the end-to-end invariant.

### 6. Respond to an observed exposure completely

Once a real credential has reached an observable or retained surface:

1. Stop future emission at the earliest serialization boundary.
2. Restrict or quarantine affected logs and collectors.
3. Identify replicas, archives, support bundles, and backups within scope.
4. Rotate or revoke the credential; assume copied values remain usable until then.
5. Delete historical copies according to the incident and retention policy.
6. Re-run the sentinel test against success and failure paths.

Changing the launch command protects future processes only. Rotation without containment leaves readable historical copies; deleting logs without rotation leaves copied credentials valid.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| ------- | -------------- | ------------- | -------------- |
| Move the secret off argv and stop | Replaced a secret-bearing flag with configuration or environment injection | The runtime serialized the parsed configuration, so the same plaintext value appeared in retained startup logs | Audit the full secret flow; transport changes do not control downstream publication |
| Test only the command builder | Asserted the sentinel was absent from the constructed container command | The test never launched the framework or inspected its actual stdout, stderr, child processes, or files | Run a sentinel through the real launch path and scan emitted and retained surfaces |
| Redact a short denylist of field names | Masked familiar keys such as `token` or `password` | Aliases, nested objects, URLs, exception text, and future fields bypassed the denylist | Publish an allowlisted diagnostic projection rather than the authoritative config |
| Rely on restrictive log permissions alone | Kept plaintext credentials in logs but limited file access | Copies can reach collectors, backups, support bundles, or later permission changes; authorized readers still receive an unnecessary secret | Remove the credential at serialization; use permissions only as defense in depth |
| Rotate without remediating retained logs | Issued a new credential after fixing future launches | Historical copies remained sensitive evidence and could disclose usage patterns or an accidentally unrevoked value | Contain and retire historical copies as part of the same response |
| Suppress all startup diagnostics | Disabled useful configuration logging entirely | Operators lost safe information needed to diagnose launches | Keep a small allowlist of reviewed, non-secret fields and authentication state |

## Results & Parameters

### Surface Contract

| Surface | Required invariant | Verification |
| ------- | ------------------ | ------------ |
| Launcher and runtime | No literal credential in argv, inline environment assignments, labels, or reconstructed commands | Inspect the rendered command and runtime metadata with a sentinel |
| Parent and child processes | No literal credential in process argv; inheritance is limited to consumers that require it | Inspect the live process tree during the test launch |
| Effective configuration | Authoritative config is never serialized directly; diagnostic output uses an allowlist | Capture startup output and exercise object formatting and exception paths |
| Logs and health output | Sentinel absent; safe state such as `auth_enabled` remains available | Scan stdout, stderr, files, and serialized diagnostics |
| Retained artifacts | Access and lifetime match the declared audience; no routine artifact contains the credential | Check modes, collectors, rotation, bundles, and backup scope |
| Incident response | Historical copies contained and credential rotated or revoked | Record containment scope, rotation completion, and post-fix sentinel evidence |

### Minimum Regression Matrix

| Case | Expected result |
| ---- | --------------- |
| Successful authenticated startup | Operation succeeds; sentinel absent from every inspected surface |
| Authentication failure | Error remains actionable; sentinel and raw exception payload are absent |
| Child-process launch | Child receives only the required secret transport; argv and logs remain clean |
| Diagnostic/config dump | Only allowlisted fields are emitted; authentication is represented as state, not value |
| Retention check | Files are created with the intended access and rotation policy |

### Related Skills

- [Credential-safe runtime diagnostics](./nats-observability-redact-credential-bearing-diagnostics.md) covers URL and exception redaction at health and logging boundaries.
- [Communication redaction](./communication-redaction-avoid-internal-leaks.md) covers publishing sanitized durable documentation and evidence.
- [Cluster incident reproducer validation](./cluster-endpoint-incident-reproducer-validation.md) covers private artifact modes, cleanup, and reproducibility bundles.

## Verified On

| Context | Evidence | Status |
| ------- | -------- | ------ |
| Containerized service startup | A cmdline-safe injection still appeared in retained logs because the runtime serialized its effective configuration; direct inspection established the missing boundary | verified-local |
