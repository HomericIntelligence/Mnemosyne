---
name: public-client-resolve-without-environment
license: BSD-3-Clause
description: "Remove ambient environment selectors from a client or SDK selection path and resolve the target from disk. Use when: (1) an issue, ADR, or release note says a client must stop reading selector or identity environment variables, (2) a partial, complete, or stale set of exported identity values stops a client command, (3) an empty or unknown selector value fails on the client path, (4) service-side startup must keep its strict readiness check while the client stops reading the same variables, or (5) the client must still accept an explicit operator selection."
category: architecture
date: 2026-11-09
version: "1.0.0"
user-invocable: false
verification: verified-local
tags:
  - environment-selectors
  - client-sdk
  - public-path
  - fail-closed-boundary
  - empirical-invariant
  - configuration-lookup
  - startup-readiness
---

# Resolve a Public Client Without Environment Selectors

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-09 |
| **Objective** | Remove every environment selector and every rendered-identity input from the public client selection path. Resolve the target from disk. Keep the strict readiness check for service startup. |
| **Outcome** | Successful. 21 behavior cases and 4 auto-resolution cases passed after the change. The plan verification run passed 233 tests. Static checks passed. |

A public client selects one deployment, cluster, or endpoint. An environment selector is a
convenient input for that selection. It is also an ambient input: a shell export, a stale job
environment, or a partial render changes the result of the same command. When the release notes
say that a documented selector is removed, a greeting in the help text is not sufficient. The
client must not read the variable at all.

## When to Use

Use this skill when any of these conditions is true:

- A requirement says that a client, a CLI, or an SDK must stop reading selector or identity
  environment variables.
- A client command fails because a job export, a stale environment, or a partial render supplies
  identity values.
- An empty or unknown selector value fails on the client path but must not fail there.
- Service startup and the client read the same variables, and startup must keep the strict check.
- The client must keep one explicit operator selection, such as a flag or an SDK argument.

Do not use this skill to keep an environment override behind a flag. That change does not remove
ambient input. It moves the input.

## Verified Workflow

### Quick Reference

Make the invariant empirical. Set each removed selector to a hostile value, then assert the same
result.

```python
@pytest.mark.parametrize("hostile", REMOVED_SELECTOR_CASES)
def test_resolution_ignores_every_wrong_selector(monkeypatch, hostile):
    monkeypatch.setenv(hostile.variable, hostile.value)  # empty, wrong, stale, or partial
    runtime = resolve_public_runtime(code_path=installed_client_path)
    assert runtime.spec == expected_production_spec
```

Call the selection function with `code_path` as the only non-default input. Do not pass an
environment mapping. If the function still accepts `environ`, the removed input is still a
supported parameter.

### Suggested Approach

1. **Name the public path and its one owner function.** Find the single function that selects the
   target for the client. The CLI and the SDK must both use it. Fix that function. Do not patch a
   flag parser and leave the SDK path open.
2. **Delete the environment parameter from the owner function.** Remove the parameter and every
   caller argument. Pass a constant empty mapping to the configuration loader, for example
   `registry.resolve(explicit_path=..., environ={})`. The loader keeps its selector support for
   other callers. The public caller supplies no values, so the loader contract does not change.
3. **Add a disk-only auto-resolution step with a named failure.** Select the canonical candidates
   whose registered root directory exists on the host. When more than one candidate matches, keep
   the candidates whose root is an ancestor of the resolved running code path. An installed client
   always lives below its root. When exactly one candidate remains, use it. Otherwise, raise one
   error that lists the candidate identifiers and the explicit-selection remedy. Do not guess.
4. **Make the tie-break testable with a parameter.** Accept a `code_path` argument that defaults to
   the running code path. Tests then supply a path without a real installation. This parameter is a
   test seam, not a supported input. State that in the docstring.
5. **Keep the explicit selection strongest.** An explicit context file or an explicit SDK target
   must win over auto-resolution and over every environment value. Assert this in a test that runs
   with hostile values set.
6. **Separate the client boundary from the service boundary.** The client fails closed on disk
   state: a missing candidate is a named error. Service startup keeps its strict check on rendered
   identity variables. Improve that error only. Name the offending variables and give the
   interactive remedy, such as an explicit unset. Do not relax the service check to match the
   client.
7. **Split the caller error classes.** A selection failure is a value error, so the caller prints
   the selection remedy. A record or publication failure is an operating-system error, so the
   caller prints the operator remedy. Test both branches.
8. **Rewrite the tests as behavior, not as deletion checks.** For each removed input, record the
   hostile case: unknown value, empty value, a value for another target, a path to another context,
   an unknown cluster, a wrong root, an administrative root, a development root, a complete stale
   identity set, and a partial identity set. Each case must resolve the canonical target.
9. **Replace the fixtures that passed a fake environment.** Callers that passed a stub environment
   mapping now call with no environment. Remove the stub argument from the shared helper, not from
   each test. Use one shared publish helper instead of a copy per test file.
10. **Write the reference page for operators.** Document the selection order: explicit selection,
    disk auto-resolution, named error. Give the temporary remedy for clients of older releases.

For evidence, sizes, and the exact commands, see the
[notes](../skills/public-client-resolve-without-environment.notes.md).

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Rewrite the tests to assert that no environment variable appears in the source | Inspect the module source, or grep for the variable prefix, and assert that it is absent. | This tests a text property, not a behavior. A helper that reads the variable indirectly still passes. | Set the variable to a hostile value and assert the result. That test fails when the client honors the variable again. |
| Keep the environment parameter and default it to an empty mapping | Leave `environ=None` on the owner function so that old callers still work. | The removed input stays a supported parameter, and the default is invisible in review. | Delete the parameter. Pass the empty mapping at the loader call. |
| Use a whole-registry stub for the resolution tests | Load a real registry in tests to check auto-resolution. | A specification for a non-default lane fails production registry validation at load. A lane change also breaks properties derived from the lane. | Stub only the registry entry list and the resolve method. This makes the test independent of registry policy. |
| List only the post-tie-break candidate in the ambiguity error | Build the error message from the candidates after the ancestor filter. | The test that requires both identifiers in one message fails, and an operator cannot see the real choice. | Build the error from the step-1 candidates. |
| Treat the client change as a replacement for the service check | Relax the rendered-identity check to match the client. | The check protects service startup, not the client. Two different boundaries must keep two different rules. | Remove the input on the client path. Improve only the service error text. |
| Collapse the helper into one test file | Copy the publish helper into the second test file. | Two copies drift, and a later change fixes one copy only. | Move the helper to the shared test module and import it. |

## Results & Parameters

### Configuration

| Input | Client path | Service startup path |
| --- | --- | --- |
| Explicit selection flag or SDK target | Wins over all other input | Wins over all other input |
| Environment selector | Ignored. The loader receives an empty mapping. | Read |
| Rendered identity set | Ignored on the public path | Required complete, strict check |
| Disk auto-resolution | Canonical candidates with an existing root, then the ancestor tie-break | Not applicable |

```python
def resolve_public_runtime(*, explicit_path=None, code_path=None, contexts_dir=DEFAULT):
    registry = DeploymentContextRegistry.load(contexts_dir)
    default = explicit_path is None
    if default:
        explicit_path = auto_public_entry(registry, code_path).path
    spec = registry.resolve(explicit_path=explicit_path, environ={})
```

### Expected Output

- A clean environment resolves the canonical target from disk.
- Every hostile selector or identity set resolves the same canonical target.
- An explicit selection resolves the explicit target and skips the auto-selection checks.
- Ambiguity raises one error with the candidate identifiers and the explicit-selection remedy.
- A service startup job with an incomplete identity set fails with a message that names the
  variables and the unset remedy.

## Verified On

| Project | Context | Details |
| --- | --- | --- |
| An operator-service repository | One implementation lane, one worktree | 21 behavior cases and 4 auto-resolution cases. 233 tests passed in the plan verification run. Static checks passed. Evidence and commands are in the [notes](../skills/public-client-resolve-without-environment.notes.md). |

## References

- [Removal scope covers every start-path gate](planning-removal-scope-all-expressers.md)
- [Plan a required config key removal](planning-required-config-key-removal.md)
- [Env-var to typed CLI option migration](planning-env-var-to-typed-cli-option-migration.md)
- [Diagnose rendered-context identity divergence](rendered-context-identity-divergence.md)