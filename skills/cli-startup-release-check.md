---
name: cli-startup-release-check
description: "Add a bounded startup check that tells an operator when a newer published release exists. Use when a CLI command can run an older installed package without a notice, or when planning a startup update check for many console scripts."
category: tooling
date: 2026-11-06
version: "1.0.0"
user-invocable: false
verification: unverified
tags:
  - cli
  - console-scripts
  - startup-check
  - release-source
  - importlib-metadata
  - pep-440
  - stderr
  - network-timeout
  - graceful-degradation
  - json-stdout
---

# Bounded Startup Release Check

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-06 |
| **Objective** | Give a CLI operator an update recommendation when the running installation is older than the newest applicable published release. |
| **Outcome** | Operational. A requirements recovery was selected, and the constraints below are the evidence-backed planning decisions. The plan is not implemented in the source repository. |

A working source checkout does not show which version a console script runs.
An operator can run an old installed package, and a defect that is already
fixed in the repository still occurs. Recovery failed, and agent work was
spent before the failure. A startup release check removes this uncertainty.

## When to Use

Use this skill when one of these conditions applies:

- A command can run an installation that is older than the published release,
  and the operator receives no warning.
- You plan or review a startup update check for one command or for many
  console scripts.
- A command gives an update advice that names the wrong installation, the wrong
  distribution, or a prerelease.

Do not use it to add automatic upgrades. The check reports; it does not install.

## Verified Workflow

### Quick Reference

```python
# Compare with package-version ordering, not string comparison.
from importlib.metadata import version as dist_version
from packaging.version import Version

# Installed side: the distribution that the running process imports.
# Release side: the newest published version from the defined release source.
if Version(latest_public) > Version(dist_version(dist_name)):
    print(notice, file=sys.stderr)  # never to stdout
```

### Suggested Approach

1. **Define the version of the running process.** Use
   `importlib.metadata.version(<distribution name>)` for the distribution that
   the command imports. The import name and the distribution name can be
   different strings, so do not derive one from the other. Never use the target
   repository checkout, a Git tag, or a `VERSION` file as the installed-version
   source. The checkout describes the source; the console script runs the
   installation.
2. **Name the release source.** State the release source in the plan and in the
   documentation. One release source gives one comparison authority. Do not
   compare against two sources with different values.
3. **Compare with package-version ordering.** Use a PEP 440 parser. String
   comparison and digit-tuple comparison both order `0.9.9` above `0.10.0`.
   A pure digit tuple also cannot read a prerelease suffix.
4. **Apply the release policy.** Recommend an update only when the release
   version is strictly greater, and only when it is applicable. A stable
   installation does not receive a prerelease recommendation. An installed
   version that is equal to or newer than the release receives no update or
   downgrade recommendation. A development or editable version is usually newer
   than the release, so the same rule gives no notice.
5. **Bound the check.** Give the release read a short timeout. Attempt the check
   on every invocation. A failure, a timeout, or a malformed response writes an
   unavailable-check notice and the command continues. An unavailable check
   must not claim that the installation is current, and it must not change the
   exit status.
6. **Write the notice.** Put one notice on stderr. Give the installed version,
   the available version, an actionable update recommendation, and the identity
   of the active installation or interpreter. Preserve optional extras in the
   recommendation. Never name a different distribution that has no relation to
   the command. Keep stdout byte-identical, including JSON output.
7. **Stop the repetition.** Use process-level state, for example a module-level
   once flag, so that shared startup helpers called more than once still do one
   check and write one notice. A new process performs a new check.
8. **Keep library imports inert.** Do the check only in the entry path, not at
   import time of the library package. A plain import performs no network
   access and writes no notice.
9. **Cover the whole surface.** Put the check in each console entry point, or in
   a shared shim that all entry points call. For an entry point that starts
   agent jobs, run the check before the job submission. Help and version output
   must stay lightweight, so keep the read small and the timeout short.

Cover each case with a controlled release-metadata response. Use an isolated
installation in the tests; do not use the live release service. Test the
numeric boundary, the prerelease case, the equal case, the development case,
an unavailable check, and JSON stdout. Run one case with a `PATH` that selects
an older installation.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| N/A | The direct approach was successful at the planning stage. | N/A | No change was necessary. |
| — | Compare versions as strings or as digit tuples. | `0.9.9` sorts above `0.10.0`, and a prerelease suffix does not parse. | Use a PEP 440 version object. |
| — | Read the installed version from the repository tag or a version file. | The checkout is not the installation. The wrong installation receives the advice. | Read distribution metadata of the running process. |

## Results & Parameters

### Configuration

```yaml
release_source: "<one published release index; state it in the docs>"
check_timeout_seconds: "<short bound; a few seconds>"
notice_stream: stderr
library_imports: no_network
once_scope: one_per_process
```

### Expected Output

- An older installation gets one stderr notice that gives both versions, the
  active installation, and an update recommendation.
- An equal or newer installation runs with no notice.
- An unavailable release source gets a short delay and one stderr notice, and
  the exit status is unchanged.
- A JSON command keeps valid JSON on stdout.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Reference Python CLI package | Requirements recovery for a startup update check | Discovery only. The source was not implemented. See [notes](cli-startup-release-check.notes.md). |

## References

- [Python packaging: version specifiers](https://packaging.python.org/en/latest/specifications/version-specifiers/)
- [importlib.metadata](https://docs.python.org/3/library/importlib.metadata.html)
- [Optional-extra console-script shims](optional-extra-console-script-shims.md)
- [Environment-gated installed CLI test lane](testing-env-gated-skip-fail-installed-cli-lane.md)