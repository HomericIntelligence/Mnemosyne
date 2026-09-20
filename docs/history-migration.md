# Companion history migration

Follow [AGENTS.md](../AGENTS.md) and the [technical-English policy](asd-ste100.md).

## Result and source

Cleanup date: 2026-09-20.

Git is the authority for prior lesson versions. The immutable source is
[the pre-cleanup commit](https://github.com/HomericIntelligence/Mnemosyne/commit/ed1bd4f54fd4aaba446af92c8b3ab9aff2589ae3).
The migration removes 613 companion history files, with a total of 27,403,455
bytes. It retains the 604 corresponding main lessons and all notes companions.
Nine histories belong to previously absorbed lessons. Their current owners are
listed below.

The [complete inventory](history-migration.json) records each source path,
current owner, original byte count, and immutable GitHub link.
Each affected main lesson records the cleanup date and source link. Links in
notes now point to the same historical content at the pre-cleanup commit.

## Stack and preservation decisions

This change starts at the exact head of
[advisory-guidance PR 3420](https://github.com/HomericIntelligence/Mnemosyne/pull/3420).
It preserves that PR's revised lesson descriptions, workflow guidance, and current
versions. The original migration commit remains available on its separate branch.
The added advisory archives preserve the prior text; their current main lessons
already contain the amended guidance. All histories present at this stack base
are included, so the parent PR cannot reintroduce companion histories below this
change.

The inventory covers every history file. Amendment summaries, current main
lessons, and notes identify the current guidance. Existing main lessons remain
the retrieval authority. Prior compaction records supply context; they do not
make superseded instructions current. Apparent older main versions in some
consolidations came from absorbed lesson versions, rather than newer canonical
amendments.

The migration keeps existing main guidance and notes. It adds useful rules from
absorbed histories to the owners below. It does not append raw snapshots to main
lessons. Original evidence classifications remain in the linked sources. A
historical implementation result does not establish new verification for this
migration or make an old tool version current.

| Absorbed history | Current owner | Decision |
| --- | --- | --- |
| `ci-cd-cross-repo-skill-maintenance` | `cross-repo-boundary-and-ecosystem-audit` | Retain explicit delivery ownership; reject blanket conflict-side selection and mandatory learning on every task. |
| `ci-cd-dependabot-conflict-resolution-pattern` | `dependency-update-automation-bot-prs` | Retain subset comparison and unique-work checks; reject direct edits on protected main. |
| `ci-cd-dependabot-pixi-lock-drift-fix` | `lockfile-and-release-pipeline-management` | Retain candidate-input lock validation and divergence checks; reject rebasing solely for freshness. |
| `ci-cd-pipeline-maintenance-patterns` | `pr-ci-failure-triage-preexisting-vs-introduced` | Retain setup-versus-product diagnosis; do not promote unverified claims that commit pins or an action are always invalid. |
| `investigate-mojo-heap-corruption` | `mojo-ci-runtime-crash-diagnosis-and-mitigation` | Retain cumulative-failure diagnosis, import preservation, CI discovery, and current entry-point syntax; old numerical split limits remain historical evidence. |
| `mojo-bitcast-always-inline-crash-fix` | `mojo-ci-runtime-crash-diagnosis-and-mitigation` | Current pointer-lifetime and inlining rules already preserve the useful guidance. |
| `mojo-jit-crash-diagnosis-and-retry` | `mojo-ci-runtime-crash-diagnosis-and-mitigation` | Retain failure classification; reject unconditional force-push and the claim that runtime frames prove a compiler defect. |
| `latex-paper-accuracy-review` | `academic-paper-accuracy-and-citation-audit` | Retain cross-section consistency, statistical interpretation, sample-unit checks, and reproducibility rules. |
| `python-circular-import-symbol-extraction` | `python-module-decomposition-and-refactor-patterns` | Current import-cycle and patch-routing rules retain the useful guidance; add source provenance. |

Historical files include obsolete workflow policy, project-specific evidence,
and redacted records. The migration does not restore redacted material or copy
protected data into current lessons. The immutable links preserve access to the
already-committed sources; they do not assert that every historical detail is
current or suitable for republication.

## Current maintenance contract

- Keep current decision rules in main lessons and privacy-safe case evidence in notes.
- Use Git source links for prior versions. Do not require companion snapshots or history completeness before an amendment.
- Treat 30,000 bytes as an editorial guideline. A longer valid lesson remains valid.
- Read large sources in bounded batches without omitting requested coverage.
- Run selected native checks through a bounded executor when delegation is available.
- Record the source commit and candidate changes. Uncommitted changes can be validated.

The frontmatter adds optional `history-source` and `history-cleanup-date` fields.
The existing extensible schema already permits this metadata; no new required
fields or runtime validation gates are added.
The retired local `history` pointer is removed from migrated lessons. CLI entry
points are unchanged. Legacy companion exclusion remains in discovery so that
older checkout content cannot become a main lesson by accident.
