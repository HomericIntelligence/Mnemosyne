# Git Branch State Triage and Recovery Notes

Supporting cases for
[`git-branch-state-triage-and-recovery.md`](git-branch-state-triage-and-recovery.md).

## Case Index

| State/case | Source | Verification | Result |
| --- | --- | --- | --- |
| Corpus branch superseded after consolidation | [Immutable source snapshot](https://github.com/HomericIntelligence/Mnemosyne/blob/1ae0cb498e5250c341c2a4bf585f97e2a28060af/skills/git-branch-state-triage-and-recovery.md) for Mnemosyne `feature/myrmidon-merge-triage` | verified-local | Three-way counts and content proved old originals were absorbed |
| Unrelated-history branch | [Immutable source snapshot](https://github.com/HomericIntelligence/Mnemosyne/blob/1ae0cb498e5250c341c2a4bf585f97e2a28060af/skills/git-branch-state-triage-and-recovery.md) for Mnemosyne `skill/debugging/fixme-todo-cleanup-v2` | verified-local | Content already on main; classified orphan/superseded |
| Diverged BF16 fix | ProjectOdyssey [issue #3088](https://github.com/HomericIntelligence/Odyssey/issues/3088), [PR #3197](https://github.com/HomericIntelligence/Odyssey/pull/3197) | verified-local | Reset to remote tip and cherry-picked intended fix |
| Squash-merge false positives | ProjectHephaestus [issue #1041](https://github.com/HomericIntelligence/Hephaestus/issues/1041), [#1282](https://github.com/HomericIntelligence/Hephaestus/issues/1282), and [#1335](https://github.com/HomericIntelligence/Hephaestus/issues/1335) | verified-local | Message/content search proved all branches subsumed |
| Selective replay after premature merge | LLM360/Inference360 [PR #460](https://github.com/LLM360/Inference360/pull/460) and [PR #462](https://github.com/LLM360/Inference360/pull/462) | verified-ci | Missing commits replayed; artifact rebuilt and exact-head review passed |
| Uncommitted follow-up on merged branch | [Immutable source snapshot](https://github.com/HomericIntelligence/Mnemosyne/blob/1ae0cb498e5250c341c2a4bf585f97e2a28060af/skills/git-branch-state-triage-and-recovery.md) for anonymized issue #907 / PR #908 | verified-local; CI pending at capture | Stash moved to fresh branch and signed commit |
| Closed PR replacement | [Immutable source snapshot](https://github.com/HomericIntelligence/Mnemosyne/blob/1ae0cb498e5250c341c2a4bf585f97e2a28060af/skills/git-branch-state-triage-and-recovery.md) for the anonymized closed-PR recovery case | verified-local | Recovered head published as replacement when reopen refused |
| Contaminated stacked child | [Immutable source snapshot](https://github.com/HomericIntelligence/Mnemosyne/blob/1ae0cb498e5250c341c2a4bf585f97e2a28060af/skills/git-branch-state-triage-and-recovery.md) for anonymized PRs #399/#400 | verified-ci | Parent rebased; child rebuilt with exact leases |
| Bulk retirement bound to fresh remote enumeration | Anonymized grouped decommission session | verified-local | Remote-only five-commit series archived before deletion; foreign mid-operation objects reported and preserved; zero-ref proof in both namespaces |

## Detailed Verification

The large Mnemosyne consolidation case compared skill counts at merge-base, branch, and main. The
branch grew while main intentionally shrank through consolidation; branch-only files were old
originals, not unreleased features. The destructive reset followed a preservation stash and direct
content review. The reusable rule is the three-way classification, not the repository-specific
counts.

For the Inference360 replay, the old PR merged while final remediation was active. The follow-up
started at current trunk and replayed only two missing commits, retaining concurrent trunk semantics.
The source-addressed Warden artifact was rebuilt, its digest checked, local validation reported
1,189 tests with 9 skips and 85.10% coverage, and nine exact-head checks plus an independent GO
review covered the final head before merge.

The stacked-child recovery preserved dated backup refs, rebased the parent first, rebuilt the child
on that new parent, and used explicit force-with-lease publication. Local suites and GitHub
CI/CodeQL passed. This is why the main workflow distinguishes parent-relative child verification
from trunk-relative PR verification.

The bulk-retirement case retired one group of classified-superseded fix branches and one
parallel-implementation branch whose tracked issue had already been fixed upstream as a strict
superset. Local branch deletions were complete and archived when the final remote enumeration found
a retired name still on the remote with five commits that no local ref had ever fetched; those
commits were exported as format-patches before the remote name was deleted. A new stash created
mid-operation by a parallel automation stream matched the cleanup pattern but was foreign to the
approved disposition list, so it was reported and left untouched. The reusable rule is to bind
execution to a fresh two-namespace enumeration, not the repository names.

## Provenance

- Superseded main SHA-256 (v2.1.0):
  `3905c17e3854940abc1637f44b305046bf8a4702f292b6a8bc51b1f4357ddd24`
- Amendment base: [`b61956fd`](https://github.com/HomericIntelligence/Mnemosyne/blob/b61956fdcafdc99cdd890be62ff1b6988c3fe306/skills/git-branch-state-triage-and-recovery.md)
- Old/new version: `2.1.0` → `2.2.0`
- Prior superseded main SHA-256:
  `6d115b78ee3f13728871ea289351e746c7933f10e2269e32cddeed02e0330b08`
- Issue #3335 base: `1ae0cb498e5250c341c2a4bf585f97e2a28060af`
- Old/new version: `1.8.0` → `2.0.0`
