---
name: timing-oracle-equalization-probe-review
license: BSD-3-Clause
description: "Review a plan or change that equalizes credential-lookup timing so an unknown identifier costs the same as a wrong secret. Check that the dummy verifier has a reachable real scope, that every non-secret answer path pays the same work, that the probe call is not deleted by the optimizer, and that the count test patches the hashing seam instead of a helper that can short-circuit it."
category: architecture
date: 2026-11-07
version: "1.0.0"
user-invocable: false
verification: unverified
tags:
  - timing-side-channel
  - user-enumeration
  - credential-lookup
  - constant-time
  - dummy-verifier
  - plan-review
  - test-seam
  - oracle-equalization
  - anonymous-probe
---

# Timing Oracle Equalization: Probe Review

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-07 |
| **Objective** | Review equalization fixes for a credential-lookup timing oracle. |
| **Outcome** | Unverified review rule, derived from one plan review. |
| **Verification** | unverified. The plan that produced this rule was rejected before implementation. |

An unknown identifier returns before any hash or constant-time compare. A known
identifier with a wrong secret runs both. The time difference tells a caller
without the secret whether the identifier exists. A common fix adds a dummy
verifier: hash the presented key against a fixed stored value, compare in
constant time, discard the result.

The fix looks small. Most failures are in the details listed below.

## When to Use

- A plan adds a dummy or padded verifier to a credential decision path.
- A plan claims that an unknown identifier and a wrong secret "cost the same".
- A review checks a test that counts hash calls.
- A decision path has several non-secret answers, such as unknown, unavailable,
  revoked, and expired.

## Verified Workflow

> **Warning:** This rule is unverified. It comes from one rejected plan. It has no executed fix or test behind it.

### Quick Reference

```text
1. SCOPE   Dummy scope must equal the scope of a real stored verifier.
2. PATHS   Every answer that leaks identifier existence pays the same work.
3. WORK    Name the variable-cost steps on the real path, not only the hash.
4. KEEP    The optimizer keeps the call, or the helper returns the value.
5. SEAM    The count test patches the function the code calls first.
6. NONCEL  Do not read unknown key bytes into the computation path.
```

### Detailed Steps

1. **Check the dummy scope.** The dummy verifier must be a value that a real
   write path can produce. Build it from the service's own authority values and
   the same class and role convention as a real grant. A digest of all zeros is
   not a real verifier. A role that no grant path writes is also not real. Grep
   every caller of the decision function, including last-good and retained
   snapshot paths, before you accept the scope.
2. **Enumerate every answer of the branch.** Each early return that tells the
   caller "this identifier does not exist" or "service unavailable" costs less
   than a wrong secret. Add the probe to all of them, or record each unmodified
   path as a residual oracle with a follow-up. Look at the exception path
   around the entry read as well as the plain answers.
3. **Add the variable-cost work.** A real lookup hashes over the observed
   class, cluster, deployment, and role text. A constant dummy removes that
   variation. State whether the equalization covers only the digest, and
   record the residual cost difference.
4. **Keep the work in the output path.** In a bytecode language the compiler can
   delete a call whose result is unused. Return the comparison value from the
   helper and then discard it, or record why the call cannot be removed.
5. **Patch the first function that the code calls.** A count test that patches
   an inner hashing helper passes when the dummy never reaches it, because the
   outer compare can reject before the hash. Patch the compare or match
   function that the decision code calls directly, assert the call count, and
   assert that the dummy stored value is the argument. Add a second case that
   shows the success path does not call the probe.
6. **Keep the secret out of the probe.** Do not read bytes from the unknown
   identifier, because the read is not constant time. Do not put the presented
   secret into a message digest that an attacker can use as a nonce.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| ------- | --------------- | ------------- | -------------- |
| All-zero dummy digest with a class and role that no write path uses | Added a fixed verifier constant in the hashing module | The dummy is not a real verifier, and it ignores the authority values of the cache | Build the dummy from the service authority values and a real grant convention |
| Probe only on the plain unknown answer | Added one call before the unknown return | The recovery and pending exception path still returns fast | Enumerate all non-secret answers of the branch |
| Count test patched at the hashing helper | Asserted one hash call per case | A compare that rejects first never reaches the helper, so the test proves less than it names | Patch the function that the decision code calls directly |
| Result discarded in the helper | Ran the compare and returned nothing | A bytecode compiler can remove the unused call | Return the value from the helper and discard it at the caller |
| Reference test listed as "answers unchanged" evidence | Used a test that asserts the answer value | The test also passes when the probe is absent, so it cannot detect a probe that changes the answer | Name a test that can fail when the probe is wrong, or delete the claim |

## Results & Parameters

| Parameter | Value |
| --------- | ----- |
| Probe placement | Inside the non-secret branch, before the answer is built |
| Probe result | Unused at the caller, returned by the helper |
| Count test seam | The compare or match function called by the decision code |
| Test cases | Unknown identifier, wrong secret, and one success path |