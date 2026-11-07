# Notes: One Environment Lookup Rule Across Shell and Python

Supporting evidence for [one-env-lookup-rule-in-shell-and-python](one-env-lookup-rule-in-shell-and-python.md).
These notes are not part of normal retrieval.

## Source (generalized)

- Session: issue planning for a defect report on a repository that uses Python control code and a
  Bash installer.
- Finding: the report named three Python sites that hard-code a temporary base. A later review of
  the plan found two more readers — the installer script and a test fake — that would keep a
  different rule.
- Outcome: three planning revisions. Each revision moved from a literal replacement toward the
  single-rule design recorded in the main entry.

## Evidence collected during planning

1. Python short form vs. full order. A shell plan that used `${TMPDIR:-/tmp}` did not match the
   candidate order and the writability probe of `tempfile.gettempdir()`. A host that exports only
   one of the upper-case temporary variables would still stage in two directories.
2. Scrubbed child environment. The staging caller in the repository starts the shell function with
   an environment that holds only `PATH`, `HOME`, and a few tool variables. A shell-side lookup of a
   temporary variable therefore cannot see the value that Python used in the same operation.
3. Duplicate path argument vs. descriptor. The shell stage function already received a directory
   file descriptor for the stage and compared it with the stage path by device and inode. A new
   optional positional argument that repeated the path gave two sources for one fact, added a
   placeholder for an optional argument in the middle of the call, and required edits at every
   test call site. The descriptor form removed all of that.
4. Cleanup hazard. The script removed the stage directory from an `EXIT` trap and from the success
   path with one variable. The safe rule was: keep a single-variable delete, use an exclusive
   create in the entry path, and keep the path suffix script-generated.
5. Test contract. Tests that build expected paths from the literal fail once the production code
   stops using the literal. The plan moved the test changes ahead of the production change to get
   a real failure record, then re-derived the expectations from the same helper.
6. Reproduction shape. A world-writable directory below a private home directory is refused by the
   same ancestor check as a top-level world-writable temporary directory. Such a fixture shows the
   guard still works. It does not show that the defect is repaired. The repair evidence must come
   from a test or command that fails on the base revision and passes after the change.

## Verification status

- verified-local for the source layout citations gathered in the planning session.
- Not yet verified against an implemented change. Treat the workflow as a design rule until a
  change with the regression pair and the guard leg gives a recorded result.

## Privacy screen

The notes record no host names, user names, organization names, internal paths, issue identifiers,
tokens, or proprietary source. The example environment function uses only standard shell syntax and
the documented temporary-variable names.