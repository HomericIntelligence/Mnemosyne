---
name: opencode-variants-explicit-not-capabilities
license: BSD-3-Clause
description: "Emit reasoning-effort variants as an explicit list for models on an OpenCode OpenAI-compatible provider, not by declaring capabilities.reasoning. Use when: (1) a provider registration declares effort levels but the model picker shows no variants, (2) you must choose per model family between the top-level reasoning_effort request field and chat_template_kwargs, (3) you add a reasoning-off (none) variant and need to know which families cannot express it, or (4) a plan or review cites a capability declaration as the variant source without a live listing receipt."
category: tooling
date: 2026-11-08
version: "1.0.0"
user-invocable: false
verification: verified-live
tags:
  - opencode
  - provider-plugin
  - model-variants
  - reasoning-effort
  - capabilities
  - request-channel
  - live-probe
  - host-evidence
---

# OpenCode variants: explicit list, not declared capabilities

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-08 |
| **Objective** | Make per-model reasoning-effort levels (`provider/model#level`) selectable for each family of models registered by one OpenCode provider, with no silently-emitted no-ops. |
| **Outcome** | Successful. A declared `capabilities.reasoning` block produced zero variants in the picker; moving every level into an explicit `variants` array made every family surface appear. A live listing receipt proved the difference, and two level-selected runs completed where an unknown variant previously failed at resolution. |

## When to Use

- You register chat-model entries for OpenCode from a provider plugin and want per-model reasoning-effort levels (`#low`, `#high`, `#max`, `none`, ...).
- A registration carries `capabilities.reasoning` (effort enum, toggle) and the picker lists no variants anyway.
- Your serving stack spans several model families whose engines read the effort level in different places, and one mistaken family emits a silent no-op.
- A card or template allows only some levels, or the default-plus-exception shape means an off value has no meaning on that family.

## Verified Workflow

### Quick Reference

Put each offered level in the model entry's `variants` array; never rely on a capability declaration alone:

```jsonc
// Protocol-field families: the package maps settings onto the top-level
// reasoning_effort body field.
{ "id": "<level>", "settings": { "reasoningEffort": "<level>" } }

// Template families: the chat template reads the level from
// chat_template_kwargs.
{ "id": "<level>", "body": { "chat_template_kwargs": { "reasoning_effort": "<level>" } } }

// An off switch only when the family enum/card actually accepts it.
{ "id": "none", "settings": { "reasoningEffort": "none" } }
```

Prove it with the host, not with the registration you wrote:

```bash
# List the catalog after registration; every level must appear as a variant.
<host-list-command> | jq '.<providers>[].<models>[].variants'
# Two selection-probe runs: an unknown variant must fail at resolution,
# and each offered variant must resolve and answer.
<host> run --model <provider>/<model>#<level-a> "<one-word prompt>"
<host> run --model <provider>/<model>#<level-b> "<one-word prompt>"
```

### Suggested Approach

1. Pick per family first, from the model card and chat template — not from the
   gateway's validation error. The serving layer accepts a superset enum and
   routes unsupported values to template defaults; an accepted value is not an
   honored value. On the public serving engine's chat path, the top-level
   field is also merged into the template kwargs, so a template that defaults
   any other value will behave like the default instead of raising.
2. Emit explicit variants for every offered level. A `capabilities.reasoning`
   declaration produced no variants at all for the OpenAI-compatible package.
   The explicit variants are applied on the surface; a capability is at best
   documentation, and the toggle field is dropped.
3. Choose the channel per family. Models whose engines read the OpenAI
   protocol field get `{id, settings:{reasoningEffort}}`. Models whose chat
   templates read a Jinja variable get `{id, body:{chat_template_kwargs}}`.
   Emitting both channels for one level can send both forms; where live
   verification is impossible, prefer the card's documented channel.
4. Ship an off switch only where it exists. A template with
   `default('high')` and a hard error on every other string cannot express
   none; the family gets no off variant. A family that accepts the value
   (probe it live) gets an explicit `none` variant.
5. Expect one model to break the family claim. Six templates were said to be
   byte-identical and raising; one of the six instead coerces an unsupported
   level to its fast-think mode. Check the checksum of every model, and write
   comments that match the verified checksums, not the assumption.
6. Verify through the host. The registration succeeds trivially but shows
   nothing: run the list command on a live registration (`/models` or the
   equivalent API), confirm the offered ids appear as variants, then run two
   levels through it. If the family has no live replica, mark those levels
   unverified in code and in the plan instead of presenting them as measured.
7. Expect that the default model selector keeps no variant. A root `model`
   reference does not retain a `#level`; variants are chosen per run, session,
   agent, or command.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Declared capabilities | Set `capabilities.reasoning` with an effort enum and a toggle flag on every family | The picker listed no variants. The package built nothing from the declaration; only the explicit entries emitted later appeared. Also, an unknown variant failed at resolution, so absence was provable, not just invisible | The variants array is the surface. A capability declaration is documentation for this provider package, and the toggle is silently dropped |
| Channel from the enum | Took the gateway's accepted effort values as the per-family supported set and planned to send one channel uniformly | A template family silently coerces any value outside its card set to its max default; another rejects out-of-card values entirely. The gateway accepts a superset enum for all models | Read the level set and channel from each family's card and template, not from transport validation |
| Uniform off switch | Planned one `none` variant for every family | Template families with `default('high')` plus a hard exception path cannot express off; one sibling maps an unknown value to a fast-think mode instead | The off switch is per-family. Emitting an unexpressible `none` is a broken menu item |
| One-template claim | Documented "six identical templates, all raise" from five checksums and one example | The sixth template checksum differed; it coerced instead of raising | Every family member needs its own checksum before a comment claims uniformity |
| Card-exact without measurement flag | Offered a level the card documents whose measured reasoning output was near-zero on the live deployment | The offered level behaves as near-off for that deployment, below a lower level | Record the measurement in the code comment and the plan; shipping a card level is a family decision, not evidence |

## Results & Parameters

### Configuration

```yaml
variant_surface:
  protocol_field_families:
    emit: '{id, settings: {reasoningEffort: <level>}}'
    off_switch: '{id: "none", settings: {reasoningEffort: "none"}}'  # only if enum accepts
  template_families:
    emit: '{id, body: {chat_template_kwargs: {reasoning_effort: <level>}}}'
    off_switch: omit  # template default + raise cannot express none
  capabilities_reasoning: omit  # this provider package builds no variants from it
verification:
  list_probe: "<host-list>: every offered id appears as a variant"
  selection_probe: "#<level> run resolves; unknown #<bogus> fails at resolution"
  down_family: mark UNVERIFIED in code and plan; card-verified only
other_constraints:
  root_model_selector: "places no #variant; select per run/session/agent/command"
```

### Expected Output

- The model listing shows exactly the offered variants per family: no silent
  missing entries, no extras from invisible capability builders.
- A selection by an offered id resolves and completes; an unoffered id fails
  at model resolution.
- Two levels on one live replica produce measurable effort differences (for
  example, none returns no reasoning), and any level whose deployment
  measures near-zero is recorded as a caveat, not hidden.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Self-hosted model gateway and its agent-host provider extension | A provider plugin needed per-family effort variants for four model families on one live deployment | Registration probe, listing probe, and selection runs across two live models; two non-live families shipped card-verified with UNVERIFIED markers. [notes.md](./opencode-variants-explicit-not-capabilities.notes.md) |

## References

- [extension-visibility-field-must-be-the-gating-field.md](./extension-visibility-field-must-be-the-gating-field.md) — the sibling OpenCode plugin decision: a config switch is not the visibility gate; only host-probed fields count.
- [debugging-openai-chat-null-content-reasoning-shape.md](./debugging-openai-chat-null-content-reasoning-shape.md) — how response shape disputes are settled on OpenAI-compatible serving.
- [OpenCode models documentation](https://opencode.ai/v2/docs/models) — variants, `capabilities.reasoning`, and the root-selector limitation.
