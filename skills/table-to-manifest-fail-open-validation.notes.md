# Notes: table-to-manifest-fail-open-validation

Supporting evidence for `table-to-manifest-fail-open-validation`. The main skill
carries the rules. This file carries the measurements and the verification
reports.

## Scale of the migration

| Parameter | Value |
| --------- | ----- |
| Source module size before | about 8,800 lines |
| Source module size after | about 6,300 lines |
| Lines removed by the move | about 2,700 |
| Tables moved | 6 static tables plus 1 context-bound family group |
| Rows in the frozen baseline | 296 |
| Rows per table | 247 / 9 / 9 / 5 / 11 / 8 / 7 |

## The four fail-open classes, as observed

Each class was present in the first delivery and was closed before merge.

1. **Document-level placeholder validation.** The original check raised only when
   an unknown token existed *and* no deferred token remained. A value shaped like
   `deferred/segment/unknown_token` therefore passed. The replacement checks each
   token against the declared deferred set and refuses any token that neither the
   supplied values nor the deferred set names.
2. **Unknown selector returns the empty tuple.** The lookup mapped an unknown key
   to `()` and cached it. A typo produced an empty policy table rather than an
   error, so a caller could believe it had a policy set of zero rows.
3. **Duplicate order value.** Rows carried an explicit `order`. Two rows sharing
   a value sorted in an arbitrary but stable-seeming order, so the effective
   sequence depended on sort stability rather than on the declaration.
4. **Unmappable row dropped.** The family expansion mapped only names present in
   a hard-coded sequence. A new row in that group was silently skipped.

A fifth case appeared in the generator: it `continue`d on a pattern it could not
map, which would have emitted a manifest that silently lacked a rule.

## Baseline fixture discipline

The fixture was first generated on an older base. After a rebase, the base had
removed two rows. The fixture then asserted rows that no longer existed. The
repair was to regenerate the fixture from an export of the current base commit
and to compare against that export, not against the working tree.

The regeneration command shape:

```bash
# Export the base commit into a clean tree.
git archive <base> | tar -x -C <clean_dir>
# Generate the fixture from the OLD tables in that tree.
cd <clean_dir> && PYTHONPATH=src python - <<'PY'
from module import tables
fixture = {name: [payload(row) for row in table] for name, table in tables.items()}
PY
```

This ordering matters: a fixture produced from the new loader proves only
internal consistency.

## Static typing of a dynamic module attribute

The public table names became module-level dynamic attributes. The type checker
rejected iteration over them when the resolver declared an `object` return. The
declared return type had to be the concrete table type. Separately, a test that
substituted a table by attribute assignment continued to take effect only because
the accessor read the module namespace before falling back to the file.

## Packaging proof

Two independent build paths had to carry the file:

- the wheel configuration that force-includes repository files into package data;
- the container build, whose context copies each data source explicitly.

The container build failed first, because the forced include named a file the
build context did not contain. Extending the image smoke check to load the
packaged copy and to build one table makes a future omission fail at image build
time instead of at run time.

## Deployment comparison

The strongest evidence compared the merged manifest against the running
deployment's module, not against the branch:

```text
for each table:
    deployed_rows = [payload(r) for r in deployed_module.table]
    merged_rows   = [payload(r) for r in merged_accessor()]
    assert deployed_rows == merged_rows
```

The deployed release predated the merge, so it still held the compiled tables.
That made it a genuine oracle. Every table matched exactly. The same comparison
can be run in reverse after a release, to prove the deployed copy still agrees.

## Verification record

- Baseline equivalence: all 7 tables, 296 rows, every field equal.
- Regression comparison against a clean export of the base commit: zero new
  failures in the primary test module.
- Fail-open probes: each of the four classes now raises.
- Generator round-trip: byte-for-byte equal to the committed file.
- Artifact: the manifest was present inside the built wheel and loaded from
  package data.
- Deployment: all tables equal to the live release's tables.
- Full check set on the merged commit: 79 success, 3 skipped (conditionally gated
  jobs), 0 failure.