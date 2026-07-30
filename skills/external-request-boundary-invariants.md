---
name: external-request-boundary-invariants
description: "Use when: (1) an external API client combines local admission, provider rate limiting, retries, and deadlines, (2) persisted logical names map to endpoint- or credential-keyed process registries, (3) batched completion/chat responses contain indexed choices and parallel optional fields, or (4) YAML/JSON safety limits may silently coerce booleans into numbers."
category: architecture
date: 2026-07-30
version: "1.0.0"
user-invocable: false
verification: verified-local
tags:
  - external-requests
  - retry-accounting
  - rate-limiting
  - admission-control
  - runtime-registries
  - persistence-identity
  - transactional-validation
  - pydantic
  - openai-compatible
---

# External Request Boundary Invariants

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-07-30 |
| **Objective** | Review external-provider integrations by testing the boundaries between local setup, local admission, provider accounting, persisted identity, runtime identity, and response commit. |
| **Outcome** | Four reusable failure modes were reproduced at an immutable pull-request head: pre-HTTP work consumed provider budget, same-name reconfiguration split persisted and live identities, malformed batches passed incomplete validation, and boolean safety limits were coerced to numbers. |
| **Verification** | `verified-local` for defect reproduction and review workflow. The reviewed source was not remediated in this session, so no fix verification is claimed. |

## When to Use

- A request path has a connection pool, token bucket, maximum attempts, per-attempt timeout, and total deadline.
- A local operation such as client construction, credential loading, or request serialization can fail before network I/O.
- Persistence upserts a model/provider by logical name while live pools or limiters use endpoint, credential, or serving keys.
- A successful HTTP response contains multiple indexed choices or optional arrays that must stay parallel.
- Pydantic or another coercive schema validates attempts, timeouts, deadlines, backoff, capacity, or rate limits.
- A green test suite covers happy paths but does not prove the observable accounting and identity invariants below.

## Verified Workflow

### Quick Reference

| Boundary | Required invariant |
| ------- | ------- |
| Local pool admission | Bounded by the total deadline; consumes neither a provider permit nor an HTTP attempt |
| Client/configuration setup | Completes before provider accounting, or is performed eagerly during registration |
| Provider-rate admission | Occurs immediately before actual outbound dispatch |
| Attempt accounting | Increments at the same outbound boundary as the provider permit |
| Per-attempt timeout | Covers the outbound HTTP attempt, not time already spent waiting locally |
| Registration | One logical name resolves to one coherent persisted and process-scoped runtime identity |
| Batched response | Fully normalized and validated before any result is committed |
| Numeric safety config | Rejects booleans; numeric-string compatibility is an explicit decision |

### 1. Draw the accounting boundary at outbound dispatch

Trace one request through these phases separately:

1. Acquire local concurrency capacity under the total deadline.
2. Construct or retrieve the provider client while no provider budget has been charged.
3. Acquire the provider-rate permit.
4. Increment the outbound-attempt counter.
5. Start the provider request under the per-attempt timeout.
6. Parse the response transactionally.
7. Release local capacity on every exit path.

Anything that can fail before step 5 is local work. It must not consume a provider permit or an
outbound attempt. If client creation cannot be moved inside this ordering cleanly, create and
validate clients eagerly during registration.

Use a behavior-first probe with concurrency `1`, provider RPM `1`, two pending rows, and a short
total deadline. Force client construction for the first row to fail before HTTP and assert:

- no provider call occurred;
- the failure reports `attempts=0` with structured setup/configuration evidence;
- the provider permit remains available;
- the pool lease is released; and
- the sibling row is not throttled by the local failure.

A test that checks only lease release is insufficient: the lease can be released correctly after
the code has already burned a provider permit and an attempt.

### 2. Compare logical persistence identity with live runtime identity

List every request-affecting field that defines a live external identity. Typical fields include:

- canonical endpoint;
- credential fingerprint or provider quota identity;
- concurrency capacity and requests per minute;
- provider/API model name;
- retry and deadline policy; and
- other request-shaping configuration retained by active clients.

Under the registration lock, load any existing record for the same logical name before mutating a
pool, limiter, endpoint registry, database row, event, or queue. Then choose one explicit lifecycle:

- allow exact idempotent re-registration and reject any effective change until restart; or
- implement an atomic drain, unregister, replace, and republish operation.

Validating only the incoming endpoint- or quota-key collision is not enough. A changed endpoint or
credential creates a new key and can therefore bypass those checks while persistence overwrites the
old logical name.

Probe endpoint `A` followed by endpoint `B` under the same logical name. On rejection, assert that
the database row and every runtime registry remain unchanged. Repeat for credential, capacity, RPM,
API model name, and retry-policy changes. If replacement is supported, include active users in the
test and prove that old and new identities never serve the same logical output concurrently.

### 3. Normalize a whole response before committing any item

Treat HTTP 2xx as transport success, not application success. For each completion/chat batch:

1. Require a concrete choice list with the exact expected length.
2. Require each `choice.index` to be an integer but not a boolean.
3. Require the index set to equal `range(expected_choices)` with no duplicates or gaps.
4. Sort by validated index before serializing output.
5. Validate required text/content and metadata shapes.
6. Validate every optional parallel field coherently across all choices.
7. Build a temporary response delta and commit it only after every check succeeds.

Do not let the first choice decide whether an optional vector such as logprobs exists for the whole
batch. Define the supported contract explicitly: either every choice supplies the field, every
choice omits it, or the output preserves one explicit placeholder per choice.

Exercise duplicate, missing, out-of-range, boolean, and out-of-order indices. Exercise mixed
optional-field presence in both orders: `[absent, present]` and `[present, absent]`. Both orderings
must produce the same documented outcome rather than silently losing evidence in one direction.

### 4. Make numeric safety policy strict by intent

In Python, `bool` is a subclass of `int`, and coercive schema libraries may turn `true` into `1` and
`false` into `0`. Range constraints alone therefore do not prove type safety.

For attempts, timeout, deadline, backoff, capacity, and rate fields:

- reject booleans before numeric coercion;
- use strict integer validation where integral values are required;
- reject non-finite floating-point values;
- decide explicitly whether numeric strings are compatible input; and
- test `true` and `false` independently for every field.

Tolerance and coercion can be appropriate at some loader boundaries, but they must be selected
field by field. Provider-safety budgets should not inherit them accidentally.

### 5. Prove effects, not helper calls

Adversarial tests should assert provider calls, remaining permits, attempt counts, persisted rows,
runtime registry contents, emitted result shape, and sibling progress. Mock-call assertions alone
can stay green while the system violates the real contract.

Run focused probes first, then the repository's full relevant suite and build/validation gates. A
green broad suite is supporting evidence, not a substitute for a test that goes red against the
specific accounting, identity, or response-shape defect.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| ------- | ------- | ------- | ------- |
| Fix only pool-lease cleanup | Guaranteed release when client construction failed | The local failure still occurred after the provider permit and attempt were charged, so another row could starve despite no HTTP call | Test provider accounting and sibling progress, not only resource release |
| Preflight only incoming endpoint/quota keys | Rejected capacity or RPM drift for an already-known key | Changing endpoint or credential produced a new key, bypassed preflight, overwrote the same persisted name, and left old runtime resources live | Compare the same logical name across persistence and every process-scoped identity before mutation |
| Validate only response choice count | Required `len(choices) == expected` | Duplicate indices such as `[0, 0]` still passed and were committed | Require the exact strict-integer index set and normalize order |
| Gate all optional output on the first choice | Serialized logprobs only when `choices[0]` contained them | `[absent, present]` silently lost valid evidence while the reverse order failed | Validate the optional field across the entire batch and preserve its parallel contract |
| Apply numeric range constraints to coercive fields | Used positive bounds without strict type handling | YAML booleans silently became numeric retry/deadline values | Reject booleans before coercion and test every safety field |
| Treat reproduced review findings as verified fixes | Captured the desired invariant after a strict review | Source-level reproduction proves the defect and the review method, not that a later remediation works | State the verification boundary and require fresh fix-specific tests before upgrading confidence |

## Results & Parameters

### Probe Matrix

| Probe | Required result |
| ------- | ------- |
| Pre-HTTP client setup fails | Zero provider calls, permits, and attempts consumed; local lease released |
| Two rows with concurrency/RPM `1` | A local failure does not throttle or expire its sibling |
| Same logical name changes identity `A` to `B` | Rejected with DB and registries unchanged, or atomically drained and replaced |
| Duplicate or missing choice index | Whole response classified as malformed before commit |
| Out-of-order complete index set | Deterministically normalized by index |
| Mixed optional parallel fields | One documented, order-independent outcome |
| Boolean numeric safety value | Validation failure, never implicit `0` or `1` |

### Parameters to Capture

Record these values with every reproduction so the evidence is portable:

- local concurrency capacity;
- requests per minute and burst behavior;
- maximum attempts;
- per-attempt timeout and total deadline;
- initial/capped backoff and jitter;
- logical name, canonical endpoint, credential fingerprint, and API model name;
- expected choice count and returned choice indices; and
- presence and lengths of all parallel response fields.

## Verified On

| Project | Context | Details |
| ------- | ------- | ------- |
| LLM360/Eval360-V2 | Strict review of PR #318 at head `ea4ab19de63f8baa1a10871226b897670ff09282` against base `f5081bfba9ef8e7b380f5bd85ed1cf61a91f90b0` on 2026-07-30 | Reviewed all 26 changed files and both diff lenses. Reproduced a pre-HTTP client-setup failure consuming the sole RPM permit and starving a sibling; same-name endpoint/RPM reconfiguration splitting the database and live registries; duplicate `[0, 0]` response indices; order-dependent mixed logprobs; and boolean retry-limit coercion. All eight substantive exact-head CI checks were green, the local scheduler bucket passed 1,090 tests with 10 skips, and focused behavior buckets passed 162 tests. These results verify the review findings and workflow only; remediation was not part of the session. |

## References

- [Backoff jitter hard-ceiling ordering](backoff-jitter-clamp-after-not-before-max-delay.md)
- [State machine and resource lifecycle patterns](state-machine-and-resource-lifecycle-patterns.md)
- [Pydantic coercion as a behavioral boundary](pydantic-basemodel-to-dataclass-behavioral-parity.md)
