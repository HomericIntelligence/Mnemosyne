---
name: architecture-config-pass-frozen-authority-directly
description: "Use when: (1) a coordinator projects a typed config into a second stage-only config object, (2) new CLI/config fields fail to reach stages without synchronized edits, (3) stage code uses `getattr` compatibility fallbacks for known fields, (4) tests mutate partial config stubs that do not match the frozen production type."
category: architecture
date: 2026-08-05
version: "1.0.0"
user-invocable: false
verification: unverified
tags:
  - typed-config
  - frozen-dataclass
  - stage-context
  - config-projection
  - cli-propagation
  - immutable-fixtures
  - single-source-of-truth
---

# Pass the Frozen Configuration Authority Directly

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-08-05 |
| **Objective** | Remove lossy stage-specific configuration projections so one frozen typed object flows from CLI construction through the coordinator into every stage context. |
| **Outcome** | Proposed refactor: add genuinely consumed fields to the authoritative config, derive inverse-facing properties there, pass the same object by identity, use direct typed access, and migrate tests to construction-time overrides. No implementation was executed in this session. |
| **Verification** | **unverified** — source occurrences and an acceptance strategy were supplied, but code, tests, type checking, and CI were not run. |

## When to Use

- A coordinator constructs `_StageConfig`, `_RunConfig`, or another projection from the real application configuration.
- Adding a config field requires editing the CLI mapping, authoritative config, projection constructor, protocol declarations, fixtures, and stage fallbacks.
- A documented CLI flag exists but is dropped before the stage that should consume it.
- Known stage settings use `getattr(config, "field", default)`, masking incomplete propagation from static type checking.
- Tests rely on `SimpleNamespace`, dynamic classes, or post-construction mutation even though production configuration is frozen.
- A context type must refer to the authoritative config but importing it at runtime would create a cycle.

## Proposed Workflow

> **Warning:** This workflow has not been validated end-to-end. Treat it as a hypothesis until the implementation passes local tests and CI.

The repository validator currently requires a literal `## Verified Workflow` section. The proposed, unverified steps therefore appear under that compatibility heading below.

## Verified Workflow

> **Warning:** This workflow has not been validated end-to-end. Treat it as a hypothesis until CI confirms it.

### Quick Reference

```python
@dataclass(frozen=True)
class PipelineConfig:
    org: str
    repos: list[str]
    no_advise: bool = False
    enable_learn: bool = True

    @property
    def enable_advise(self) -> bool:
        """Return the positive stage-facing form of ``no_advise``."""
        return not self.no_advise
```

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..coordinator_types import PipelineConfig


@dataclass(frozen=True)
class StageContext:
    config: PipelineConfig
    # remaining collaborators...


ctx = StageContext(config=self.config, ...)
assert ctx.config is self.config
```

```python
# Known fields use typed access; dynamic phase selection may remain dynamic.
if not ctx.config.run_pre_pr_tests:
    return Continue(next_state=COMMIT_PUSH_WAIT)

if not ctx.config.enable_learn:
    return StageOutcome(Disposition.FINISH_PASS, "merged")
```

```python
# Frozen production-realistic fixtures are configured before context creation.
config = replace(
    PipelineConfig(org="test-org", repos=["test-repo"]),
    enable_learn=False,
)
ctx = StageContext(config=config, ...)
```

### Detailed Steps

1. **Census the projection before deleting it.** Search the projection type, the producer that constructs it, every consumer, protocol/host annotations, and tests. Separately search each projection-only field to distinguish real production behavior from dead fixture surface.
2. **Complete the authoritative type.** Add fields that stages genuinely consume to the frozen application configuration. Prefer a derived property for polarity aliases such as `enable_advise = not no_advise` instead of storing two booleans that can disagree.
3. **Do not promote dead projection fields.** If a field exists only on the duplicate config and in test mutations, delete it instead of expanding the authoritative public surface.
4. **Pass the object by identity.** Construct every stage context with `config=self.config`; delete the projection instance, its host attribute, exports, and type-only declarations. Future config fields then reach stages without another constructor edit.
5. **Type the stage boundary without creating a runtime cycle.** Put the authoritative config import behind `TYPE_CHECKING` when coordinator types already import stage types. With postponed annotations, static checking sees the type while runtime import order stays unchanged.
6. **Replace compatibility fallbacks for known fields.** Use direct attribute access for declared settings so misspellings and missing propagation fail under mypy. Retain dynamic lookup only when the selected key is inherently dynamic, such as choosing among phase-specific model fields.
7. **Wire every existing CLI flag at the sole construction point.** A typed field is inert unless wrapper code maps parsed arguments into it. Add a regression test that captures the constructed config and asserts the flag's positive stage-facing value.
8. **Migrate tests to the real frozen type.** Centralize a fixture that accepts either a complete config or a mapping of construction-time overrides, rejects both at once, and uses `dataclasses.replace`. Remove partial namespaces, dynamic config classes, assignments after context construction, and `object.__setattr__` bypasses.
9. **Prove propagation with identity, not a field list.** Assert `ctx.config is config`, then spot-check derived and behavior-critical fields. Identity is the regression guard that covers every present and future field automatically.
10. **Verify production and test surfaces together.** Run stage/coordinator/wrapper tests and the complete type checker. Finish with searches showing the projection, host attribute, compatibility fallbacks, and mutable config stubs are gone.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Project the config into a stage-only dataclass | Copied selected application fields into `_StageRunConfig` before building contexts | Every added field requires synchronized type and constructor edits; omitted fields silently disappear downstream | Pass the authoritative frozen object directly |
| Keep positive and negative booleans as stored fields | Stored both `no_advise` and `enable_advise` | Two writable values can contradict each other and require precedence rules | Store one canonical field and derive the inverse with a property |
| Use `getattr` for declared settings | Read known fields with compatibility defaults | Missing propagation and misspellings become plausible runtime defaults instead of type errors | Use direct attribute access for statically known configuration |
| Preserve an unused projection-only flag | Considered promoting `enable_follow_up` to the main config because tests set it | No production stage consumed it, so promotion would turn dead duplicate surface into permanent API | Search production consumers and delete unused test mutations |
| Mutate frozen config after context construction | Used assignments or `object.__setattr__` in tests | Fixtures no longer represent production immutability and can conceal invalid initialization paths | Build the desired config first or use `dataclasses.replace` |
| Use partial namespaces as config doubles | Supplied only the one field a test happened to read | Static typing cannot validate the stage/config contract, and new direct accesses fail far from fixture construction | Reuse the real config with small construction-time overrides |
| Add a typed field without wrapper mapping | Declared `enable_learn` but omitted `enable_learn=not args.no_learn` | The documented CLI option still had no effect in the pipeline | Test parsed-argument-to-config construction explicitly |

## Results & Parameters

### Acceptance Invariants

```python
ctx = coordinator._ctx_for_repo("repo-a")

assert ctx.config is coordinator.config
assert ctx.config.enable_advise is (not coordinator.config.no_advise)
```

The refactor is complete only when:

- exactly one production configuration type defines stage-consumed fields;
- the context holds that type, and every cached context receives the same instance;
- known fields use direct typed access;
- wrapper tests prove existing CLI flags reach the config;
- tests configure frozen values before `StageContext` construction;
- projection names, projection host attributes, obsolete mutable assignments, and unused duplicate fields have no remaining production/test hits.

### Proposed Audit and Verification

```bash
rg -n "_StageRunConfig|_stage_config" hephaestus tests
rg -n "getattr\(ctx\.config|SimpleNamespace|object\.__setattr__" \
  hephaestus/automation/pipeline tests/unit/automation/pipeline

uv run pytest \
  tests/unit/automation/pipeline/test_coordinator.py \
  tests/unit/automation/test_coordinator_shutdown.py \
  tests/unit/automation/test_implementer_main.py \
  tests/unit/automation/pipeline/stages

uv run mypy hephaestus/ scripts/ tests/
```

Expected post-change search result: no `_StageRunConfig` or `_stage_config` references, no mutation-based config fixture setup, and no compatibility `getattr` for statically declared fields.

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| ProjectHephaestus | Issue #1950 design session | Proposed deleting `_StageRunConfig`, passing frozen `PipelineConfig` through `StageContext`, wiring `--no-learn`, and migrating mutable test doubles. No implementation or verification was performed. |
