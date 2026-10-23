# Supporting evidence: non-interactive installer wrapper

Privacy-safe session detail for `bash-noninteractive-installer-wrapper`. Source
session: 2026-10-23. Repository, host, and issue identifiers are withheld; the
upstream installer in question is public.

## Source context

A setup script in a private CLI-tooling monorepo installs the public Pi
coding-agent CLI (`<https://pi.dev>`) when it is missing: it downloads the
upstream `install.sh` script and runs it. The wrapper must run unattended in
three environments: an agent harness, user terminals, and CI. The feature
landed through issue-scoped work and a merge-reviewed pull request with one
review round; the review round produced three non-blocking nits and a
carried GO. Related follow-up work for parity between two CLI frontends was
filed separately.

## Installer source inspection (public artifact)

`curl -fsSL https://pi.dev/install.sh` at session time showed:

- An action menu (`install` vs `upgrade` selection) that opens `/dev/tty` on a
  separate file descriptor (fd 3) and reads from it, so stdin redirection cannot
  reach it.
- A PATH-update prompt read from the same descriptor, with shell rc-file edits
  on acceptance.
- A final offer to start the interactive terminal UI from the same descriptor.
- A fallback branch that prints "No terminal detected; continuing without
  confirmation" when no controlling terminal is available, skips the prompts
  and the rc-file edits, and does not start the UI.
- An exit-0 path when the user cancels at the action menu.

These properties are the evidence basis for the main skill: `/dev/tty` prompt
reads explain why `< /dev/null` fails, the fallback branch is the documented
non-interactive path to trigger, and the cancel path is why exit code 0 is not
an installed-state signal.

## Verification receipts from the session

- Direct terminal run of the installer before wrapping: all three prompts
  appeared with stdin from `/dev/null` (Failed Attempts, Attempt 1).
- Wrapper with `subprocess.call(["sh", script], stdin=devnull,
  stdout=sys.stdout.buffer, stderr=sys.stderr, start_new_session=True)` on a
  headless Linux host: the installer printed the non-interactive line, made no
  prompt reads, made no rc-file edits, and placed the launcher under
  `~/.local/bin`.
- Review round 1 caught the non-portable template
  `mktemp "${TMPDIR:-/tmp}/install.XXXXXX.sh"` (BSD/macOS reject suffixes
  after the X's); the fix ended the template in X's before merge
  (Failed Attempts, Attempt 2).
- Post-run detection replaced exit-code trust after the review round raised the
  cancel-path case (Failed Attempts, Attempt 3). The cancel path was confirmed
  in the installer source.
- Hermetic contract suite: the wrapper exposes a `<TOOL>_INSTALL_URL` override;
  tests point it at a `file://` stub installer and put a fake launcher on
  `PATH`. The suite verifies installed-state detection, the no-rc-edit
  contract, and the cancel-path report without network access. The full
  repository test suite (13 files) passed; `sh -n` and shellcheck were clean.

## Disposition and boundary against neighbors

Disposition `create` after duplicate analysis against these corpus entries:

- `concurrency-and-process-reliability-patterns`: uses `start_new_session=True`
  to isolate children of an interactive application for signal delivery and
  descendant cleanup. The trigger there is a broken signal or cleanup
  contract; the trigger here is an installer that opens `/dev/tty`. The same
  mechanism serves a different decision.
- `detached-launch-survives-harness-restart`: uses `setsid` plus `nohup` so
  long-running work survives a supervisor restart. The desired outcome there
  is persistence; here it is prompt suppression. No overlap in retrieval
  intent.
- `shell-wrapper-container-detection`: checks terminal presence to detect
  container exec flags. Adjacent vocabulary, unrelated decision.
- `testing-integration-fake-binary-on-path`: PATH-stub seam for hermetic
  integration tests. This entry's test contribution is the download-side
  URL-override and `file://` stub seam, kept here because it belongs to the
  installer-wrapper decision, not to PATH stubbing.
- `bash-stderr-mktemp-trap-return`: mktemp for stderr separation with trap
  RETURN cleanup. The portability rule here (X's at the end of the template)
  is a template-shape rule from installer buffering and is filed as a failed
  attempt in this entry, not as a separate skill (AHA: one case only).

Rejected candidates from the same session:

- Deployment-name charset validation plus explicit-env conflict handling: the
  same decision class as `cli-flag-validation-prevent-silent-noop`
  (parse-time validation, fail fast on incompatible explicit inputs). No new
  decision value.

## Notes on mechanism alternatives

- From POSIX shell, `setsid sh script </dev/null` is sufficient: util-linux
  `setsid(1)` forks when it starts as a process-group leader, so the child
  lands in a fresh session with no controlling terminal.
- Python `subprocess` with `start_new_session=True` applies `setsid(2)` in the
  child before `exec`. It composes with `stdin=devnull` and per-stream output
  routing, which is why the session used it from a Python helper embedded in
  the shell wrapper.
- `ssh`-style `BatchMode`, `yes |`, and `expect` were not needed: the
  documented fallback branch made synthetic answers unnecessary.
