# Notes: opencode-compaction-trigger-window-budget

Supporting evidence for the main skill. Recorded 2026-11-13.

## Source session evidence

The lesson comes from a configuration session on an OpenCode V2 setup that talks to a
custom OpenAI-compatible gateway provider. Objective: automatic compaction at an absolute
budget of 262,144 tokens (256k) on all models whose windows support it, with proportional
triggers elsewhere. Outcome: successful; the config below is the working shape (generic
provider and model names replace the local ones).

## Verification trail

1. **Semantics**: The V2 documentation states the trigger as "compaction starts when context
   approaches `window - buffer`" and gives the buffer forms (percentage string or token count)
   plus the default (`"15%"`, with an effective minimum of 16k). Fetched from the V2 docs pages
   on 2026-11-13:
   - `https://opencode.ai/v2/docs/compaction`
   - `https://opencode.ai/v2/docs/config`
   - `https://opencode.ai/v2/docs/providers`
2. **Schema**: `https://opencode.ai/config.json` was queried for the relevant paths:
   - `compaction.buffer` accepts `string | number`.
   - Per-provider and per-model `settings.compaction` accepts `type: summary | native` only.
     No `buffer` or `keep` inside model scope. This rules out per-model trigger overrides.
   - `providers.<id>.models.<model>.limit.context` accepts `number` and lowers the window the
     trigger math uses.
3. **True windows**: The model catalog from `https://models.dev/api.json` gives each model's
   `limit.context`. The catalog also confirms which served models have large windows. Read the
   catalog before writing caps; the session found one served model whose window equals the
   trigger number exactly (262,144) and left it uncapped (proportional group).
4. **Receipt**: `opencode api get /api/config` returned the merged configuration with the
   `compaction` block and both `limit.context` caps. This proves the running service saw the
   change; OpenCode reloads config files without a restart.

## Arithmetic

- Trigger for a capped model: `(1 - p) x limit.context`.
- For `T = 262144`, `p = 25%`: cap = `ceil(262144 / 0.75) = 349525.33 -> 349525`;
  trigger = `0.75 x 349525 = 262143.75` (within 1 token of the target).
- Headroom for the summary request on a capped model: `cap - T` (about 87381 tokens at these
  values). The compaction summary request itself consumes output tokens against the window;
  the headroom is why the cap must sit above the true budget.
- Smaller models fall to the percentage branch: a model with a 262,144-token window and a
  25% buffer compacts at 196,608 used.

## Failure detail: silent token-buffer fallback

A token-count `buffer` at least as large as a model window is ignored for that model, and the
default (`"15%"`, at least 16k) applies. In the source session the global buffer was tuned for
a 1,000,000-token window, so small models silently reverted to the 85%-used trigger. Detection:
compute the expected trigger per window size and compare with observed compaction points, or
review the smallest served window before choosing a token buffer. The percentage form avoids
the failure because every window shares the same relative rule.

## Config note

The session also observed that a commented-out `settings.compaction` override in the file was
dead content after the schema rejection; the working configuration keeps `compaction` at the
top level and caps only through `limit.context`. Keep no duplicate trigger tuning in model
scope; validators reject it and readers can mistake it for active configuration.
