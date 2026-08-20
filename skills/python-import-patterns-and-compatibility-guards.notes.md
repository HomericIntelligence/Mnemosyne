# Python Import Patterns and Compatibility Guards — Case Notes

These notes retain project-specific evidence moved during
[Mnemosyne #3335](https://github.com/HomericIntelligence/Mnemosyne/issues/3335).

## Case index

| Case | Source | Status | Disposition |
| --- | --- | --- | --- |
| Local correlation-ID import | [ProjectHephaestus PR #633](https://github.com/HomericIntelligence/ProjectHephaestus/pull/633) | verified-ci | Deferred initialization; did not establish graph acyclicity |
| Automation lazy exports | [Issue #775](https://github.com/HomericIntelligence/ProjectHephaestus/issues/775) / [PR #968](https://github.com/HomericIntelligence/ProjectHephaestus/pull/968) | verified-ci | Synchronized `__all__`, lazy map, type imports, phase exclusions, surface test |
| Add/add export conflict | [Issue #799](https://github.com/HomericIntelligence/ProjectHephaestus/issues/799) / [PR #988](https://github.com/HomericIntelligence/ProjectHephaestus/pull/988) | verified-local | Rebase kept one peer entry; merge conflict was the blocker |
| Stale strict surface pin | [PR #1067](https://github.com/HomericIntelligence/ProjectHephaestus/pull/1067) | verified-local | Updated test literal after proving peer export legitimate; no source rollback |
| `tomllib` matrix guard | [PR #657](https://github.com/HomericIntelligence/ProjectHephaestus/pull/657) | verified-ci | `sys.version_info` branch plus conditional `tomli` dependencies |
| Windows importability | [Issue #539](https://github.com/HomericIntelligence/ProjectHephaestus/issues/539) | verified-ci | `curses`/`fcntl` guards and Windows `tzdata` |
| Lazy deprecation warning | [Issue #1545](https://github.com/HomericIntelligence/ProjectHephaestus/issues/1545) | verified-local | Warned in `__getattr__`, cache-busted test, retained direct-call warning |
| CLI public re-exports | [Issue #1511](https://github.com/HomericIntelligence/ProjectHephaestus/issues/1511) | verified-local | Eager identity-preserving re-exports; subset surface assertion |
| API-table alignment | [Issue #1419](https://github.com/HomericIntelligence/ProjectHephaestus/issues/1419) | verified-local | Same-cycle version anchor; whole validation module required |
| Logging stable surface | [Issue #1513](https://github.com/HomericIntelligence/ProjectHephaestus/issues/1513) | unverified plan | Export/identity/table plan; original tag-arithmetic assumption superseded |
| Lazy `__dir__` | [Issue #1512](https://github.com/HomericIntelligence/ProjectHephaestus/issues/1512) | unverified plan | Union globals, declared exports, lazy names; subset tests |
| Runtime graph acyclicity | Reviewed implementation plan | unverified plan | AST graph + neutral leaf + Tarjan SCC; not executed |

## Durable case details

The stale-surface case failed with an extra legitimate symbol after an independent PR landed.
Environment-only local failures were separated from the real assertion by running with a clean
environment and checking CI logs. The production surface stayed unchanged.

For access-time deprecation, the issue named `__all__`, but the symbol actually lived in the lazy
map. The test removed the cached module attribute before access, asserted the warning points at the
caller with `stacklevel=2`, and kept the call-time warning for direct imports.

The API-table validator scanned the live tree. Its single test could pass alone even with a missing
row and fail only in the full module. The authoritative run was the complete validation module.
The “since” value came from same-cycle sibling symbols, not latest-tag arithmetic.

## Verification boundaries

The complete runtime-graph design and `__dir__` plan remain unverified. Local cases had focused
tests/lint/type checks but pending CI at capture. Only the rows marked `verified-ci` establish remote
evidence.
