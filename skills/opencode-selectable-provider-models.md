---
name: opencode-selectable-provider-models
license: BSD-3-Clause
description: "Register the chat models of a hosted OpenAI-compatible provider as individually selectable entries in the OpenCode host configuration. Use when: (1) a provider guide binds one model with an environment placeholder and you need every supported chat model in the picker, (2) a reasoning model needs per-model replay of the reasoning trace, (3) a non-chat model is nominated as a chat model."
category: tooling
date: 2026-11-16
version: "1.0.0"
user-invocable: false
verification: verified-local
tags: [opencode, provider, openai-compatible, models, reasoning-content]
---

# OpenCode Selectable Provider Models

## Overview

| Field | Value |
| --- | --- |
| **Date** | 2026-11-16 |
| **Objective** | Make each supported chat model of a hosted OpenAI-compatible provider selectable in OpenCode, with reasoning traces replayed, from one host configuration entry. |
| **Outcome** | Successful for the listing probe. The registered chat models appear in the host model listing. The live chat path was not exercised because no provider API key was available to the session. |

## When to Use

- A provider integration guide binds one model with an environment placeholder (for example, a
  single `{env:PROVIDER_MODEL}` key) and the host must offer more than one supported chat model.
- The provider's models emit their reasoning trace in `reasoning_content` and multi-step
  conversations break or go empty.
- A provider catalogs a non-chat model (for example, a speech-to-text model) and a user asks to
  add it as a chat model.

## Verified Workflow

### Quick Reference

```jsonc
// host global config (for example opencode.jsonc)
{
  "provider": {
    "<id>": {
      "npm": "@ai-sdk/openai-compatible",
      "name": "<Display Name>",
      "options": {
        "baseURL": "<https://api.example.invalid/v1>",
        "apiKey": "{env:<PROVIDER_API_KEY>}"
      },
      "models": {
        "<provider>/<chat-model-a>": { "interleaved": "reasoning_content" },
        "<provider>/<chat-model-b>": { "interleaved": "reasoning_content" }
      }
    }
  }
}
```

Prove the result with the host listing, not with the config as written:

```bash
opencode models | grep "<id>"
```

Every registered chat model must appear. A restart of the host is required before a fresh
configuration is visible.

### Suggested Approach

1. Enumerate the provider catalog and keep only models served on the chat API. A
   transcription-only or embedding model cannot answer chat requests. A picker entry for such a
   model looks usable and fails on every request. Record the exclusion and its reason.
2. Register one entry per supported chat model in the provider's `models` map. A single
   environment-placeholder key yields one picker entry and breaks when the variable is unset.
3. Put host-specific per-model settings inside each model entry. Settings such as `interleaved`
   are ignored at provider level. The host then does not replay the reasoning trace, and
   conversations degrade as soon as a model returns an empty trace.
4. Keep the API key in an environment variable. A literal `baseURL` is acceptable when the hosted
   endpoint is fixed. Use a whole-value variable when a self-hosted endpoint needs to change.
5. Do not set a root default model as a side effect of adding a provider. Choose the default
   deliberately, or leave the existing default unchanged.
6. Verify through the host listing after a restart. The registration itself proves nothing about
   what the host loads.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --- | --- | --- | --- |
| Single environment-placeholder model key | Registered one `{env:...}` entry as the provider's only model | The picker offered exactly one model and failed resolution when the variable was unset | Enumerate each supported chat model explicitly in the `models` map |
| Provider-level `interleaved` | Set `interleaved: "reasoning_content"` on the provider object | The host ignores model settings at provider level; the reasoning trace was not replayed across turns | Move the setting into each model entry |
| Non-chat model as a chat entry | Added a transcription-only model to the `models` map | It cannot answer chat completions; every request would fail | Exclude non-chat models and record the reason |

## Results & Parameters

### Configuration

A public example from the IFM OpenCode guide (<https://docs.ifm.ai/docs/opencode.md>), with two
registered chat models instead of one environment-pinned model:

```jsonc
{
  "provider": {
    "ifm": {
      "npm": "@ai-sdk/openai-compatible",
      "name": "IFM",
      "options": {
        "baseURL": "https://api.ifm.ai/v1",
        "apiKey": "{env:IFM_API_KEY}"
      },
      "models": {
        "IFM/K2-Horizon-375B-A23B": { "interleaved": "reasoning_content" },
        "IFM/Jais-3-MoVA-36B-A4B": { "interleaved": "reasoning_content" }
      }
    }
  }
}
```

The IFM catalog lists two hosted chat models (both advance a reasoning trace) and one hosted
speech-to-text model (`IFM/Jais-ASR`, available through the Transcriptions API only). The
speech-to-text model is not a chat entry. K2 Horizon accepts `high` reasoning effort only; Jais 3
accepts `low` and `high`.

### Expected Output

- The host listing shows one selectable entry per registered chat model.
- Selecting a reasoning model replays its reasoning trace across turns.
- The excluded non-chat model does not appear and is documented as out of scope.

## Verified On

| Project | Context | Details |
| --- | --- | --- |
| OpenCode host | 2026-11-16 configuration session | `opencode models` listed both registered chat models after a restart. The live chat path was not exercised because no provider API key was available; treat reasoning-replay behavior as documented, not measured, on this host. |

## References

- [IFM OpenCode guide](https://docs.ifm.ai/docs/opencode.md) — the host-config pattern this entry extends to multiple models.
- [IFM reasoning documentation](https://docs.ifm.ai/docs/reasoning.md) — effort support per model family and the `reasoning_content` field.
- [opencode-variants-explicit-not-capabilities.md](./opencode-variants-explicit-not-capabilities.md) — per-model reasoning-effort levels emitted from a provider plugin; a different decision from plain host-config registration.
- [debugging-openai-chat-null-content-reasoning-shape.md](./debugging-openai-chat-null-content-reasoning-shape.md) — the response-shape failure that follows when the reasoning trace is not replayed.
