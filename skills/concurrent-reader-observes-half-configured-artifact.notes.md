# Notes: concurrent-reader-observes-half-configured-artifact

Supporting evidence for the main entry. Details are generalized to the pattern. The main rule is in
[the skill](concurrent-reader-observes-half-configured-artifact.md).

## Evidence chain

The classification came from a continuous-integration traceback, not from a local reproduction.

1. A default-branch run failed on exactly one test in the concurrency suite. The next two default-branch
   heads passed. That pattern usually reads as a flake.
2. The full traceback, read from the job log instead of the summary line, showed the raise inside an
   identity validator, called from a create-or-retain helper in a second module.
3. The printed arguments at the raise were `expected_state = None`, with two different descriptor numbers
   for the parent directory and the artifact. That combination identifies the "another process already
   created it" branch, which passes no expectation.
4. The create-or-retain helper in that module opened the final name with `O_CREAT | O_EXCL`, and only then
   applied `fchown`, `fchmod`, and `fsync`.

Step 4 is the defect. Steps 1 through 3 locate it.

## Why the local reproduction did not work

Three separate local attempts produced no failure:

| Attempt | Setup | Result |
| ------- | ------- | ------- |
| Direct loop | 16 concurrent creators, 300 fresh roots | 0 failures |
| Instrumented loop | Same, with a spy on the validator that recorded which metadata fields diverged | 0 failures in 400 iterations, so no field data collected |
| Injected delay | Added a sleep inside the creator's `fchmod` | 0 failures in 60 iterations |

The third attempt also did not widen the claimed window, because the rival opened the directory itself
rather than racing on the published name. An injected delay is useful only when you first prove that it
sits between the publish and the validation.

A metadata experiment confirmed the comparison cannot fail for a stable inode. Applying `fchown`,
`fchmod`, `fsync` on the descriptor and `fsync` on the parent, then comparing `fstat` against a
path `stat`, produced no divergence at any step. The refusal therefore always indicates a different inode
at that name, which is consistent with a rival observing a file that is complete but was misjudged, or one
replaced during the window.

## Reading the traceback

The summary line names only the exception type and message. The useful facts are in the frames:

```text
Raise in a shared identity validator
  called from <module A>._startup_lock
    with expected_state = None
  created by os.open(NAME, O_RDWR | O_CREAT | O_EXCL | O_CLOEXEC)
    then os.fchown / os.fchmod / os.fsync
```

Two facts change the decision:

- The failing caller was not the entry point that an adjacent fix had already changed.
- The "no expectation" argument shows the branch that treats an existing file as normal.

## Coverage check before approving a fix

When more than one module creates the same artifact, enumerate all creators:

```bash
grep -rn "O_CREAT.*O_EXCL" src/ --include=*.py
grep -rn "<artifact-name>" src/ --include=*.py
```

For each hit, decide whether the module applies attributes after publishing at the final name. A fix that
converts one creator leaves the others with the same defect, and the test that covers the shared path can
still fail through the unconverted one.

## Decision boundary with the sibling entry

`lockless-snapshot-create-race-refuses-own-writer` covers a different rule. There, the create is fine and
the *comparison* uses a stale snapshot, so the fix re-validates after the create. Here the comparison is
correct and the *publication order* is wrong, so the fix moves configuration before publication. Applying
the sibling fix to this case would not help, because the visible entry is genuinely incomplete when the
rival reads it.

Use both entries together when a single scope has both a snapshot comparison and a create-then-configure
publication. They repair different branches.