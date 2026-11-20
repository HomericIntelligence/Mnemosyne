---
name: release-context-change-prior-client-before-cutover
license: BSD-3-Clause
description: "Run the release steps that talk to a live control-plane service with the prior installation's client and context, when the release changes the deployment context that the service registered. Use when: (1) a new client refuses the prior context file as 'not a registered deployment context', (2) the live service refuses the new context as a registered-context mismatch, (3) a step before the service restart fails with one of these two messages, or (4) you think about reordering numbered release steps or adding a script gate to avoid the failure."
category: ci-cd
date: 2026-11-20
version: "1.0.0"
user-invocable: false
verification: verified-local
tags: [release, deployment-context, version-skew, control-plane, rollback-save, observe, hot-swap, typed-verbs]
---

# Release That Changes the Registered Context: Use the Prior Client Before the Cutover

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-20 |
| **Objective** | Run the read-only and save steps of a release before the service restart, when the new release changes the context file that the live service registered. |
| **Outcome** | Operational. Two steps failed in turn with a context error. Both ran when they used the prior installation's client with the prior context. The numbered order and the release scripts stayed unchanged. The later steps (service restart, authoring, publish, migrate, hot swap) ran with the new tree and passed. |

A client accepts only context files from its own installation. Its registry is data of that installation. A live service accepts only the context contents that it registered at its start. When a release changes the context contents, the new client and the old service cannot agree. The old service still runs until the step that restarts it on the new tree.

## When to Use

- A release step that runs before the service restart fails with `<path> is not a registered deployment context`. The path is the prior release's context file.
- The same step, run with the new context file, fails with `The registered service context does not match`.
- The context file of the new release differs from the prior release (a policy block was removed or added), and the live service is on the prior release.
- You consider moving the restart step first, or adding a script check that refuses the step. Do neither until you test the prior client.

## Verified Workflow

### Quick Reference

```text
Before the step that restarts the service on the new tree:
  client  = the PRIOR installation's client (live release tree, not the staged tree)
  context = the PRIOR installation's context file
  verb    = a verb that the prior client already has (compare flags with the new client)
The step that restarts the service on the new tree is the first step that uses the NEW client and context.
```

```bash
# Compare the flags of one verb in both installations. Equal flags: call the prior client directly.
diff <(prior-client release observe --help | grep -o -E -- '--[a-z-]+' | sort -u) \
     <(new-client   release observe --help | grep -o -E -- '--[a-z-]+' | sort -u) && echo same
```

### Suggested Approach

1. Read the error. "Not a registered deployment context" comes from the client: the file is not in its registry. "Registered service context does not match" comes from the service: the context digest differs from its registration. Both point to the same cause, a changed context.
2. Diff the context files of the two releases to confirm that the contents changed.
3. For each step before the service restart, check if the prior client has the verb. Compare the flags of both installations. Use the prior client and the prior context for a verb that has the same flags (an observe verb) and for a save verb that has fewer flags.
4. A prior-client save verb can write fewer records than the new one. Copy the records that later steps read to the place where those steps look, as a plain copy.
5. Keep the numbered order and let the typed verbs refuse real damage. Do not add a script gate for this case. The first step with the new client is the restart step. Its typed verb is designed for the changed context.
6. After the restart step, use the new client and the new context for all steps.
7. A pre-flight that runs the observe verb must use the prior client until the restart step is done. Treat a pre-flight failure as a warning.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| New client, new context | Ran the save step with the staged client and the new context file. | The live service refused it with a registered-context mismatch. | The service keeps the context of its own start. Use the context of the running release. |
| New client, prior context path | Gave the staged client the prior release's context file. | The client refused a path that is not in its own registry. | A client reads only its own installation's registry. Use the prior client for the prior context. |
| Reorder the steps (proposed, not run) | Proposed moving the restart step before the observe and save steps. | The owner rejected it: it puts the riskiest step before the rollback records exist and breaks the numbered order. | The prior client can do these steps in the numbered order. |
| Script gate | Release scripts carried their own checks that refused a step (tree or file checks) before the typed verb ran. | The owner removed them: they duplicated checks that the typed verbs already make and stopped runs on a live lane. | Let the typed verb carry the restriction. |

## Results & Parameters

```yaml
pre_restart_steps:
  client: prior installation (live release tree)
  context: prior installation context file
  condition: the verb exists in the prior client with the same flags, or fewer flags with an explicit copy step
restart_step:
  client: new installation (staged tree)
  context: new installation context file
after_restart:
  client: new installation
  context: new installation
step_order: unchanged
script_gates_added: none
```

### Expected Output

- The observe and save steps pass before the restart.
- The restart step moves the service onto the new tree with the changed context.
- The hot swap that follows runs in the same allocation.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| A scheduler-managed model-serving deployment | Release that removed a policy block from the production context, 2026-11 | The staged client refused the prior context path. The live service refused the new context. The prior release's observe and save verbs ran with the prior context and passed. The service restart, the database writes, the publish, the migrations and the hot swap then passed with the new tree. |

## References

- [immutable-release-publish-target-live-candidate](immutable-release-publish-target-live-candidate.md): guard the one step that creates an immutable object.
- [control-plane-allocation-move-inventory](control-plane-allocation-move-inventory.md): inventory what lives in an allocation before a control-plane move.
- [cutover-stop-previous-release-daemon](cutover-stop-previous-release-daemon.md): stop the previous release's daemon through a supported stop at a cutover.
