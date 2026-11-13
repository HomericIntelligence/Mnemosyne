---
name: fix-flaky-glob-ordering
license: BSD-3-Clause
description: 'Fix nondeterministic filesystem enumeration order, in a single process or across
  processes. Use when: (1) a test passes sometimes and fails other times with identical code and
  asserts on file order; (2) parallel tasks partition work by position in a directory listing and a
  re-run of one task exports different items than the design assigned; (3) coverage or gap checks
  compare a stored record against an enumerated set and report a gap that no missing output
  confirms; or (4) a stored identifier is derived from text that a redaction or transform rewrites.'
category: debugging
date: 2026-03-05
version: 1.1.0
user-invocable: false
---
## Overview

| Field | Value |
| ------- | ------- |
| **Problem** | Directory enumeration order is not guaranteed. Code that depends on it breaks, either intermittently in one process or systematically between processes. |
| **Root Cause** | `pathlib.glob()`, `os.listdir()`, and `os.scandir()` return an OS- and filesystem-dependent order. The order can differ between two processes on the same directory. |
| **Fix** | Sort before use. For a partition that several processes must agree on, derive each item's bucket from the item itself, not from its position in the listing. |
| **Related** | A stored identifier derived from transformed text does not match the untransformed source, so a set comparison against it gives a false gap. |

## When to Use

- A test fails on some CI runs but passes on others with **identical code and compiler version**.
- The test loads several files and asserts on index-based order (for example `loaded[0].name == "weights"`).
- The loading function uses `pathlib.glob()`, `os.listdir()`, or `os.scandir()` without sorting.
- The failure is intermittent, for example passed on one date and failed on another with no code change.
- **Several processes must agree on who processes what.** Each task of an array job, or each worker,
  takes a contiguous slice of one listing and the slices must be identical in every process.
- **A coverage check reports a gap** that no missing output confirms, or reports that every count
  matches while the names do not.

## Verified Workflow

### Single process: sort at the source

1. **Confirm the root cause.** Check that the loading function iterates the listing without sorting.
2. **Fix the source function, not only the test.**
   - In pure Python: `sorted(p.glob("*.weights"))`
   - In Mojo through Python interop: `Python.import_module("builtins").sorted(p.glob("*.weights"))`
3. **Determine the sorted order.** Alphabetically, `"bias.weights" < "weights.weights"`.
4. **Update the test assertions** to the now-deterministic order.
5. **Verify no other caller** depends on the previous order.

### Several processes: derive the bucket, do not slice a listing

A contiguous slice of a listing is a different partition in each process. The two
listings can hold the same names in a different order, so task N processes one set
in one run and a different set in the next. The total count still balances, which
disguises the defect: the union of the tasks can miss some items and export others
twice.

```python
# WRONG - bucket depends on the listing order of this process
names = sorted(os.listdir(stage))
groups = [names[i:i + size] for i in range(0, len(names), size)]

# CORRECT - the item's own bytes choose its bucket, identically in every process
def buckets(stage):
    out = defaultdict(list)
    for name in os.listdir(stage):
        out[int(hashlib.sha256(name.encode()).hexdigest(), 16) % N].append(name)
    return out
```

1. Choose a fixed bucket count `N` and a stable hash of the item's own identity.
2. Let every process compute the same partition from that rule alone. Do not pass a
   position range between processes.
3. Give each bucket its own output directory and its own exit record, so a failed
   bucket names itself.
4. Merge buckets in one serial step. When outputs are content-addressed, a repeated
   name is the same content by construction and can be counted and skipped.
5. **Verify by name, not by count.** A correct count does not prove coverage.

### A stored identifier derived from transformed text

If a record stores a path or name after a redaction or normalization pass, do not
compare it with the untransformed enumeration. A hash filename can contain digit
runs that a redaction rule rewrites, so the two forms never match.

1. Keep the untransformed identity in the manifest, or keep a separate coverage
   list of the enumerated names.
2. Confirm coverage with a direct sample: export one enumerated item on its own and
   compare the result byte for byte with the merged copy.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| `sorted(p.glob("*.weights"))` | Called `sorted()` directly in Mojo as if it were a builtin | Mojo compile error: `use of unknown declaration 'sorted'`. `sorted()` is a Python builtin | In Mojo, Python builtins are reached through `Python.import_module("builtins")` |
| Fix only the test assertions | Reordered the test to match the observed output | Does not remove the nondeterminism. A different filesystem returns a different order | Fix the source of nondeterminism, not the symptom |
| Sort, then slice by position across processes | `sorted(listdir())[a:b]` in each array task | Sorting makes each process stable but not equal to another process. The partition still differs | Derive the bucket from the item's identity, not its index |
| Trust matching totals | Compared the number of enumerated items with the number of stored records | The totals match while the membership differs. A single item can be missing and another duplicated | Compare identities, and confirm a sample end to end |
| Compare a redacted stored path with the raw name | Checked coverage against the identifier the writer stored | The writer stored the identifier after a transform that rewrote digit runs in hash-like names | Keep the canonical identity, or verify by an independent re-export |

## Results & Parameters

### The single-process fix (two files)

```mojo
# Before (non-deterministic)
var weight_files = p.glob("*.weights")

# After (deterministic)
var builtins = Python.import_module("builtins")
var weight_files = builtins.sorted(p.glob("*.weights"))
```

```mojo
# Before (assumed filesystem ordering)
assert_equal(loaded[0].name, "weights", ...)

# After (matches alphabetical sorted order: "bias" < "weights")
assert_equal(loaded[0].name, "bias", ...)
```

### Diagnosing flaky CI

A commit that passed on one date and failed on another, with no code change, is
almost always ordering or timing nondeterminism rather than a logic error.

```bash
gh run list --workflow "Comprehensive Tests" --branch main --limit 5
```

### Choosing the right fix

| Symptom | Cause | Fix |
| --- | --- | --- |
| Same code, some runs pass | One process, unsorted listing | Sort before use |
| Every task succeeds, coverage is short | Several processes slice one listing | Derive the bucket from the item identity |
| Counts agree, names disagree | A stored identifier was transformed | Compare canonical identities, then confirm a sample |