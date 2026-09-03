---
name: security-privileged-local-control-plane-boundary
license: BSD-3-Clause
description: "Use this skill when an unprivileged client requests privileged local mutations. Replace caller-supplied identity and free-form execution with a closed operation protocol, kernel-derived peer identity, fixed service identity, scoped authorization, and immutable dispatch policy."
category: architecture
date: 2026-08-28
version: "1.0.0"
user-invocable: false
verification: verified-local
tags:
  - privileged-service
  - local-control-plane
  - unix-socket
  - peer-credentials
  - authorization
  - closed-schema
  - least-privilege
  - confused-deputy
---

# Privileged Local Control Plane Boundary

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-08-28 |
| **Objective** | Keep caller-controlled data from selecting identity, privilege, or an executable action at a local privilege boundary. |
| **Outcome** | Use a closed typed protocol, kernel peer credentials, fixed service identity, scoped roles, and one immutable operation registry. |
| **Verification** | Verified locally with focused schema, operation-registry, authorization, identity, scope, and lock-policy tests. |

## When to Use

- An unprivileged client requests mutations from a privileged local service.
- A Unix domain socket or similar local transport crosses a privilege boundary.
- A legacy helper accepts `command`, `argv`, `env`, script, path, image, or owner fields.
- The client can state its actor, effective user, service owner, or scheduler owner.
- Different resources use the same display name and require separate authorization or locks.
- Policy revocation must apply without a service restart.

Do not use this skill for a read-only dispatcher that does not cross a privilege boundary.
For that case, use the dispatcher-seam guidance in the References section.

## Verified Workflow

### Quick Reference

```text
client request
  -> strict operation schema
  -> kernel peer credentials
  -> current role policy and resource scope
  -> immutable operation specification
  -> resource-scoped lock
  -> typed owner seam
```

The request selects only a reviewed operation and its typed business parameters.
The service selects the caller identity, execution identity, authorization rule, lock policy, and implementation seam.

### 1. Define a closed request envelope

Use one versioned envelope with these minimum fields:

```yaml
protocol_version: 1
operation_id: <stable-uuid>
operation: <reviewed-operation-name>
cluster_id: <immutable-cluster-id>
deployment_id: <required-for-instance-operation>
instance_id: <required-for-instance-operation>
payload: <operation-specific-object>
```

Reject unknown fields in the envelope and every payload model.
Make validated models immutable when the language and schema library support this control.
Require cluster identifiers for all operations.
Require instance identifiers only for instance operations.

Do not accept these caller-controlled concepts:

- actor, owner, effective user, or effective group;
- command, executable, arguments, environment, or shell text;
- arbitrary path, URL, mount, image, SQL, or scheduler-owner fields;
- caller-selected role, audit action, target type, or lock key.

### 2. Derive identity from trusted local state

Read peer credentials from the operating system at the accepted socket.
Resolve the kernel user and group identifiers through the host identity service.
Do not use identity fields from the request body.

The service must also verify its own effective user and group at startup.
Bind the execution identity to the deployment contract or to one fixed service account.
An authorized caller can request an operation but cannot become the execution identity.

### 3. Store policy in one immutable operation registry

Define one specification for each supported operation.
The specification must include these values:

```yaml
name: instance.enable
payload_type: InstanceLifecyclePayload
scope: instance
required_role: instance-operator
owner_seam: instance-registry
audit_action: enable
audit_target: instance
lock_policy: [instance]
read_only: false
```

Generate dispatch, authorization, audit classification, and lock selection from this registry.
Do not keep separate mutable maps for these decisions.
Reject an operation name that is not in the registry.

### 4. Authorize the trusted actor for the exact scope

Load role grants from a service-owned file that is not writable by clients.
Validate ownership, type, link status, size, mode, schema, and supported policy version.
Fail closed when any check fails.

Reload the policy before authorization when revocation must apply immediately.
Check both the required role and the resource scope.
A cluster-wide role can cover all instances only when the policy states this rule.

### 5. Derive lock keys from immutable scope

Build lock keys from immutable identifiers and the operation specification.
Sort all keys before acquisition.
Use nonblocking exclusive locks when callers must receive a retryable conflict.

Include the parent instance in keys for instance-owned resources:

```text
instance:<instance-id>
pool:<instance-id>:<pool-name>
job:<instance-id>:<job-id>
domain:<instance-id>:<domain-name>
```

This rule prevents equal display names in different instances from sharing one lock.
It also prevents a client from selecting a lock outside its authorized scope.

### 6. Dispatch only to typed owner seams

Give each operation one typed handler interface.
The handler receives validated business parameters and trusted service context.
It must not receive raw request JSON, free-form shell text, or caller identity claims.

Keep protocol parsing, authorization, and dispatch separate from the domain implementation.
This separation permits unit tests without a live privileged service.
It also keeps the privilege boundary small enough for a complete review.

### 7. Test the boundary with adversarial inputs

Test accepted operations and the complete rejection families.
At minimum, include these tests:

- unknown operation and unknown field;
- wrong payload type or wrong scope identifiers;
- actor, owner, executable, argument, environment, and path injection;
- unauthorized role and unauthorized instance;
- policy revocation without restart;
- service identity mismatch at startup;
- equal resource names in different instances;
- deterministic lock order for multi-resource operations;
- direct handler lookup that cannot bypass registry admission.

Assert effects at the boundary.
For rejected input, assert that no privileged handler ran.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Trust a request actor field | The client supplied its user or owner identity. | The client could claim a more privileged identity. | Derive caller identity from kernel peer credentials. |
| Allow free-form execution with filters | The service accepted command text or arguments and blocked known unsafe values. | The remaining input still selected executable behavior and future filters could miss new forms. | Expose only reviewed typed operations. |
| Keep separate policy maps | Dispatch, roles, audit labels, and locks used independent dictionaries. | The maps could drift and give one operation inconsistent policy. | Generate all boundary decisions from one immutable specification. |
| Authorize only a role name | The service checked the role but did not check the resource scope. | A valid operator could mutate a sibling instance. | Check the role and immutable scope together. |
| Cache role grants until restart | The service loaded grants only during startup. | Revocation did not take effect while the service remained active. | Reload or safely refresh policy before authorization. |
| Lock by display name only | Equal resource names used the same global lock. | Independent instances blocked each other and lost isolation. | Include immutable parent identifiers in resource lock keys. |

## Results & Parameters

### Boundary Contract

```yaml
request_controls:
  - reviewed_operation_name
  - typed_business_parameters
service_controls:
  - trusted_actor_identity
  - fixed_execution_identity
  - required_role
  - resource_scope
  - owner_seam
  - audit_classification
  - lock_keys
forbidden_request_fields:
  - actor
  - owner
  - command
  - argv
  - env
  - path
  - url
  - image
  - mount
  - sql
```

### Required Invariants

```text
accepted request => operation is in the immutable registry
accepted request => payload matches the exact operation schema
authorized request => actor came from trusted local credentials
handler invocation => role and resource scope were authorized
handler invocation => execution identity came from service state
lock key => key came from immutable scope and registry policy
request data cannot select executable behavior or identity
```

### Verification Boundary

The local tests verified the schema, registry, authorization, identity, scope, and lock-key rules.
They did not verify a production socket server, crash recovery, or scheduler mutation.
Verify those behaviors separately before production use.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Project-neutral Python prototype | Focused local unit tests | The tests covered strict schemas, immutable operation policy, kernel-derived actors, service identity checks, scoped roles, revocation, and lock isolation. |

## References

- [Exact argv admission](tooling-command-admission-exact-argv-boundary-enforcement.md)
- [Dispatcher seam](architecture-mcp-server-dispatcher-seam.md)
- [Durable state before effects](architecture-pipeline-durable-state-ac3.md)
- [Scheduler service identity continuity](scheduler-service-replacement-identity-continuity.md)
