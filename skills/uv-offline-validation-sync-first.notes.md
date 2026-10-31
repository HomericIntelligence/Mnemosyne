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

## Amendment of 2026-10-31

Added decision value for a third failure mode of the same subsystem: the tool falls back to a
host-installed executable, and the diagnostic points inside the project suite.

### New trigger and failure mode

A project declares pytest and the other test tools only in an optional dependency group (a `dev`
extra), not in the default dependencies. An agent ran a plain `uv run pytest <path> -q` on a fresh
checkout with no pre-synchronized environment. Observed sequence:

1. uv created the environment, built the project, and reported a successful install of the default
   dependencies (tens of packages, including the project itself).
2. pytest is not in the default set, so the environment never received it. uv resolved a
   host-installed `pytest` from `PATH`.
3. The host executable runs against its own interpreter, which has no project package. Collection
   failed in `conftest.py` with `ModuleNotFoundError: No module named <project package>`, even
   though step 1 reported the project installed.

The same failure reproduced identically on a sequential re-run, so it is deterministic, not a
creation race. Passing the extra on the run itself repaired it in one command:

```bash
uv run --locked --extra dev pytest <path> -q    # all focused tests passed
```

Confirmed the selection difference with `uv run which pytest`: with no extra flags it resolves a
host `PATH` entry; with `--extra dev` it resolves the project environment.

### Why this is a distinct branch

The earlier branches assume an environment that was deliberately synchronized, and are about
keeping it (`--no-sync`) or about what an exact sync removes. This branch has no prior sync at
all, and its failure signature is misleading: the build report says the project installed, while
the `ModuleNotFoundError` names the project package, so the evidence points away from executable
selection. The discriminator is the same check the entry already requires (`sys.executable`, tool
path), and the direct remedy is the extra on `uv run` itself.
