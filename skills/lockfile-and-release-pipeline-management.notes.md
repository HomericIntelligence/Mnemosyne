# Lockfile and Release Pipeline Notes

Supporting cases for
[`lockfile-and-release-pipeline-management.md`](lockfile-and-release-pipeline-management.md).

## Case Index

| Case | Source | Verification | Material result |
| --- | --- | --- | --- |
| Verbatim known-green lock recovery | [Immutable source](https://github.com/HomericIntelligence/Mnemosyne/blob/d377a8924aff84e5cc193b720130b4c57e38c5c3/skills/lockfile-and-release-pipeline-management.md) | verified-ci | Restored generated lock only after manifest equality and main evidence |
| npm manifest/lock resynchronization | [Immutable source](https://github.com/HomericIntelligence/Mnemosyne/blob/d377a8924aff84e5cc193b720130b4c57e38c5c3/skills/lockfile-and-release-pipeline-management.md) | verified-local | Regenerated root entries and proved clean `npm ci` |
| Release no-op recovery and single version source | [Immutable source](https://github.com/HomericIntelligence/Mnemosyne/blob/d377a8924aff84e5cc193b720130b4c57e38c5c3/skills/lockfile-and-release-pipeline-management.md) | verified-ci | Made bump/commit conditional and validated metadata/tag identity |
| Multi-ecosystem Renovate setup | [Immutable source](https://github.com/HomericIntelligence/Mnemosyne/blob/d377a8924aff84e5cc193b720130b4c57e38c5c3/skills/lockfile-and-release-pipeline-management.md) | verified-local | Covered native managers and checked nonzero discovery |
| Garbage-collected nightly pin | [Immutable source](https://github.com/HomericIntelligence/Mnemosyne/blob/d377a8924aff84e5cc193b720130b4c57e38c5c3/skills/lockfile-and-release-pipeline-management.md) | verified-ci | Proved artifact absence, repinned available build, regenerated lock |
| Dependabot contract stabilization | [Immutable source](https://github.com/HomericIntelligence/Mnemosyne/blob/d377a8924aff84e5cc193b720130b4c57e38c5c3/skills/lockfile-and-release-pipeline-management.md) | verified-ci | Replaced current-version literals with structural parity and grouped exact peers |

## Evidence Detail

The full source contains exact manifests, resolver commands, version examples, configuration blocks,
and dependency-family incidents. Those remain historical evidence. The compact workflow requires
the target repository’s current resolver version, channel availability, and release policy.

Verbatim restoration and regeneration are mutually exclusive dispositions: manifest equality plus a
known-green base supports restore; any source change or unavailable pin requires a fresh resolution.

## Provenance

- Superseded main SHA-256: `30b5740fb3ba63eab80a18e90c0b3639f5c842ff0f52685ae1ec40f8df9c7b39`
- Issue #3335 base: `d377a8924aff84e5cc193b720130b4c57e38c5c3`
- Old/new version: `1.2.0` → `2.0.0`
