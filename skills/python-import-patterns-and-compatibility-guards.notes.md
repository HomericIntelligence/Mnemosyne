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
| Runtime graph acyclicity | [Immutable archived plan](https://github.com/HomericIntelligence/Mnemosyne/blob/1ae0cb498e5250c341c2a4bf585f97e2a28060af/skills/python-import-patterns-and-compatibility-guards.md) | unverified plan | AST graph + neutral leaf + Tarjan SCC; originally not executed |
| Import-form prefix edge | anonymized repository with acyclic automation runtime graph guard | verified-local | The guard first reported one cycle, then none after the import form changed; the leaf module and its dependencies were identical in both runs |

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

## Import-form prefix edge detail

A session added a new leaf module to a package whose initializer imports the module that consumes
the leaf. The consumers first imported the leaf as a relative `from . import <leaf> as <alias>`.
The acyclic-graph guard reported one strongly connected component that covered the package, the
coordinator modules, the stage package, and the new leaf.

The cause was the guard's target resolver, not the module layout. For an absolute
`from <prefix>.a.b import c`, the resolver yields every module prefix plus each resolvable child,
so the edge reaches `<prefix>`. For a relative `from . import c`, it yields the resolved parent
package plus the child, so the edge also reaches the package. Only `import <prefix>.a.b as name`
yields the leaf alone, because the prefix walk keeps a package prefix only when that package
initializer performs a runtime import.

The repair changed three import sites from the relative form to the fully qualified leaf form and
adapted the three call sites. No module moved and no dependency direction changed. The guard then
reported zero components.

The verification sequence that made the rule trustworthy, all reproduced with the guard's own
functions rather than by inspection:

1. Resolve the targets of each import form against the real module set. The relative form yielded
   the package and the leaf; the fully qualified form yielded the leaf only.
2. Inject the pre-repair edge into the current graph. The component count returned from zero to one,
   which proved the removed edge was exactly the closing edge.
3. Run the full guard module. It passed with a nonempty collection.

The reusable rule is to evaluate the proposed import line with the guard's resolver before the
commit, because the two forms look equivalent in ordinary Python yet differ in the graph. Comparing
the node sets directly is cheaper than reading the resolver source and reasoning about it.

## Verification boundaries

The complete runtime-graph design and `__dir__` plan remain unverified. Local cases had focused
tests/lint/type checks but pending CI at capture. Only the rows marked `verified-ci` establish remote
evidence.
