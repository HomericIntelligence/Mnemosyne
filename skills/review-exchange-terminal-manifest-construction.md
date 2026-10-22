---
name: review-exchange-terminal-manifest-construction
description: "Build a terminal-delivery closure manifest in the verified dependency order — deterministic ledger first, visible-content digest before reduce, render, canonical JSON — so the designated terminal delivery helper accepts it. Use when: (1) a review flow routes a terminal-eligible round through a designated terminal delivery helper that consumes a closure manifest, (2) the helper rejects the manifest with an input-validation error such as an uncanonical JSON form or a visible-ledger mismatch, (3) you must decide what belongs in the terminal visible content and which digest to bind in the reduce event, or (4) you must distinguish a pre-publication input rejection (fix and resubmit) from a publication-state wedge (do not retry)."
category: tooling
date: 2026-10-22
version: "1.0.0"
user-invocable: false
tags:
  - pr-review
  - review-exchange
  - terminal-delivery
  - closure-manifest
  - deterministic-ledger
  - canonical-json
  - visible-content-digest
  - input-validation
  - safe-retry
---

# Review Exchange Terminal Manifest Construction

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-22 |
| **Objective** | Deliver a terminal reviewer state through the designated terminal delivery helper on the first accepted submission. |
| **Outcome** | Operational rule derived from one live terminal GO delivery. Hand-written visible prose and a pretty-printed manifest were rejected by fail-closed input guards. Inputs rebuilt in the verified order were accepted, and the helper published the terminal carrier and the exclusive terminal label. |
| **Verification** | verified-live in one zero-finding terminal GO delivery (2026-10-22) at the exact head. Single-case evidence; the invariants follow from deterministic fail-closed input validation. |

## When to Use

Use this skill when these conditions apply:

- A review flow routes a terminal-eligible round (GO state, findings resolved) through a designated terminal delivery helper that consumes a schema-identified closure manifest.
- The helper rejects a manifest before publication with an input-validation error. Examples: the file is not canonical JSON; the terminal visible ledger does not match its manifest entries.
- You must decide what text goes into the manifest's terminal visible content field, and which digest goes into the reduce event's visible-content digest.
- You must classify a rejection: a pre-publication input rejection (fix the input and resubmit), or a publication-state wedge (stop; apply wedge recovery rules).

The publisher-routing decision and wedge recovery are a different rule. See References.

## Verified Workflow

### Quick Reference

```text
1. Compute the deterministic terminal ledger with the terminal helper's own
   generator (binding, ordered closure entries). Never write it by hand.
2. Hash the exact ledger bytes into the reduce event's visible-content digest.
   Then reduce, then render. This order is mandatory: the state binds the digest.
3. Put the same exact ledger bytes in the manifest's terminal visible content.
4. Serialize the manifest as canonical JSON (sorted keys, minimal separators),
   then deliver.
5. An input-validation rejection is pre-publication: fix the input and resubmit.
```

### Suggested Approach

1. Decide the publisher before this rule applies. Once the terminal round is routed to the designated helper, build its inputs in dependency order. The helper derives the visible terminal ledger deterministically from the binding and the ordered closure entries; hand-written prose cannot match it. Call the helper's own ledger generator, treat the output as opaque bytes, and reuse the identical bytes wherever the ledger is required.
2. Respect the digest order. The render step refuses a carrier whose visible-content digest does not equal the digest bound in the reduce event. So: compute the ledger, hash it, write the digest into the reduce event, reduce, render. Any edit to the visible content after reduce invalidates the state; recompute the ledger and reduce again.
3. Serialize the manifest file in the canonical byte form the exchange defines: UTF-8 JSON, sorted object keys, minimal separators. A pretty-printed document parses as JSON but fails the byte-level canonical-form check.
4. Check the helper's interface details against its actual signature. The positional argument is the review identity (number or URL), not a mode word. Requirement-issue flags belong to manifest-preparation mode, not to response-manifest delivery. When importing the helper in-process, reproduce its script entry-point module context so the helper's own module fallback resolves.
5. Triage rejections by class. An input-validation rejection proves nothing was published: correct the input and resubmit; retries are safe. A rejection that names a conflicting terminal review or a nonforking chain is a publication-state wedge: stop and apply the wedge rules; do not fix-and-retry.

### If a step is unavailable

- An exchange generation without a deterministic-ledger binding: this rule does not apply. Record which visible-content convention the flow uses before the terminal round.
- No usable in-process import: run the helper's command-line entry point to produce inputs instead of importing its functions.
- A validation error not covered here: treat it as input construction until proven otherwise. Confirm with the forge readback that nothing was published before you resubmit.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Hand-written prose as terminal visible content | Composed a detailed assessment report and used it as the manifest's terminal visible content | The helper rejected it: the terminal visible closure ledger does not match its manifest entries. The published body is deterministic over the binding and entries; prose cannot match | Generate the ledger with the helper's own generator. Detailed prose belongs in the user-facing report, never in the terminal visible content |
| Digest bound to prose before the ledger decision | Hashed the prose into the reduce event's visible-content digest, then learned the published body must be the deterministic ledger | The reduce output bound the wrong digest; continuing would fail at render or delivery. The fix required a new reduce with the correct digest | Compute the ledger first and bind its digest; the reduce event is not the place to discover the visible content |
| Pretty-printed manifest JSON | Wrote the closure manifest with indentation for readability | The helper rejected it: the response manifest is not canonical JSON. It enforces the exchange canonical byte form, not JSON parseability | Serialize the manifest with the exchange canonical encoder (sorted keys, minimal separators) before delivery |
| Mode word as positional argument | Passed a mode word as the helper's positional argument | The parser treated the word as the review identity and failed | Read the helper's actual argument signature; the positional argument is the review identity (number or URL) |
| In-process import without entry-point context | Imported the helper module directly to reuse its ledger generator | A package-relative import failed in-process although the script entry point worked | Reproduce the script's module-loading context (empty package context) when importing, or use the command-line entry point |

## Results & Parameters

### Configuration

```text
visible content   = terminal helper ledger generator(binding, ordered entries)  # opaque bytes
reduce digest     = sha256(visible content)   # written into the reduce event before reduce
manifest field    = the same visible content bytes
manifest file     = canonical JSON: UTF-8, sorted object keys, minimal separators
retry decision    = input-validation rejection          -> fix input, resubmit (safe: pre-publication)
                  = conflicting-terminal / chain error  -> stop; apply wedge recovery rules
```

### Expected Output

- The reduce step accepts the event; the render step produces the state carrier with no digest mismatch.
- The helper publishes exactly one terminal COMMENT carrier at the exact head, applies the exclusive terminal-state label, and closes the authorized fixture set. An independent forge readback shows the published ledger and its closure digest.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| An internal repository review flow | Terminal GO delivery for a single-file installer fix; zero-finding round 1 at the exact head; two manifest submissions rejected on input validation, the third accepted and read back from the forge | [notes](review-exchange-terminal-manifest-construction.notes.md) |

## References

- [review-exchange-terminal-carrier-sole-publisher](review-exchange-terminal-carrier-sole-publisher.md) — the publisher-routing decision and wedge recovery. Apply it before this construction rule, and whenever a rejection is publication-state (conflicting terminal review, nonforking chain) rather than input validation.
