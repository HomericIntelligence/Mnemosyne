---
name: audit-driven-remediation-workflow
description: "Turn audit findings into scoped fixes. Use for source verification, duplicate detection, independent batches, downstream consumers, and evidence-based completion reports."
category: tooling
date: 2026-07-06
version: "2.2.0"
user-invocable: false
license: BSD-3-Clause
verification: verified-ci
tags: [audit, remediation, triage, github, verification, producer-consumer, cross-module, strict-review, provenance]
history-source: "https://github.com/HomericIntelligence/Mnemosyne/blob/1956c91d76867bc2e484eaf573a57051855186f8/skills/audit-driven-remediation-workflow.history"
history-cleanup-date: "2026-09-20"
---

# Audit-Driven Remediation Workflow

## Overview

Use current source evidence to confirm an audit finding and identify its owner. A focused
reproduction or acceptance test can help when practical. Select investigation, batching,
verification, and independent review according to the finding and its risk.

This workflow remains `verified-ci`. Case-specific fleet limits, corpus passes, and incident details
are in [the notes](./audit-driven-remediation-workflow.notes.md); exact prior content is in
[history](https://github.com/HomericIntelligence/Mnemosyne/blob/1956c91d76867bc2e484eaf573a57051855186f8/skills/audit-driven-remediation-workflow.history).

## When to Use

- A strict/manual/scanner audit produced findings that need issues and PRs.
- Counts differ across code, manifests, and documentation.
- An alleged missing or stale artifact may already exist on another branch or current main.
- Many low-risk fixes need batching across files or repositories.
- A 20+ file documentation corpus needs parallel, collision-free repair, or a 500+ skill corpus needs
  evidence-based duplicate clustering without deleting distinct retrieval angles.
- Deprecated compatibility code is being removed after migration.
- Implementation must be checked against an ADR/design/research contract.
- A producer adds a verdict, state, event, or field that downstream consumers may ignore.
- One copy-pasted defect was fixed and sibling modules may retain it.
- An epic appears complete and needs an independent strict audit.
- Review agents inspect recently merged work while their local checkout may be stale.
- Multiple reviewers produce overlapping or conflicting findings that need synthesis.

## Verified Workflow

### Quick Reference

```bash
git fetch origin
git rev-parse origin/main
git status --short

# Reproduce finding against the authoritative tree.
git show origin/main:path/to/file | rg '<pattern>'
git ls-tree -r --name-only origin/main | rg '<claimed-path>'

# Deduplicate tracking and implementation.
gh issue list --state all --search '<signature>' --limit 200
gh pr list --state all --search '<issue-or-signature>' --limit 200

# Verify final branch scope and gates.
git diff --stat origin/main...HEAD
pre-commit run --all-files
```

### 1. Freeze authoritative evidence

Record repository, `origin/main` SHA, issue/audit revision, local status, and worktrees. For freshly
merged code, read through `git show origin/main:<path>` or a clean checkout; a stale working tree can
make files appear missing or preserve already-fixed defects. Do not let reviewers silently choose
different SHAs.

When auditing multiple repositories, establish one SHA and owner per repo. A local build in a sibling
does not prove its hosted CI or current main.

### 2. Reproduce and classify every finding

It applies when a scanner, linter, or audit tool reports findings across many files and the fix
must stay in one reviewable change. It does not apply when one verified defect needs a design
change; use the deferred branch below for that.

Verify file existence, symbol/pattern, execution path, and current behavior. Scanner output is a lead,
not proof. Classify:

| Class | Disposition |
| --- | --- |
| Small, clear, low-risk defect | Include in a coherent batch |
| Safe pragmatic improvement | Include with focused acceptance evidence |
| Ambiguous or possibly stale | Investigate before issue/implementation |
| Design-heavy or broad refactor | Separate issue and PR |
| External/toolchain blocker | Document owner, version, and unblock condition |
| Administrative setting | Route as settings work, not a code patch |
| Deliberate pattern the rule cannot model | Keep the code; add a scoped suppression with a reason that names the pattern |
| Rule misfires on the detected text, not the code | Keep the code; disable that rule in the repository configuration with a comment that states why |
| Accepted risk | Record owner, expiry/revisit trigger, and rationale; never silently suppress |

Assign severity from impact and exploitability/likelihood, not scanner label alone. Record exact
source coordinates at the immutable SHA and a command that proves the current failure.

**Split the finding population by class before you estimate effort.** Line-level rule families such
as size, parameter count, and nesting describe architecture that predates the scan. Treat them as
deferred design work with their own issues, not as defects in the remediation batch. Fix or
disposition only the defect and convention classes. Then rescan and compare the residue: the
remaining count must equal the deferred set exactly. A residue above it means a fix or suppression
did not apply.

**Match the suppression to what the rule got wrong.** Put a directive on the reported line, with
the rule id and a short reason, when the code deliberately uses the pattern the rule condemns. Use
repository-wide configuration only when every hit for that rule is a text-level misfire, and only
after you read each hit. State the trade-off: a disabled rule cannot report a future real instance.
Never narrow an exception handler or delete behavior to satisfy a style rule without a test that
proves the behavior change is intended.

### 3. Deduplicate and create tracking

Use this step for finding families whose every hit is a name, key, or literal that the detector
misreads, such as an identifier-shaped dictionary key or a standard-library import.

Search all issue and PR states by symbol, path, diagnostic, and acceptance phrase. Verify whether a
prior commit or unmerged worktree already delivered the fix. Reconcile audit finding count against
unique actionable items; several scanner rows may share one root cause, while one finding may require
multiple repository-owned issues.

Each issue contains objective, evidence, scope, exclusions, owner, severity rationale, deliverables,
acceptance commands, dependencies, and rollback. Use labels that actually exist. Capture the issue
number from structured CLI output or URL parsing with validated shape; do not assume creation
succeeded.

### 4. Build safe batches

Batch defect classes together only when they share rollback and verification cost. Defer a
class when its remedy is a refactor that needs its own review.

Batch only findings with shared context, no conflicting file ownership, compatible rollback, and a
verification runtime that stays reviewable. Split security boundaries, API/architecture changes,
large decompositions, cross-repo changes, and unrelated red CI. One branch and PR has one owner.

Use isolated worktrees. Recheck main and open PRs immediately before edits. Preserve unrelated user
changes and avoid destructive cleanup. Keep deferred items explicitly linked; “not implemented” is
not a silent omission.

### 5. Implement and verify incrementally

Rescan with the exact tool version that produced the baseline. A newer version adds rules, so
the residue comparison is not valid against it.

For behavior changes, prefer a focused failing test or reproduction when practical. For
documents/configuration, use relevant existing checks rather than wording snapshots. Select
focused or broader verification according to the change and applicable repository policy. Review `git diff` for exact
scope and unintended generated/lockfile changes.

Count reconciliation derives entities from the canonical source, then updates all consuming docs or
generators. Do not hand-edit a generated count without its source. Compatibility removal searches
all callers/imports/config aliases and tests both rejected legacy input and supported current input.

### 6. Trace producer-to-consumer contracts

A new field, verdict, marker, or event is incomplete until every consumer reads or intentionally
ignores it. Search writes and reads separately, then build a table: producer, transport/persistence,
consumer, decision, test. A test that mocks the consumer result can mask the missing read, so include
at least one integration path carrying the real produced value.

Check logs, serializers, state restoration, retry/recovery, CLI/API presentation, metrics, and final
routing. “Producer emits it” is not acceptance evidence.

### 7. Search sibling modules for the same pattern

Translate the fixed defect into a structural search signature and scan peers, variants, tests, and
templates. Inspect each hit; do not bulk-rewrite semantically different code. Add a parameterized or
shared regression when one invariant applies across implementations. This step is especially
important after swarm/bundle work where agents copied a pattern independently.

### 8. Independent review when useful

For broad or high-risk remediation, consider reviewers separate from the implementers and bind them to the final SHA. Divide work by
nonoverlapping concerns/files. Require evidence and severity for every candidate. Synthesize results:
deduplicate, reproduce against the same SHA, reject stale/unsupported claims, resolve conflicts, and
only then file issues or reopen the implementation.

Run all required checks on the final head. Report pre-existing failures with provenance; never call a
red gate green. Publish exact commands, results, commit SHA, deferred items, and rollback.

### 9. Corpus-specific remediation

For large document corpora, enumerate all defect classes before dispatch, mark files touched by more
than one class as conflict risks, and assign each file to exactly one writer. Follow with an
independent read-only residual scan and a conflict-marker gate. Do not add change-log prose describing
the remediation itself unless a product consumer requires it.

For skill deduplication, filename overlap is only a candidate signal. Compare triggers, tags,
headings, commands, and unique decision content. Cross-category prefix matches require multiple strong
signals; distinct audiences or failure modes remain separate. Stop when another pass yields little
actionable overlap instead of forcing consolidation to an arbitrary count.

**Verify the directive attachment before you trust a clean rescan.** Suppression directives attach
to one exact line, and the reported line is often not the handler line you expect. Probe the
mechanism on a scratch file: place the directive, rescan, and confirm the finding disappears. A
formatted file can also move your directive to a line that no longer covers the finding.

```python
    # <directive> attached above the try body: does not cover the handler
    try:
        risky()
    except SpecificError:  # <directive> attached here: covers the handler
        pass
```

Shorten the reason text so the trailing form stays within the line limit. If the formatter splits
the handler header, the directive on the closing line no longer applies. Grade the result on a
rescan, never on the presence of a directive.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --- | --- | --- | --- |
| Trust audit assertion | Implemented a claimed missing file | The artifact already existed | Reproduce every finding first |
| Audit stale checkout | Reviewers used local files after merge | They reviewed missing/old code | Fetch and read immutable `origin/main` |
| File every scanner row | Created one issue per report line | Duplicates shared one root cause | Deduplicate by behavior and ownership |
| Deduplicate by filename | Collapsed similarly named skills | Distinct triggers and audiences were lost | Require semantic overlap and preserve unique decisions |
| Batch broad refactors | Mixed small fixes with decomposition | Review and rollback became unsafe | Split by risk and dependency |
| Add producer only | Emitted a new signal | Consumers ignored it | Trace the complete producer-consumer path |
| Fix one copied module | Patched the reported file | Sibling implementation retained defect | Run structural sibling search |
| Trust mocked unit test | Consumer behavior was stubbed | Real transport never carried the value | Add an integration contract path |
| Let implementer self-certify | Same context reviewed its own choices | Blind spots survived completion | Dispatch independent strict review |
| File raw swarm findings | Accepted reviewer outputs directly | Duplicates, stale reads, and contradictions remained | Synthesize and re-reproduce first |
| Treat every scanner row as a defect | Planned one PR that refactored all reported sizes and arities | Most rows were pre-existing architecture; the batch was not reviewable | Split defect classes from design classes and defer the latter |
| Delete behavior to silence a style rule | Narrowed exception handlers or removed operator output to clear findings | The findings described deliberate behavior, not defects | Keep behavior and add a scoped, reasoned suppression |
| Suppress a whole rule from one sample | Disabled a rule across the repository after reading one hit | Unread hits could be real defects | Read every hit before repository-wide configuration |
| Place the directive above the reported construct | Put the suppression above the `try` body, then reformatted | The directive covers the line below it, which was not the handler; the finding stayed | Verify each directive with a rescan, and keep it on the reported handler line |
| Trust a directive that formatting moved | Let the formatter split a handler header after adding a trailing directive | The directive sat on the closing line and stopped applying | Shorten the reason and re-verify placement after formatting |
| Claim sibling CI from local build | Ran tests in another checkout | Hosted branch and CI could differ | Verify the other repository PR/checks directly |

## Results & Parameters

| Artifact | Minimum evidence |
| --- | --- |
| Finding | Immutable SHA, path/symbol, reproduction, severity rationale |
| Tracking issue | Dedup search, scope/exclusions, owner, acceptance commands |
| Batch | Dependency/file ownership map, rollback, expected checks |
| Producer change | Every consumer and persistence/transport path classified |
| Pattern fix | Sibling search results and shared/parameterized regression where valid |
| Corpus batch | Complete pre-scan, exclusive file ownership, residual and conflict-marker checks |
| Completion | Final diff, required gates, independent audit synthesis |
| Deferral | Separate issue/owner and explicit unblock or revisit condition |
| Cross-repo claim | Hosted PR/main SHA and that repositories checks |

## Verified On

- CI-backed audit/remediation cases, producer-consumer follow-ups, sibling-pattern fixes, and strict
  post-completion reviews are indexed in the notes.

## Companions

- [Case notes](./audit-driven-remediation-workflow.notes.md)
- [Version history and exact superseded snapshot](https://github.com/HomericIntelligence/Mnemosyne/blob/1956c91d76867bc2e484eaf573a57051855186f8/skills/audit-driven-remediation-workflow.history)
