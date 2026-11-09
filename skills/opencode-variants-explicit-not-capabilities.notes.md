# Notes: opencode-variants-explicit-not-capabilities

Privacy-safe supporting evidence. All deployment-specific names, internal
paths, and model-family identifiers are omitted. Describe the intent with
public terms: one self-hosted OpenAI-compatible serving gateway and its
agent-host provider extension, from November 2026.

## Measured evidence

### Probe 1 — declared-vs-explicit surface

- Registration form A: every model entry carried
  `capabilities.reasoning = { supported: true, effort: [...] }` plus, where
  applicable, a toggle.
- Listing after install: the model entries showed an empty variants list.
- Registration form B (same entries, variant list explicit): each offered
  level appeared in the listing.
- A live model-selection attempt confirmed an unoffered variant id fails at
  resolution, so absence is provable and not provider masking.

Root cause evidence from host inspection: for the OpenAI-compatible provider
package, only a built-in provider builds capability variants; other provider
IDs pass capability blocks through a dispatcher that emits nothing. The
toggle flag (off switch) has no builder in this path.

### Probe 2 — engine behavior per channel

On a live serving engine (public open-source chat API path at the pinned
release):

- The request protocol funnel accepts one superset enum of effort levels
  (validated at protocol level) plus a numeric value in (0,1).
- Template rendering merges the top-level field into the chat-template kwargs
  before rendering.
- A template that says `default(X)` and reads a variable never sees a bad
  value silently: a value it does not accept either raises a hard exception
  or is coerced to the default.

Family-specific evidence (anonymized):

- Family P (protocol-field channel, five levels plus none): one live model's
  reasoning token count was monotone except at the top two levels, and none
  returned zero reasoning tokens. The lowest offered level was kept above the
  level that measured equivalently as it.
- Family Q (template channel, three levels): no live replicas while writing.
  Published as card-verified with an UNVERIFIED marker in code comments.
- Family R (template channel, three levels including max): template coerces
  anything outside low/high to max default, so middle and off levels are
  impossible operations that read as max.
- Family S (template channel, same parser as R): five of six checksums are
  identical (raise); the sixth coerces an unsupported level to a fast-think
  mode. Comments and commit text match the measured behavior per checksum,
  not the hypothesis.

### Deployment defect recorded, not shipped quietly

One card-documented level measured near-zero reasoning tokens (below a lower
level) on the live deployment. It stays visible in the offered surface
because the decision was to ship card-exact levels, and the measurement is
recorded in a code comment. A separate follow-up is the correct remediation,
not hiding the level.

## Verification receipts (sanitized)

- Syntax check on the installer file: exit 0.
- Plugin generation against a sandbox home: exact variant JSON surface for
  every family, including an exact-id guard that keeps a sibling checkpoint
  from the wrong prefix out of the surface.
- Live listing receipt: every offered level appears per family.
- Two level-selection runs now succeed where unknown variants previously
  failed at resolution.

## Policy notes

- The repo removed script-targeted contract tests in a recent cull; the
  lesson learned is that verification for a plugin generator is execution
  receipts (listing probes and sandbox installs), not a test-file extension.
- Rollback truth: the generated-user-plugin restore only recovers the
  pre-first-install state. For a user with an existing install, rollback is
  re-running the previous release's installer. Record this whenever a rollout
  plan cites the restore path.
