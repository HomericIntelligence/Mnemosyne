---
name: hephaestus-agent-timeout-refactor-planning-risks
description: "Remove deprecated timeout environment aliases without changing canonical overrides, defaults, call-time reads, or malformed-value fallback. Use when: (1) deleting alias fallback support from a shared env reader, (2) narrowing a public helper signature, (3) replacing compatibility tests with ignored-alias regressions, (4) preserving a library-to-product dependency boundary during configuration cleanup."
category: architecture
date: 2026-08-06
version: "2.0.0"
user-invocable: false
verification: verified-local
history: hephaestus-agent-timeout-refactor-planning-risks.history
tags:
  - timeout
  - environment-variable
  - deprecated-alias
  - canonical-configuration
  - public-api
  - call-time-read
  - malformed-value
  - regression-testing
  - hephaestus
---

# Canonical Timeout Environment Variable Contracts

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-08-06 |
| **Objective** | Remove deprecated phase-specific timeout aliases and the shared reader's alias parameter while preserving every canonical override, default, per-call read, and malformed-value fallback. |
| **Outcome** | Successful in a disposable ProjectHephaestus checkout: the helper accepts one environment-variable name, six former alias mappings are ignored, canonical behavior remains unchanged, and documentation names the exact supported variables. |
| **Verification** | `verified-local` — 81 focused unit tests passed; Ruff and mypy passed on all modified Python surfaces. CI validation is pending. |
| **History** | [changelog](./hephaestus-agent-timeout-refactor-planning-risks.history) |

## When to Use

- Removing deprecated environment-variable aliases after the canonical names have become the only supported operator contract.
- Narrowing a shared configuration reader from one primary name plus fallback names to exactly one canonical name.
- Replacing tests that preserve compatibility behavior with regressions proving deprecated inputs are ignored.
- Preserving canonical defaults, call-time lookup, integer conversion, warning text, and malformed-value fallback during API cleanup.
- Multiple accessors share one canonical budget but previously accepted different aliases, or one alias previously affected multiple accessors.
- A product-layer configuration module imports a library-layer helper and the cleanup must preserve that dependency direction.

## Verified Workflow

Verified locally only — CI validation pending.

### Quick Reference

```bash
# Re-inventory the compatibility surface from the current checkout.
rg -n "legacy_names|DEPRECATED_ENV_NAME" <source-paths> <test-paths> <docs-paths>

# Run behavior-first focused regressions without the repository-wide coverage gate.
uv run pytest --no-cov \
  <timeout-test>::test_canonical_timeout_envs_are_read_per_call \
  <timeout-test>::test_deprecated_timeout_aliases_are_ignored \
  <constants-test>::test_read_timeout_env_has_no_legacy_names_parameter -v

# Run the complete modified test files and static validation.
uv run pytest --no-cov <constants-test> <timeout-test> -v
uv run ruff check <modified-python-files>
uv run mypy <modified-python-files>
```

```python
def read_timeout_env(env_name: str, default: int) -> int:
    """Read one canonical timeout env var at call time."""
    raw = os.environ.get(env_name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        logger.warning(
            "Ignoring non-integer %s=%r; using default %ds",
            env_name,
            raw,
            default,
        )
        return default
```

### Detailed Steps

1. **Inventory the exact alias surface.** Search production, tests, and documentation for the helper parameter and every deprecated variable. Count mappings, not just distinct aliases: one deprecated name can feed multiple accessors and needs a regression row for each behavior.

2. **Write the public-signature regression first.** Use `inspect.signature()` to assert that the helper exposes only `env_name` and `default`. This makes removal of the public compatibility seam executable rather than relying on a source grep.

3. **Replace compatibility tests with ignored-input tests.** Parameterize `(canonical_env, deprecated_env, accessor, default)`. Delete the canonical variable, set only the deprecated variable, and assert the accessor returns its unchanged default. Include every former mapping; in ProjectHephaestus the planner alias formerly controlled both the planner-agent budget and the outer planning wrapper, so it requires two rows.

4. **Simplify the shared reader.** Read only `os.environ.get(env_name)`. Retain call-time lookup, `int()` conversion, the same warning shape, and fallback to the passed integer default. Do not add caching or move the read to module import time.

5. **Remove fallback arguments from all callers.** Keep each canonical variable and numeric default byte-for-byte unchanged. The change is alias removal, not timeout consolidation or default tuning.

6. **Correct the operator documentation.** List the exact canonical variables. Avoid generic claims such as `HEPH_<PHASE>_AGENT_TIMEOUT` when the actual supported names use different word order or include a wrapper-specific name. State explicitly that deprecated aliases are not consulted.

7. **Verify all preserved behavior.** Test defaults with variables absent, canonical overrides, two successive values in one process, malformed canonical values plus warning records, ignored deprecated aliases, and the narrowed signature. Then run lint and type checking on every modified Python file.

8. **Preserve dependency direction.** Keep the product layer importing the lower-level helper. Removing fallback behavior does not justify a new configuration module, dependency, cache, migration state owner, or security boundary.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Preserve aliases through a generic fallback parameter | The original helper iterated over the canonical name followed by `legacy_names`, and six caller mappings retained deprecated phase-specific inputs. | The deprecated contract remained public and any caller could perpetuate or reintroduce aliases. | Remove the helper parameter itself, not only known caller arguments; guard the signature with `inspect.signature()`. |
| Delete compatibility tests without replacement | Old fallback and precedence tests could simply be removed when aliases are retired. | That would not prove deprecated variables are ignored, especially when one alias formerly affected two accessors. | Replace support tests with a complete parameterized ignored-alias matrix. |
| Verify removal with grep alone | `rg "legacy_names"` locates current source references. | A grep does not define the public callable contract and can be fooled by wrappers, generated code, or renamed parameters. | Combine inventory grep with a runtime public-signature assertion and behavior tests. |
| Run a tiny pytest node selection with default coverage options | Focused RED tests were invoked under ProjectHephaestus's global `--cov=hephaestus --cov-fail-under=83` configuration. | The behavioral failures were correct, but the partial selection also reported only 4.84% repository coverage, obscuring the focused result. | Add `--no-cov` to partial acceptance commands; rely on the repository's full suite/CI for the global coverage gate. |
| Document a generic phase-specific naming formula | Documentation said every phase used `HEPH_<PHASE>_AGENT_TIMEOUT`. | Canonical names use `HEPH_AGENT_<ROLE>_TIMEOUT`, while the outer wrapper uses `HEPH_PLAN_STAGE_TIMEOUT`; the generic formula described deprecated ordering. | Enumerate exact canonical variables and explicitly say aliases are ignored. |

## Results & Parameters

ProjectHephaestus's locally verified mapping was:

| Accessor | Canonical variable | Default | Deprecated input now ignored |
|---------|--------------------|---------|------------------------------|
| Planner agent | `HEPH_AGENT_PLAN_TIMEOUT` | 1200 s | `HEPH_PLANNER_AGENT_TIMEOUT` |
| Outer planning wrapper | `HEPH_PLAN_STAGE_TIMEOUT` | 7200 s | `HEPH_PLANNER_AGENT_TIMEOUT` |
| Plan reviewer | `HEPH_AGENT_REVIEW_TIMEOUT` | 1200 s | `HEPH_PLAN_REVIEWER_AGENT_TIMEOUT` |
| Implementer | `HEPH_AGENT_IMPL_TIMEOUT` | 1800 s | `HEPH_IMPLEMENTER_AGENT_TIMEOUT` |
| PR reviewer | `HEPH_AGENT_REVIEW_TIMEOUT` | 1200 s | `HEPH_PR_REVIEWER_AGENT_TIMEOUT` |
| Learn agent | `HEPH_AGENT_LEARN_TIMEOUT` | 1200 s | `HEPH_LEARN_AGENT_TIMEOUT` |

Preserved invariants:

- Canonical values are read on every function call, so environment changes take effect without module reload.
- An absent canonical variable returns the accessor's existing default.
- A malformed canonical value logs the same warning and returns the default instead of failing startup.
- Deprecated aliases are not read, do not affect values, and do not participate in precedence.
- The automation product layer continues importing the library-layer reader; no reverse dependency is introduced.

Observed local results:

```text
Focused canonical/alias/signature regressions: 13 passed
Complete modified unit-test files: 81 passed
Ruff modified-surface check: All checks passed
mypy modified-surface check: Success, no issues in 4 source files
CI: pending
```

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| ProjectHephaestus | Canonical timeout alias-removal experiment from `main` at `23050a27` | Disposable checkout; unit tests, Ruff, and mypy passed locally on 2026-08-06. |

Related skills:

- `planning-env-var-to-typed-cli-option-migration` for replacing environment controls with typed CLI options.
- `deprecated-api-removal-plan-review` for wider public-surface removal audits.
- `planning-reuse-existing-public-env-reader` for preferring an established low-level configuration helper over a new duplicate.
