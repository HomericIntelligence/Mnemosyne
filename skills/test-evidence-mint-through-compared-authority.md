---
name: test-evidence-mint-through-compared-authority
description: "Mint fabricated evidence fields through the same authority the comparison under test uses, resolved at call time. Use when a test that builds fake scheduler, registry, or telemetry evidence passes on the continuous-integration runner but fails on another host with an ownership-drift, identity-mismatch, or foreign-evidence rejection, when a fixture hardcodes a uid, user name, or host value that production re-derives, or when you plan to change a shared evidence factory while sibling suites stub the authority to a constant."
category: testing
date: 2026-10-26
version: "1.0.0"
license: BSD-3-Clause
user-invocable: false
verification: verified-local
tags:
  - test-fixture
  - evidence-factory
  - identity-authority
  - monkeypatch
  - host-portability
  - euid
  - shared-default
---

# Mint Test Evidence Through the Compared Authority

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-26 |
| **Objective** | Keep fabricated test evidence in agreement with the identity or ownership authority the comparison under test uses, on every host that runs the suite. |
| **Outcome** | Successful. Twelve host-dependent failures in one test module were fixed when the fabricated owner started to be minted through the identity resolver at call time; an attempted shared-factory change was reverted after it broke 75 tests in suites that pin the resolver to a constant. |
| **Verification** | verified-local — pristine-vs-patched runs on a host whose euid differs from the runner default, full-module sweeps, and pinned-suite regression probes. |

## When to Use

- A test passes on the builder image (for example uid 1001) but fails on a development host with an ownership-drift, identity-mismatch, or foreign-evidence rejection.
- A fixture or factory fills identity fields (owner uid, user name, hostname) with literal constants while production compares them against a resolver, for example a principal database or a service-identity lookup.
- A session-wide fixture remaps the authority to the current process, for example the principal lookup to the process euid, so the authority and the constants agree only on one host class.
- You plan to change a shared evidence factory default and suspect that some suites stub the resolver to a fixed value.

This rule covers test-side evidence. For product-side identities that several hosts must compute identically, see `cross-host-identity-divergence-volatile-hash-inputs`.

## Verified Workflow

### Quick Reference

For each field that production validates against an authority, mint the test value by calling that authority at call time, through module-attribute access so test stubs stay authoritative:

```python
# In the test helper: import the module, not the function.
from package import authority_module

def make_evidence(context, *, owner_uid=None):
    if owner_uid is None:
        # Follow the resolver, including monkeypatch pins, on every host.
        owner_uid = authority_module.resolve_identity(
            context.spec.service_principal
        ).uid
```

### Suggested Approach

1. Identify the comparison authority first. Read the production check and find the resolver that produces the trusted side of the comparison. Do not copy the value that a green run happens to show; that value is host luck when the authority follows the process.
2. Mint at call time through the module attribute. `monkeypatch.setattr("package.authority_module.resolve_identity", stub)` replaces the module attribute. A helper that binds the function at import time (`from package.authority_module import resolve_identity`) keeps the pre-stub reference and ignores the pin.
3. Fix the local call site, not the shared factory, until every consumer is enumerated. Suites that pin the authority to a constant pass only while the shared default equals the pin. Deliberate-drift tests already pass explicit values; a `None` default that resolves keeps them untouched.
4. Classify a suspected host sensitivity before assigning cause. Run the failing nodes (a) in the CI-like masked environment, (b) in the host environment, and (c) pristine, with the proposed change reverted. Record the first cause of each failure before the next attempt; do not re-run a failing check without a recorded first cause.
5. Declare completion only when the previously failing nodes pass on the divergent host in classes (a) and (b), and probes of the pinned suites match the pristine result.

Measured branches from the verification case:

- Constant default versus process-derived authority: the session fixture mapped the principal lookup to the process euid, so the hardcoded default owner agreed with the authority only on the builder image. On a host with a different euid, every comparison under test failed closed: six nodes reported owner drift at the identity comparison, five were rejected as foreign evidence at a second guard, and one cascaded to a capacity-limit error when a rejected terminal record could not free a claim. Minting the owner through the resolver fixed all twelve nodes; the full module then passed.
- Pinned sibling suites: three other modules pin the same resolver to the constant on purpose. Changing the shared factory default to resolver-minted values made the fabricated evidence disagree with the pinned side: 75 tests failed with drift from the pinned value while pristine runs of the same nodes passed. The change moved into the local helper of the affected module, and both the fixed module and the pinned suites passed.
- Stub-following import style: the failing variant bound the resolver at import time, so even pinned suites observed the process euid through the helper. The accepted variant imports the module and calls the attribute at call time, so pins, session fixtures, and the live resolver all apply as each suite intends.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Shared-default fix | Changed the shared evidence factory default from the constant to resolver-minted values. | Every suite that pins the resolver to the constant failed: the fabricated evidence disagreed with the pinned authority (75 failures; the same nodes passed pristine). | Enumerate authority-pinning consumers before changing a shared default; fix the local call site when pins exist. |
| Import-time binding | `from package.authority_module import resolve_identity` in the helper. | The helper kept the pre-stub reference; `monkeypatch.setattr` on the module attribute had no effect, and evidence followed the process instead of the pinned value. | Import the module and call the attribute at call time. |
| Copying the CI value | Kept the hardcoded constant that the green CI run shows. | Agreement was host luck: the constant and the process-derived authority coincide only on the builder image, so hosts with a different euid failed every guarded comparison. | Mint through the authority that the comparison uses, never from an observed value. |

## Results & Parameters

### Configuration

The only parameter is the evidence-field default contract:

```python
def make_evidence(context, *, owner_uid=None):
    # None: mint through the comparison authority at call time.
    # int:   explicit value, for deliberate-drift and pinned cases.
```

### Expected Output

- Previously failing nodes pass on the divergent host in masked and unmasked runs.
- Suites that pin the authority to a constant keep their pristine results.
- A shared-factory default change without a consumer enumeration produces drift failures on the pinned side; treat that count as the signal to move the fix to the local call site.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| A proprietary model-serving control plane (unnamed per the privacy policy) | Host-failure repair in a capacity-limits test module and three pinned-authority suites | Measurement detail in [the notes](test-evidence-mint-through-compared-authority.notes.md). |

## References

- [cross-host-identity-divergence-volatile-hash-inputs](cross-host-identity-divergence-volatile-hash-inputs.md) — the product-side boundary: identities several hosts must compute identically.
- [pytest monkeypatch documentation](https://docs.pytest.org/en/stable/how-to/monkeypatch.html) — why module-attribute access at call time follows `monkeypatch.setattr` pins.
