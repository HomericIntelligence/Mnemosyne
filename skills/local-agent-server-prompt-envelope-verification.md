---
name: local-agent-server-prompt-envelope-verification
license: BSD-3-Clause
description: "Verify that a local OpenAI-compatible agent server can carry a coding agent's full prompt envelope before you rely on it. Use when: (1) you stand up a local LLM endpoint as the backend for a coding or tool agent, (2) a client reports a generic connection or sampler error on the first request, (3) an agent check ends with a context-size error while the plain completion path works, or (4) tools-incapable small models are registered as agent backends."
category: tooling
date: 2026-11-10
version: "1.0.1"
user-invocable: false
tags:
  - agent-server
  - local-llm
  - openai-compatible
  - ctx-size
  - tool-call
  - readiness-verification
---

# Local Agent Server: Prompt Envelope Verification

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-10 |
| **Objective** | Prove that a local OpenAI-compatible server can serve a coding agent's full prompt envelope before you trust it for real work. |
| **Outcome** | Successful. End-to-end agent check after server sizing: request succeeds, tool-calls are emitted, and a small co-resident stack stays within available memory. |

## When to Use

- You connect a coding agent or tool agent to a self-hosted OpenAI-compatible endpoint.
- The agent answers a plain chat probe but fails or behaves erratically with tools.
- The backend logs a context-size error while the chat path appears to work.
- You serve several small co-resident models and the agent path is used for one of them.
- You add a new local model as an agent backend and want a readiness check.

## Verified Workflow

### Quick Reference

Load the backend with an explicit context sized to the agent's full envelope, then verify with the agent itself:

```bash
# Size at load, not after. Verify the full agent loop, not a chat probe.
<load-cli> <model-name> --ctx-size 16384
# Read back the effective context.
<probe> <server>/v1/models | jq '.context_length'
# End-to-end agent check: prompt with system + tool schemas.
<agent> run --model <provider>/<model> "List N files in the working directory."
```

### Suggested Approach

1. **Budget the entire agent prompt, not the chat prompt.** A coding agent's prompt is its system prompt plus the serialized tool schemas plus the conversation. Measure it once against your client's actual payload; do not estimate from the raw user message. A local small-model backend typically selects a default or auto-tuned context far below this.
2. **Set the context at load time.** Many servers select `n_ctx` themselves (auto-tune, model card, or a default), and silently load a smaller envelope than the agent needs. Load with an explicit large-enough `ctx_size` and read the effective value back before use.
3. **Verify through the agent, not the endpoint.** A one-word completion probe does not exercise the tool-call path or the full prompt size. Run a small real task with tools enabled before you declare the model ready for agent work.
4. **Treat declared model capabilities as documentation, not as control.** A model entry that says `tools: false` can still be sent tool schemas by the agent; a model entry that says `tools: true` can still fail for grammar or context reasons. Judge the backend by execution.
5. **If the backend cannot express the tool-call grammar**, the failure appears only when the agent sends tools. Either verify with tools enabled, or configure the agent not to send tools for that backend.
6. **Restrict co-residency with measured trade-offs.** Loading all local models at their full envelopes can exhaust memory; if memory is tight, verify the agent model at its required envelope and keep other models at their smaller envelopes. Measure decode throughput with and without co-residency and document the cost.
7. **Keep the first failure cheap.** The first request carries the largest prefill; budget for it in timeouts and retries before you open a long session.

### Notes

Current envelope sizes and failure artifacts change with each client and server version. Re-measure with your own client and backend before you freeze numbers into a deployment profile.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| -------- | --------------- | ---------------- | ---------------- |
| Load with default envelope | Served a small model for agent work at the server's default context | The agent's full prompt exceeded it; the build request returned a context-size error; the client's auto-compaction crashed and the session died with no answer | The default envelope is for chat, not for agents. Size from the agent payload |
| Chat probe declared ready | A one-word completion check passed | Every tools request failed with a sampler/grammar error; the tools path was never exercised | Verify the agent's actual request path, including tool schemas and grammar support |
| Declared `tools: false` in the model record | Expected tool schemas to stop being sent | The agent still sent tool schemas because agent tools are defined by the agent config, not by the model record | Readiness evidence comes from the client's tool-call path, not from declaration |
| Large envelope for everything | Loaded all local models at maximum envelope | Unavailable memory; the small models could not share the host | Size each model to its own use case and the host's memory budget |

## Results & Parameters

### Configuration

```yaml
agent_server:
  load:
    ctx_size: 16384          # >= system prompt + tool schemas + conversation
    n_threads: null          # set explicitly if the default under-utilizes cores
  probe:
    endpoint: "/v1/chat/completions"
    with_tools: true         # must exercise tool-call grammar
  verification:
    end_to_end: "real agent task, tools enabled"
    read_back: "/v1/models or equivalent for effective ctx"
  co_residency: "measure decode throughput; prefer fewer resident models"
```

### Expected Output

- The agent completes a real tool-using task without a context-size or sampler error.
- The effective context read back is at least the agent's prompt envelope.
- Co-residency does not exhaust host memory.
- The first request's prefill remains within your timeout and retry budget.

## Verified On

| Project | Context | Details |
| -------- | -------- | -------- |
| Self-hosted local agent backend | A local OpenAI-compatible server registered as an OpenCode-compatible provider | Chat probe passed; build request exceeded the default envelope; effective-ctx fix resolved the failure; an end-to-end agent task completed. See [notes.md](./local-agent-server-prompt-envelope-verification.notes.md) for the measured envelope, throughput, and failure artifacts |

## References

- [openai-agentic-serving-parser-flags.md](./openai-agentic-serving-parser-flags.md) — engine-side flags that agent tool calls depend on.
- [opencode-variants-explicit-not-capabilities.md](./opencode-variants-explicit-not-capabilities.md) — capability declarations are not the gating surface.
- [engine-argument-compat-before-launch.md](./engine-argument-compat-before-launch.md) — verify flags at launch, not after first failure.
