# Python Packaging and Editable Install Notes

Supporting cases for
[`python-packaging-pyproject-editable-install.md`](python-packaging-pyproject-editable-install.md).

## Case Index

| Case | Source | Verification | Material result |
| --- | --- | --- | --- |
| hatch-vcs dynamic version migration | [Immutable source](https://github.com/HomericIntelligence/Mnemosyne/blob/d377a8924aff84e5cc193b720130b4c57e38c5c3/skills/python-packaging-pyproject-editable-install.md) | verified-local | Aligned build backend, generated file, metadata lookup, and invariant checks |
| Distribution-name correction | [ProjectHephaestus PR #434](https://github.com/HomericIntelligence/ProjectHephaestus/pull/434) | verified-local | Resolved metadata lookup using published distribution identity |
| Stale editable console script | [ProjectHephaestus PR #707](https://github.com/HomericIntelligence/ProjectHephaestus/pull/707) | verified-local | Editable reinstall regenerated entry points after pull |
| Full console-script inventory | [ProjectHephaestus PR #603](https://github.com/HomericIntelligence/ProjectHephaestus/pull/603) | verified-local | Pyproject enumeration found callable names missed by `def main` grep |
| Hatchling artifacts and trusted publishing | [ProjectScylla PR #1905](https://github.com/HomericIntelligence/ProjectScylla/pull/1905) | verified-ci | Built wheel/sdist and exercised OIDC publishing contract |
| Coordinator resource preflight | [ProjectHephaestus issue #2283](https://github.com/HomericIntelligence/ProjectHephaestus/issues/2283) | unverified | Proposed pre-side-effect render and exact source/wheel/sdist parity |

## Evidence Detail

The editable-install case distinguished importability from generated console metadata: the module
loaded while the executable was absent until the environment was reinstalled. The CLI sweep used the
manifest’s script table and found callable suffixes a source grep omitted.

The package-data preflight case remained an implementation plan. Its error classification,
side-effect ordering, and source-to-artifact equality rules are retained without claiming CI proof.

## Provenance

- Superseded main SHA-256: `b76b6eab5476a3d8e063d2c0d9630df0052f68ec978ec336b242af191c33e4da`
- Issue #3335 base: `d377a8924aff84e5cc193b720130b4c57e38c5c3`
- Old/new version: `1.3.0` → `2.0.0`
