# Notes: Unbounded Primary Request, Bounded Diagnostic Requests

Supporting evidence for `unbounded-request-diagnostic-timeouts`. Project names,
model identifiers, endpoints, credentials, repository paths, and review
identifiers are omitted. The reusable timeout policy and failure shape are the
evidence.

## Source failure and repair

- A provider-neutral evaluation client used a finite probe timeout for a
  deterministic capability control. Slow valid serving pools exceeded that cap.
  The requirement removed the cap from the capability control only. Discovery
  and runtime request bounds had to stay unchanged.
- The first implementation changed the shared preflight default to the
  transport's unbounded sentinel. A review traced the value through primary
  failure handling. The transport sequence showed unbounded primary and
  fallback controls, followed by an unbounded model-inventory diagnostic.
- The inventory call was not an approved unbounded operation. It inherited the
  sentinel through remaining-budget and error-classification helpers. This
  created an indefinite-wait path and contradicted the documented discovery
  bound.
- The repair mapped the unbounded primary value to the established finite
  discovery default at both inventory-revalidation call sites. Explicit finite
  callers kept their remaining-budget behavior. A separately classified route
  confirmation retained its intentional unbounded policy.
- Widening the timeout type also exposed a direct comparison between the new
  sentinel and zero in route-confirmation deadline handling. Existing route
  tests detected it. The guards became `None`-safe without changing explicit
  expired-deadline behavior.
- A new regression forced the primary failure that triggers inventory
  revalidation. It asserted nonempty observations, unbounded primary controls,
  and finite inventory calls. Existing explicit-deadline tests remained green.

## Verification boundary

The repaired source passed its focused suite, complete repository checks, and
independent implementation review. Live validation discovered the served model
set at run time and completed non-strict generation for every discovered model.
Strict runs retained their documented failure contract. Published evidence was
sanitized.

The delayed-transport check also confirmed that the source transport interpreted
its `None` timeout as blocking behavior rather than as a hidden finite default.
This is transport-specific evidence, not a universal library guarantee.

This knowledge entry itself has local corpus validation only until its own pull
request checks report a result. No source repository identifiers or access
material are needed to apply the rule.

## Corpus comparison

The existing timeout-hierarchy entry sizes finite guardians around one total
request arbiter. The external-request entry covers provider accounting and
per-attempt boundaries. The failure-diagnostics entry covers bounded state
reconciliation and causal evidence. None covered an intentionally unbounded
primary operation leaking its sentinel into a bounded diagnostic error path.
This entry records that distinct trigger and repair without replacing those
rules.
