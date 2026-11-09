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

## Exclusion-by-construction evidence (v1.1.0)

Supporting evidence for the design-time branch. Shapes are generalized; the
decision rule is the artifact.

- A policy model feeding a full-dump serialized-identity digest
  (`model_dump(mode="json")` with no `exclude_*` switches) gained a serving
  knob that had to leave every existing record byte-identical while unset.
  The same model already carried two exclusion-declared optional fields
  (`Optional`, `Field(exclude_if=lambda value: value is None)`), a
  family-local convention whose admitted digests had never rotated on those
  fields.
- Probe evidence, two lines, bound the mechanism: dumping a validated
  instance with the field set showed the key with its value; dumping a
  default instance showed the key absent. A defaulted non-optional field
  would have appeared with its default and rotated every existing digest —
  the near-miss the branch exists to prevent.
- Lock-in came from three focused tests, not a golden vector: a
  serialization-invariance test asserting the unset field's key is disjoint
  from the dump, a parametrized field-limits contract test sharing the
  family's bounds, and a presence/absence render test on the one consumer.
- The exporter-regenerated schema companion showed exactly the new field's
  block and nothing else; no byte-sync gate existed for that generated file,
  so the diff itself was recorded as the change evidence.
- The same model's other family (always-serialized per-stage timeouts)
  stayed on the re-admission rule from v1.0.0; the two conventions coexist
  because each is applied per family, never averaged.

## Digest-projection exclusion across multiple owners (v1.2.0)

Supporting evidence for the multi-owner projection branch. Identifiers, paths,
digest values, and issue references are generalized; the decision rule is the
artifact.

- A deployment policy model gained a defaulted, non-optional operational timing
  field. The field must stay in the schema and in the public status projection,
  so the exclude-when-unset branch did not apply.
- The model feeds three independent identity families:
  - a recipe and checkpoint binding digest over the full model dump;
  - a runtime-contract digest over the resolved model and the nested policy
    model;
  - a launch-identity digest with an existing top-level exclude set.
- The full dump put the field in two positions: the top level and every entry
  of a nested per-scope override map. The override entries serialized the
  field as `null` when the operator did not set it. A top-level pop alone left
  the nested copies in the digest.
- The recipe and runtime-contract owners shared one strip helper. The launch
  identity kept its existing exclude set because that set already drops the
  whole nested override map.
- The helper builds new nested override mappings. A caller that passes a
  shallow mapping copy keeps its own nested dictionaries; an in-place nested
  pop would mutate the caller.
- The first invariance test for the runtime contract changed the target
  override but replaced the whole override map. The sibling override
  disappeared, so the digest changed for an unrelated reason and the test
  failed as a false positive. Preserving every sibling override and changing
  only the target key fixed the test.
- Per-owner invariance tests changed the top-level field and one nested
  override and asserted an unchanged digest. A mapping-mutation test asserted
  that the caller keeps its nested override value.
- Verification: the focused identity and policy suites passed, the generated
  schema showed only the new field, and the full repository checks passed in
  CI.
