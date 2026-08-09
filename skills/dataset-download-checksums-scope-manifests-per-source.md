---
name: dataset-download-checksums-scope-manifests-per-source
description: "Scope download checksums to the artifact owner instead of a shared basename. Use when: (1) multiple datasets or sources publish identically named files with different digests, (2) a shared downloader must preserve retry, transport, unknown-file, and corrupt-file behavior while fixing integrity selection."
category: architecture
date: 2026-08-07
version: "1.0.0"
user-invocable: false
verification: unverified
tags: [datasets, downloads, checksums, md5, integrity, pytest, manifests]
---

# Scope Download Checksum Manifests per Source

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-08-07 |
| **Objective** | Prevent checksum collisions when independent artifact owners reuse the same filename. |
| **Outcome** | Proposed design: each concrete downloader owns its manifest and passes that manifest explicitly through every verification seam. Authentic MNIST and Fashion-MNIST values were corroborated against Torchvision, but the code change and tests have not been executed. |
| **Verification** | unverified |

The integrity lookup key is not merely a filename. It is the pair `(artifact owner, filename)`.
Representing that relationship with one basename-only map silently discards the owner namespace
and cannot model two authentic files that share a name but differ in content.

## When to Use

- Two datasets, mirrors, model families, or vendors publish the same archive basename with different authentic digests.
- A generic downloader centralizes retry and transport behavior while concrete downloaders know artifact identity.
- A checksum fix must not change public constructors, download method signatures, URL enforcement, or retry behavior.
- Tests need to prove correct checksum selection without making live network requests.
- A download is verified more than once, such as immediately after transfer and again before extraction.

## Verified Workflow

No workflow has been verified yet. The implementation and acceptance checks remain pending;
the section below is intentionally proposed rather than presented as completed evidence.

## Proposed Workflow

> **Warning:** This workflow has not been validated end-to-end. Treat as a hypothesis until CI confirms.

### Quick Reference

```python
from collections.abc import Mapping
from pathlib import Path

_SOURCE_A_MD5 = {"shared-name.gz": "<source-a-authentic-md5>"}
_SOURCE_B_MD5 = {"shared-name.gz": "<source-b-authentic-md5>"}


def verify_or_remove(
    path: Path,
    filename: str,
    checksums: Mapping[str, str],
) -> bool:
    expected = checksums.get(filename)
    if expected is None:
        logger.warning("No checksum recorded for %s -- skipping verification", filename)
        return True
    if file_md5(path) == expected:
        return True
    with contextlib.suppress(OSError):
        path.unlink()
    return False


class Downloader:
    _checksums: Mapping[str, str] = {}

    def download_with_retry(self, filename: str, output_path: Path) -> bool:
        # Keep the established transfer and retry implementation.
        ...
        return verify_or_remove(output_path, filename, self._checksums)


class SourceADownloader(Downloader):
    _checksums = _SOURCE_A_MD5


class SourceBDownloader(Downloader):
    _checksums = _SOURCE_B_MD5
```

### Detailed Steps

1. Inventory the checksum table and every verifier call site before editing. Confirm whether post-download, pre-extraction, cache, or resume paths repeat verification.
2. Identify the narrowest owner namespace already represented by the object model. If concrete downloader classes represent datasets or vendors, make each class own one private `Mapping[str, str]` manifest.
3. Give the generic base downloader an empty manifest. This preserves existing unknown-file behavior for generic or extensible callers without expanding a public constructor.
4. Change the private verifier to accept the active manifest explicitly. Resolve `expected = checksums.get(filename)` only within that manifest; do not search other owners or fall back to a global basename map.
5. Pass `self._checksums` at every verification seam, including any recheck before extraction. Using different lookup logic at the second trust boundary recreates the ambiguity.
6. Preserve surrounding behavior exactly: HTTPS validation, redirect policy, URL construction, response streaming, retries, warnings for unknown files, and deletion after a mismatch.
7. Add a behavior-first parameterized test for the Cartesian set of artifact owners and shared filenames. Drive the public download method, mock the network response, and stub only the digest calculation to the authentic value for that case.
8. Keep focused private-helper tests for valid, mismatched, and unknown files. Pass the manifest explicitly and assert that mismatches delete the file while unknown names remain present.
9. Pin digest values from an authoritative upstream manifest. Record the source and remember that legacy MD5 compatibility detects accidental corruption but is not collision-resistant provenance against a malicious publisher.
10. Run the focused collision regression, all downloader tests, transport-security tests, linting, and type checking before upgrading this workflow's verification level.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| One global basename-to-digest map | Stored all dataset archives in a flat dictionary keyed only by filename | Later entries overwrite or exclude earlier authentic values when two owners reuse the same basename | Include artifact ownership in the lookup boundary; a per-owner manifest is the simplest representation when owner-specific classes already exist |
| Test only the private verifier | Passed a hand-selected expected digest directly to a helper test | This can prove digest comparison while missing the production bug in manifest selection | Drive the public download path and vary both downloader class and shared basename |
| Patch the manifest entry to make each case pass | Replaced the production digest lookup during the regression test | The test no longer proves that the correct built-in owner manifest was selected | Stub file hashing or generate fixtures, but leave the production manifest and owner binding intact |
| Fix checksum lookup while refactoring transport | Changed URL validation, retries, streaming, or deletion in the same patch | The integrity fix becomes harder to review and can regress independent security boundaries | Keep the change confined to manifest ownership and explicit verifier plumbing |
| Treat authentic MD5 as adversarial security | Described upstream MD5 values as cryptographically secure provenance | MD5 is collision-broken even though many legacy dataset manifests still publish it | Preserve upstream compatibility for corruption detection and use a stronger authenticated digest when the protocol permits |

## Results & Parameters

### Behavioral Contract

| Case | Expected result |
|------|-----------------|
| Known filename with matching digest in active owner's manifest | Accept the file |
| Known filename with another owner's authentic digest | Reject and delete the file |
| Known filename with corrupt bytes | Reject and delete the file, then preserve existing retry semantics |
| Filename absent from active owner's manifest | Warn, accept, and keep the file if that is the established compatibility contract |
| Plaintext initial URL or redirect | Reject through the unchanged HTTPS boundary |
| Pre-extraction recheck | Use the same active owner manifest as the initial verification |

### Network-Isolated Regression Shape

```python
@pytest.mark.parametrize(
    ("downloader_cls", "filename", "authentic_digest"),
    [
        (SourceADownloader, "shared-name.gz", "<source-a-authentic-md5>"),
        (SourceBDownloader, "shared-name.gz", "<source-b-authentic-md5>"),
    ],
)
def test_shared_names_use_owner_manifest(
    downloader_cls: type[Downloader],
    filename: str,
    authentic_digest: str,
    tmp_path: Path,
) -> None:
    response = MagicMock()
    response.__enter__.return_value = response
    response.__exit__.return_value = False
    response.headers.get.return_value = "7"
    response.read.side_effect = [b"payload", b""]

    with (
        patch.object(module.HTTPS_OPENER, "open", return_value=response),
        patch.object(module, "file_md5", return_value=authentic_digest),
    ):
        assert downloader_cls().download_with_retry(filename, tmp_path / filename)
```

For MNIST-family regression coverage, use all four shared basenames against both manifests:

| Filename | MNIST MD5 | Fashion-MNIST MD5 |
|----------|-----------|-------------------|
| `train-images-idx3-ubyte.gz` | `f68b3c2dcbeaaa9fbdd348bbdeb94873` | `8d4fb7e6c68d591d4c3dfef9ec88bf0d` |
| `train-labels-idx1-ubyte.gz` | `d53e105ee54ea40749a09fcbcd1e9432` | `25c81989df183df01b3e8a0aad5dffbe` |
| `t10k-images-idx3-ubyte.gz` | `9fb629c4189551a2d022fa330f9573f3` | `bef4ecab320f06d8554ea6380940ec79` |
| `t10k-labels-idx1-ubyte.gz` | `ec29112dd5afa0611ce80d1b7f02629c` | `bb300cfdad3c16e7a12a480ee83cd310` |

### Verification Commands

```bash
<package-manager> pytest <test-path>::TestChecksumScoping -v
<package-manager> pytest <downloader-test-path> -v
<package-manager> ruff check <downloader-module> <downloader-test-path>
<package-manager> mypy <downloader-module> <downloader-test-path>
```

Successful execution means every owner/filename pair accepts only its own authentic digest,
the complete downloader suite passes without live network access, and existing HTTPS,
unknown-file, retry, and corrupt-file deletion tests remain green.

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| ProjectHephaestus | Dataset downloader checksum-scoping plan | `unverified`: Torchvision source values were corroborated, but the implementation, local tests, and CI were not run in this learning session. |

## References

- [Torchvision MNIST and Fashion-MNIST resource manifests](https://github.com/pytorch/vision/blob/main/torchvision/datasets/mnist.py)
- [Testing Python CLI Apps with Mocked Subprocess and HTTP](./testing-cli-mock-subprocess-http.md)
