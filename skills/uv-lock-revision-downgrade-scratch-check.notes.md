# Notes: uv-lock-revision-downgrade-scratch-check

Supporting evidence for the main entry. Privacy-safe: no repository, organization,
host path, or issue identifiers.

## Source evidence

- A Python project pinned `uv.lock` at `revision = 5`. The installed uv writes
  `revision = 3` for the same package set.
- Plain `uv lock` (regeneration for one dependency addition): the header changed
  to `revision = 3`. Recovery: hand-edit the lock (add the `[[package]]` entry and
  the `requires-dist` line) and restore the header line.
- `uv lock --check` after that restore, run in the real tree: `git diff uv.lock`
  showed `-revision = 5` / `+revision = 3` with no other change. The rewrite was
  found in a later diff review, not by the command output. Recovery: restore the
  header line again.
- Scratch copy: `pyproject.toml` + `uv.lock` copied to a disposable directory;
  `uv lock --check` exited 0 ("Resolved 112 packages"); the copy header stayed
  `revision = 5`.
- Real tree: `uv sync --locked --extra dev` reported "Checked 84 packages";
  `grep -m1 '^revision' uv.lock` stayed `revision = 5`; `git diff uv.lock` held
  only the new dependency lines.

## Relation to sibling entries

- `tooling-pixi-lockfile-churn-self-reference` and
  `ci-cd-pixi-lock-version-skew-regeneration` cover the same family: the writing
  tool's version determines the lockfile format. Their trigger is an explicit lock
  regeneration, and their recovery is to match the writer binary.
- Delta recorded here: the downgrade direction (installed tool older than the
  pinned revision), the read-only command class (`uv lock --check`,
  `uv sync --locked` mutate under skew), and scratch-copy verification that
  protects a pinned revision without changing tools.

## Limits

- verified-local only; no CI run.
- The rewrite was observed with one tool-version pair (writer newer, installed
  older). Other pairs may or may not rewrite. The scratch-copy check makes the
  behavior visible per environment before the command is trusted.
