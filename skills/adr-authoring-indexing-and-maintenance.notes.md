# ADR Authoring, Indexing, and Maintenance — Case Notes

These notes retain repository-specific ADR variants and cases. The complete superseded main is
archived only in history.

## Case Index

| Case | Source | Verification |
| --- | --- | --- |
| Missing ADR index row | [Immutable source at batch base](https://github.com/HomericIntelligence/Mnemosyne/blob/d377a8924aff84e5cc193b720130b4c57e38c5c3/skills/adr-authoring-indexing-and-maintenance.md) | verified-ci |
| `Accepted (Deferred)` lifecycle correction | [Immutable source at batch base](https://github.com/HomericIntelligence/Mnemosyne/blob/d377a8924aff84e5cc193b720130b4c57e38c5c3/skills/adr-authoring-indexing-and-maintenance.md) | verified-ci |
| Duplicate FP16 limitation consolidated into one ADR | [Immutable source at batch base](https://github.com/HomericIntelligence/Mnemosyne/blob/d377a8924aff84e5cc193b720130b4c57e38c5c3/skills/adr-authoring-indexing-and-maintenance.md) | verified-ci |
| Epic child-PR tense correction | [Immutable source at batch base](https://github.com/HomericIntelligence/Mnemosyne/blob/d377a8924aff84e5cc193b720130b4c57e38c5c3/skills/adr-authoring-indexing-and-maintenance.md) | verified-ci |
| Cross-repository citation correction | [Immutable source at batch base](https://github.com/HomericIntelligence/Mnemosyne/blob/d377a8924aff84e5cc193b720130b4c57e38c5c3/skills/adr-authoring-indexing-and-maintenance.md) | verified-local |
| Four-digit Nygard records and bidirectional guard | [Immutable source at batch base](https://github.com/HomericIntelligence/Mnemosyne/blob/d377a8924aff84e5cc193b720130b4c57e38c5c3/skills/adr-authoring-indexing-and-maintenance.md) | verified-local |
| Pre-implementation automation architecture skeleton | [Immutable source at batch base](https://github.com/HomericIntelligence/Mnemosyne/blob/d377a8924aff84e5cc193b720130b4c57e38c5c3/skills/adr-authoring-indexing-and-maintenance.md) | verified-ci |

## Core Maintenance Cases

ProjectOdyssey issue #3150 / PR #3338 added a missing ADR index row by reading the canonical title,
status, and date from the file and inserting one numerically ordered table row. Issue #3151 / PR
#3339 changed both status locations for the memory-pool decision to `Accepted (Deferred)` without
rewriting the already-correct limitation body.

Issue #3291 / PR #3886 moved duplicated FP16 SIMD limitation prose into ADR-010 and replaced every
source/sibling reference with short direct ADR links. Issue #3252 / PR #3820 reconciled an embedded
helpers tree with files actually present on disk.

## Epic-Tense Case

ProjectOdyssey issue #5191 / PR #5504 corrected ADR-014 after open child PR #5503 had been described
as complete. Both the remediation list and Consequences section required pending tense. The case
shows that one false state claim often appears in several ADR sections; search for all completion
verbs after correcting the first review thread.

## Cross-Repository Citation Case

An Odysseus ADR draft asserted ADR-015 and ADR-016 based on plans and external docs, but local disk
contained only ADRs 001–009. The corrected record cited implementation commits and exact internal-doc
lines, and qualified the unverified numbers as labels used by external documentation. Because the
record would become append-only, the claim inventory was checked before acceptance.

## Tracked-Symbol and Guard Case

ProjectHephaestus issue #1452 used a four-digit Nygard format. A proposed canonical symbol lived in
an untracked file, so the ADR was re-anchored to tracked runtime symbols and the untracked artifact
was marked illustrative. The issue also called the runtime dual-agent, while the live type admitted
three providers; the ADR recorded the live tri-provider reality.

The structural test checked filename format, contiguous unique numbering, required Nygard metadata
and sections, title identity, and exact equality between README links and files on disk. Four focused
tests and markdownlint passed locally; hosted CI was pending in the archived evidence, so this case
remains `verified-local`.

## Architecture-Skeleton Case

ProjectHephaestus issue #1810 / PR #1811 added ADR-0006 and a pre-implementation automation pipeline
skeleton. Review exposed inconsistent abbreviated route identifiers, partial diagram line ranges,
and prompt-builder references that omitted file paths in some sections. The corrected document used
one full-name ROUTES vocabulary, complete anchors, topology and coordinator/worker contracts,
seeding/reconstruction rules, and explicit cutover-finalized sections.

## Format and Lint Notes

- The three-digit variant used `ADR-NNN-<slug>.md` and bold metadata.
- The Hephaestus variant used `NNNN-<slug>.md`, `# ADR-NNNN`, and list metadata.
- Long linked bullets were wrapped after the closing link to satisfy MD013.
- The working lint entry point varied by repository; invoking an unavailable `npx` or `just`
  wrapper was a tooling error, not an ADR-content failure.

## Compaction Disposition

- Kept in main: format discovery, evidence rules, status/index/consolidation/tree workflows,
  epic/cross-repo language, membership guard, skeleton contract, and failed approaches.
- Moved here: issue/PR narratives, local format details, and evidence outcomes.
- Archived only: repeated templates, long command transcripts, and the complete prior main.
