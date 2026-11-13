# engine-argument-compat-before-launch — notes

Supporting evidence for the main entry. Nothing here is required for
retrieval; the main file carries the operative rules.

## Privacy-safe incident summary (generalized)

A model-serving platform pins engine command-line flags in one recipe per
model. One recipe combined three incompatible choices:

- an FP8-native sparse prefill kernel,
- a bfloat16 key-value cache data type, and
- a decode backend that requires bfloat16 on CUDA.

The engine checks these constraints only after it verifies the model
checkpoint. Each of several launch trials died after a multi-minute
verification phase, each with a different engine refusal:

1. the FP8-only prefill backend rejected the bfloat16 cache type;
2. the cache type moved to FP8, after which the decode backend rejected it
   as CUDA-incompatible;
3. a third decode backend rejected the produced index layout.

A valid recipe then carried the (bfloat16 cache, compatible prefill, same
family decode) combination, which also had a throughput measurement behind
it. Subsequent jobs started and registered.

The fix encoded the engine's three constraints as one shared check and ran
it at the config model validator and again at the launch-render pre-flight.
The render-level refusal prevents script creation. Behavioral tests refuse
each engine-refused combination (both flag spellings, and the
omitted-flag/default fill case), accept the measured combination, accept
the no-flags case, and prove the render leaves no script. The merged change
passed the platform's required checks, and both linked recipe issues closed.

## Why a new entry

Retrieval intent: attach a consumer's own cross-field argument rules to the
boundaries that run before launch, because the consumer checks them after
expensive startup. Nearest entries and the boundary where they stop short:

- `cli-flag-validation-prevent-silent-noop` (tooling, v1.1.0, verified-local):
  parse-time rejection of flags a selected backend silently ignores. This
  failure class is a silent no-op on a developer tool, at CLI parse time.
  The learn case is an engine that refuses only after a minutes-long GPU
  startup, on a production render path, and it contributes two additional
  constraints the older entry does not carry: engine default fill before
  evaluation, and a repeated render-time check for models built by
  update-copy paths.
- `config-validation-and-schema-alignment` (tooling, v1.2.0, verified-local):
  schema generation from Pydantic and schema wiring conventions. It validates
  shape and schema, not runtime-argument compatibility held only by the
  consumer.
- `fatal-check-downgrade-real-load-root` (architecture, v1.0.0,
  verified-local): convert fatal checks to warnings at the load root without
  accidental loss. The direction is opposite — this lesson keeps the check
  fatal and duplicates it onto the render path using one shared rule.
- `serving-pool-replica-outage-diagnosis` (debugging, v1.0.0; at discovery
  time an open pull request adds a startup-failure branch for replicas that
  never register): an operations-diagnosis workflow that reads the first
  engine error after replicas die. This lesson is the prevention side in
  config/render code: make the refusal precede the startup, so there is no
  outage to diagnose. The two intents are complements, not duplicates.
- An open pull request at the delivery base adds the diagnosis branch above;
  no open pull request changes the same file set as this entry.

## Inert flag family across an image change

A recipe pinned an engine's sparse-attention flag family (a prefill and a
decode backend pair), plus the flag naming the decode kernel. One image
served those flags. A review asked for the kernel flag to be removed on the
reasoning that the surviving pair selects it.

That reasoning held only on an engine whose source applies the model-profile
predicate for that architecture. The image's engine gated the whole flag
family on a family-membership predicate. A later release branch did not list
the architecture in that predicate, and it also carried no implementation
class for it. On such an image both flags are accepted, produce no error and
no warning, and the engine serves through its generic default kernel instead
of the measured one.

What made this hard to see:

- The configuration validated. The flags are syntactically valid on every
  revision.
- The render pre-flight recorded a drift warning and continued, which is the
  documented behavior for an engine-argument difference.
- The profile served in production with a floor that keeps a warm replica.
- The measurement that justified the flags came from the older image, so the
  evidence was real and no longer applied.

The durable checks that catch it:

- Classify each flag family as rejected-with-error or inert-without-error for
  the exact image source revision, not the current default branch.
- Name the flag that selects the behavior, so a deletion cannot re-expose an
  inherited default.
- Assert in a test that the naming flag is present, so a future edit that
  removes it fails in CI rather than in production.
- Record which rows are measured and which are open, including any row where
  the chosen path differs from the reference numerics.

## Verification record

- All platform required checks passed for the merged change that this entry
  generalizes (gate `implementation-go`, exact-head checks).
- Focused tests: accepted/refused combinations, both spellings, default
  fill, and the render boundary. Broader config, render, capacity, and
  deployment-surface suites pass.
- The platform's entire shipped recipe set loads without new refusals.

## Provenance binding

Created at delivery base revision `d33ae7500bbfe9fe029b606420bcdd1708692fb3`
of the knowledge repository, verified clean and refreshed. Private project
identities, model identifiers, issue and job identifiers, infrastructure
paths, and exact metrics are intentionally omitted; durations are stated in
the approximate form the engine behavior exhibits ("several minutes").
