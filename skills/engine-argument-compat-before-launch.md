---
name: engine-argument-compat-before-launch
description: "Mirror a serving engine's cross-flag and flag-to-dtype compatibility rules at config validation and again at the launch-render pre-flight, so an incompatible combination fails before the engine's minutes-long startup instead of after it, and name each flag family that can go inert so an image change cannot silently return the launch to an engine default. Use when: (1) a recipe or manifest pins engine command-line flags that the engine validates only at startup, (2) replicas die after a long startup phase with the engine's own argument error, (3) the config model can be built or updated programmatically around its constructor validator, (4) an omitted flag silently inherits an engine default that constrains other fields, or (5) a pinned recipe must stay correct across an engine image, source, or runtime change."
category: tooling
date: 2026-11-09
version: "1.1.0"
user-invocable: false
tags:
  - serving
  - engine-arguments
  - cross-field-validation
  - pydantic
  - render-time
  - fail-before-launch
  - flag-spellings
---

# Mirror Engine Argument Compatibility Before Launch

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-09 |
| **Objective** | Refuse a recipe whose engine flag combination the engine rejects, at config validation and at render time, before a launch script exists. |
| **Outcome** | Operational. One compatibility rule serves both boundaries, covers both flag spellings and engine default fill, and names the conflicting fields. Launch trials that each cost several minutes are replaced by an immediate, correctable refusal. |
| **Verification** | verified-ci |

## When to Use

- A recipe, manifest, or cookbook pins engine command-line flags, and the
  engine checks the compatibility of those flags only at startup.
- Startup is expensive: the engine verifies a model checkpoint or compiles
  kernels for minutes before it reaches its argument checks.
- Replicas die after the long startup phase with the engine's own argument
  error, so every trial wastes the full startup time.
- The config model can be built programmatically (`model_copy`, update dicts)
  in a way that bypasses constructor-time validators, yet still reaches the
  launch-rendering path.
- The engine fills an omitted flag with a default, and that default carries
  its own constraint (for example, a default attention backend that needs a
  specific cache data type).
- A pinned recipe stays bound while the engine image, source revision, or
  runtime changes under it. A flag that a previous revision acted on can
  become inert in a later revision without an error, because the engine
  gates that flag family on a model-profile predicate that no longer matches.

## Verified Workflow

### Quick Reference

```python
def _flag_value(extra_args: list[str], flag: str) -> str | None:
    """One lookup covers both --flag value and --flag=value spellings."""
    for index, item in enumerate(extra_args):
        if item == flag:
            return extra_args[index + 1] if index + 1 < len(extra_args) else ""
        if item.startswith(f"{flag}="):
            return item.split("=", 1)[1]
    return None
```

Materialize engine defaults before the check. An omitted backend flag is not
absent to the engine: it inherits the engine default, and that default has
constraints of its own.

```python
effective_prefill = engine_default if prefill is None else prefill
```

Keep the compatibility facts in one frozen table and call one check function
from two boundaries:

- the config model validator (fail at authoring and load time), and
- the launch-render pre-flight (the last boundary before a script exists,
  which no programmatic model update can bypass).

The refusal message names the two fields in conflict and the observed values,
so the operator corrects the recipe in one edit.

### Suggested Approach

1. Collect every constraint from the engine first. The engine's error text
   and engine code are the authoritative source of its flag compatibility
   rules. One trial often exposes only the next constraint; write the table
   of allowed combinations from all of them, and do not infer the table one
   failure at a time. A public engine's server-arguments documentation and
   source are usable references; the rendered launch spec of a waiting job
   shows the flags a recipe actually rendered.
2. Model each constraint as one rule. In the verified incident: an FP8-only
   sparse prefill kernel requires an FP8 key-value cache; an attention
   backend family requires bfloat16 on CUDA; a decode backend family supports
   more than one index pool only on specific backends. Each becomes one
   conditional refusal keyed by the effective pair.
3. Check effective values, not written values. Fill an omitted flag with the
   engine default before the lookup, and evaluate that default against the
   other fields.
4. Put identical checks behind identical messages at two boundaries. A
   constructor validator alone does not cover models that arrive by an
   update-copy path, which then still reaches rendering. The render-time
   refusal must prevent script creation; a warning that lets rendering
   continue reproduces the expensive trial.
5. Scope the refusal. Skip the check when the recipe sets no relevant flags
   and selects no pinned cache data type: in that case the engine picks a
   matching default pair and the recipe stays valid.
6. Classify each pinned flag as rejected or inert when the engine disagrees.
   A flag family that the engine gates on a model-profile predicate is
   rejected only when the predicate matches, and inert when it does not. An
   inert family produces no error, no warning, and no drift record, so the
   engine silently serves with the flag's default. Check the predicate
   against the exact source revision that the image was built from, not the
   current default branch: a profile that exists in one revision can be
   absent from a later release branch.
7. Make the outcome explicit for each flag family that can go inert. Name the
   flag that selects the behavior, so the launch states the choice instead of
   inheriting a default that a future image can change. Where the family
   cannot be named, add a pre-flight refusal that names the image and the
   missing profile. A drift warning is not sufficient for a profile that a
   deployment serves.
8. Re-measure the pinned path after any image, source, or runtime change, and
   record the result next to the values. A recipe that served correctly is
   evidence for one image, not for the next.
9. Prove the check with behavior tests: refuse every combination the engine
   refused (including both flag spellings and the default-fill case), accept
   one measured-working combination, and accept the no-flags case. Add one
   render-level test showing no launch script is produced. Add one test that
   asserts every flag family that can go inert is named explicitly, so a
   deletion that re-exposes the inherited default fails the suite.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --- | --- | --- | --- |
| Attempt 1 | Changed one flag per launch trial, letting the engine's own startup error find each conflict. | Several flags were constrained jointly, so each trial exposed only the next conflict after a minutes-long checkpoint verification; three trials revealed three distinct refusals. | Enumerate the engine's full constraint set from its errors once, encode all of it, and let one launch carry the correct combination. |
| Attempt 2 | Enforced the compatibility check in the config model validator only. | A model produced by an update-copy path skipped construction validation yet still reached the launch renderer. | Repeat the same check at the launch-render pre-flight; the renderer is the only path every launch traverses. |
| Attempt 3 | Matched the flag as a bare token. | The `--flag=value` spelling bypassed the lookup while remaining valid input to the engine. | One lookup covers both spellings. |
| Attempt 4 | Recorded one measured-working flag pair and removed the flag that named the kernel, on the reasoning that the surviving flags select it. | The surviving flags were inert on a later image whose engine did not match the model profile, so the launch silently used the engine's generic default. A drift warning let rendering continue, and the profile served in production. | Name the flag that selects the behavior. A flag family can be valid and inert at the same time, and only the image's own source revision tells you which. |

## Results & Parameters

### Configuration

```yaml
engine_argument_compat:
  sources: [engine error text, engine source, rendered launch spec, public engine argument documentation]
  lookup: one function for "--flag value" and "--flag=value"
  semantics: evaluate effective flags after engine default fill
  boundaries: [config model validator, launch-render pre-flight]
  message: names the conflicting fields and observed values
  render_failed_check_result: no launch script created
  skip_condition: neither relevant flags nor a pinned dtype is set
  flag_family_state: [rejected-with-error, inert-without-error]
  inert_detection: check the engine's model-profile predicate at the image source revision
  inert_mitigation: name the flag that selects the behavior
  revalidation: re-measure the pinned path after every image, source, or runtime change
```

### Expected Output

- The invalid recipe fails at load or render time with a message that names
  the conflicting fields; no scheduler or launch script is created.
- A recipe with no relevant flags stays valid (engine default pair applies).
- One launch with a measured, valid combination passes the engine's own
  checks, and the replica reaches registration.

## Verified On

| Project | Context | Details |
| --- | --- | --- |
| Private model-serving platform | Merged fix cross-referenced by two recipe issues; all required checks green | Refusal coverage for three engine-refused flag and dtype combinations, both flag spellings, engine default fill, plus one accepted measured combination; render-level test proves no script is created. Private repository name, model identifiers, issue numbers, infrastructure paths, and job identifiers are intentionally omitted. |

## References

- The public engine's server-arguments documentation and source code hold the
  authoritative compatibility facts for its flags.
- [CLI flag validation to prevent silent no-ops](cli-flag-validation-prevent-silent-noop.md):
  the silent-ignore failure class at CLI parse time.
- [Serving-pool replica outage diagnosis](serving-pool-replica-outage-diagnosis.md):
  classifying a replica that dies before gateway registration.
- [Config validation and schema alignment](config-validation-and-schema-alignment.md):
  schema-definition and wiring patterns for config validators.
