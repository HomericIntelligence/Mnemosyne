---
name: local-test-env-guard-divergence
description: "Attribute environment-sensitive validation failures to the shell before you search for a code regression. Use when an ownership-, mode-, or ancestor-permission-sensitive check is red in a developer shell but green in CI (or the inverse): a divergent umask, a shared or group-writable TMPDIR, an unsynchronized virtual environment, or an ambient environment variable is a first-class suspect."
category: debugging
date: 2026-10-29
version: "1.0.0"
user-invocable: false
tags: [ci-parity, umask, tmpdir, permissions, test-environment, attribution, venv]
---

# Local Test Environment Guard Divergence

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-29 |
| **Objective** | Separate shell-environment artifacts from real code regressions when permission-sensitive validation fails only in a developer shell. |
| **Outcome** | Operational: the developer reaches the correct attribution in one bounded check before any code bisect. |

## When to Use

Use this skill when a test or a guard fails in a developer shell and:

- the same check passes in CI, in a container, or on another host;
- the failing message cites ownership, uid/gid, mode bits, link counts, sticky
  bits, or write bits on an ancestor directory;
- the test uses files or directories that it creates itself through the usual
  file API, so the creator identity is the current account but the mode is not
  controlled;
- the run relied on an implicitly selected interpreter, a tool runner, or an
  inherited temporary directory; or
- the failure appears after a runner or sync change, and imports report
  `ModuleNotFoundError` for code that is present in the tree.

## Verified Workflow

### Quick Reference

Run permission-sensitive local verification under a CI-equivalent environment
before you attribute a failure to code:

```bash
umask 022                              # match the CI process umask
export TMPDIR=$(mktemp -d)            # private, owner-only temporary root
chmod 700 "$TMPDIR"
env -i PATH=... HOME="$HOME" bash -c '<test command>'
```

Confirm each suspect with one read-only probe:

```bash
umask                                 # observe the shell umask
stat -c '%a %U:%G %n' <file-or-dir>   # compare mode and owner with the guard
stat -c '%a %u' <ancestor>            # examine writable bits on the chain
```

### Suggested Approach

1. Read the guard. A permission-sensitive check usually names its violation:
   the check class (`ancestor-group`, `unsafe identity`), the expected state,
   and the observed octal mode. Convert the error fields into a short list of
   `stat` probes.
2. Examine the resource that the message names. If the probe matches the
   guard's expectation, the message describes an artifact of the environment
   that produced the file, not the file itself.
3. Match the producer. Recreate the file exactly as the test creates it and
   compare the mode. `open` and `Path.write_text` honor the process umask;
   only an explicit `chmod` or creation-mode argument controls the bits.
4. If a created file is wider than the guard permits, suspect the umask
   first. If an ancestor is wider than the guard permits, suspect an
   inherited or shared temporary root, such as a network mount that is
   group-writable for a team.
5. Current checkout locality matters: a tool runner that silently falls back
   to a global interpreter can import none of the project and emit
   `ModuleNotFoundError`. Sync the project environment explicitly and call
   the interpreter through the project, not through a bare name.
6. Re-run the same test under the CI-equivalent environment from the quick
   reference. A red-to-green flip marks the environment as the cause and the
   code as unchanged. A persistent red under the controlled environment
   proceeds to a code bisect with the artifact excluded.

Do not change a guard to make an environment-conformant failure silent, and do
not commit a code change that an environment artifact produced. Keep the
environment fix in the run wrapper, not in the product, unless the repository
itself documents such a wrapper.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Attempt 1 | Attributed a locally red guard test to a recent code change and prepared a code bisect. | The test was red at the pristine base revision in the same shell; CI was green at the same revision. | Establish the local baseline first: re-run the failing test at the unmodified base before any bisect, so the environment and the code side are separated by evidence. |
| Attempt 2 | Ran the test with the repository's tool runner and expected the project environment. | The runner fell back to a global executable in a fresh tree; the import of the project failed with `ModuleNotFoundError`. | Sync the project environment explicitly the first time, then call the runner with sync disabled; verify the interpreter reports the project path. |

## Results & Parameters

### Configuration

| Parameter | Value | Meaning |
| --------- | ----- | ------- |
| `umask` | `022` | Default CI umask: created files are `0644` and directories are `0755`. Common developer shells use `002`, which adds group-write bits (`0664`, `0775`) and trips `mode & 0o022` style guards. |
| `TMPDIR` | `$HOME`-owned or newly-created directory, mode `0700` | A team-shared or network-mounted temporary root can be group-writable (`1775`) or carry an unexpected setgid bit, and trips ancestor chain guards. |
| environment | `env -i` with explicit `PATH`, `HOME`, `TMPDIR` | Prevents inherited variables and runner state from producing a second, hidden divergence. |

### Verification

- The guard test is green at the same source revision under the CI-equivalent
  environment.
- The guard test was red at the unmodified base revision in the developer
  shell before the fix, so the fix does not hide a real regression.

## Provenance

Local failure evidence came from a developer shell whose `umask` was `002`
and whose inherited temporary root on a shared Network file system was
group-writable. Two guard classes failed only in that shell: an
operator-document identity check (`st_mode & 0o022`) and an ancestor-group
check on the temporary chain. Both were green in CI at the same source
revision, and the developer shell showed the same red result at the pristine
base revision. Environment-matching removed the divergence without a product
change.
