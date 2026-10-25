# Notes: enumerated-registry-assertion-drift

Privacy-safe session evidence for the skill. Facts from the v0.2.4 drive on
LLM360/comet, 24–25 October 2026, during a multi-lane merge wave.

## The observed event

- Promotion PR LLM360/comet#2951 (main → prod) CI at head `735a2ac0` showed
  ~26 of 30 `postgres-full-shard-*` jobs red plus the two rollup gates
  (`postgres`, `lint-typecheck-test`).
- Failing assert class (example, shard 0):
  `{"error_kind":"AssertionError","line":2109,"path":"tests/postgres/test_migrations.py","phase":"call"}`.
  Line 2109 is inside `_resource_predecessor_migrations` and asserts
  `await db.apply_migrations(connection, MIGRATIONS) == [<exact ordered list>]`.

## Drift producers (append without test sync)

- `b2d09eb1` `feat(release): publish the viewer behind a fenced blue-green
  handoff (#963) (#2942)` — added `migrations/0092_release_viewer_publication.sql`
  and `0093_viewer_writer_fence.sql`; no test changes.
- `d7252763` `feat(release): add recovery rollback cancel and cleanup (#3069)`
  — added `0095_release_operation_recovery.sql`.
- `522d3a71` `chore: [feature]: correct partial-node accounting for public
  model pools (#2943)` — added `0096_fleet_node_accounting.sql`.

## The partial repair

- `1832b3c7` `fix(ci): repair deterministic main test failures after
  parallel merges (#3030)` extended the expected lists through 0094
  (`VIEWER_SAME_STATE_UPDATE_MIGRATION`) and added nothing for 0095/0096.
  Verification: `git show origin/main:tests/postgres/test_migrations.py`
  grep for the 0095/0096 stems matched nothing in the expected lists;
  `git ls-tree origin/main --name-only migrations/` shows both files
  present. The expected lists therefore trail the registry by two entries
  at merge time, which reproduces the class exactly.

## Correct repair shape (proposal-grade)

- Bind diagnostics to the ref: `git ls-tree`/`git show`, never the
  incumbent working tree. In the source engagement, a stale working-tree
  `ls migrations/` first suggested that 0092+ were absent; the ref-bound
  listing showed 0091–0096 present and inverted the conclusion.
- Sync the expected lists to the complete stem set (0091–0096 stems) in
  the same change.
- Add the drift guard in the same change: one cheap check that diffs
  `migrations/` stems against the test expectation constants and fails
  with the exact missing/extra stems. `scripts/ci`-adjacent placement
  matches the repository's existing convention checks; see the linked
  convention-guard skill.

## Context that matters for retrieval

- The same red main blocked a review-GO'd promotion PR whose automerge was
  armed: review and merge gating are independent, but the merge queue
  never proceeds until required checks are green.
- The per-lane review of each drift-producer PR could not see the future
  break, because each lane's adding commit did not touch the asserting
  tests; this is why reviewer blocking of unsynced registry appends is the
  operative rule.
