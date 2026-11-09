# Notes: pydantic-discriminator-multi-variant-state

Supporting evidence for the main skill. Generalized per privacy rules: no
repository names, issue identifiers, paths, or payload values.

## Source change

An internal deployment-state repository had a state document with two
historical schema variants. Older writers produced one mapping shape; newer
writers produced a different mapping shape, with a shared field that only
the new shape requires. A runtime defect wrote provenance of one variant
into the active document of the other variant. At the next boot, every
reader validated the document against a raw Pydantic v2 `Union[V1, V3]`
alias and the process stopped.

## Measurements

- Raw-Union failure fan-out at the incident: 92 validation errors
  = 18 entities x 5 variant-shape errors each (90) + 2 true causes.
- After the callable-Discriminator change: the same poisoned fixture
  produced exactly the 2 true-cause errors. The location path of each
  failing error contains the variant tag literal, for example
  `('entities', '<entity-name>', 'v1', 'field')`.
- Tagged-union error locations in Pydantic v2 name the tag literal in the
  third tuple position; value mismatches that the tag selects keep type
  `value_error` at the leaf.
- 13 targeted tests: RED before the change (exact 92-count assertion),
  GREEN after (exact 2-count assertion plus tag edge cases and an
  identity-unchanged guard). Sibling module suites (1000+ tests) passed;
  the only failures were pre-existing host-environment conditions that
  failed identically on a pristine base worktree.

## Review evidence for the regeneration rule

The first review round of the merged change rated the missing JSON Schema
regeneration as a required finding: pydantic
(`_internal._generate_schema.tagged_union_schema` and
`_internal._json_schema`) emits `oneOf` for a callable-discriminated union,
while the checked-in generated schema still had `anyOf`. The merged fix
regenerated the checked-in file and refreshed a shared sibling schema that
the regeneration also touched. A second fresh review of the same head
produced the same finding independently.

Verify freshness with:

```python
generated = Model.model_json_schema()
# compare with the checked-in schema file
```

Discriminator-alias placement: both discriminated aliases (document-level
and map-level) appeared in the `oneOf` output of the regenerated schema.

## Tag-rule details

The verified tag rule, in order:

1. Instance checks on already-constructed model objects.
2. Mapping checks on raw payloads: the structural markers of each newer
   shape. The markers were shared-field presence checks, because the shared
   fields were stable across writers and required in the newer model.
3. Fallback to the earliest variant for unknown and future shapes.

A fallback keeps the message typed and actionable: an unrecognized document
fails against the v1 rules that it broke, with entity-level locations,
instead of an untyped `union_tag_not_found` error from a missed tag.

## Reader-message helper details

One shared helper served every reader of the document. The helper accepted
the document path, the raw payload bytes, and the `ValidationError`, and
returned a message with:

- the file path;
- the first failing location tuple, with the variant tag literal;
- the validator message, with content digests only, no payload values;
- the stable document identity (a content-addressed ID);
- a pointer to the recovery procedure in the operations guide.

Each reader raised its reader-facing error with `raise ... from error`, so
`__cause__` preserved the `ValidationError`. The supervisor-style status
reporter attached machine-readable file evidence (digest, size, owner
`st_uid`, `st_mtime_ns`, `st_ctime_ns`) reading the file once, so the stat
values and the digest described the same bytes. The operations guide stated
that `st_uid` names the file owner, not the writer.

Residual gap recorded after merge: the activation reader on an alternate
transition path still validated with a raw `model_validate`; a follow-up
issue tracks the same wrapper there. The gap shows the workflow rule: wrap
every reader, including migration and activation readers, not only the
primary boot reader.

## Writer-search commands

The writer enumeration that preceded the change compared the shipped
release tag with the current head:

```text
git grep -n <write-pattern> <release-tag> -- <boundaries>
git grep -n <write-pattern> -- <boundaries>
```

The writer sets at the tag and at the head matched exactly, so the plan
proceeded without unknown-writer risk. If the sets differ, stop and resolve
the unknown writer first.
