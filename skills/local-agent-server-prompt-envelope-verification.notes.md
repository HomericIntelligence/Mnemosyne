# Notes: Local Agent Server Prompt Envelope Verification

Supporting evidence and failure signatures for
[local-agent-server-prompt-envelope-verification](./local-agent-server-prompt-envelope-verification.md).
Hostnames, paths, model names, ports, organization details, counts, and
per-environment configuration values are omitted by policy. All numbers below
are generalized functional observations, not configuration for any other
environment.

## Observed envelope behavior

- The agent client's full envelope (system prompt plus serialized tool schemas
  plus a short conversation) was roughly twice the size of the server's
  auto-tuned default context.
- The build request returned a context-size error; the client-side
  auto-compaction then failed with a "compaction failed" error, and the session
  ended with no answer.
- After loading with an explicit context sized well above the default (for
  example 16,384), all checks completed, including a tool-invoking round trip.

## Throughput observations

- A mid-size MoE reasoning model served only a few tokens per second on the
  probe prompt. A sub-billion-parameter vision-language model was
  significantly faster but could not express the tool-call grammar for any
  request even with tools declared.
- Co-residency of several small models reduced headroom. Removing co-residency
  increased throughput but was not required for correctness.
- The first request carries the full prefill. One run hit the serving stack's
  internal HTTP client timeout during the initial prefill; a retry succeeded
  with the server's prompt cache and no configuration change.

## Failure artifacts

- Context-size errors appeared only in the agent path with tools, never in the
  plain completion path, so a chat probe is not adequate evidence.
- Sampler-grammar errors named no model, token, or prompt; the client could not
  attribute them without reading the backend log. Schema-aware clients that
  see only the client-side error should capture the backend envelope.
- Declared `capabilities.tools: false` in the model record did not suppress
  tool advertisement; the agent emitted tool schemas anyway.

## Recovery

- The load-time context fix was applied once and verified by the native agent
  probe rather than by an endpoint-level completion probe.
- The intermittent HTTP timeout on the first prefill was handled by retrying
  after the prompt cache warmed.
