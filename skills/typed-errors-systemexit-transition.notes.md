# typed-errors-systemexit-transition — notes

Supporting evidence for
[typed-errors-systemexit-transition.md](typed-errors-systemexit-transition.md). These notes are not
part of normal retrieval.

## Evidence summary

| Item | Evidence |
| --- | --- |
| Symbol inventory | `rg -n "SystemExit" src/<package>` showed 9 raise sites in the scheduler module where the approved plan named 7. The review binding was one revision behind the worktree head. |
| Broad-handler count | 52 `except Exception` handlers in the supervisor module, including the autoscale recovery and scale call paths. |
| Protected contract | The deprecation policy named a two-release plus 90-day window and two written notice channels. Contract tests asserted the documented `SystemExit` exception. |
| Message invariant | A caller built a failure envelope from `str(exc.code or ...)`. A message-only subclass with inherited `__init__` preserved that envelope. |

## Verification commands used locally

```bash
python -m ruff check <changed files>
python -m ruff format --check <changed sdk files>
python -m ty check
python -m pytest <sdk test files> -q
python -m pytest <pool tests> -q
python -m pytest <entry-point and control-plane tests> -q
```

Results: SDK files 293 passed and 1 skipped (an optional dependency is absent); the pool file 37
passed; the entry-point and control-plane files passed 81 tests; lint, format, and type checks
passed.

## Host-policy failures that reproduce on the base commit

Three failure families appear in the source worktree. Each was reproduced with the change stashed at
the base commit, so none is a regression:

1. An ancestor-directory policy rejected a group-writable parent directory outside the configured
   infrastructure groups. This failed the capacity reservation tests and most operator-service
   tests.
2. The process group identity did not match the fixture's expected identity, which failed the
   credential-store child-process tests.
3. One operator-service test asserted an intent set that lacked a newer intent; it fails on the base
   commit too.

**Lesson:** separate host policy failures from change failures by running one representative test
of each family with the change stashed. Report the pairs, not a pass count.

## Plan supersession observed

A merged base commit removed an enforcement path that the approved plan still converted
(`require_production_qualified`). The rebase conflict made this visible. Record such removals in the
pull request body as superseded plan steps, and do not restore the removed code to keep the plan
literal.