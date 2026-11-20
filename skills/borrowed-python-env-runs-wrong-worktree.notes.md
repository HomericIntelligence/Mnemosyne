# Notes: borrowed-python-env-runs-wrong-worktree

Session evidence for the v1.1.0 amendment. Generalized; no internal paths, hostnames, project names, or account identifiers.

## Source operation

- One worktree for a guard change in an image-build staging path of a serving platform. The worktree had no virtual environment.
- The test commands used the primary checkout's virtual environment interpreter. That interpreter resolved the package from the primary checkout, so the new guard code was absent from the imported package.

## Evidence for the hang failure mode

- Two test runs (one foreground with a timeout, one background) did not fail. They hung in the staging and job-polling path: the foreign package accepted a build workspace that the new guard refuses, and the suite began real staging work against a shared store.
- The main entry's covered symptom (false failures) did not appear. The absence of the guard converted a should-be test refusal into long-running real work.

## Evidence for the PYTHONPATH remedy

- Re-running with `PYTHONPATH=<worktree>/src` and the same interpreter resolved the package inside the worktree. Verified before the run:

```bash
PYTHONPATH=<worktree>/src <primary>/.venv/bin/python -c "import <package>; print(<package>.__file__)"
```

- Focused tests for the guard then passed in seconds (four tests, about 12 seconds).
- The repository uses a source layout (`src/<package>`), which is why the override worked.

## Verification evidence

- Import-path check before and after the override, printed path compared against the worktree prefix.
- Focused selection: three new guard tests plus one adjacent lock test, all passing after the remedy; the same selection hung before it.
