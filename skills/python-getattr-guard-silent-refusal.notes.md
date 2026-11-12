# Notes: python-getattr-guard-silent-refusal

Privacy-safe session evidence for the main skill. Names of people, hosts,
repositories, and internal identifiers are generalized; only shapes, sequences,
and counts are kept.

## Source case

A guard of the shape `_require_served_model(context, model)` was added to two
service-side commands. Its purpose: refuse a model name that the selected
deployment does not configure, before the command touches durable state.

First implementation:

```python
models = getattr(getattr(context, "policy", None), "models", None)
if models is not None and model in models:
    return
raise RefusalError(f"pool {model} is not configured ...")
```

The context type has no `policy` attribute; its policy hangs off `spec`
(`context.spec.policy.models`). Both `getattr` calls returned `None`, so the
membership check was never true, and every model - configured or not - was
refused.

## How the defect surfaced

- The guard's own suites passed, because their cases exercised refusal-shaped
  paths for unregistered models only.
- An existing service-side round-trip test failed on the first run with the
  guard's refusal for a declared model: the accept path had never been walked.

## Diagnostic sequence that worked

1. Direct probes of the accessor chain in isolation looked correct - because
   they rebuilt the object instead of using the runtime's object.
2. A temporary test printed the object the service actually passes:

   ```text
   PROBE ctx=RuntimeContext policy=None models=[]
   PROBE2 spec=RuntimeContextSpec specpolicy=RuntimePolicy models=['model-a']
   ```

   The first probe also showed the wrong guess (`ctx.policy` is `None`); the
   second located the real path on `spec`.
3. The accessor was corrected to `context.spec.policy.models`. The previously
   failing round trip passed immediately (10 passed), and two new parametrized
   cases for the refusal paths brought the suite to 12 passed.

## Non-vacuity evidence

With the guard call removed from both command sites, the two new refusal cases
failed (2 failed, 3 passed in that module). With the guard restored, all 12
passed.

## Related counts from the same round

- Guard module suites: 10 passed before the new tests, 12 passed after.
- Wider contracts touched by the same change (command matrix, transport
  refusals): 78 passed.

## Why the wrong accessor looked right

- Each `getattr` step had a `None` default, so the chain never raised and never
  revealed the wrong path.
- The guard's refusal branch was correct and well worded; only the data lookup
  was wrong. Review of the refusal logic could not find the defect.
- The failure mode was "refuse everything", which is easy to mistake for
  "the refusal test passes".
