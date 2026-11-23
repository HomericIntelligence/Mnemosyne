---
name: tooling-opencode-v2-session-model-audit
description: "Audit, explain, and retarget the model selection of OpenCode V2 sessions by provider or cost class. Use when sessions must leave free, deprecated, or incorrect models, when a bulk per-session model inventory is needed, or when a session uses a model that no configuration file declares."
category: tooling
date: 2026-10-18
version: "1.1.0"
user-invocable: false
tags: [opencode, session-management, model-selection, model-provenance, local-discovery, sqlite, api, bulk-migration]
---

# OpenCode V2 session model audit and retargeting

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-18 |
| **Objective** | Find each session that uses an unwanted provider or model class and move it to an approved model without direct database writes. |
| **Outcome** | Successful: inventory and bulk retarget verified against OpenCode v2.0.31. All matched sessions retargeted through the official API; verification query returned zero remaining matches. Model provenance was also verified against OpenCode v2.3.2: a session model with no configuration entry came from a built-in local runtime provider. |

## When to Use

- A user asks which OpenCode sessions use a specific provider, free tier, or deprecated model.
- Sessions must leave an unwanted model in bulk, for example after a policy change.
- Unwanted model usage can come from a configuration default, a manual per-session selection, or a live local runtime server, and the correct repair differs.
- A session uses a model that the global, project, and CLI configuration do not declare, or a model appears in the picker with no provider entry and no credential.
- A string match on the message store would produce false positives from model-switch event rows.

## Verified Workflow

### Quick Reference

1. Identify the target models. Enumerate the provider models and read their cost fields; zero-cost models report 0 for input, output, and cache prices.
2. Establish the model source before you choose a repair. Read the session record, then the configuration defaults, then the live local runtime endpoints. A configured default, a manual selection, and a discovered local model need different repairs.
3. Query the current model of each session from the local SQLite store (read-only).
4. Scan assistant message rows for historical usage. Filter by message type; event rows cause false positives.
5. Retarget each affected session with the official `session.switchModel` API operation.
6. Verify by re-running the inventory query.

### Provenance Sources

Read these sources in order. The session record tells you which model the session uses. The other sources explain why.

| Source | Positive evidence | Repair |
| --- | --- | --- |
| Session record | `session_v2.model` holds the provider and model. | Identify the model, then continue to the next sources. |
| Configuration default | A `model` field in the global, project, or CLI configuration matches the session model. | Edit that configuration file. |
| Local runtime discovery | A documented local endpoint returns the model from its model list. | Stop or repoint the server, or disable the built-in provider. |
| Manual session selection | A `model-switched` row in the session history shows the selection, and no configuration default or live endpoint matches. | Switch the session model; no configuration change is needed. |

### Suggested Approach

Do discovery with read-only SQLite queries against `~/.local/share/opencode/opencode.db`. The V2 troubleshooting documentation prohibits database edits while the service owns the state; do all mutations through the HTTP API.

Current model per session. Table `session_v2` has a `model` column that stores the last-selected model as JSON:

```sql
SELECT id,
       json_extract(model, '$.providerID') AS provider,
       json_extract(model, '$.id') AS model_id,
       title,
       datetime(time_updated/1000, 'unixepoch') AS updated
FROM session_v2
WHERE json_extract(model, '$.providerID') = '<provider>'
ORDER BY time_updated DESC;
```

Configuration and local discovery. Search the global `opencode.json(c)`, each project `opencode.json(c)`, and `cli.json` for a `model` field and a `providers` entry. If these files declare neither, do not conclude that the model is unexplained. OpenCode V2 also probes local runtime servers at their default addresses and adds the discovered models without a configuration entry. The documented defaults are Ollama at `http://127.0.0.1:11434`, LM Studio at `http://127.0.0.1:1234/v1`, and vLLM at `http://127.0.0.1:8000/v1`.

Probe the endpoint before you name a configuration cause. For vLLM, request `/health`, then `/v1/models`. OpenCode keeps only model cards whose `owned_by` is `vllm`. A positive result makes the live server the source: the model disappears when the server stops, or when you disable the built-in provider with `"plugins": ["-opencode.provider.vllm"]`. To use a different endpoint, set `providers.vllm.settings.baseURL`. Do not change the root `model` field to repair this case.

If the discovered endpoint is a process on a shared host, attribute the process from scheduler metadata before you name an owner. See [Slurm running-job content attribution](slurm-job-content-attribution.md).

Historical usage. The `session_v2.model` column shows only the last selection. Sessions that used the target model and then switched back need a scan of `session_message` rows. Count only rows with `type = 'assistant'`; the assistant row `data` JSON carries the response model:

```sql
SELECT session_id,
       json_extract(data, '$.model.providerID') AS provider,
       json_extract(data, '$.model.id') AS model_id,
       COUNT(*) AS assistant_messages
FROM session_message
WHERE type = 'assistant'
  AND json_extract(data, '$.model.providerID') = '<provider>'
GROUP BY session_id, model_id;
```

Retarget through the API. OpenCode exposes an HTTP API on its background service. List operations with `opencode api get /openapi.json`; the model-switch operation is `POST /api/session/{sessionID}/model` (`session.switchModel`). The request body takes a model reference with `providerID`, `id`, and an optional `variant`:

```bash
opencode api post /api/session/<session-id>/model \
  --data '{"model":{"providerID":"<approved-provider>","id":"<approved-model>","variant":"default"}}'
```

Retargeting changes only the model used for future turns of that session. It does not change history and is reversible by selecting a model in the interface.

When no background service is running or the API is unavailable, report the gap and keep the read-only inventory; do not fall back to direct database writes.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| String match on the message store | `WHERE data LIKE '%"providerID":"<provider>"%'` on all `session_message` rows | The store contains `model-switched` event rows that record provider changes; the match counts them as usage | Filter `type = 'assistant'` so only actual responses count |
| Session table alone | Read only `session_v2.model` for the inventory | The column holds the last-selected model; sessions that used the target model earlier and then switched back are missed | Scan assistant message rows for a complete usage inventory |
| Configuration-first blame | Assumed a configuration default caused the usage | The global and project configs had no `model` field; selection was manual per session | Verify defaults in configuration before choosing a repair scope |
| Stop after the configuration check | Found no `model` field and no provider entry, then called the model unexplained | A built-in local provider had discovered a live server at its default endpoint, so the model was absent from all configuration | Probe the documented local runtime endpoints before you attribute the model to configuration or to a manual selection |

## Results & Parameters

### Configuration

Model reference shape used by the API and by the `session_v2.model` column:

```json
{ "id": "<model-id>", "providerID": "<provider-id>", "variant": "default" }
```

### Expected Output

- A list of sessions still set to the target provider, with title and last-update time.
- A list of sessions with historical-only usage (current model already approved).
- The provenance of a model that no configuration declares: configuration default, manual selection, or local runtime discovery.
- After retargeting, the inventory query against `session_v2.model` returns zero matches.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| OpenCode v2.0.31 on Linux | Live audit and bulk retarget of a multi-project session store | Evidence in [notes.md](../skills/tooling-opencode-v2-session-model-audit.notes.md) |
| OpenCode v2.3.2 on Linux | Session model with no configuration declaration | Discovery from a local vLLM server; evidence in [notes.md](../skills/tooling-opencode-v2-session-model-audit.notes.md) |

## References

- [OpenCode troubleshooting guide: storage locations and service inspection](https://opencode.ai/v2/docs/troubleshooting)
- [OpenCode API reference](https://opencode.ai/v2/docs/api)
- [OpenCode V2 models guide: local runtime discovery](https://opencode.ai/docs/models#local)
- [Related skill: OpenCode V2 session deletion effects](tooling-opencode-v2-session-deletion-effects.md)
- [Related skill: Slurm running-job content attribution](slurm-job-content-attribution.md)
