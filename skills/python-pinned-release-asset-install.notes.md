# Pinned Python Release Install: Supporting Evidence

## Scope and verification

- Source: one interactive install session on a developer workstation.
- Verification level: `verified-local`. The workflow ran end to end. No CI run
  consumed this entry.
- Requested outcome: an exact release version installed locally, with a
  usable command surface.

## Generalized conditions from the source

- The configured package index listed only older releases of the target
  distribution. The exact requested version was absent.
- A search for the short package name returned an unrelated distribution with
  unrelated release versions. The project's own install documentation named a
  prefixed distribution and a short import name.
- The project metadata declared a `requires-python` range narrower than the
  host default interpreter. A dedicated virtual environment with a compatible
  interpreter was required.
- The project published a wheel and a publisher attestation as release assets.
  The forge attestation API had no record for that asset digest and returned
  404. The attestation was still present in the release assets.

## Public technical facts used

- Publisher attestations can be in-toto statements with a PyPI publish
  predicate. The subject carries a SHA-256 digest of the wheel.
- A forge attestation API does not necessarily index publisher attestations
  that are attached only as release assets. A 404 from that API is not proof
  of a bad artifact.
- A local wheel path can carry extras in brackets on an install command. Quote
  the whole path so the shell does not expand the brackets.

## Commands used, with evidence generalized

```bash
# Identity and releases came from project-authored documentation.
forge release view "v${VERSION}" --repo OWNER/REPO --json assets

uv venv --python COMPATIBLE_VERSION ./venv
forge release download "v${VERSION}" --repo OWNER/REPO \
  -p "*${VERSION}-py3-none-any.whl" -p "*.attestation"

# Digest check: wheel SHA-256 equals the in-toto statement subject digest.
# Signature verification through the forge API was unavailable (404).

uv pip install --python ./venv/bin/python "./wheel-${VERSION}-py3-none-any.whl[all]"
./venv/bin/python -c "import PKG, importlib.metadata as m; \
  print(PKG.__version__, m.version('DIST'))"
./venv/bin/console-script --help
```

## Observed results

- Wheel digest and attestation subject digest matched exactly.
- Import version and installed metadata version both equaled the requested
  version.
- The product-layer import succeeded.
- A real console-script `--help` run printed arguments and exited zero.

## Intent boundaries

- `python-multi-env-install-consolidation` covers enumeration of copies,
  canonical environment selection, `requires-python`, extras, and version plus
  CLI verification. It assumes the requested release is obtainable from a
  configured index.
- `release-version-verification-tag-wheel-exact-match` covers release
  publication authority and the tag-to-wheel check before publishing. It does
  not cover selecting an artifact for a local install.
- This entry covers the gap: source selection and provenance verification when
  an exact install request cannot be satisfied by the configured index.

## Privacy note

No internal paths, hostnames, account names, monitor identifiers, project
identifiers, or environment-specific configuration values are recorded here.
Only the general decision rule, public technical conventions, and generalized
verification results are preserved.
