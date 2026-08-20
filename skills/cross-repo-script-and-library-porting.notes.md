# Cross-Repository Porting — Notes

## Case index

| Case | Source | Verification | Disposition |
| --- | --- | --- | --- |
| Port automation library in dependency-layer PRs | [immutable source documenting ProjectHephaestus PRs #209–#212](https://github.com/HomericIntelligence/Mnemosyne/blob/d377a8924aff84e5cc193b720130b4c57e38c5c3/skills/cross-repo-script-and-library-porting.md) | `verified-ci` in recorded campaign | Retained sequential layering and source-cleanup-last rules |
| Port validation/resilience scripts and modules | [ProjectHephaestus PR #213](https://github.com/HomericIntelligence/ProjectHephaestus/pull/213) | `verified-ci` across recorded PR series | Retained per-script adaptation and dependency elimination |
| Port staged 15-file automation module | [ProjectHephaestus PR #268](https://github.com/HomericIntelligence/ProjectHephaestus/pull/268) | `verified-ci`: 596 tests, 80.63% coverage | Retained destination-as-base and full-surface verification |
| Modular Apache-2.0 skills integration | [Mnemosyne PR #1213](https://github.com/HomericIntelligence/Mnemosyne/pull/1213) | `verified-ci` | Retained overlap, license, format, and attribution audit |
| Third-party MIT skills integration | [ProjectHephaestus PR #206](https://github.com/HomericIntelligence/ProjectHephaestus/pull/206) | `verified-ci` in recorded campaign | Retained canonical-skill merge and hook-scope decisions |

## Port inventory template

Record source/destination SHAs, license, public symbols, CLI flags/exit codes, dependency edges,
configuration sources, tests, packaging entry points, supported runtimes, destination-only deltas,
and source cleanup consumers.

## Nuance retained

- A lockfile is coupled to the manifest CI actually installs, not necessarily the local environment
  file used by developers.
- Dependency elimination is valid only when the replacement preserves authentication, structured
  data, timeouts, and error behavior.
- Cross-repo staging code must be treated like any other source revision; it does not outrank live
  destination fixes.
- Source shims are useful only if the destination is installable and downstream consumers can
  resolve it.
- License compatibility and required attribution are per-source facts, not implied by “open source.”

## Evidence boundary

The indexed campaigns verify their own source/destination pairs. A new port requires fresh overlap,
dependency, license, and runtime analysis.
