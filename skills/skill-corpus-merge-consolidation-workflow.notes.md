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
