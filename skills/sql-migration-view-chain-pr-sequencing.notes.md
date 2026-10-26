# Notes: SQL Migration View-Chain PR Sequencing

Concrete guard and renumbering patterns from the verified case. Replace `<shared_object>` with the
redefined view or table, and `<vN>`/`<vN+1>`/... with the chain's stem numbers.

## Guard 1 — defining-set enumeration (fail loudly on a new definer)

Scan the migrations directory once. An object is "touched" when its name appears in a migration;
it is "defined" when the redefinition statement appears. Every migration that touches the shared
object must define it, and the defining set must equal an explicit list:

```python
pattern = re.compile(r"create\s+or\s+replace\s+view\s+<shared_object>", re.I)
touching, defining = {}, {}
for path in MIGRATIONS.glob("*.sql"):
    text = path.read_text()
    if "<shared_object>" in text.casefold():
        touching[path.stem] = text
    if pattern.search(text.casefold()):
        defining[path.stem] = text
assert set(defining) == set(touching)                      # no shadow touchers
assert sorted(defining) == [*STATIC_PREFIX, "<vN>", "<vN+1>", "<vN+2>"]   # loud on arrivals
```

When a fourth definer legitimately arrives, its own PR must extend the explicit list in the same
change — reuse shows up as a test failure, never as silent shadowing.

## Guard 2 — monotonic literal prefix

For chain members whose redefinition carries literal rows (`VALUES (..., ...)`) in previously
semantically-static positions, extract tuples per stem and require each earlier stem's row set to
be a subset of the next stem's set across the STATIC prefix only:

```python
def rows(stem):
    return dict(re.findall(r"\('([^']+)', '([^']+)'\)", defining[stem]))
for previous, current in itertools.pairwise(STATIC_PREFIX):
    assert rows(previous).items() <= rows(current).items()
```

Do not extend the pairwise check across the boundary where the chain becomes dynamic (a projection
or fleet-driven replacement); parse-literal row sets are not comparable there. Pin dynamic members
with behavior tests at the database instead.

## Guard 3 — behavior tests bind the final definition only

Database-level tests assert the effect of the highest-stem definition: seed-table content,
projection coverage (entities visible after one state report with no row threshold), alias
canonicalization (`COALESCE(canonical, raw)` keeps unaliased names visible), and data preserved on
both install paths (empty database == upgraded template catalog fingerprint).

## Guard 4 — order-free ledger/receipt assertions

Ledger-style integrity tests assume receipts are recorded "blocked-first, late-arrival inserted
later"; compare as sets or sort:

```python
assert [s for s in after if s != LATE_STEM] == sorted(before + [p.stem for p in blocked])
```

Any new stem sorting after the last blocked dependent otherwise breaks the assertion even though
the ledger contents are correct.

## Renumber checklist for chain delivery

1. Pick stems so lexical order == semantic layering; the final definition owns the highest stem.
2. Rename the migration FILES, then update every in-repo reference: test file constants and
   index lists, index/docs enumerations, seed markers like `VALUES ('0100_...')`, and provisioning
   or onboarding docs that cite a stem.
3. Re-resolve prose sentences that mention the old numbers ("migration `0099` derives ...") —
   global search for each changed stem string, not only the filename.
4. Re-run the migration-guard tests locally; they must enumerate exactly the final chain.
5. Rebase each branch onto current main in low-stem-to-high-stem order; compose conflict
   resolutions semantically (union additive constants, fold upstream row additions into literal
   redefinitions) rather than taking one side.
6. Arm only the lowest-stem open PR's auto-merge; after it lands, disarm/re-arm the next one up.
