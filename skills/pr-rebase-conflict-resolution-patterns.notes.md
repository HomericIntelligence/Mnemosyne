# PR Rebase and Conflict Resolution Patterns — Case Notes

These notes preserve project-specific evidence and worked-case provenance from
version 1.15.0. The complete v1.15.0 retrievable content is archived once in the
[history file](./pr-rebase-conflict-resolution-patterns.history).

## Case Index

| Case | Source | Status | Retained lesson |
| --- | --- | --- | --- |
| Large rebase queues | [Archived multi-repository queue sessions](./pr-rebase-conflict-resolution-patterns.history) | verified-ci / verified-local | Fix trunk first, isolate branches, serialize shared hot files |
| Stacked fixes | Mnemosyne [PR #1976](https://github.com/HomericIntelligence/Mnemosyne/pull/1976) / [PR #1978](https://github.com/HomericIntelligence/Mnemosyne/pull/1978); Odyssey [PR #3189](https://github.com/HomericIntelligence/Odyssey/pull/3189) | verified-ci / verified-local | Retargeting does not carry later fixes; prove and cherry-pick orphan commits |
| Full rewrite versus small delta | [Odysseus PR #64](https://github.com/HomericIntelligence/Odysseus/pull/64) | verified-local | Keep the coherent rewrite and port the small edit |
| Already-upstream add/add | Hephaestus [PR #967](https://github.com/HomericIntelligence/Hephaestus/pull/967), [issue #768](https://github.com/HomericIntelligence/Hephaestus/issues/768) | verified-local | Compare both versions and final diff; close if superseded |
| DIRTY with green checks / modify-delete | Hephaestus [PR #1014](https://github.com/HomericIntelligence/Hephaestus/pull/1014) / [PR #720](https://github.com/HomericIntelligence/Hephaestus/pull/720) | verified-ci | Conflict is the blocker; verify stale base before deletion |
| SHA-pin policy blocks required dependency | [Archived 2026-06-13 Mnemosyne session](./pr-rebase-conflict-resolution-patterns.history) | verified-ci | Rebase to inherit pinned workflow; empty commit cannot repair stale YAML |
| Parallel module extraction | Hephaestus [PR #1360](https://github.com/HomericIntelligence/Hephaestus/pull/1360) / [PR #1361](https://github.com/HomericIntelligence/Hephaestus/pull/1361) | verified-ci | Trunk source plus union of unique tests; 1,747 tests passed |
| Cross-PR semantic collision | Hephaestus [PR #1336](https://github.com/HomericIntelligence/Hephaestus/pull/1336) / [PR #1337](https://github.com/HomericIntelligence/Hephaestus/pull/1337), fix [PR #1340](https://github.com/HomericIntelligence/Hephaestus/pull/1340) / [issue #1339](https://github.com/HomericIntelligence/Hephaestus/issues/1339) | verified-local at capture | Prove common failure on trunk and fix once |
| AA without markers | [Odyssey PR #5500](https://github.com/HomericIntelligence/Odyssey/pull/5500) | verified-local | Use status codes and inspect `HEAD`/`REBASE_HEAD`; skip upstream-equivalent commits |
| Same-file serial train | [Archived Hephaestus issue/PR train](./pr-rebase-conflict-resolution-patterns.history) | verified-ci | Smallest diff first; union helpers and thin delegates; re-sign replayed commits |
| Mock/API divergence | Hephaestus [PR #1633](https://github.com/HomericIntelligence/Hephaestus/pull/1633), [issue #1405](https://github.com/HomericIntelligence/Hephaestus/issues/1405) | verified-ci | Regenerate tests against current implementation; 335 focused tests passed |
| False rebase success | [Hephaestus PR #1657](https://github.com/HomericIntelligence/Hephaestus/pull/1657) | verified-ci | Verify merge base and a known trunk-only symbol after push |
| Half-applied layered timeout contract | [Hephaestus PR #1657](https://github.com/HomericIntelligence/Hephaestus/pull/1657) | verified-ci | Check constants, readers, helpers, defaults, callers, and contract tests |
| Import-line union | [Hephaestus issue #1429](https://github.com/HomericIntelligence/Hephaestus/issues/1429) | verified-local | Union symbols, lint, and import at runtime |
| Dirty Inference Service checkout | [Archived Inference Service PR #289 evidence](./pr-rebase-conflict-resolution-patterns.history) | verified-ci | Preserve staged work, use `origin/master`, keep Warden names and `srun --mem=0`; 489 tests passed |
| HAProxy lifecycle reconciliation | [Archived 2026-07-07 Warden branch evidence](./pr-rebase-conflict-resolution-patterns.history) | verified-local | Keep `-sf` process replacement and master-CLI stats; 557 targeted and 1,227 pre-push tests passed; image validation unavailable |
| Silent complexity/test/policy/inventory drift | [Hephaestus PR #2056](https://github.com/HomericIntelligence/Hephaestus/pull/2056) | verified-local | Whole-tree lint, tests, whole-file policy search, and inventory hooks catch distinct defects |

## Additional Ecosystem Evidence

- ProjectOdyssey: PR #3097 had 23 conflicts; PR #5348 required semantic
  resolution; PRs #5485/#5487 required optimizer numeric-equivalence checks, with
  the unproven Shampoo change deferred to #5491.
- ProjectScylla: PR #1931 ported a feature after #1929 decomposed `runner.py`;
  issue/PR chain #832 to #882 exercised deletion across a rebase.
- ProjectKeystone: PRs #577-#581 used decouple, port, then delete under ADR-015/016.
- ProjectNestor: PRs #83/#87/#94/#97/#99/#101 formed a serial hot-file train;
  #101 exposed accidental clang-format on CMake and the need for a local build.
- AchaeanFleet PR #661 exposed a TypeScript shadow/TDZ failure created only by
  combining two branches.
- Agamemnon PRs #419/#420/#421 and Odysseus PR #43 preserved extraction and NATS
  reconciliation behavior; Agamemnon #422 used an empty commit only to retrigger
  absent checks, not to repair stale workflow policy.

## Semantic Audit for v2.0.0

The compaction retained every materially distinct action from v1.15.0:

- triggers for single, stacked, mass, same-file, add/add, modify/delete, workflow-
  policy, full-rewrite, semantic-collision, and clean-but-broken rebases;
- the rebase inversion of ours/theirs, status-code diagnosis, both-stage reads,
  generated-file regeneration, import/test union, serial trains, superseded-PR
  detection, signature renewal, explicit force leases, and auto-merge re-arming;
- checks for current merge base, trunk-only behavior, markers, whole-tree lint,
  tests, type/build contracts, policy restatements, inventories, mocks, and layered
  APIs;
- named failed approaches and their corrective decisions;
- verification boundaries, including the unavailable Inference Service image
  validation and cases that were local-only at capture.

Repeated command transcripts, exact historical SHAs, long project narratives,
and duplicate tables moved here or remain in history. No unverified evidence was
upgraded.
