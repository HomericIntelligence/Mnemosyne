---
name: adr-authoring-indexing-and-maintenance
description: "Use when creating or maintaining Architecture Decision Records, their index and status lifecycle, consolidating duplicated design notes, correcting directory trees, documenting in-flight epic work, citing cross-repository evidence, or adding an ADR membership guard. Match the repository's local ADR format, verify every frozen claim against tracked/live evidence, and update the document plus every consumer together."
category: documentation
date: 2026-07-04
version: "2.0.0"
verification: mixed
license: BSD-3-Clause
user-invocable: false
history: adr-authoring-indexing-and-maintenance.history
tags:
  - adr
  - architecture-decision-record
  - documentation
  - index-maintenance
  - provenance
  - append-only
  - membership-guard
---

# ADR Authoring, Indexing, and Maintenance

## Overview

Use this skill for the complete ADR lifecycle: choose the local format, verify evidence, author the
decision, index it, maintain status and references, and guard the disk/index relationship. Accepted
ADRs are durable records; unverifiable claims and stale implementation tense become permanent debt.

Verification is `mixed`: the core authoring/index/status/consolidation workflow is `verified-ci`;
tracked-symbol anchoring and the bidirectional Nygard-format guard were recorded `verified-local`
with hosted CI pending. Case details are in the
[notes](./adr-authoring-indexing-and-maintenance.notes.md); the byte-preserved source and prior
changelog are in [history](./adr-authoring-indexing-and-maintenance.history).

## When to Use

- A significant architectural choice needs rationale, alternatives, and consequences.
- An ADR exists on disk but is absent or stale in `docs/adr/README.md`.
- An accepted design is temporarily bypassed and its status should be `Accepted (Deferred)`.
- Multiple functions repeat the same limitation/workaround explanation.
- An ADR’s embedded directory tree no longer matches the repository.
- An epic ADR describes child PRs that have not all merged.
- A cross-repository claim cites an ADR number, commit, or internal-document statement.
- A Decision section names a code symbol that may be untracked or absent from main.
- The repository needs an executable README-to-disk ADR membership contract.
- A pre-implementation multi-stage architecture needs topology, routes, contracts, and cutover
  boundaries without pretending the runtime already exists.

## Decision Rules

1. **Read local policy and recent ADRs first.** Do not impose a three-digit `ADR-NNN-*` format on a
   repository using four-digit Nygard names and list-style metadata.
2. **Allocate from disk, not memory.** Enumerate ADR files and inspect the index before choosing the
   next number.
3. **Freeze only verified claims.** Check every cited ADR file, commit, symbol, path, and internal-doc
   line. If an external number cannot be verified, say “external docs cite ADR-NNN” and attach the
   verifiable commit or file:line evidence.
4. **Anchor decisions on tracked artifacts.** `git ls-files <path>` must resolve a named canonical
   implementation. Mark untracked or future artifacts illustrative, not authoritative.
5. **Describe state, not intention, as completed.** Use past tense only for work already on the
   branch/base being documented. Open child PRs stay pending and retain their PR links.
6. **Update both sides of every relationship.** A new ADR needs its index row; consolidation needs
   every duplicate/sibling cross-reference replaced; a tree description must match disk.
7. **Change status everywhere.** If metadata repeats status, update and verify every occurrence.
8. **Guard set equality.** The ADR files linked by the index must equal the ADR files on disk. A
   one-way “all files linked” check misses stale links.
9. **Preserve append-only governance.** Do not edit an accepted ADR when repository policy requires a
   superseding ADR. Status/index maintenance is permitted only under local policy.
10. **Separate design from implementation.** Mark a skeleton pre-implementation and name which
    sections are finalized during cutover.

## Verified Workflow

### 1. Discover the local contract

```bash
rg -n 'ADR|architecture decision|append-only|supersed' AGENTS.md CONTRIBUTING.md docs
find docs/adr -maxdepth 1 -type f -name '*.md' | sort
sed -n '1,220p' docs/adr/README.md
git log --oneline -5 -- docs/adr
```

Read the newest accepted and proposed ADRs. Capture filename/title/metadata/section conventions,
index order, status vocabulary, lint commands, and whether accepted records may be edited.

Two recorded variants:

| Aspect | Three-digit variant | Four-digit Nygard variant |
| --- | --- | --- |
| Filename | `ADR-NNN-<slug>.md` | `NNNN-<slug>.md` |
| Title | `# ADR-NNN: Title` | `# ADR-NNNN: Title` |
| Metadata | bold `Status`/`Date` | list `- Status:` / `- Date:` / optional `- Tracks:` |
| Sections | Context, Decision, Rationale, Consequences, Alternatives | Context, Decision, Alternatives considered, Consequences |

Match the target repository exactly, including case.

### 2. Verify evidence and current state

```bash
git ls-files <claimed-canonical-path>
git log --oneline -- <claimed-path>
git -C <dependency> log --oneline --all -- <path>
rg -n 'ADR-[0-9]+|<claim-keyword>' docs/adr <dependency>/AGENTS.md <dependency>/CLAUDE.md
gh pr view <child-pr> --json state,mergedAt,headRefOid
```

Verify the audit’s characterization too. A cited line can be current while its prose summary is
wrong (for example, describing a three-provider union as dual-provider). Record the immutable SHA
or file:line used for cross-repository evidence.

### 3. Author or update the ADR

A minimal decision record contains:

```markdown
# ADR-NNN: Title

**Status**: Proposed
**Date**: YYYY-MM-DD

## Context

What constraint or conflict requires a durable decision?

## Decision

What is selected, including scope and invariants?

## Rationale

Why does this option best satisfy the constraints?

## Consequences

### Positive

- Benefit.

### Negative

- Cost or risk.

## Alternatives Considered

### Alternative

Why it was rejected.
```

Add deciders, supersession criteria, neutral consequences, or implementation references when local
convention requires them. Keep status `Proposed` until the repository’s review/acceptance event.

The common lifecycle is `Proposed` (under review) to `Accepted` (active), then `Deprecated` (no
longer recommended) or `Superseded` (replaced by a named later ADR). `Accepted (Deferred)` means the
decision remains accepted while its implementation is deliberately postponed; it is not a synonym
for rejected or obsolete.

For `Accepted (Deferred)`, first verify the design remains valid but implementation is explicitly
bypassed. Update every metadata occurrence, then confirm the body already explains the limitation;
do not add unrelated redesign prose.

### 4. Maintain the index and directory descriptions

Read title, status, and date from the ADR itself; never infer them from the filename. Insert one row
in numeric order using the exact local table shape:

```markdown
| [ADR-NNN](ADR-NNN-<slug>.md) | Title | Status | YYYY-MM-DD |
```

For an embedded tree, compare the actual directory listing and tracked paths against the prose.
Remove phantom files, add missing files, and preserve the existing connector/comment style.

### 5. Consolidate repeated design notes

1. Find every duplicated block and every “see sibling function” reference.
2. Put the complete constraint, workaround, consequences, alternatives, and supersession criteria
   in one ADR.
3. Replace each source block with a two- or three-line direct reference:

```text
# <Limitation>; using <workaround>.
# See docs/adr/ADR-NNN-<slug>.md for rationale.
```

4. Search again for obsolete wording and indirect sibling references.

### 6. Represent epic and cross-repository state accurately

| Evidence state | Required language |
| --- | --- |
| On the documented base/main | “was implemented”, “now has” plus commit/merged PR |
| Open child PR | “pending”, “will reach once PR #N merges” |
| External ADR number verified on disk | State it and link/cite the file |
| External number not verified | “External docs cite ADR-NNN”; add commit or file:line evidence |
| Untracked planned artifact | “Illustrative/future”, never canonical |

Recheck child PR state immediately before finalizing because tense can change during an epic.

### 7. Add a bidirectional membership guard when consumed

```python
def test_readme_index_lists_exactly_the_adr_files() -> None:
    readme = (ADR_DIR / "README.md").read_text(encoding="utf-8")
    linked = set(re.findall(r"\(([0-9]{4}-[a-z0-9-]+\.md)\)", readme))
    on_disk = {path.name for path in ADR_DIR.glob("[0-9][0-9][0-9][0-9]-*.md")}
    assert linked == on_disk, (
        f"index out of sync: missing={on_disk - linked}, stale={linked - on_disk}"
    )
```

Where local policy requires it, also validate filename pattern, contiguous unique numeric prefixes,
required metadata, title identity, and required section headings. Test behavior and membership, not
exact prose strings.

### 8. Structure a pre-implementation architecture skeleton

Include:

1. a visible pre-implementation status banner;
2. queue/topology diagram and coordinator/worker ownership;
3. message, state-transition, and handoff contracts;
4. per-stage steps, verdicts, failure routes, budgets, labels, and exact source anchors;
5. one ROUTES table using full consistent identifiers;
6. seeding and reconstruction rules for stuck state;
7. sections explicitly marked “finalized in cutover issue #N”.

Cite complete line ranges and repeat consistent file:line anchors wherever the same prompt-builder or
route appears. Abbreviated identifiers that differ between the route table and stage prose are not
searchable contracts.

### 9. Validate

```bash
pre-commit run markdownlint-cli2 --files docs/adr/<adr>.md docs/adr/README.md
git diff --check
git diff -- docs/adr
<repository-command-for-ADR-guard-and-link-tests>
```

Use the repository’s actual tool wrapper. Wrap long linked list items after the link when line-length
lint applies. Before delivery, repeat file enumeration, index equality, tracked-symbol checks, child
PR state reads, and cross-repository citations.

## Examples

### Pending child outcome

Write “`module.mojo` will reach the target once PR #5503 merges,” not “is now at the target,” while
the PR is open. After merge, update only under the repository’s ADR mutation/supersession policy.

### Unverifiable external ADR number

If a meta-repository contains ADRs 001–009 but an external plan says ADR-015 performed an extraction,
do not assert that ADR-015 exists locally. Cite the external wording as external and attach the
verified implementation commit.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --- | --- | --- | --- |
| Failure 1 | Guess format or next number | Creates a nonconforming or colliding ADR | Read disk, index, and recent ADRs |
| Failure 2 | Update only one status occurrence | Header and metadata disagree | Replace and verify every occurrence |
| Failure 3 | Keep “see sibling” comments | Design rationale remains duplicated and indirect | Point every site to the ADR |
| Failure 4 | Trust issue line numbers | Coordinates drift | Search the current tree |
| Failure 5 | Use past tense for open PRs | Freezes a false implementation claim | Query live state and use pending language |
| Failure 6 | Assert external ADR numbers from plans | The referenced record may not exist | Verify on disk or qualify and cite commits |
| Failure 7 | Cite an untracked canonical symbol | Main cannot satisfy the decision | Anchor on tracked symbols |
| Failure 8 | Check index in one direction | Stale README links pass | Assert set equality |
| Failure 9 | Trust an audit’s summary | Characterization can be wrong despite real lines | Read the live symbol/value |
| Failure 10 | Abbreviate ROUTES inconsistently | Breaks search and cross-reference | Use full stable identifiers everywhere |
| Failure 11 | Cite a partial line range | Omits part of the claimed artifact | Read and cite the complete range |
| Failure 12 | Reformat unrelated ADR prose | Expands review surface and risks frozen drift | Make the smallest policy-compliant edit |
## Results & Parameters

| Parameter | Contract |
| --- | --- |
| Format | Match repository-local filename, title, metadata, and section case |
| Accepted record | Append-only or superseded according to local policy |
| Cross-repo claim | Verified file/commit/line, otherwise explicitly qualified |
| Epic state | Completion language only for work present on documented base |
| Index guard | Exact README-link set equals on-disk ADR set |
| Evidence status | Core verified-ci; tracked-symbol/guard additions verified-local |

## Output Contract

Return the local ADR convention, verified evidence inventory, files and index rows changed, status
and tense decisions, cross-repository citations, membership/directory proof, lint/link/test commands
and outcomes, and every remaining unverified claim. Never mark `mixed` evidence as fully CI-verified.

## Companions

- [Case notes](./adr-authoring-indexing-and-maintenance.notes.md)
- [Version history and superseded snapshot](./adr-authoring-indexing-and-maintenance.history)
