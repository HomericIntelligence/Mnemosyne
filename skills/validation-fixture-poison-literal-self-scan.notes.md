---
name: validation-fixture-poison-literal-self-scan
license: BSD-3-Clause
companion: skills/validation-fixture-poison-literal-self-scan.md
type: notes
---

# Notes: Validation-Fixture Poison-Literal Self-Scan

Supporting detail for the main entry. These notes stay outside normal retrieval.

## Fixture shape used in the evidence

The test class in evidence builds each fixture with one directory copy of the
repository root, excluding VCS, tool caches, and build output:

```python
shutil.copytree(
    ROOT,                       # the repository under test
    fixture,
    ignore=shutil.ignore_patterns(
        ".git", ".venv", "dist", "build",
        "__pycache__", "*.pyc", ".coverage*",
    ),
)
```

Each test then writes extra seed files into `fixture` and runs the
repository gate on `fixture`, not on the live tree.

## Seed layout from the evidence

The regression test under evidence pinned that two local-state top-level
directories stay invisible to the gate scan:

```text
fixture/
  .worktrees/feature/.venv/lib/pkg/mypy.<abi-triplet>.so   (compiled artifact)
  .opencode/node_modules/sdk/dist/<payload>.gen.d.ts        (forbidden prefix)
```

The gate walk examines every file under the root and skips a top-level part
that appears in an ignore set (`.git`, `.mypy_cache`, `.pixi`, `.venv`,
build output, and friends at the time of the session). The pre-fix ignore set
omitted the two directories above, which is what the regression test exists
to pin.

## What made the suite fail in mass

The payload string was written as one contiguous literal in the test module
source. Because the fixture copy carries every source file, the gate scanned
the fixture's copy of the test module and reported:

```text
The file 'tests/.../test_module.py' uses the forbidden Project prefix.
```

Every test in the class calls the same fixture-and-gate path, so one seed
literal failed them all (24 tests plus subtests in the evidence run). The
failing file name in the gate report, not the count, gave the cause away.

## Remediation pattern

```python
part = "Proj"
(payload / "payload.gen.d.ts").write_text(f"{part}ectListData")
```

The contiguous form never exists in any source; the payload file still
carries the assembled form, so the test distinguishes a missing ignore entry
(an inspected payload fails the gate) from a correct ignore entry (the
payload is never scanned).

## Run evidence

- With the contiguous literal in the test source: 24 failed, 32 passed
  (focused test file), every failure surfacing the fixture's copy of the
  test module as the offender.
- After run-time assembly, before the gate fix: exactly one failure, the new
  regression test, failing on the seed under a not-yet-ignored top-level
  directory. This is the intended RED state.
- After the ignore-set fix: full pass, including the new regression test.

The fixture copy shape and the ignore-set mechanism come from the session
repository's validator; the literal token in this note is a synthetic
stand-in for whichever prefix the scanned gate forbids.
