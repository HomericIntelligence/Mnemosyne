---
name: dataset-pickle-stage-verify-convert-cleanup
license: BSD-3-Clause
description: "Contain downloaded pickle-based datasets by staging the archive and extracted payload in a private temporary directory, rechecking the pinned digest at the verification-to-extraction seam, and converting to inert outputs before cleanup. Use when: (1) a downloader extracts pickle or another executable serialization format into a caller-controlled directory, (2) verification occurs inside a download helper but consumption resumes later by pathname, (3) tests mock extraction without proving permissions, isolation, tamper rejection, and lifecycle cleanup, or (4) a security rationale overstates what private staging protects."
category: architecture
date: 2026-08-05
version: "1.0.0"
user-invocable: false
verification: verified-local
tags: [dataset, pickle, deserialization, temporary-directory, staging, checksum, toctou, archive, extraction, trust-boundary, security-testing]
---

# Dataset Pickle Deserialization: Stage, Verify, Convert, Cleanup

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-08-05 |
| **Objective** | Keep a verified downloaded archive and its executable serialized payload out of caller-controlled storage, detect pathname replacement before extraction, and couple conversion to the private staging lifecycle without changing the public downloader API. |
| **Outcome** | A reusable archive-to-derived-output pattern: private staging, a second digest check at the consumer seam, safe extraction, conversion before context exit, caller-directory isolation, and automatic cleanup on every return and exception path. |
| **Verification** | verified-local — exercised in a disposable ProjectHephaestus clone; the CIFAR-10 regression tests passed locally, while CI validation remains pending. |

## When to Use

- A dataset archive contains Python pickle, joblib, or another format whose loader can execute code.
- A download helper verifies an archive, returns, and a separate consumer later opens the same pathname.
- The caller selects the output directory and may already have files whose names collide with extracted archive members.
- The implementation deletes only the archive while leaving executable extracted payloads behind after conversion or failure.
- A security comment claims that URL pinning, a checksum, or a project directory blocks every local attacker.
- Tests assert that a safe-extraction helper was called but do not observe where the archive and extracted payload live through conversion.

## Verified Workflow

### Quick Reference

```python
from pathlib import Path
import tempfile

output_path = Path(output_dir)
output_path.mkdir(parents=True, exist_ok=True)

with tempfile.TemporaryDirectory(prefix="dataset-stage-") as stage:
    staging_path = Path(stage)
    archive_path = staging_path / archive_name

    if not download_and_verify(archive_name, archive_path):
        return False
    if not verify_or_remove(archive_path, archive_name):
        return False

    extracted_path = staging_path / expected_member_root
    safely_extract(archive_path, staging_path)
    success = convert(extracted_path, output_path)

return success
```

```bash
# Run lifecycle and tamper regressions without a repository-wide coverage gate.
<package-manager> pytest <test-path>::<downloader-test-class> --no-cov -q

# Validate edited files and the intentional deserialization exception.
<package-manager> ruff check <downloader-path> <test-path>
<package-manager> bandit -c <config-path> -r <downloader-path> --severity-level medium
```

### Detailed Steps

1. **Map the executable-data lifecycle before editing.** Identify the archive pathname, the first digest verification, extraction destination, deserialization call, derived outputs, cleanup points, and every early return. Search production callers before adding abstractions; a single private caller usually needs no new public API.
2. **Write behavior-first regressions.** Construct a deterministic in-memory tar archive containing a synthetic serialized member. Patch the pinned-digest map to the archive's computed digest, and make the fake downloader write those exact bytes to the pathname it receives.
3. **Prove caller-directory isolation.** Pre-create a caller-controlled directory and a colliding member containing decoy bytes. During conversion, assert that the batch directory is under a different staging root and contains the verified archive bytes, while the caller's decoy remains unchanged after the call.
4. **Create one private lifecycle boundary.** Create the caller-selected output directory only for derived writes. Put the downloaded archive and extraction root beneath `tempfile.TemporaryDirectory`; on POSIX, assert the staging root's permission bits are `0o700` while the context is active.
5. **Recheck at the consumer seam.** Keep the download helper's normal verification, then invoke the same fail-closed verifier again immediately after the helper returns and before opening the archive. This detects replacement across the helper-return boundary and removes a mismatched archive.
6. **Extract safely into staging.** Retain the existing traversal-resistant tar extraction helper. Private staging addresses local visibility; safe extraction separately addresses malicious member paths. Neither control substitutes for the other.
7. **Convert before leaving the context.** Pass the staged extracted directory to the converter and the caller directory only as the destination for derived, non-executable outputs. Keep extraction and all deserialization inside the temporary-directory context.
8. **Let context exit own cleanup.** Do not manually unlink only the archive. Context cleanup removes the archive and extracted serialized payload on success, verification failure, extraction failure, conversion failure, and exceptions. Ignore pre-existing caller batch directories rather than deleting them.
9. **Test pathname replacement explicitly.** In a fake downloader, write and verify the expected bytes, replace the archive pathname with different bytes, then return success. Assert that the outer recheck returns false, extraction and conversion are never called, and the staging root no longer exists.
10. **Write a bounded trust rationale.** Name the actual pinned-digest map and the exact seam that is rechecked. State that the caller directory is not trusted and receives only derived writes. Private owner-only staging prevents access by other local identities; it does not protect against code running as the same operating-system identity or with elevated privilege.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Extract into the caller-selected output directory | Downloaded the archive and unpacked pickle batches beside final outputs | A caller-controlled colliding path could be consumed, and executable payloads remained visible beyond conversion | Stage archive and extracted payload privately; reserve caller storage for derived writes |
| Trust only the download helper's successful verification | Assumed a verified return value permanently authenticated the pathname | The pathname could be replaced after the helper's check and before extraction | Re-run the fail-closed verifier immediately when the consumer regains control |
| Delete only the archive after extraction | Explicitly unlinked the tarball before conversion | Extracted executable payloads survived, and early returns required scattered cleanup | Enclose download, recheck, extraction, and conversion in one temporary-directory context |
| Treat a write-restricted project directory as protection from local attackers | Claimed directory placement plus URL and checksum pinning closed the local threat | Same-identity and privileged processes can still access or replace staged files; caller storage may not be restricted at all | State the operating-system identity boundary precisely and avoid absolute security claims |
| Mock only the extraction helper | Pre-created an empty archive in the output directory and asserted one helper call | The test encoded the unsafe location and proved neither permissions, provenance, lifecycle coupling, cleanup, nor tamper rejection | Observe the real extraction wrapper and inspect paths and bytes during the conversion callback |
| Remove an existing caller batch directory | Considered deleting the colliding extraction directory before use | Destructive cleanup would erase caller-owned data and still make caller storage part of the trust decision | Ignore caller batch directories completely by extracting only inside private staging |

## Results & Parameters

- **Lifecycle boundary:** one `TemporaryDirectory` covers download, second verification, safe extraction, deserialization, and conversion.
- **POSIX staging mode:** `0o700` while the temporary directory exists.
- **Caller-visible artifacts:** derived outputs only; no archive or extracted serialized batches.
- **Verification count:** retain the downloader's verification and add one consumer-side recheck immediately before extraction.
- **Tamper behavior:** digest mismatch returns failure before extraction or conversion; temporary staging is removed automatically.
- **Public API:** unchanged; the implementation only moves private intermediate paths.
- **Digest caveat:** a recheck detects bytes that do not match the pinned value, but it is only as strong as the digest and provenance contract. Prefer a collision-resistant digest for new formats; if compatibility requires an upstream MD5 map, do not describe it as stronger authenticity than it provides.
- **Local verification evidence:** the new tests failed against caller-visible extraction and the missing consumer recheck, then all four CIFAR-10 downloader tests passed after private staging was introduced. Ruff reported no violations, and Bandit reported no medium- or high-severity findings with the two intentional deserialization suppressions recognized.
- **Coverage note:** a narrow pytest node selection can trip an unrelated repository-wide coverage threshold. Use the repository's supported targeted-test override (for example `--no-cov`) for the red/green loop, then rely on the normal full-suite coverage gate before merge.

## Verified On

| Project | Context | Details |
| ------- | ------- | ------- |
| ProjectHephaestus | Disposable local implementation of CIFAR-10 private staging and post-verification replacement regressions | 4 CIFAR-10 tests passed locally on Python 3.13.11; Ruff passed; Bandit found no medium/high issues; CI pending |

## Attribution

Generalized from CIFAR-10 downloader hardening. Project-specific filenames, checksum-map names, output formats, and test node IDs are examples rather than requirements; the transferable rule is to keep executable downloaded data inside a private, verified, ephemeral conversion lifecycle.
