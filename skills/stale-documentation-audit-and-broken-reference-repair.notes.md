# Stale Documentation Repair — Case Notes

These notes retain project-specific evidence moved during
[Mnemosyne #3335](https://github.com/HomericIntelligence/Mnemosyne/issues/3335).

## Case index

| Case | Source | Status | Disposition |
| --- | --- | --- | --- |
| Scylla doc-drift corpus | ProjectScylla issues #753, #758, #880, #1112, #1477, #1503, #1507 | mixed verified | Future work, counts, roles, contradictions, phantom paths, anchors |
| Scylla targeted repairs | [PR #954](https://github.com/HomericIntelligence/ProjectScylla/pull/954), [#811](https://github.com/HomericIntelligence/ProjectScylla/pull/811), [#925](https://github.com/HomericIntelligence/ProjectScylla/pull/925), [#1362](https://github.com/HomericIntelligence/ProjectScylla/pull/1362), [#990](https://github.com/HomericIntelligence/ProjectScylla/pull/990) | verified-ci | Broken references, policy examples, tier/version labels, future-work annotations |
| Hephaestus ADR LoC | [Issue #1177](https://github.com/HomericIntelligence/ProjectHephaestus/issues/1177) / [PR #1281](https://github.com/HomericIntelligence/ProjectHephaestus/pull/1281) | verified-ci | Re-measured `26,125 / 48,498 = 53.9%`; updated all scoped copies |
| Stale installer citations | [Issue #1222](https://github.com/HomericIntelligence/ProjectHephaestus/issues/1222) | verified-local | Located constructs by content; independent stale line ranges |
| Phantom shared directory | [Issue #1211](https://github.com/HomericIntelligence/ProjectHephaestus/issues/1211) / [PR #1236](https://github.com/HomericIntelligence/ProjectHephaestus/pull/1236) | verified-ci | Removed unsupported `.claude/shared/` reference |
| Onboarding consolidation | [Issue #1216](https://github.com/HomericIntelligence/ProjectHephaestus/issues/1216) | unverified plan | Consolidate duplicated setup onto `just bootstrap` |
| Version-currency guard | [Issue #1208](https://github.com/HomericIntelligence/ProjectHephaestus/issues/1208) | unverified plan | Hatch-vcs/tag authority and `>=` semantics |
| Count-annotates-list | Hephaestus issues #2351/#2373 | salvaged evidence | Reconcile caption with curated list, not raw filesystem |
| Pixi command validation | Hephaestus issues #2352/#2372 | verified-ci for prefix rule | Feature `dev` was not an environment; use `pixi run` for env tools |
| Manifest count drift | Hephaestus issues #2397/#2398 | salvaged evidence | Enforced artifact beats prose; phrase-scoped grep |
| File-line citation/lint skip | Hephaestus issues #2399/#2401 | salvaged evidence | Content-anchored citation; skipped hook is not lint evidence |
| Mixed recipe naming | [Odysseus #182](https://github.com/HomericIntelligence/Odysseus/issues/182) / [PR #312](https://github.com/HomericIntelligence/Odysseus/pull/312) | verified-local | One claimed phantom already fixed; corrected only `nestor-start` |
| Recursive normative docs | ProjectHephaestus implementation plan, 2026-07-20 | unverified plan | Recursive scope, semantic sources, injected dates, read-only hook |

## Durable case details

The LoC repair measured the current tree rather than copying the audit and used a phrase-scoped
search to locate duplicates. The citation case found separate documents had independently stale
line ranges; replacing them with another current line number would merely restart the drift.

The Pixi cases distinguish features from environments. `pixi run -e dev` failed because `dev` was
not declared under environments. Separately, bare environment-tool commands failed on clean PATHs;
documentation needed `pixi run pre-commit`, `pixi run pytest`, and equivalents.

The Odysseus justfile mixed naming conventions: Agamemnon/Nestor recipes were verb-first while
Hermes/Argus/Keystone were prefix-first. Ground-truth enumeration showed only one of two reported
phantoms still existed, demonstrating why all entries need live cross-checking but only actual
defects should change.

## Verification boundaries

The base workflow includes CI-confirmed repairs. Onboarding consolidation, tag-based currency, and
recursive living-document governance were planning artifacts with no implementation/CI evidence.
Historical case numbers remain evidence records rather than current universal values.
