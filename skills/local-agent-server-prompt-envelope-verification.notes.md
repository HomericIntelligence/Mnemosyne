# Notes: Local Agent Server Prompt Envelope Verification

Evidence collected on 2026-10-31 to 2026-11-09 while operating a local
OpenAI-compatible agent server for a coding-agent client. Host names, paths,
model names, ports, and organization details are omitted by policy; all
numbers below are functional observations, not configuration for any other
environment.

## Measured envelopes

- The agent client's full envelope (system prompt + tool schemas + a short
  conversation) was 4,700–5,100 tokens across task probes.
- The server's auto-tuned default context was 4,096 tokens, smaller than the
  full envelope. The build request returned a context-size error; the
  client-side auto-compaction then failed with a "compaction failed" error,
  and the session ended with no answer.
- After loading with `ctx_size=16384`, all checks completed, including a
  tool-invoking round trip.

## Throughput observations

- A mid-size MoE reasoning model served 4–7 tokens per second on the probe
  prompt; a 450M VL-class model served about 38 tokens per second and failed
  the tool-call grammar for every request even with tools declared.
- Co-residency of five models kept the agent model resident; removing
  co-residency increased throughput but was not required for correctness.
- The first request carries the full prefill; a later run hit the serving
  stack's internal HTTP client timeout during the initial prefill, and a retry
  succeeded with the server's prompt cache.

## Failure artifacts

- Context-size errors appeared only in the agent path with tools, never in the
  plain completion path, so a chat probe is not adequate evidence.
- Sampler-grammar errors named no model, token, or prompt; the client could
  not attribute them without reading the backend log. Schema-aware clients
  that see only the client-side error should capture the backend envelope.
- Declared `capabilities.tools: false` in the model record did not suppress
  tool advertisement; the agent emitted tool schemas anyway.

## Recovery

- Personally, the load-time context fix was applied once and verified by the
  native agent probe rather than by an endpoint-level completion probe.
- The intermittent HTTP timeout on the first prefill was handled by retrying
  after the server's prompt cache warmed; a second attempt succeeded with no
  configuration change.
