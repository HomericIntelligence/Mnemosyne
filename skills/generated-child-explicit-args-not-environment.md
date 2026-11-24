---
name: generated-child-explicit-args-not-environment
description: "Replace an environment-variable handoff from a generated script to a fixed child command with explicit positional arguments. Use when: (1) a rendered job or launcher exports per-run identity for its payload, (2) a policy forbids environment variables for run configuration, (3) an environment-surface scan rejects a new exported name, or (4) an older rendered artifact must keep its baked behavior."
category: architecture
date: 2026-11-24
version: "1.0.0"
user-invocable: false
tags: [environment-variables, explicit-arguments, generated-script, child-process, run-configuration, allowlist, shell-quoting]
---

# Generated Child Commands Take Explicit Arguments, Not Environment

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-24 |
| **Objective** | Remove a per-run environment handoff from a generated child job and give the fixed payload command explicit inputs. |
| **Outcome** | Successful. The generated script passes the values as positional arguments. The retired environment names and their allowlist rows are gone. Behavior tests and CI passed. |

A generated script often starts one fixed command. That command can need values that exist only at launch, such as a recipe identifier or a node count. An `export` is a short solution. It is also ambient run configuration: every descendant inherits it, a stale export changes behavior, and a surface scan must record the new name. Pass the values as arguments to the command instead.

## When to Use

- A rendered batch script, launcher, or child-job template exports identity or shape values for its payload command.
- A repository policy forbids environment variables for run configuration.
- An environment-surface check rejects a new variable name, or reports a stale allowlist row after a removal.
- The payload command is fixed at render time and accepts a stable positional interface.
- Older rendered artifacts are already running and must keep their baked behavior until they finish.

Do not use this skill to hide an environment override behind a new flag. That change moves the input; it does not remove it. Do not put a secret in positional arguments. Secrets need a protected file or descriptor.

## Verified Workflow

### Quick Reference

Replace the export with quoted positional arguments:

```bash
# Before: ambient state for the whole child tree.
export JOB_RECIPE_ID="$recipe_id"
export JOB_NODE_COUNT="$node_count"
exec "$payload_command"

# After: explicit inputs to one command.
exec "$payload_command" "$recipe_id" "$node_count"
```

Define and document the argument order. Update the command contract in the same change.

### Suggested Approach

1. **Find the complete handoff.** Search the generated script and its renderer for `export`, `env`, and the payload command line. Do not stop at the source module. Include documentation, help text, and tests that repeat the variable names.
2. **Define one positional contract.** Put stable values in a fixed order, for example `payload <recipe-id> <node-count>`. Quote every value with the shell's quoting helper or a portable quoting routine. A value that is safe today can contain whitespace or shell syntax later.
3. **Remove the exports.** Pass the values directly on the `exec` line. Do not add a fallback that reads the old environment value. A fallback keeps the ambient input and defeats the removal.
4. **Update the user-visible contract.** Change the help text and the task guide. State what the command receives and in what order. If the payload command is optional, state that the default command serves no traffic until the caller supplies one.
5. **Remove the retired surface rows.** A literal scan fails in both directions. When the last occurrence of a name is gone, delete every allowlist row for that name and path pair. Then run the repository's environment-surface check.
6. **Keep older artifacts compatible.** A rendered artifact already in flight keeps its own text. Make the new renderer use arguments. Do not rewrite or signal a running artifact to force the new interface. State this boundary in the change description.
7. **Prove the new handoff with behavior.** Assert that the generated script passes the expected arguments in order. Do not add a test that only checks for the absence of the old literal. That test string becomes a new surface occurrence and can fail the same scan.
8. **Run the focused tests, the type check, and the surface check.** Report the exact commands and results.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Keep the exports and add allowlist rows | Treated the new names as an accepted surface | The policy forbids environment-based run configuration, and the allowlist is not an approval mechanism | Remove the handoff. Do not grow the surface to make a forbidden pattern pass |
| Add a test that asserts the old name is absent | Searched the generated script text for the retired literal | The test literal is itself a new occurrence, so the surface scan fails again | Assert the positive argument handoff. Do not test a text absence with the forbidden text |
| Keep an environment fallback for old callers | Read the variable when the argument is absent | The ambient value still changes behavior and remains a supported input | Remove the fallback. Give old rendered artifacts their baked behavior and make new artifacts use arguments |
| Pass unquoted values | Interpolated the values directly into the command line | A space or shell metacharacter splits the argument or changes the command | Quote every positional value with the platform's shell-quoting routine |
| Change the source but not the documentation | Updated the renderer only | The help text and task guide still promised the environment variables, so users kept the removed workflow | Update the command contract, help text, and guide in the same change |

## Results & Parameters

### Configuration

```python
# Render-time command contract.
# argv[1] = recipe identifier
# argv[2] = node count
script = (
    "set -uo pipefail\n"
    "umask 077\n"
    f"exec {payload_command} {quote(recipe_id)} {quote(str(node_count))}\n"
)
```

```json
{
  "surface_check": "remove every allowlist row for a retired name and path pair",
  "behavior_test": "assert the payload receives the identifiers in the documented order",
  "compatibility": "older rendered artifacts keep their baked script"
}
```

### Expected Output

- The generated script contains no `export` of run identity.
- The payload receives one argument per documented value.
- The environment-surface check passes with no rows for the retired names.
- The focused tests pass.
- Older running artifacts keep their previous behavior.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| A scheduler-managed model-serving repository | A rendered child-job artifact with a fixed payload command | The environment handoff was removed. Behavior tests, type check, surface check, and CI passed. |

## References

- [Plan an env-var to typed CLI-option migration](planning-env-var-to-typed-cli-option-migration.md): operator-facing knobs become typed options.
- [A scheduler job inherits the submitter's environment](scheduler-job-inherits-submitter-environment.md): diagnose unintended environment inheritance.
- [One environment lookup rule in shell and Python](one-env-lookup-rule-in-shell-and-python.md): keep one owner for an environment-derived path.
