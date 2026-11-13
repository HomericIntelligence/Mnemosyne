---
name: opencode-compaction-trigger-window-budget
license: BSD-3-Clause
description: "Set an absolute OpenCode V2 automatic-compaction trigger, such as 256k tokens, across models with different context windows by combining one global percentage buffer with per-model limit.context caps. Use when: (1) compaction must fire after the conversation crosses a fixed token budget, (2) a single global token buffer gives wrong triggers on other window sizes, (3) smaller-window models must compact at a proportional share of their window, or (4) per-model compaction tuning seems impossible."
category: tooling
date: 2026-11-13
version: "1.0.0"
user-invocable: false
verification: verified-live
tags:
  - opencode
  - compaction
  - context-window
  - model-limits
  - config
---

# OpenCode compaction trigger with a fixed token budget across window sizes

## Overview

| Field | Value |
| ----- | ----- |
| **Date** | 2026-11-13 |
| **Objective** | Make OpenCode V2 automatic compaction start at a chosen absolute token budget (for example 262,144 tokens) on every model whose window can support it, and at a proportional share of the window on every other model. |
| **Outcome** | Successful. A global `compaction.buffer` percentage plus `limit.context` caps on large-window models produced the target trigger on both model groups. The running service applied the config without a restart, and `opencode api get /api/config` returned the merged values as a receipt. |

## When to Use

- The fleet has models with different context windows, and one absolute trigger (tokens used) must apply to the large ones.
- A single global token buffer tuned to one window size fires too early or too late on the other sizes.
- A model-level override of `compaction.buffer` or `compaction.keep` seems necessary but the schema rejects it.
- A model whose window is close to the trigger must still compact before it reaches the window edge.

## Verified Workflow

### Quick Reference

OpenCode computes the automatic-compaction trigger as `context window - buffer`. There is no
absolute-usage trigger. To fire at budget `T` with a percentage buffer `p`:

```jsonc
// ~/.config/opencode/opencode.json (global config)
{
  "compaction": {
    "auto": true,
    "keep": { "tokens": 15000 },
    "buffer": "25%"
  },
  "providers": {
    "<provider>": {
      "models": {
        "<large-window-model>": { "limit": { "context": 349525 } }
      }
    }
  }
}
```

Trigger per model = `(1 - p) x limit.context` for capped models, `(1 - p) x true window` for the rest.
For `T = 262144` and `p = 25%`, the cap is `ceil(T / 0.75) = 349525`. Verify the merged config with
`opencode api get /api/config`; OpenCode watches config files and reloads without a restart.

### Suggested Approach

1. Confirm the semantics before any edit. The trigger is `window - buffer`; `buffer` accepts a
   percentage string (`"1%"` to `"99%"`, decimals allowed) or a token count. A token count at
   least as large as a model window is ignored, and the default (`"15%"`, at least 16k) applies
   to that model. The published schema at `https://opencode.ai/config.json` shows that per-model
   `settings.compaction` accepts only `type: summary | native`; `buffer` and `keep` are
   top-level only.
2. Choose the buffer percentage so one global rule covers the small models. `buffer: "25%"`
   makes every uncapped model compact at 75% of its window.
3. Cap each large-window model with `limit.context = ceil(T / (1 - p))` under
   `providers.<provider>.models.<model>`. The cap lowers the trigger to `T` and still leaves
   headroom of about `(T / (1 - p)) - T` tokens for the summary request itself. Do not cap a
   model whose true window is not comfortably above the cap; a configured limit above the real
   window lets the conversation overflow the provider.
4. Confirm true windows from a public catalog (for example the `models.dev` API) or the vendor
   documentation before capping. Do not guess.
5. Apply the edit, then read back the merged document with `opencode api get /api/config` and
   match the `compaction` block and each `limit.context` value. Config changes apply without a
   restart; a restart is not part of this workflow.
6. Treat "supports the budget" as "true window is at least the cap value with margin". A model
   with a 262,144-token window cannot fire at 262,144 used; it belongs in the proportional
   group even though its window names the same number.

`keep.tokens` keeps its default (15000) unless the session needs more recent context beside the
summary. Changing the trigger does not require changing `keep`.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| ------- | -------------- | ------------- | -------------- |
| 1 | One global token buffer tuned to the largest window (`window - T`, for example 744000 for a 1,000,000-token window) | The trigger became `W - 744000` for every model, so it was exact only for the tuned window and wrong for every other size | A token buffer encodes one window size only; use a percentage for a fleet |
| 2 | Per-model `settings.compaction.buffer` overrides | The published schema allows only `type` inside per-provider and per-model `settings.compaction`; unknown keys fail validation | The absolute trigger needs `limit.context` caps, not compaction settings |
| 3 | Cap every model at the cap value, including models with small true windows | A configured `limit.context` above the real window would let the conversation grow past what the provider accepts | Cap only models with a catalog-confirmed window above the cap; leave the rest on the percentage rule |

## Results & Parameters

### Configuration

| Parameter | Value | Effect |
| --------- | ----- | ------ |
| `compaction.buffer` | `"25%"` | Every uncapped model compacts at 75% of its window |
| `limit.context` (capped models) | `ceil(T / (1 - p))` | Compaction fires at `T` tokens used |
| `compaction.keep.tokens` | `15000` (default) | Recent conversation kept beside the summary |
| `compaction.auto` | `true` (default) | Automatic compaction near the trigger and one too-long recovery |

### Expected Output

- `opencode api get /api/config` shows the merged `compaction` block with the chosen `buffer`
  and each capped model with its `limit.context`.
- Large-window models compact at about `T` tokens of conversation; small models compact at
  `1 - p` of their true window.
- After compaction, the context returns below the trigger with the summary plus the kept
  recent tokens.

## Verified On

| Project | Context | Details |
| ------- | ------- | ------- |
| Comet | Session configuration change for a multi-model gateway fleet | [notes.md](./opencode-compaction-trigger-window-budget.notes.md) |

## References

- [OpenCode V2 compaction guide](https://opencode.ai/v2/docs/compaction)
- [OpenCode V2 configuration guide](https://opencode.ai/v2/docs/config)
- [OpenCode V2 providers guide](https://opencode.ai/v2/docs/providers)
- [Published OpenCode configuration schema](https://opencode.ai/config.json)
