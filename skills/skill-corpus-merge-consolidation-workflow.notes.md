# Skill Corpus Merge Consolidation Notes

Supporting cases for
[`skill-corpus-merge-consolidation-workflow.md`](skill-corpus-merge-consolidation-workflow.md).

## Case Index

| Case | Source | Verification | Material result |
| --- | --- | --- | --- |
| Complete cluster enumeration and collision gates | [Immutable source](https://github.com/HomericIntelligence/Mnemosyne/blob/d377a8924aff84e5cc193b720130b4c57e38c5c3/skills/skill-corpus-merge-consolidation-workflow.md) | verified-ci | Prevented example omissions, duplicate absorption, and canonical deletion |
| Exact superseded snapshots | [Immutable source](https://github.com/HomericIntelligence/Mnemosyne/blob/d377a8924aff84e5cc193b720130b4c57e38c5c3/skills/skill-corpus-merge-consolidation-workflow.md) | verified-ci | Preserved retrievable originals while reducing active duplicates |
| Hierarchical/dual-directory migrations | [Immutable source](https://github.com/HomericIntelligence/Mnemosyne/blob/d377a8924aff84e5cc193b720130b4c57e38c5c3/skills/skill-corpus-merge-consolidation-workflow.md) | verified-ci | Established flat single-source discovery with overwrite guards |
| Post-drain closed-PR salvage | [Immutable source](https://github.com/HomericIntelligence/Mnemosyne/blob/d377a8924aff84e5cc193b720130b4c57e38c5c3/skills/skill-corpus-merge-consolidation-workflow.md) | verified-local | Found absent new skills and carrier PRs containing unique amendments |
| Stranded clone recovery | [Immutable source](https://github.com/HomericIntelligence/Mnemosyne/blob/d377a8924aff84e5cc193b720130b4c57e38c5c3/skills/skill-corpus-merge-consolidation-workflow.md) | verified-local | Backed up work and republished from a canonical-main worktree |
| Accidental de-consolidation | [Immutable source](https://github.com/HomericIntelligence/Mnemosyne/blob/d377a8924aff84e5cc193b720130b4c57e38c5c3/skills/skill-corpus-merge-consolidation-workflow.md) | verified-ci | Reconciled new nuance into canonical and removed duplicate fix-forward |

## Evidence Detail

The source retains corpus-specific cluster sizes, category maps, migration scripts, commands, and
observed closure rates. They are evidence for the method, not universal thresholds. Current corpus
discovery and host manifests remain the authoritative inputs.

The closure audit distinguishes missing target artifacts from ordinary closed duplicate PRs. A high
closed rate motivates inspection but does not justify copying every closed diff.

## Provenance

- Superseded main SHA-256: `d5e4531904b333a41391ac4aa1c80ef52bd0d441d5d57f2c5387c7d73396fde7`
- Issue #3335 base: `d377a8924aff84e5cc193b720130b4c57e38c5c3`
- Old/new version: `2.2.0` → `3.0.0`

## Version-Fixture Drift Case (2026-10-27)

Timeline for the section-9 co-update rule (skill version 4.0.0 → 4.1.0):

1. During a `/learn` validation run at base `90ce47e9`, the full-suite `pytest` showed exactly one
   failure: `test_consolidated_canonicals_keep_versions_and_immutable_provenance` with
   `assert '3.4.0' == '3.3.0'`. The same failure reproduced on a clean `origin/main` checkout,
   classifying it as pre-existing main breakage, not an introduced regression.
2. Root cause: an earlier merged amendment (#3575) bumped
   `planning-verify-issue-premise-before-implementing` from 3.3.0 to 3.4.0 without touching the
   `CONSOLIDATIONS` fixture in `tests/test_skill_consolidation_integrity.py` (pin near line 30).
   The version-equality assert reports the two bare values and names neither the canonical nor the
   fixture, so cause identification needed the fixture grep.
3. Filed as issue #3606 with the reproduction and both resolution options. The drift was fixed on
   main by `04a3d20a` (integrity test green again); the issue itself was still open at capture
   time.
