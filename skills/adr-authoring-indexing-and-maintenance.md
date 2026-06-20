---
name: adr-authoring-indexing-and-maintenance
description: "Use when: (1) generating a new Architecture Decision Record (ADR) to document a significant architectural decision; (2) an ADR file exists but is not listed in the index table (docs/adr/README.md); (3) updating ADR status to Accepted (Deferred) when implementation is bypassed pending platform support; (4) two or more functions have nearly identical limitation comments and need consolidating into a single ADR with cross-references replacing duplicates; (5) updating ADR directory tree listings to reflect actual filesystem contents after file deletions or additions; (6) writing an ADR on an epic branch where some child PRs have not yet merged to main — use pending-tense language for open PRs, past-tense only for work already on main."
category: documentation
date: 2026-06-20
version: "1.1.0"
user-invocable: false
history: adr-authoring-indexing-and-maintenance.history
tags:
  - adr
  - architecture-decision-record
  - documentation
  - index-maintenance
  - markdownlint
  - consolidation
  - directory-tree
  - pending-pr
  - epic-branch
  - in-flight-work
---
# ADR Authoring, Indexing, and Maintenance

End-to-end skill for the lifecycle of Architecture Decision Records: creating new
ADRs, keeping the `docs/adr/README.md` index table in sync, updating ADR status
through its lifecycle (including `Accepted (Deferred)`), consolidating duplicate
limitation comments into a single ADR with cross-references, and keeping ADR
directory-tree listings accurate against the real filesystem.

## Overview

| Field | Value |
| ------- | ------- |
| Date | 2026-06-07 |
| Objective | Author and maintain ADRs and their index, status, cross-references, and embedded directory trees |
| Outcome | Consistent, traceable ADRs; index always reflects on-disk ADRs; status reflects code reality; no duplicate limitation comments |
| Category | documentation |
| Verification | verified-ci |

## When to Use

- **Authoring**: Making a significant architectural decision, choosing between technical alternatives, documenting design trade-offs, or recording rationale for future reference.
- **Indexing**: An ADR file exists under `docs/adr/` but its row is absent from the `## ADR Index` table in `docs/adr/README.md`; a quality audit or GitHub issue flags a missing ADR index entry; a new ADR was merged without the author updating the index table.
- **Status lifecycle**: An ADR has `**Status**: Accepted` but the implementation explicitly bypasses the architecture (e.g., `# Temporary: Direct malloc`); a bypass comment references a known platform gap (e.g., Mojo global variable support); the underlying design decision is still valid but the active status is wrong.
- **Consolidation**: A GitHub issue says "consider a single shared ADR instead of cross-referencing between two function docstrings"; two or more functions contain nearly identical `# NOTE:`/`Note:` blocks describing the same limitation; an audit finds that updating a limitation note requires editing multiple files.
- **Directory-tree accuracy**: A file is deleted/added in a PR but the ADR directory tree was not updated; a follow-up issue asks to verify a helpers/tests directory is accurately documented; `grep` finds an ADR tree listing fewer files than `ls` shows on disk.

## Verified Workflow

### Quick Reference

| Task | Key command / action |
| ------ | ---------------------- |
| Create ADR | `docs/adr/ADR-NNN-<slug>.md`; fill Context/Decision/Rationale/Consequences/Alternatives; Status `Proposed` → `Accepted` |
| Add index row | Edit `docs/adr/README.md`; insert row `[ADR-NNN](ADR-NNN-<slug>.md) \| Title \| Status \| YYYY-MM-DD` (ascending order) |
| Defer status | Edit with `replace_all: true`: `**Status**: Accepted` → `**Status**: Accepted (Deferred)` (header + Document Metadata) |
| Consolidate dupes | Create ADR, replace each verbose block with 2–3 line `See docs/adr/ADR-NNN-<name>.md` cross-ref |
| Fix dir tree | Compare ADR ASCII tree vs `ls`; Edit to match real files using `├──`/`└──` connectors |
| Lint | `pixi run pre-commit run markdownlint-cli2 --files docs/adr/<file>.md` (NOT `npx`/`just`) |
| Land | conventional commit `docs(adr): ...`, push, `gh pr create --label documentation`, `gh pr merge --auto --rebase` |

### Detailed Steps

#### A. Generating a new ADR

1. **Identify the decision** — what choice needs documentation.
2. **Research alternatives** — gather evidence and performance data.
3. **Check the next ADR number** with `ls docs/adr/` and read one recent ADR to match its structure.
4. **Create the file** at `docs/adr/ADR-NNN-<slug>.md` using the template below.
5. **Fill sections** — Context, Decision, Rationale, Consequences (Positive/Negative/Neutral), Alternatives Considered.
6. **Add the index row** (section B) and set status `Proposed` → `Accepted` after review.

```markdown
# ADR-NNN: Title

**Status**: Proposed | Accepted | Deprecated | Superseded
**Date**: YYYY-MM-DD
**Deciders**: Names/roles

## Context
What is the issue we're facing?

## Decision
What decision are we making?

## Rationale
Why this decision? Key reasons.

## Consequences
### Positive
- Benefit 1

### Negative
- Drawback 1

### Neutral
- Other impact 1

## Alternatives Considered
### Alternative 1
Why not chosen.
```

**Status lifecycle**: `Proposed` (under consideration) → `Accepted` (active) → `Deprecated` (no longer recommended) → `Superseded` (replaced by a newer ADR). `Accepted (Deferred)` is a valid variant — see section C.

#### B. Adding a missing ADR index entry

1. **Read the ADR file** to get the canonical title, status, and date — never guess from the filename:

   ```bash
   head -10 docs/adr/ADR-NNN-<slug>.md
   ```

   Extract the `**Status**:` value, the `**Date**:` value, and the title after the colon in the `# ADR-NNN: ...` heading.

2. **Read the current index** (`cat docs/adr/README.md`) and find the last row of the `## ADR Index` table; the new row goes immediately after it, maintaining ascending ADR-number order.

3. **Edit README.md** using the exact previous last row as `old_string` and append:

   ```markdown
   | [ADR-NNN](ADR-NNN-<slug>.md) | <Title> | <Status> | <Date> |
   ```

   These updates are always exactly one table row — no surrounding context changes are needed.

#### C. Updating status to Accepted (Deferred)

1. **Read the ADR** to confirm it has a status in two places — the header (line ~3) and the Document Metadata section near the tail:

   ```text
   **Status**: Accepted          ← header
   ...
   - **Status**: Accepted        ← Document Metadata section
   ```

2. **Use `replace_all: true`** in the Edit tool to update both occurrences in one operation:

   ```text
   old_string: **Status**: Accepted
   new_string: **Status**: Accepted (Deferred)
   replace_all: true
   ```

3. **Verify both locations** were updated by reading the header and the tail.
4. If the ADR body already documents the bypass (a "Current Limitation" / "Known Limitation" section), only the status label needs changing — no body edits required.

#### D. Consolidating duplicate ADR references

1. **Read the issue and its plan** (`gh issue view <number> --comments`) to confirm scope.
2. **Locate all duplicate comment blocks** before editing — e.g. `Grep pattern="NOTE.*<keyword>" glob="**/*.mojo" output_mode="content"`.
3. **Create the ADR** (section A). Fill an Executive Summary (the limitation + workaround), Context/Key Findings (compiler/runtime facts), Decision (the workaround), Consequences (quantify perf/maintenance impact), Alternatives Considered (include "keep duplicate comments" and explain why rejected), and Supersession Criteria (explicit conditions to mark it Superseded).
4. **Add the index row** (section B).
5. **Edit each source file** — replace the verbose block with a 2–3 line cross-reference, and rewrite any "see sibling function" comments to point directly at the ADR:

   ```mojo
   # <Short description of limitation>; using <workaround>.
   # See docs/adr/ADR-NNN-<name>.md for rationale.
   ```

   For docstring `Note:` blocks, keep the `Note:` label and shorten the body:

   ```text
   Note:
       <Limitation> uses <workaround> (~Xx slower than optimized path).
       See docs/adr/ADR-NNN-<name>.md for full rationale.
   ```

   Update ALL cross-references (including inline body comments that referenced a sibling function) to point at the new ADR — leaving "see sibling_fn()" defeats the purpose.

#### E. Keeping the ADR directory tree accurate

1. **Confirm the actual state** with `gh issue view <number> --comments` and `ls <directory>/`; verify whether a deletion/addition actually happened (it may already be done by a prior PR).
2. **Find the stale reference**: `grep -n "<dir>\|<deleted-file>" docs/adr/ADR-*.md`.
3. **Compare** the ADR listing against `ls` — look for phantom references (listed but gone) and incomplete listings (on disk but missing).
4. **Edit the tree** to match reality, preserving the existing ASCII format (`├──`/`└──` connectors and trailing comments):

   ```text
   └── helpers/
       ├── __init__.mojo                     # Package re-exports
       ├── fixtures.mojo                     # Test fixture utilities
       ├── utils.mojo                        # Tensor debugging utilities
       ├── test_fixtures.mojo                # Self-tests for fixtures.mojo
       └── test_utils.mojo                   # Self-tests for utils.mojo
   ```

#### F. Validate and land (all tasks)

1. **Lint** with pre-commit's markdownlint (works in pixi-managed environments; does NOT require `npx` or `just`):

   ```bash
   pixi run pre-commit run markdownlint-cli2 --files docs/adr/<file>.md
   # or for broader changes
   pixi run pre-commit run --all-files
   ```

   Watch for MD013 (120-char line limit) — URLs in list items are NOT exempt; wrap after the closing `)` of the URL. GLIBC-related mojo errors in stderr on older hosts are non-blocking; the relevant hooks still run and pass.

2. **Commit, push, PR, auto-merge**:

   ```bash
   git add docs/adr/<changed-files>
   git commit -m "docs(adr): <summary>

   Closes #<issue-number>"
   git push -u origin <branch>
   gh pr create --title "docs(adr): <summary>" --body "Closes #<issue-number>" --label documentation
   gh pr merge --auto --rebase
   ```

#### G. Pending-PR accuracy on epic branches

When writing an ADR on an **epic branch** that pulls together work from multiple child PRs,
some of those child PRs may not yet be merged to `main`. Use the correct tense for each item:

| Work state | Language to use | Example |
| ------------ | ----------------- | --------- |
| Already on `main` (merged PR or direct commit) | Past tense — "was split", "now has", "reduced to" | "Split of `any_tensor.mojo` is now ≤3,000 lines (PR #5503 / commit abc1234)." |
| Open child PR, not yet merged | Pending tense — "pending split", "will reach", "once PR #N merges" | "Pending split of `any_tensor.mojo` (4,106 lines) into 6 focused sibling modules (PR #5503 — pending merge to main)." |

**Rule**: Only use completion language for work that is already on `main` at the time the ADR
is written. If a child PR is still open, describe the work as pending/in-flight and include
the PR number so readers can check the merge status themselves.

**Template — pending entry (Remediation section)**:

```markdown
- **#NNNN**: Pending <description>. (<implementation detail>) (PR #XXXX — pending merge to main)
```

**Template — completed entry (Remediation section)**:

```markdown
- **#NNNN**: <Past-tense description>. (PR #XXXX / commit <hash>)
```

**Template — Consequences section, pending work**:

```markdown
- `file.mojo` will reach <target> once PR #XXXX merges, with <benefit>.
```

**Verification**: Before finalising the ADR, run:

```bash
# Confirm which child PRs are actually merged
for pr in <list of PR numbers>; do
  gh pr view "$pr" --json state,mergedAt --jq '"\(.state) mergedAt=\(.mergedAt)"'
done
# merged + mergedAt set → use past tense
# OPEN / mergedAt null  → use pending tense
```

Reviewers will flag any past-tense claim on an epic branch if the underlying PR is still open
(the file on the branch will contradict the claim). Fix before requesting re-review.


## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Single Edit without `replace_all` | Edited only the header status field when deferring | ADR has two status locations (header + Document Metadata); only one was updated | Use `replace_all: true` to catch all occurrences in one edit |
| `pixi run npx markdownlint-cli2` | Ran markdownlint via npx | `npx: command not found` even inside the pixi environment | Use `pixi run pre-commit run markdownlint-cli2 --files <file>` — pre-commit has the tool |
| `just pre-commit-all` | Ran `just pre-commit-all` to validate markdown | `just` not available in the worktree shell environment | Use `pixi run pre-commit run ...` instead |
| Long URL list item on one line | Put `[Issue #NNN](https://...): description` on one line | MD013 fired (line > 120 chars) | Wrap after the closing `)` of the URL onto the next line |
| Referencing sibling function in comment | Left "see sibling_fn() for details" instead of pointing to the ADR | Still requires navigating to another function — defeats consolidation | Update ALL cross-references to point directly at the new ADR path |
| Trusting issue-body line numbers | Edited the line number an issue cited for a stale entry | Line number referenced an earlier state of the file | Don't trust line numbers from issue descriptions; grep for the actual pattern |
| Past-tense claim for open child PR | ADR said "#5182: Split of `any_tensor.mojo` is now ≤3,000 lines" | On the epic branch `any_tensor.mojo` was still 4,106 lines because PR #5503 had not merged; reviewer flagged two threads (line 24 and line 55) — factually false | Use pending tense for open PRs: "Pending split … (PR #XXXX — pending merge to main)"; past tense only for work already on main |
| "is now" in Consequences for pending PR | Consequences said "`any_tensor.mojo` is now ≤3,000 lines" when PR #5503 was unmerged | False on the branch; same code review thread flagged it as a second major finding | Write "will reach ≤3,000 lines once PR #XXXX merges" for pending outcomes; "is now" only after the PR lands |
| Assuming the deletion was pending | Searched for an allegedly-stale deleted-file reference | No matches — the file was already removed by a prior PR | Always check both the filesystem AND the ADR independently before editing |

## Results & Parameters

### ADR file naming

`docs/adr/ADR-NNN-<kebab-description>.md` where `NNN` is the next integer after the highest existing ADR.

### Index row format

```markdown
| [ADR-NNN](ADR-NNN-<slug>.md) | Title | Status | YYYY-MM-DD |
```

### Deferred-status edit

```text
Tool: Edit
file_path: docs/adr/ADR-NNN-<name>.md
old_string: **Status**: Accepted
new_string: **Status**: Accepted (Deferred)
replace_all: true
```

### Replacement comment pattern (2–3 lines max)

```mojo
# <Limitation summary>; using <workaround>.
# See docs/adr/ADR-NNN-<name>.md for rationale.
```

### Markdown line-length fix for long issue links

```markdown
- [Issue #NNN](https://github.com/Org/Repo/issues/NNN):
  Description text that would have exceeded 120 chars
```

### Lint command (pixi)

```bash
pixi run pre-commit run markdownlint-cli2 --files docs/adr/<file>.md
```

### Expected outcomes

- Index updates are typically a single inserted table row; pre-commit passes (Markdown Lint, ruff, yaml, trailing-whitespace).
- Status-defer changes are pure label updates with no formatting impact; markdownlint passes first try.
- Directory-tree fixes are small (e.g., 1 removed, 5 added) and complete in a few minutes.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| ProjectOdyssey | Issue #3150, PR #3338 — add missing ADR index row | [history](adr-authoring-indexing-and-maintenance.history) |
| ProjectOdyssey | Issue #3151, PR #3339 — ADR-003 memory pool Accepted (Deferred) | [history](adr-authoring-indexing-and-maintenance.history) |
| ProjectOdyssey | Issue #3291, PR #3886 — consolidate FP16 SIMD limitation into ADR-010 | [history](adr-authoring-indexing-and-maintenance.history) |
| ProjectOdyssey | Issue #3252, PR #3820 — ADR-004 helpers directory tree accuracy | [history](adr-authoring-indexing-and-maintenance.history) |
| ProjectOdyssey | Issue #5191, PR #5504 — ADR-014 pending-PR accuracy: corrected past-tense claim for open child PR #5503 (commit 20b0d7c7) | [history](adr-authoring-indexing-and-maintenance.history) |
