# Supporting evidence: shell TTY interactivity detection and verification

Privacy-safe session detail for `shell-tty-interactivity-verification`. Source
session: 2026-10-31. Repository, harness, and issue identifiers are withheld;
every probe in the main skill was reproduced on a headless Linux host.

## Source context

A functional check was written for a repository onboarding shell script. One
harness step asked the user to confirm an action, and the script decided on
the confirmation from terminal presence. The check first used
`test -r /dev/tty` as the interactivity test. That test passed on hosts with
no controlling terminal, so the check gave false evidence about when the
prompt would appear. The fix detected interactivity with an open of
`/dev/tty`, and the functional check verified both branches: interactive runs
under a pty, non-interactive runs in a new session with stdin from
`/dev/null`.

## Verification receipts

Predicate probes on a headless Linux host (agent shell, no controlling
terminal):

- `test -r /dev/tty` and `test -c /dev/tty` both returned true; `ls -l
  /dev/tty` reports `crw-rw-rw-` (mode 0666), so `access(2)` succeeds without
  a controlling terminal.
- `(exec 9<>/dev/tty) 2>/dev/null` failed in the same shell and under
  `setsid ... </dev/null`, which is the correct negative result.

Behavior probes with a two-command helper (predicate, then a prompt read from
`/dev/tty`):

- `printf 'y\n' | script -qec <helper> /dev/null`: the helper reported a
  controlling terminal, the prompt read the piped answer, and the helper
  continued on the confirmed path.
- `setsid <helper> </dev/null`: no controlling terminal, no prompt read; the
  unguarded read failed with `/dev/tty: No such device or address` (`ENXIO`).

These receipts are the basis of the Failed Attempts table and the Expected
Output section of the main skill.

## Disposition and boundary against neighbors

Disposition `create`. Duplicate analysis against the corpus (helper-listed
main-skill files, then full-text search for `/dev/tty`, `script -q`, pty
allocators, `setsid`, and terminal-presence checks):

- `bash-noninteractive-installer-wrapper` (+ notes): uses `setsid` /
  `start_new_session=True` to remove the controlling terminal so an upstream
  installer takes its documented non-interactive path. The trigger there is a
  third-party installer that reads prompts from `/dev/tty`; the outcome is
  prompt suppression and no rc-file edits. This entry's trigger is a script's
  own interactivity decision, its failure mode is the always-true
  `test -r/-c /dev/tty` predicate, and it adds pty-based verification of the
  interactive branch, which the neighbor does not contain.
- `shell-wrapper-container-detection`: terminal checks route container `exec`
  flags. Adjacent vocabulary, unrelated decision.
- `ci-podman-containerized-validation`: uses `[ -t 1 ]` only to select
  container `-t` flags; not a prompt decision and not about `/dev/tty`.
- `bats-shell-test-patterns`, `shell-script-integration-test-tier-coverage`:
  shell test mechanics (shims, branch coverage); no TTY behavior.

Open Mnemosyne PRs at write time changed three unrelated `skills/*.md`
artifacts (review-premise sweep, session-rename entries); none overlap.

## Probe limitations

- Util-linux `script -qec` was the pty allocator. Hosts that ship a different
  `script(1)` (for example BSD) need an equivalent allocator; the main skill
  names the Python `pty` module as the fallback.
- The 0666 mode for `/dev/tty` was observed on the probe host and is the
  common configuration; the failure evidence does not depend on the exact
  mode, only on `access(2)` succeeding without a controlling terminal.
