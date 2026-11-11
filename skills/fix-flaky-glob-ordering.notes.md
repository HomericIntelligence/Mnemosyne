# Session Notes: Fix Nondeterministic Enumeration Order

## Session Date

2026-03-05 (single-process case); 2026-11-11 (cross-process case)

## Single-process case

A named-tensor collection test failed on CI on one date and passed earlier with
identical code and compiler version.

Root cause: the loader used an unsorted `p.glob("*.weights")`. The assertion expected
`loaded[0].name == "weights"`, which held when the OS returned that file first and
failed when another file came first.

Fix: sort at the source. In Mojo, `Python.import_module("builtins").sorted(...)`.
Then swap the assertion order to alphabetical.

Second failure: the first attempt used a bare `sorted()` in Mojo and did not compile.
The `link-check` failure on the same pull request was pre-existing.

## Cross-process case

A redaction export ran over a large corpus of session logs. The first attempt was one
process that kept its manifest in memory and wrote it only at the end. It failed with
exit code 1, empty stderr, and no completion record, so the whole run was discarded.

Measurements that ruled causes out:

| Probe | Result |
| --- | --- |
| Largest single input in isolation | Peak RSS about 80 MB, exit 0 |
| Sixty ordinary inputs | Peak RSS about 30 MB, exit 0 |
| Three inputs larger than 1 GB in one process | Exit 0, manifest written |
| Live process during a sliced run | Flat RSS about 43 MB |
| Free space at failure | Hundreds of TB |

The job's reported peak RSS, about 30 GB, did not belong to the exporter. That
reading was never explained from node-level evidence and is recorded here as unknown.

The replacement ran each slice as its own process with its own output directory,
exit code, and log, and marked a completed slice with a marker file so a re-run
skipped it. All slices then completed with exit 0.

## The partition defect the slicing exposed

The first sliced version built its groups from a sorted listing:

```python
names = sorted(os.listdir(stage))
groups = [names[i:i + size] for i in range(0, len(names), size)]
```

A single-task mode rebuilt the same groups from a fresh `os.listdir()`. Sorted order
was stable within one process, but the array tasks and the single-task runs saw
different listings, so task N processed a different set than the design assigned.

Signature: every slice reported the expected number of items and exit 0, while the
union across slices left 264 enumerated items unprocessed and processed 264 others
twice. Name comparison showed the two sets were equal in size and different in
membership.

Fix: bucket by the item's own identity.

```python
bucket = int(hashlib.sha256(name.encode("utf-8")).hexdigest(), 16) % N
```

This makes the partition a pure function of the name, identical in every process.

## The false-gap defect

A gap check compared enumerated names with the identifier each writer stored. That
stored identifier came from the path *after* redaction, and the redaction rule for
payment-card-shaped digit runs rewrote some hash-like filenames. The comparison
therefore reported a gap that did not exist, and a "gap fill" re-exported items that
were already present.

Symptom: the derived gap count was nonzero, while every gap item's output was already
in the merged tree.

Resolution: coverage was proven by exporting one enumerated item independently and
comparing it byte for byte with the merged copy. They were identical. The comparison
was then rewritten to use the untransformed identity.

## Final verification

| Field | Value |
| --- | --- |
| Enumerated sources | 56,931 |
| Unique outputs | 48,485 |
| Manifest rows | 48,485 |
| Unmanifested files | 0 |
| Outputs missing from disk | 0 |
| Records | 31,247,606 |
| Redactions applied | 58,959,491 |

The difference between sources and outputs is genuine duplicate content: the same
sessions appeared in more than one input family.

## Reusable commands

Count-only checks that cannot detect a membership defect:

```bash
find "$STAGE" -type l | wc -l
ls "$OUT"/*.jsonl | wc -l
```

Use them only after a name-based check has passed. Name-based coverage:

```bash
sort <(ls "$STAGE") > /tmp/staged.txt
sort <(jq -r .source_identity "$OUT/_manifest.jsonl") > /tmp/claimed.txt
comm -23 /tmp/staged.txt /tmp/claimed.txt
```