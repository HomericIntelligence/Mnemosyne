---
name: http-response-rewrap-double-decode
description: "Audit or repair an HTTP client transport that reads a provider response and constructs a new response object. Use when: (1) a wrapper accumulates the body through a decoding API and reconstructs the response with the original headers, (2) every mock-based test passes but the first live call fails with a decompression or decoding error, or (3) a bounded-read, redirect-refusal, or header-normalization transport copies a provider response into a fresh object."
category: debugging
date: 2026-10-28
version: "1.0.0"
user-invocable: false
verification: verified-ci
license: BSD-3-Clause
tags: [http, transport, content-encoding, gzip, double-decode, response-reconstruction, mock-divergence, live-only-failure, bounded-read, wire-form-headers]
---

# HTTP Response Rewrap: Decoded Body Double-Decodes

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-28 |
| **Objective** | Find and repair HTTP transports that fail only live because the reconstructed response decodes an already-decoded body a second time. |
| **Outcome** | Successful. A live gate that had failed on 100% of its runs was repaired, verified end-to-end against the live provider, and delivered through the normal review path. |
| **Verification** | verified-ci: the behavior test failed before the repair with the live signature and passed after it; the gate's own read-only command then succeeded against the live provider; the pull request and its required checks are on record. |

## When to Use

- A client wrapper reads the provider response body and constructs a new response
  object from it, for a bounded read, a redirect refusal, header normalization, or
  a typed re-wrap. The httpx form is `httpx.Response(status, headers=original,
  content=accumulated)`. aiohttp, urllib3, and requests layers have the same
  pattern.
- Every unit and CI test passes, but the first live request raises
  `DecodingError`, `zlib.error ... incorrect header check`,
  `ContentDecodingError`, or a wrapper-typed error that swallows the cause.
- The failure repeats on every live run, at the same step, from a known date.
  A credential-hygiene layer converts the decoding error into one generic marker,
  so the run log does not show the root cause.
- Mock transports in the suite return identity (uncompressed) bodies with no
  `Content-Encoding` header, while the real provider compresses every response.

Do not use this skill for genuinely corrupt provider bytes or socket-layer
protocol errors. Those reproduce with raw tools such as curl and without the
wrapper.

## Verified Workflow

### Quick Reference

1. Read the failing job log segment before you form a hypothesis.
2. Reproduce with one behavior test: the provider double returns a real
   gzip-compressed body, a `Content-Encoding: gzip` header, and the compressed
   `Content-Length`. Run the full wrapper path. The test must fail before the
   repair with the live signature.
3. At the reconstruction site, copy the original headers minus exactly the
   wire-form fields: `content-encoding`, `content-length`,
   `transfer-encoding`. Keep status, `content-type`, `link`, `etag`, location,
   and rate-limit headers.
4. Meter your response-size bound on the same bytes that the consumer receives:
   the decoded body. Do not meter compressed bytes and then deliver decoded
   content through the constructed response.
5. Verify end-to-end with the gate's own read-only command and the real
   credential and endpoint path before merge. Record the live run identity.

### Suggested Approach

1. Classify the divergence first. Mock suite green on every run; live red on
   every run; same step; same generic marker. Each divergence points at
   behavior that the mocks cannot express: compression, redirect chains,
   chunked streaming, or pagination cursors. For the GitHub API, compression
   is constant: the client library advertises `Accept-Encoding: gzip, deflate`
   and the provider compresses every response.
2. Localize the two decode layers. Decode happens (a) on body consumption:
   `iter_bytes()` and `read()` apply the content decoder for the
   `content-encoding` response header. It happens (b) again on reconstruction:
   `httpx.Response.__init__` with a ByteStream triggers `read()`, which decodes
   per the still-present `content-encoding` header. The defect binds (a) and
   (b): accumulate decoded bytes with (a), then rebuild with (b)'s original
   headers. The second decode receives plaintext and raises
   `zlib.error: Error -3 ... incorrect header check`.
3. Make one mock tell the truth. Mock transports ship uncompressed bodies, so
   no existing test can see (b). Add one behavior test whose provider double
   returns `{"content-encoding": "gzip", "content-length": compressed_size,
   "content-type": "application/json"}` with `gzip.compress(plaintext)` as the
   body. Assert that the wrapper returns exactly the plaintext bytes, that
   `.json()` parses, and that the reconstructed response no longer declares a
   wire coding. RED before the repair; GREEN after.
4. Repair minimally at the reconstruction site. Build the new headers as the
   original headers minus the three wire-form fields. Do not drop unrelated
   metadata: pagination uses `link`, and budget accounting uses the rate-limit
   headers. Do not change the returned type: typed consumers expect the
   response contract (`.json()`, `.status_code`, `.headers`).
5. Check every sibling and re-wrap site. Subclasses that delegate to the parent
   request method share the repair after they stop re-wrapping themselves.
   Search the module for every new-response construction
   (`httpx.Response(`, assembled `requests.Response`, wrapped aiohttp
   `ClientResponse`) and apply the same audit.
6. Grade the evidence. The RED/GREEN pair proves the mechanism. A read-only
   live execution of the gate command with the repaired module proves the
   end-to-end behavior. When the gate validates a pinned identity, also record
   that the live identity fields match their frozen values byte for byte.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Accept mock-suite green as live behavior | Audited diffs and reasoned that the gate should pass | The gate had failed on 100% of live runs for weeks; file reasoning cannot see wire compression | A systematic CI/live divergence names the defect class. Audit what mocks cannot express before you propose anything |
| Send `Accept-Encoding: identity` outbound | Force identity to avoid compressed responses | Not enforceable: an intermediary can encode the body anyway, so the latent double-decode stays | Egress hygiene is not a repair. Fix the reconstruction and keep live-shape coverage |
| Keep raw bytes and the original headers | Accumulate with the raw byte API and rebuild with original headers | The size bound then meters compressed bytes while the consumer receives decoded content: the bound is bypassed and `content-length` becomes false | The bound must meter the bytes the consumer receives, whichever byte source you choose |
| Diagnose from the swallowed marker | Read only the generic `::error::` line of the failed job | The credential-hygiene layer hides provider detail by design; the cause is not recoverable from the marker | Reproduce the pipeline's exact call sequence read-only against the live endpoints and let the true exception escape at the seam |

## Results & Parameters

### Configuration

```yaml
strip_on_reconstruct: [content-encoding, content-length, transfer-encoding]
keep_headers: [content-type, link, etag, location, x-ratelimit-*]
size_bound_semantics: meter the delivered (decoded) body bytes
coverage_rule: one behavior test per transport wrapper with a compressed provider body and its encoding header
live_verification: run the gate's own read-only command with the repaired module before merge
```

### Expected Output

- One behavior test that fails on unfixed code with the provider decode
  signature and passes after the repair.
- An end-to-end live gate success, or the next genuine gate finding. A further
  finding is progress past this defect, not this defect.
- No behavior change for identity responses: all pre-existing transport tests
  stay green.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| LLM360/comet | Issue #3235 and pull request #3239: a production docs admission gate failed on five consecutive deployed-branch pushes, all at the same step; root cause reproduced and repaired at the single reconstruction site; PR required checks 50/50 green; post-fix live read-only admission verification passed | [notes](http-response-rewrap-double-decode.notes.md) |

## References

- Public library behavior at httpx 0.28: `iter_bytes()` applies content
  decoders per the `content-encoding` header; `Response.__init__` with a
  ByteStream triggers `read()`, which applies the same decoders from the
  supplied headers.
- [ci-failure-triage-and-diagnosis](ci-failure-triage-and-diagnosis.md) —
  CI/live divergence classification and log-first triage.
- [external-request-boundary-invariants](external-request-boundary-invariants.md) —
  provider boundary invariants for external API clients.
