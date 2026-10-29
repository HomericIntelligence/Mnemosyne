# Notes: Descriptor-Digest Re-Admission vs Exclusion After Additive Fields

Supporting evidence for `descriptor-digest-readmission-additive-fields`. Internal
identifiers, digest values, and paths are generalized; the decision rule is the
artifact.

## Evidence shape

- A change added three defaulted fields to a lifecycle-policy model. A golden-vector
  guard for a registered target serialized the full deployment spec
  (`model_dump` with `by_alias=False`, `exclude_none=False`,
  `exclude_defaults=False`, `exclude_unset=False`), so the admitted descriptor
  digest rotated: `/tmp`-local reproduction `old != new`, and an independent
  label-triggered CI shard showed the identical actual value in its assertion.
- Convention evidence: the same model already carried a five-member operational
  timeout family (candidate-ready, quiesce, drain, term, reap). Those fields had
  always been inside the admitted digest. No exclusion or allowlist projection
  existed anywhere in the descriptor assembly.
- The guard's own provenance comment described rotation as a deliberate
  re-admission event, "recomputed on the admitting tree", from an earlier
  alignment. The same wording was extended to name the new cause.

## Why re-admission won, in one paragraph

The envelope's established contract is "the full spec is the identity". Additive
fields that change serving behavior are identity-relevant under that contract.
An exclusion for exactly the new fields would have created a second, unwritten
rule ("some operational fields count, some do not"), weakened the deliberate-event
guarantee for the next additive change, and made the guard less capable of its
purpose: making admissions visible. Rotation plus records preserves one rule.

## Reproduction command shapes (generalized)

```bash
# Attribution: base passes, head fails.
git worktree add <base-wt> <merge-base> && (cd <base-wt> && pytest <guard-suite> -q)
pytest <guard-suite> -q   # at the branch head

# Recompute with the guard's own helpers (import them; do not re-implement).
python3 - <<'PY'
from tests.<guard_module> import _load_spec, _digest, _identity
spec = _load_spec("<spec-name>")
d = _digest("<registry-entry>", spec)
print(d)
print(_identity("<target-kind>", d))
PY
```

Match the printed values against the failing assertion's actual values before you
bind them. Byte equality across your run and CI is the attribution proof.

## Gate-list wording that stuck

Record the suite as a permanent line in the change's test-plan section, with the
verbatim command and result. The review's finding attached to the suite gap was
closed only when the gate list named the suite, not when the suite turned green.

## Adjacent adjunctions recorded during the same round

- A fixture-style boundary suite was umask-sensitive through a pre-existing
  directory-validation rule: it failed 7-of-9 under `umask 002` and passed 9-of-9
  under `umask 022`. Matching an earlier review's record avoided a false
  regression chase; the sensitivity predated the change.
- A foreign static-analysis family (5 diagnostics, tests-only) was shown
  byte-identical between base and head and was carried as pre-existing debt until
  a sibling change healed the base; after that rebase, the full check reported
  zero diagnostics. Defer to the existing pre-existing-gate-failure entry for
  the classification discipline.
