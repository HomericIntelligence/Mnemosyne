---
name: python-pinned-release-asset-install
description: "Install an exact Python release version from authoritative release assets when the configured index lacks that version or the bare package name is ambiguous. Use when a pinned install must come from a verified wheel, when the import name differs from the distribution name, or when a publisher attestation cannot be checked through the forge API."
category: tooling
date: 2026-11-23
version: "1.0.0"
user-invocable: false
tags:
  - python-install
  - pinned-version
  - release-asset
  - wheel
  - attestation
  - requires-python
  - extras
  - version-verification
---

# Pinned Python Release Install From Authoritative Assets

## Overview

| Field | Value |
| ----- | ----- |
| **Date** | 2026-11-23 |
| **Objective** | Install the exact requested release of a Python distribution and prove the source, the version, and the runtime surface. |
| **Outcome** | Successful in one local session; the pinned wheel was installed in an isolated environment and verified. CI consumption is pending. |

An exact-version request is not a newest-version request. The configured index
can omit the requested version, and a short package name can belong to an
unrelated distribution. Treat the project's own install documentation and its
official release assets as the source of truth.

## When to Use

Use this skill when one or more of these conditions applies:

- A user requests an exact release version that the configured package index does not list.
- The distribution name differs from the import name, or a search for the short name finds an unrelated distribution.
- A release wheel ships with a publisher attestation that the forge attestation API cannot verify.
- The default interpreter on the host does not satisfy the distribution's `requires-python` range.

Do not use this skill to choose a newer version or to consolidate copies across
environments. For that intent, use
[python-multi-env-install-consolidation](python-multi-env-install-consolidation.md).

## Verified Workflow

### Quick Reference

```bash
DIST="distribution-name-from-project-docs"; VERSION="X.Y.Z"; PKG="import-name"

# 1. Confirm the exact tag and its release assets from the official release.
forge release view "v${VERSION}" --repo OWNER/REPO --json assets

# 2. Create an isolated venv with a compatible interpreter.
uv venv --python COMPATIBLE_VERSION ./venv

# 3. Download the wheel and its attestation from that exact release.
forge release download "v${VERSION}" --repo OWNER/REPO \
  -p "*${VERSION}-py3-none-any.whl" -p "*.attestation"

# 4. Verify the wheel digest against the attestation subject digest.

# 5. Install with the required extras from the local wheel path.
uv pip install --python ./venv/bin/python "./wheel-${VERSION}-py3-none-any.whl[EXTRA]"

# 6. Verify the exact version and one real command.
./venv/bin/python -c "import ${PKG}, importlib.metadata as m; \
  print(${PKG}.__version__, m.version('${DIST}'))"
./venv/bin/console-script --help
```

Replace `forge`, `OWNER/REPO`, `DIST`, `PKG`, `VERSION`, `EXTRA`, and the script
name with values from the project's own documentation.

### Suggested Approach

1. **Resolve identity from project-authored material.** Read the distribution
   name, import name, and install command from the project's own install
   documentation. An index lookup by the short name can return an unrelated
   distribution whose versions look plausible. Compare the index result with
   the requested version before any install.
2. **Select the source before the command.** When the index omits the requested
   version, use the wheel attached to the exact release tag. Do not substitute
   a branch tip, a local source checkout, or a nearby version. If no asset
   matches the tag, report the limit and ask for direction before a source
   build.
3. **Bind the environment to the project constraint.** Read `requires-python`
   from the project metadata. When the host default interpreter is outside
   that range, create a dedicated venv with a compatible interpreter. Do not
   change a shared environment to satisfy one install request.
4. **Verify provenance at the download boundary.** Compute the wheel SHA-256
   and compare it with the digest in the attestation statement subject. When
   the forge attestation API returns 404 for a publisher attestation, report
   that signature verification is unverified and keep the digest comparison.
   A 404 of this kind is a verification limit, not a tampering finding. Do not
   claim a verified signature from a digest match alone.
5. **Carry the extras into the install.** Quote the local wheel path with its
   extras so the shell does not expand the brackets. Omitting an extra can
   install the right version and still leave a console script unusable.
6. **Verify closure.** Require the import version and the installed metadata
   version to equal the requested version exactly; a shared prefix is not a
   match. Run one real console-script smoke command. A successful import alone
   does not prove the product surface is usable.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| ------- | -------------- | ------------- | -------------- |
| 1 | Look up the requested package by its short name on the configured index. | The short name belonged to an unrelated distribution, and the index did not list the requested version. | Confirm the distribution name from project-authored documentation and compare available versions before installation. |
| 2 | Rely on the configured index for the pinned release. | The index did not list the requested version. | Use the wheel from the exact official release tag when the index lacks the version. |
| 3 | Check the release attestation through the forge attestation API. | The API returned 404 for a publisher attestation that was shipped as a release asset. | Compare the wheel digest with the attestation subject digest and report signature verification as unverified. |

## Results & Parameters

### Configuration

```yaml
source_selection:
  identity: "distribution and import names from project install documentation"
  release: "exact tag that matches the requested version"
environment:
  interpreter: "compatible with requires-python from project metadata"
  isolation: "dedicated virtual environment"
provenance:
  wheel_digest: "sha256 of the downloaded wheel"
  attestation_subject: "digest in the in-toto statement subject"
  forge_api_result: "a 404 for a publisher attestation is a verification limit"
install:
  form: "local wheel path with required extras, quoted"
verification:
  version: "import version and installed metadata version equal the request exactly"
  runtime: "one console-script --help or --version run exits zero"
```

### Expected Output

- The wheel digest equals the attestation subject digest.
- The import version and the installed metadata version both equal the requested version.
- A required console script runs and exits zero.
- Any unverifiable signature check is reported as a limit, not as success.

## Verified On

| Project | Context | Details |
| ------- | ------- | ------- |
| Public open-source Python distribution with an organization-prefixed name | Developer workstation, pinned release install | One local session produced the workflow; see [notes](python-pinned-release-asset-install.notes.md). |

## References

- [pip install documentation](https://pip.pypa.io/en/stable/cli/pip_install/)
- [uv documentation](https://docs.astral.sh/uv/)
- [PyPI attestations](https://docs.pypi.org/attestations/)
- [in-toto attestation framework](https://in-toto.io/attestation/)
- Related: [python-multi-env-install-consolidation](python-multi-env-install-consolidation.md)
- Related: [release-version-verification-tag-wheel-exact-match](release-version-verification-tag-wheel-exact-match.md)
