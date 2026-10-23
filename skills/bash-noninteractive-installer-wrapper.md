---
name: bash-noninteractive-installer-wrapper
description: "Run an interactive upstream installer unattended from a wrapper script. Use when an installer that a script downloads (for example curl-fed) reads its prompts from /dev/tty directly, so '< /dev/null' does not suppress them, or when an unattended run must not edit shell rc files, start an interactive UI, or hang on a prompt."
category: tooling
date: 2026-10-23
version: "1.0.0"
user-invocable: false
tags: [installer, noninteractive, dev-tty, controlling-terminal, setsid, start-new-session, subprocess, setup-script, mktemp, hermetic-test]
---

# Run an interactive upstream installer non-interactively in a wrapper

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-23 |
| **Objective** | Run an upstream installer that expects a terminal safely inside an unattended setup script: no prompt reads, no rc-file edits, no interactive UI, no hang. |
| **Outcome** | Successful: the installer takes its documented non-interactive path after the wrapper removes its controlling terminal. |

## When to Use

Use this skill when all or some of these conditions apply:

- Automation downloads and runs an upstream installer, usually with `curl <url> | sh` or the file-based equivalent.
- The installer source opens `/dev/tty` directly for one or more prompts, so redirecting stdin from `/dev/null` does not suppress them.
- The wrapper runs without user interaction (CI, provisioning, headless bootstrap) or reserves its own stdout and must not share the terminal with the installer.
- The installer offers a cancel path that can exit with status 0, so the exit code alone cannot confirm the installation.

## Verified Workflow

### Quick Reference

Remove the controlling terminal from the installer process. From Python:

```python
with open(os.devnull, "rb") as devnull:
    code = subprocess.call(
        ["sh", installer_path, *extra_args],
        stdin=devnull,           # no terminal input
        stdout=sys.stdout.buffer,  # installer output stays out of structured channels
        stderr=sys.stderr,
        start_new_session=True,  # new session => no controlling terminal =>
                                 # the installer takes its non-interactive path
    )
```

From POSIX shell, the equivalent is `setsid sh "$installer" </dev/null`. `setsid(1)`
forks when it is a process-group leader, so the wrapper and the installer do not
share a session.

Apply this only after you confirm that the installer reads prompts from `/dev/tty`
and has a non-interactive fallback. Prefer a documented switch (`CI=true`, `--yes`,
or a skipped prompt when no terminal is detected) when the installer provides one.

### Suggested Approach

1. Inspect the installer before you wrap it. `grep -n "/dev/tty" install.sh` finds
   prompts that ignore stdin redirection. Look for file descriptors bound directly
   to `/dev/tty` (for example `exec 3<>/dev/tty`) and reads from those descriptors.
   Find the documented non-interactive fallback and what disables it.
2. Buffer the download to a temporary file instead of piping `curl | sh`. You can
   read the source first, keep one network fetch for repeated runs, and substitute
   a stub in tests. Use a portable template: keep the `XXXXXX` at the end of
   `mktemp "${TMPDIR:-/tmp}/install.XXXXXX"`. BSD and macOS `mktemp` reject a
   suffix after the X's.
3. Give the download a URL-override environment variable (for example
   `<TOOL>_INSTALL_URL`) that defaults to the upstream URL. This keeps air-gapped
   operation possible and lets tests substitute a `file://` stub, so the
   integration suite stays hermetic.
4. Run the installer in a new session as in the Quick Reference. The failing
   `/dev/tty` open then makes the installer take its scripted or CI path: prompts
   are skipped, rc files stay unchanged, and no interactive UI starts.
5. Do not trust the exit code alone. An installer that offers a cancel path can
   exit 0 without installing. After the run, detect the installed state: the
   launcher on `PATH`, a working version command, or managed directories. Report
   "not installed" when detection fails.
6. Verify the wrapper's own side-effect contract in tests: rc files unchanged,
   structured stdout not polluted by installer output, and a cancel-path stub
   reported as "not installed" even with exit code 0.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Attempt 1 | Run the installer in a terminal with only stdin redirected from `/dev/null`. | The action menu, the PATH-update prompt, and the "start the UI now" prompt still appeared: the installer reads them from `/dev/tty` directly, and a later unattended wrapper run would hang or accept defaults. | `/dev/tty` reads bypass stdin redirection. Remove the controlling terminal with a new session, not only stdin. |
| Attempt 2 | Buffer the downloaded installer with `mktemp "${TMPDIR:-/tmp}/install.XXXXXX.sh"` to keep a `.sh` suffix. | BSD and macOS `mktemp` reject the template: characters after the X's make it invalid, so the temp-file helper returned nothing on those hosts. | Keep the X's at the end of a `mktemp` template. Put a required suffix in the prefix or in the directory name. |
| Attempt 3 | Treat installer exit code 0 as "installed" and skip a post-run check. | The same installer exits 0 when the user cancels its action prompt, so the wrapper could report success without the tool on `PATH`. | Re-detect the installed state after the run. Use the exit code only as transport status. |

## Results & Parameters

### Configuration

```bash
# URL-override seam: default upstream URL, overridable for air-gapped
# operation and for hermetic tests (file:// stub).
install_url="${<TOOL>_INSTALL_URL:-<upstream-installer-url>}"

# Portable temp template: X's at the end.
install_script="$(mktemp "${TMPDIR:-/tmp}/install.XXXXXX")"

# -L: the upstream host can answer with a redirect.
curl -fsSL "$install_url" -o "$install_script"

# New session: no controlling terminal for the installer.
python3 - "$install_script" <<'PY'
import os, subprocess, sys
with open(os.devnull, "rb") as devnull:
    code = subprocess.call(["sh", sys.argv[1]], stdin=devnull,
                           stdout=sys.stdout.buffer, stderr=sys.stderr,
                           start_new_session=True)
sys.exit(code)
PY

# Post-run detection, not exit-code trust.
command -v <tool-launcher> >/dev/null 2>&1 || echo "not installed; see installer output"
```

### Expected Output

A successful unattended run shows these properties:

- The installer prints its non-interactive path line (for example
  "No terminal detected; continuing without confirmation") and never blocks on
  a prompt.
- Shell rc files are unchanged and no interactive UI starts during the run.
- The wrapper reports the detected installed state, and a cancel-path stub
  with exit code 0 is still reported as "not installed".

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Private CLI-tooling monorepo (privacy-generalized) | Setup script that wraps the public Pi coding-agent CLI installer; contract suite runs against a `file://` stub installer and a fake launcher on `PATH`; end-to-end pass on a headless Linux host | See [bash-noninteractive-installer-wrapper.notes.md](bash-noninteractive-installer-wrapper.notes.md). |

## References

- Upstream installer source inspected for this skill: <https://pi.dev/install.sh> (public; prompt reads on `/dev/tty`, non-interactive fallback line).
- `setsid(2)`, `setsid(1)`, and `mktemp(1)` manual pages, including the BSD template rule.
- [concurrency-and-process-reliability-patterns](concurrency-and-process-reliability-patterns.md) — related mechanism, different intent: `start_new_session=True` for child isolation and descendant cleanup in an interactive application. This entry uses the same mechanism to remove a controlling terminal.
- [detached-launch-survives-harness-restart](detached-launch-survives-harness-restart.md) — related mechanism, different intent: `setsid` plus `nohup` for lifetime decoupling from a supervisor. This entry uses session detachment for prompt suppression, not persistence.
- [testing-integration-fake-binary-on-path](testing-integration-fake-binary-on-path.md) — related test seam: fake binaries on `PATH` for hermetic integration tests. This entry adds the URL-override and `file://` seam for installer downloads.
