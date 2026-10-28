# Notes: Verify a Deployed Composition Delivers Its Contracted Error Behavior

Supporting evidence for `pr-review-deployed-composition-error-contract.md`. Project
identifiers, issue and pull-request numbers, file names, environment-variable names, and the
review artifact itself are omitted; the roles and the failure chain are preserved.

## Source context

A report-only, exact-head source review (corrective round two) of a target-routing feature in
a public open-source multi-deployment inference gateway. The feature lets a front-door service
forward a request to a registered destination deployment when a request header selects one. The
interface contract promises that an unavailable destination answers a specific `503` response
with a retry header, and the front-door service runs under a supervisor that renders a service
identity into each child process environment.

Round one verified the routing surface with substitutes injected at the caller seam and shipped
no defect. Round two traced the default composition production uses and found one major
defect. The evidence chain below shows how each check exposed a side of it.

## Evidence chain: environment class

| Link | Source-derived fact | Effect |
| ---- | ------------------- | ------ |
| Spawn | The supervisor builds each front child with the rendered service identity in its environment; a multi-worker launcher additionally writes the same fields into the process environment before workers start | The deployed host always carries one management-root variable and one deployment-identifier variable |
| Preconditions | The composed discovery resolver refuses to run when the management-root variable is set, and conflicts when the ambient deployment identifier differs from the resolved destination | The default wiring violates both preconditions on every remote-target request |
| Default wiring confirmed as production | No production call site injects the substitute seam the call offers | The default composition is the production composition; injected-seam tests did not grade it |
| Caller catch set | The caller maps only the domain unavailable error to the contracted `503` | The refusal and conflict raises escape to the framework default `500`: remote-target routing fails in deployment before any routing decision |

Local-target selections returned before the composition and were unaffected; absent-header
traffic was unaffected. Existing behavior was not degraded, which is why no regression suite
alarm fired.

## Evidence chain: unavailability class (environment-independent)

| Cause | Rest state | Raise in composed chain | Contract wants |
| ----- | --------- | ----------------------- | -------------- |
| Destination registered but not published (normal dependency-down state) | Record file absent | File-not-found error | `503` + retry header |
| Record malformed | Schema violation | Validation error | `503` + retry header |
| Record conflicts with its registration | Mismatch | Value error | `503` + retry header |

The caller's fallback branches that would have converted these causes were placed after the
raises that fire first; they were reachable only through a same-instant race. That shape
recorded the intent to convert the causes and the gap of the composition; the review cited it
as evidence of the defect, not of coverage.

## Evidence chain: the test gap that hid both classes

The two destination-record unit tests patched attributes on the caller module — the same
attributes whose real implementations raise under exactly the stated conditions. Other tests in
the same file faked the genuine external boundary instead (record files under a temporary
path). So the mocked tests pinned a `503` mapping the real composition does not deliver, and
no test ran the resolver under an environment that carried the host identity variables.

## Corrective sketch accepted by the review

- Resolve the destination from the registry entry without the client-discovery environment
  contract: pass an explicit minimal environment, or read the destination spec and the record
  through the registry readers directly.
- Convert every destination-not-servable cause to the domain unavailable error so the caller
  answers the contracted `503`.
- Add one real-composition end-to-end test per contracted outcome (registered-but-unpublished
  destination answers `503` plus retry header and no backend call), and one resolver test under
  an environment that carries the host identity variables.

## Duplicate-analysis record

Corpus inspection at revision `90ce47e9650dc0380aa9ae91721e7d722dfef328` (upstream refresh
verified) grouped and read the nearest entries; none covers this intent:

- `resilience-circuit-breaker-error-translation` — author-side wrap-and-translate guidance for
  a new boundary. No reviewer trigger, no environment precondition check, no raise-to-contract
  mapping, no mock audit.
- `testing-shared-host-env-pinning-and-baseline` — pins shell environment for reliable suite
  execution on a shared host; opposite direction of the environment axis.
- `testing-env-leak-local-fail-ci-pass` — ambient environment leaks that make local tests fail
  where CI passes; not a deployed-process precondition review.
- `planning-test-coverage-verify-premise-and-mock-targets` and
  `tdd-workflow-and-test-coverage-expansion` — authoring-side mock-target guidance; no review
  workflow and no deployed-environment check.
- `silent-boundary-observability-exception-classification` — logging classification at broad
  exception boundaries; not a contract-status mapping review.
- Review-family entries checked for overlap: `agents-pr-review-evidence-discipline`,
  `verification-evidence-audit`, `create-review-checklist`,
  `code-review-before-merge-workflow`, `external-request-boundary-invariants` — none traces a
  deployed composition against a contracted failure status.
- Open pull requests changing `skills/*.md` at analysis time (numbers 3581–3624): none creates
  or amends this intent; no amend-lock target.

Disposition: `create` — materially different trigger (review of a deployed composition),
failure mode (environment precondition plus unmapped raise inventory), and decision branches
(three checks) versus the author-side translation entry.
