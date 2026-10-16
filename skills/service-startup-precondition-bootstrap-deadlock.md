---
name: service-startup-precondition-bootstrap-deadlock
description: "Find and break a bootstrap deadlock in which a service requires a startup artifact that only that same service can create. Use when a new deployment cannot reach first start, or when a startup precondition and its only producer form a dependency cycle."
category: architecture
date: 2026-10-15
version: "1.0.0"
user-invocable: false
tags: [bootstrap, startup, dependency-cycle, credential, first-start, service-lifecycle]
---

# Service Startup Precondition Bootstrap Deadlock

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-15 |
| **Objective** | Detect a dependency cycle in which a service cannot start until an artifact exists, and the only code that creates that artifact runs inside the service |
| **Outcome** | Successful. The cycle was found by tracing the single writer and the single caller, and the precondition was removed from the first-start path only |

## When to Use

Apply this skill when:

- A service refuses to start and reports that a credential, key, or registration artifact is missing.
- The only tool that can create that artifact is the service that will not start.
- A new deployment cannot reach first start while the required artifact does not exist.
- You plan to add an installer that runs before the service starts. Treat that plan as a signal, not as a solution.
- Observed runtime behavior contradicts the registered configuration.

## Verified Workflow

### Quick Reference

Trace the cycle before you change anything:

```bash
# 1. Find every writer of the missing artifact.
git grep -n '<artifact-writer>' -- src/

# 2. Find the callers of that writer.
git grep -n '<artifact-writer>' -- src/ tests/

# 3. Decide whether the caller runs inside the guarded transport.
git grep -n '"<operation-name>":' -- src/

# 4. Decide whether the service consumes the artifact or only proves it.
git grep -n -A4 '<artifact-loader>' -- src/
```

### Suggested Approach

Complete these steps in order. The order matters, because step 4 selects between two opposite repairs.

1. Reproduce the refusal and record the exact missing-artifact message.
2. Find the single writer of the artifact, and then its single caller.
3. Confirm that the caller is the server-side handler for an operation that is submitted over the transport which the artifact guards. That confirmation closes the cycle.
4. Read the startup call site, and decide whether the loader result is used or discarded.
5. Apply the repair that the answer in step 4 selects.
6. Verify that the transport still authenticates every request.
7. Test both the first-start branch and the ordinary branch.

A discarded return value means that the artifact is a possession proof and not a dependency. A used return value means that the service authenticates outward with it.

| Observation at the startup call site | Meaning | Repair |
| --- | --- | --- |
| The loader result is discarded | The service proves ownership and does not use the artifact | Remove the precondition from the first-start path, and keep it on every other path |
| The loader result is stored and used for outbound calls | The service needs the artifact in order to run | Add a first-start provisioning path that creates the artifact only when it is genuinely absent |
| The only caller is the server-side handler for a socket operation | The producer runs inside the guarded transport | Repair the causal direction. Do not add a second writer |
| The same check runs on two independent paths | Defence in depth, and a doubled cycle surface | Scope both paths together, or remove both |

One diagnostic signal deserves separate attention. When a command path selects a lighter context resolution function than its sibling paths, that code signals an intended earlier lifecycle state. An unconditional heavy precondition on the next line defeats that signal. Check for this case before you design any workaround.

Do not loosen the loader. A loader that returns an empty artifact instead of refusing converts a loud startup refusal into a deployment that starts and cannot authenticate. Keep the refusal for every consumer that did not need the artifact at first start.

### Continue When A Step Is Unavailable

If you cannot confirm the cycle from source, reproduce the refusal and record the artifact path from the message. A refused start that names an artifact and shows no second producer is sufficient evidence to escalate. Do not infer the cycle from the message alone.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Designed an out-of-band installer that creates the artifact before first start | The installer added a second writer and preserved the cycle | The premise was wrong, because the service never used the artifact | Decide consumption before you design a workaround. An unnecessary precondition invites a permanent bypass |
| Treated the registered configuration as the effective configuration | The conclusion inverted, because the running service contradicted the registered file | The live service used a configuration that the repository did not record | When observed runtime behavior contradicts the registered configuration, the effective configuration is not the registered one. Resolve it before you draw any conclusion from either source |

## Results & Parameters

### Configuration

No configuration keys apply. The decision is structural:

```yaml
first_start:
  require_artifact: false   # the transport that creates the artifact must be able to run
ordinary_start:
  require_artifact: true    # every other consumer keeps the fail-closed load
```

### Expected Output

- The service starts without the artifact on a fresh deployment.
- The artifact appears only through the sanctioned path, with its own scope binding and its own revocation route.
- Every other consumer still refuses a malformed, foreign, or policy-violating artifact.
- The transport rejects an unauthenticated request exactly as it did before.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| A managed service with a typed administration transport | First-start credential bootstrap for a non-production deployment | The precondition ran on two paths, and the credential loader did not use its result |

## References

- [ASD-STE100 technical English](../docs/asd-ste100.md)
- [Fail-closed tool policy separation](cli-validator-fail-closed-tool-policy-separation.md)
- [Explicit path fail-closed behaviour](config-explicit-path-fail-closed.md)