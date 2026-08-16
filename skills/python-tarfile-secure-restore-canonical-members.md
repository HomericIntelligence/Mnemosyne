---
name: python-tarfile-secure-restore-canonical-members
license: BSD-3-Clause
description: "Harden manifest-driven Python tar restores by validating a canonical, inventory-authorized archive index before reading payloads or writing destinations. Use when: (1) restoring repository state from untrusted or self-consistent tar archives, (2) duplicate names or non-regular members could make tarfile lookup ambiguous, (3) symlinks beneath an allowed destination can redirect writes outside that destination."
category: architecture
date: 2026-08-07
version: "1.1.0"
user-invocable: false
verification: unverified
history: python-tarfile-secure-restore-canonical-members.history
tags: [python, tarfile, restore, archive, manifest, path-traversal, symlink, sha256, fail-closed]
---

# Secure Python Tar Restore with Canonical Members

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-08-07 |
| **Objective** | Make a manifest-driven tier-3 restore accept only uniquely named regular files strictly beneath configured inventory roots, while preserving legitimate backup and verification behavior plus a no-write guarantee for validation failures. |
| **Outcome** | A proposed fail-closed design validates the complete tar index, strict manifest, exact membership, header sizes, and resolved destinations before reading state payloads, then stages verified bytes before writing. Its untouched-repository guarantee applies to pre-write validation failures, not filesystem failures after the write phase begins. |
| **Verification** | unverified — derived from a reviewed ProjectHephaestus implementation plan; the implementation, local tests, and CI were not executed in the source session. |
| **History** | [changelog](./python-tarfile-secure-restore-canonical-members.history) |

## When to Use

- A Python disaster-recovery script restores files from `tarfile.TarFile` using a manifest of sizes and digests.
- A digest-valid archive could include an unauthorized repository path such as `pyproject.toml` and remain internally self-consistent.
- Duplicate tar names or normalization-equivalent names could make name-based `extractfile()` lookup select a different entry than the validator inspected.
- Directories, symbolic links, hard links, devices, or other non-regular members must never participate in restore.
- A pre-existing symlink inside an authorized inventory directory could redirect a restored file outside that directory.
- Restore must leave the repository untouched on validation failure: all structure, metadata, destinations, sizes, and digests succeed before the first write.
- Archive-open, tar-processing, and payload-read failures must cross the restore refusal boundary consistently, without misclassifying later repository write errors as malformed archives.

## Verified Workflow

> **Warning:** This workflow has not been validated end-to-end. Treat it as a hypothesis until implementation tests and CI confirm it.

### Proposed Workflow

The following sequence is the proposed implementation contract until end-to-end tests and CI establish it as verified.

### Quick Reference

```python
from pathlib import PurePosixPath


def canonical_member_name(name: str) -> str:
    """Return one safe canonical POSIX archive-member name."""
    if not name or "\x00" in name or "\\" in name:
        raise RestoreError(f"unsafe archive member path: {name!r}")

    path = PurePosixPath(name)
    if path.is_absolute() or ".." in path.parts:
        raise RestoreError(f"unsafe archive member path: {name!r}")

    normalized = path.as_posix()
    if normalized == ".":
        raise RestoreError(f"unsafe archive member path: {name!r}")
    return normalized
```

```text
getmembers() once
  -> canonicalize every raw name
  -> reject canonical duplicates and every non-regular member
  -> bind exactly one manifest TarInfo
  -> authorize every other TarInfo strictly below an inventory prefix
  -> parse the manifest strictly through its validated TarInfo
  -> canonicalize and authorize manifest keys
  -> require manifest keys == archive data-member keys
  -> resolve every destination beneath repository and lexical inventory root
  -> read and verify every payload into memory
  -> write only after all members pass
```

### Detailed Steps

1. Keep the restore path dependency-light when it is disaster-recovery tooling. Use Python's standard library so recovery does not depend on importing the application or optional packages.
2. Define one canonicalization authority for raw tar names and manifest keys:
   - reject empty names, NUL, backslashes, absolute paths, `..` components, and names that normalize to `.`;
   - use `PurePosixPath`, because tar member names are POSIX paths regardless of the host platform;
   - return the normalized POSIX spelling and perform duplicate detection only on that spelling.
3. Keep inventory ownership separate from path safety. Given an already-canonical name, require it to be strictly below one configured inventory prefix. The prefix itself is not a restorable data file.
4. Call `TarFile.getmembers()` exactly once before reading any payload. For every `TarInfo`:
   - canonicalize its name and reject exact or normalization-equivalent duplicates;
   - require `isreg()` so directories, links, devices, FIFOs, and unknown types fail closed;
   - permit exactly one canonical regular `manifest.json`;
   - require every other member to belong to a configured inventory prefix.
5. Bind validated names to their actual `TarInfo` objects. Later calls must use `tar.extractfile(validated_tarinfo)`, not `tar.extractfile(name)`, so duplicate-name lookup behavior cannot change which bytes are read.
6. Parse the manifest fail-closed:
   - decode as UTF-8 and convert decoding or JSON errors to the restore boundary exception;
   - use `object_pairs_hook` to reject duplicate JSON keys at every object level;
   - require exactly one top-level `members` object;
   - require each metadata object to contain exactly `sha256` and `size`;
   - require a 64-character hexadecimal digest and `type(size) is int` with `size >= 0`, rejecting booleans.
7. Canonicalize and inventory-authorize every manifest key using the same helpers as tar members. Reject normalization-equivalent manifest duplicates and require an exact one-to-one set match with the validated data members. Unknown, undeclared, and missing members all fail before payload reads.
8. Apply the same structural validator in both `verify` and `restore`. Verification should preserve its public return contract: valid content returns `0`; structural, metadata, size, or digest failure prints a `FAIL` message and returns `1`.
9. Before reading each restore payload, resolve its destination and require it to be within both the resolved repository root and its lexical inventory root. This second boundary prevents a symlink already present beneath an authorized inventory prefix from redirecting the write elsewhere. Reject two archive members that resolve to the same destination.
10. Compare each validated `TarInfo.size` with the manifest's declared size during destination validation, before opening any state payload. This catches header/manifest disagreement without consuming archive content.
11. Preserve a validate-then-write boundary. After structure, manifest, destinations, and header sizes pass, read every member through its bound `TarInfo`, verify the actual byte length and SHA-256, and stage bytes in memory. Create directories and write files only after every member succeeds.
12. Convert archive opening, indexing, manifest parsing, and payload-read failures into the restore API's refusal exception. Keep directory creation and file-write operations outside that conversion so a repository I/O failure is not mislabeled as an invalid archive. This means validation failures are no-write, but the write phase is not automatically atomic across multiple files.
13. Drive the implementation with behavior tests that build explicit tar entries. Cover unauthorized in-repository files, absolute and parent paths, undeclared and missing members, exact and normalized duplicates, directories, symbolic and hard links, devices, malformed manifests, bad hashes, boolean or negative sizes, destination symlinks, tar-header size disagreement, tampering, and legitimate round trips. Also assert verifier and restore CLI exit contracts for malformed archives.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Trust a self-consistent manifest | Accept any member whose size and digest match manifest metadata | An attacker can add `pyproject.toml` to both the tar and manifest, producing valid metadata for an unauthorized overwrite | Authorization is independent of integrity; every normalized name must be owned by an inventory prefix |
| Validate only names requested by the manifest | Read manifest entries and ignore the rest of the tar index | Unknown members, duplicate names, and unsafe member types remain hidden in the archive and name lookup can be ambiguous | Validate the complete `getmembers()` result before any payload read |
| Read members by string name after validation | Call `extractfile(normalized_name)` after inspecting one `TarInfo` | Tar archives may contain duplicate raw names, so name lookup can return bytes from a different entry | Bind canonical names to validated `TarInfo` objects and read those objects directly |
| Check `..` without canonical duplicate detection | Reject obvious traversal but retain raw spellings as dictionary keys | Safe-looking aliases such as `a//b` and `a/b` normalize to the same destination and can bypass uniqueness assumptions | Normalize once, then detect duplicates and authorize using the canonical spelling |
| Allow links because their names are inventory-owned | Accept symbolic or hard-link tar entries beneath an allowed prefix | Link targets can redirect extraction or create unexpected filesystem topology | Restore only regular files; reject every other tar member type |
| Check only that destinations remain in the repository | Resolve `<repo>/<member>` and test only the repository boundary | An authorized inventory path can traverse a pre-existing symlink and overwrite a different file elsewhere in the repository | Require the resolved destination beneath both the repository and the member's lexical inventory root |
| Write each member immediately after verifying it | Verify and write in one loop | A late mismatch leaves an incomplete, partially updated recovery state | Stage all verified bytes and perform writes only after the complete archive succeeds |
| Use ordinary `json.loads()` | Parse the manifest without duplicate-key detection or strict shape checks | Duplicate JSON keys are silently overwritten, booleans pass `isinstance(value, int)`, and extra fields weaken the contract | Reject duplicate object keys, exact shapes, malformed digests, and non-exact integer sizes |
| Call staging "transactional" without scoping the guarantee | Treat in-memory staging as proof that every restore failure leaves the repository untouched | Validation is no-write, but a directory creation or file-write error after the write phase starts can still leave partial output | Promise an untouched repository only for failures before the write phase unless writes use a separate atomic commit mechanism |
| Wrap archive processing and repository writes in one broad `OSError` conversion | Convert every `OSError` into `RestoreError("invalid or unreadable archive")` | A permissions or disk failure while writing the repository is falsely reported as archive corruption | End the archive-error conversion before directory creation and file writes begin |

## Results & Parameters

### Security Invariants

| Invariant | Required result |
|-----------|-----------------|
| Manifest count | Exactly one canonical regular `manifest.json` |
| Data member type | Regular file only |
| Data member location | Strict descendant of one configured inventory prefix |
| Name uniqueness | Unique after POSIX normalization |
| Manifest membership | Exact set equality with validated data members |
| Digest | String of exactly 64 hexadecimal characters |
| Size | Exact non-negative `int`; booleans rejected |
| Header size | Validated `TarInfo.size` equals manifest size before payload read |
| Member read | `extractfile()` receives the previously validated `TarInfo` |
| Destination | Resolved beneath both repository root and lexical inventory root |
| Validation write timing | No filesystem writes until all members pass every validation check |
| Error boundary | Archive failures become the restore refusal exception; write-phase filesystem errors remain filesystem errors |

### Behavior-Test Matrix

```text
valid:       backup round trip, force overwrite, empty inventory, CLI verify
paths:       empty, absolute, backslash, NUL, parent traversal, normalized duplicate
membership:  unauthorized, undeclared, missing, duplicate manifest key
types:       directory, symlink, hard link, block/character device, FIFO
manifest:    invalid UTF-8, invalid JSON, wrong root, wrong members shape,
             bad metadata shape, bad digest, boolean size, negative size
content:     missing stream, size mismatch, digest mismatch
filesystem:  pre-existing symlink redirects an inventory destination
errors:      malformed/unreadable archive maps to restore refusal; write I/O stays distinct
validation:  every pre-write rejection leaves inventory and protected files untouched
cli:         malformed verify returns 1 with FAIL archive; malformed restore returns 2
```

### Expected Verification Commands

Adapt paths to the repository under test:

```bash
python -m pytest <restore-test-module> -v
ruff check <restore-script> <restore-test-module>
ruff format --check <restore-script> <restore-test-module>
```

Successful implementation evidence should show the valid backup/verify/restore regressions passing, every malicious archive case failing through the documented restore exception or verifier return code, and no file created or modified by any archive rejected during validation. Test write-phase I/O failures separately; staging alone does not make multi-file writes atomic.

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| ProjectHephaestus | Reviewed plan to harden stdlib-only tier-3 state archive restore | unverified planning capture; implementation and CI validation pending |

## Related Skills

- [Manifest Config-Derived Limits and Digest Hardening](manifests-config-derived-limits-digest-hardening.md) — strict relative paths and digest validation for a different manifest-driven serving context.
- [Python Path Resolution CWD Resolve Contract](python-path-resolution-cwd-resolve-contract.md) — consistent resolved-path return contracts, distinct from archive authorization.
