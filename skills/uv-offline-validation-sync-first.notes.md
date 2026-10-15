# Notes: uv Offline Validation: Synchronize Before Running

This file holds supporting evidence for
[uv-offline-validation-sync-first](uv-offline-validation-sync-first.md). It is not part of normal
retrieval.

## Amendment of 2026-10-14

Added decision value for a second failure mode of the same subsystem and resolved the ambiguity in
the `--no-sync` guidance.

### New trigger and failure mode

A build helper synchronized its own extra exactly, then a later plain `uv run` of the test suite
removed that extra again. The suite then failed with a missing-module error for a declared base
dependency that the earlier exact sync had just uninstalled.

Sequence observed:

1. A helper script ran an exact `uv sync` with the extra the build needs. Because the sync was
   exact, it also removed packages that another command had installed, such as the test runner.
2. A subsequent plain `uv run pytest` synchronized toward the default extra set, so the extra
   from step 1 was no longer present.
3. The suite failed to import a module that is a declared base dependency.

The recovery is a pairing, not a single flag:

```bash
# deliberate, complete environment
uv sync --extra gui --extra detect --extra build --extra dev

# every follow-up step keeps that environment
uv run --no-sync pytest
uv run --no-sync python -m PyInstaller --noconfirm --clean <spec>
```

A helper that only needs to add its own extra must not remove anything else:

```bash
uv sync --extra build --inexact
```

### Why this resolves an earlier ambiguity

The prior text warned that `--no-sync` can resolve a global tool or another interpreter, and
advised against treating it as a fix. That warning is about an environment that is absent or
incomplete.

The amendment states the discriminator explicitly. `--no-sync` is correct when the environment is
already complete and was deliberately synchronized with the extras the later commands need, and
unsafe before that. `uv run` synchronizes toward the default extra set, so without the flag it
removes extras that an earlier `uv sync --extra` installed.

The amendment keeps the existing check, printing `sys.executable` and running
`python -m pytest --version`, and makes it the test that separates the two cases. Two failure
modes now produce opposite advice, resolved by environment state rather than by the flag name.

### Verification

- Without `--no-sync`, the follow-up invocation synchronized again and the suite failed on a
  missing base dependency.
- With `--no-sync`, the suite passed after an explicit sync that included every required extra.
- An exact sync inside the build helper removed the test packages. The same helper with
  `--inexact` left them in place, and the suite passed afterward.

## Related but separate

Lockfile platform coverage is a different intent and belongs with the lockfile and release
pipeline entry, so it is pointed at from here rather than merged. A manifest that restricts the
resolver to one operating system produces a lock without wheels for other platforms, so an exact,
frozen sync fails on a runner for a different platform. Recover the lock by widening the resolver
environment and re-locking, then confirm that the packages resolved for the original platform did
not change.
