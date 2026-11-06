# dataset-tree-readback-validator — notes

Supporting evidence for the main entry. These details explain why each check
exists; the main entry keeps the rules.

## What the audit found on the captured tree

Bound to one revision of a published measurement dataset: 6 model groups,
63 cells, 1375 points, 4125 leaves, about 816 MB.

| Finding | Count | Severity | Notes |
| --- | ---: | --- | --- |
| Points without exactly three repetitions | 0 | — | The contract held. |
| Leaves that did not decode | 0 | — | |
| Summary documents with stale totals | 5 of 6 | ERROR | One document held totals from the first small batch: it stated 87 points where the tree held 182. |
| Summary documents with stale per-group rows | 5 of 6 | ERROR | Every stale document listed one placement group at 2 points while the tree held 22 to 25. |
| Units whose repetitions disagreed on output length | 1 | ERROR | One repetition produced one fewer token than its two siblings. |
| Records using a second key shape | 6 | WARNING | All from one group produced through a single-request code path. |
| Records omitting an identity field the directory encodes | 6 | WARNING | Same six records. |
| Achieved length below requested length | 493 | WARNING | The server stops short on very long decodes. |
| Interval series shorter than the tokens produced | 1623 | WARNING | One runtime reports fewer intervals than tokens. |
| Repetitions disagreeing on interval-series length | 509 | WARNING | Same runtime; each repetition reports a different count. |

The second key shape is the important detection case. The publisher is a
passthrough: it strips packaging fields and adds derived statistics, and it
assumes the input already has the standard shape. A different upstream path
supplied a leaner record, so the published group differed from every other
group in the tree while `upstream` timing data stayed identical. Nothing in
the write path noticed.

## Why a count histogram first

The first pass printed a histogram of leaves per point for every group. It
returned one bucket, `3: N`, for all groups. That immediately closed the
question the reviewer asked and left the audit free to search the other
invariants. Running the same histogram again later exposed the single
cross-repetition mismatch, because a histogram over units hides a difference
inside a unit.

## Two verdicts for one observation

Before the validator existed, the same physical condition was recorded two
ways in the published tree. A group of 35 points stated `passed: true` with
full statistics; 77 sibling points with the identical two-token shortfall
stated `passed: false` with a bare reason list. The older records were written
before a gate was relaxed, the newer ones after. Both were intentional, and
both were documented in an operational ledger, but no tool could report the
inconsistency because no tool read the tree.

This is the general lesson: a relaxed gate that leaves a marker unchanged
creates two populations in one tree. A read-back validator should print the
population counts so the difference is visible even when both are accepted.

## Why warnings are not errors

The shortfall conditions are produced by the source systems. Treating them as
errors would make the gate permanently red and hide the defects that are worth
fixing. Each gets a stable code, a count, and an `--allow` switch. Accepting a
code keeps the check running and keeps the finding counted, so a change in
its rate is still visible.

## Non-vacuity check

The proof used a copy of one group with three deliberate edits:

```text
rm <point>/run3_results.json.gz      -> POINT_RUN_SET
echo "not gzip" > <point>/run2_results.json.gz -> LEAF_UNREADABLE
edit a stated total                  -> README_TOTALS_STALE, README_ROWS_STALE
```

Each code appeared, and the exit status changed from 1 to 1 with a higher
error count. The copy was discarded. Without this step a validator that
always returns clean is indistinguishable from a correct one.

## Repair order

1. Regenerate summary documents from the tree.
2. Re-run the validator and confirm only real data defects remain.
3. Report remaining defects to the owner; do not change records to make the
   validator pass. A validator that is satisfied by editing the evidence is
   not a validator.