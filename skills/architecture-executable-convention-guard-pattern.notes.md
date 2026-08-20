# Architecture Executable Convention Guard — Case Notes

These notes retain project-specific evidence moved out of the retrievable skill during
[Mnemosyne #3335](https://github.com/HomericIntelligence/Mnemosyne/issues/3335).
The complete superseded main is archived in the companion history.

## Case index

| Case | Source | Status | Disposition |
| --- | --- | --- | --- |
| Crash-bundle invocation marker | [ProjectHephaestus #1207](https://github.com/HomericIntelligence/ProjectHephaestus/issues/1207) / [PR #1247](https://github.com/HomericIntelligence/ProjectHephaestus/pull/1247) | verified-ci | Library-first predicate, read-only resolution, prefix markers, exit 3 |
| Reverse source/test parity | [ProjectHephaestus #1543](https://github.com/HomericIntelligence/ProjectHephaestus/issues/1543) | unverified plan | Add reverse difference and rationalized allowlist; cover orchestrator stderr branch |
| Ghost package directories | [ProjectHephaestus #1448](https://github.com/HomericIntelligence/ProjectHephaestus/issues/1448) / [PR #1703](https://github.com/HomericIntelligence/ProjectHephaestus/pull/1703) | verified-local | Fourth check in existing orchestrator; both fixture sides require `__init__.py` |
| API-table membership guard | [ProjectHephaestus #1506](https://github.com/HomericIntelligence/ProjectHephaestus/issues/1506), [#1507](https://github.com/HomericIntelligence/ProjectHephaestus/issues/1507) | unverified plan | Guard membership only; parser-empty branch; scope lock to named packages |
| DCO trailer guard | [ProjectHephaestus #1516](https://github.com/HomericIntelligence/ProjectHephaestus/issues/1516) | unverified plan | Parse full final trailer block; dual PR-policy/commit-msg integration |
| Install smoke self-test | [ProjectKeystone #596](https://github.com/HomericIntelligence/ProjectKeystone/issues/596) / [PR #600](https://github.com/HomericIntelligence/ProjectKeystone/pull/600) | verified-local | Installed-layout parity and downstream `find_package` consumer; mutated negative copies |
| Dataset `release` check | [Myrmidons #751](https://github.com/HomericIntelligence/Myrmidons/issues/751) | verified-local | Deterministic archive + manifest; empty-data refusal; read/write job split |
| Publish-pipeline validator | [ProjectScylla #2027](https://github.com/HomericIntelligence/ProjectScylla/issues/2027) | unverified plan | Validate tag/OIDC/pins/dist versions without publishing |
| Scripts catalog completeness | [ProjectHephaestus #2168](https://github.com/HomericIntelligence/ProjectHephaestus/issues/2168) | unverified plan | `git ls-files` population; backticked relative paths; prose descriptions |

## Durable case details

The ghost-package implementation reused `check_test_structure` and its already-required gate.
The detector intersects source/test package sets after their existing filters; an empty test
directory is therefore not a valid negative fixture. Both sides need package markers. Tests must
cover the helper and the orchestrator so formatting/exit behavior cannot remain uncovered.

The install smoke case installed into a clean staging prefix, checked archives and CMake package
files, compared source/installed headers in both directions, and compiled a minimal static-library
consumer. It explicitly failed on missing/empty header directories before `diff`, then reran layout
checks against a copy with a header and archive removed. Container-absolute install metadata meant
install and consumer configuration had to run in the same container.

The dataset release case derived deterministic metadata from the commit, refused an empty dataset,
and split read-only validation from tag-gated publishing. Under `pipefail`, archive membership was
captured once before searching; piping `tar` into `grep -q` risks SIGPIPE. Third-party action pins
were resolved against the intended tag before use.

## Verification boundaries

`verified-local` means the recorded commands passed locally but CI was pending at capture. The
ProjectHephaestus parity/table/DCO/catalog designs and ProjectScylla release validator were plans
only. Do not promote them without implementation evidence.
