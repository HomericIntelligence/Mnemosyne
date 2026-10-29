---
name: review-exchange-epoch-token-classification
description: "Classify an advertised lineage token ('source epoch', 'source revision') as a content digest of the requirements source versus a VCS revision before verifying a legacy-import plan's measured claims, and bind every file/line pin to the authoritative measurement base — the carrier's explicit revision field when present, else the artifact-publication main tip. Use when: (1) a review-exchange legacy import advertises a 64-hex epoch token that git cannot resolve as an object, (2) a reviewer must distinguish authoring-true pins from base drift on a moving target, (3) an author must close a 'no source epoch' or 'drifted pins' finding with an epoch pin or a re-pin, or (4) two parties report different commit counts or ranges for the same interval and one authoritative enumeration is required."
category: tooling
date: 2026-10-29
version: "1.0.0"
user-invocable: false
tags:
  - review-exchange
  - legacy-import
  - lineage-verification
  - source-epoch
  - content-digest
  - base-drift
  - pin-classification
---

# Review Exchange Epoch Token Classification

## Overview

| Field | Value |
| --- | --- |
| Date | 2026-10-29 |
| Objective | Identify what an advertised lineage token actually is before any lineage verification, then measure claims against the true base. |
| Outcome | Lineage pins verified at the correct epoch; failures classified as plan defect or base drift with reproducible git evidence; no wasted fetch or proxy-checkout detours. |

## When to Use

- A legacy plan or requirements record advertises a "source epoch" or "source revision" token (for example a 64-hex string), and `git fetch <token>` / `git cat-file -t <token>` fails although planning clearly measured real code.
- A reviewer of a legacy-import plan must decide whether a measured file/line/symbol claim that fails at the current base was ever true.
- An author response must close an epoch or drift finding and must choose between naming an epoch and re-pinning to the current base.
- The plan and the reviewer disagree on a commit count or a range for one interval.

## Verified Workflow

1. Classify the token before fetching. A 64-hex token on a SHA-1 repository cannot be a commit; attempt the cheap identity proofs first:
   - Hash the requirements or issue source the token claims to bind (`sha256` of the exact source bytes). A byte-match proves the token is a content digest, not a revision.
   - Inspect the carrier or artifact for an explicit `revision` field or a base marker; treat a present field as the authoritative measurement base and prove it by spot-pin.
   - Only then try VCS resolution (`git cat-file -t`, `git rev-parse`) to rule out a real revision.
2. Bind verification to the base the claims were measured against, in this order: explicit revision field > base marker in the artifact > `git rev-list -1 --before="<artifact publication time>" <mainline>` for the publication-preceding tip > reconstructed proxy (last resort; record it as approximate).
3. Re-derive every measured claim at that base. Each claim that passes at the measurement base but fails at the current base is base drift; each claim that fails at the measurement base is a plan defect. Prove the classification:
   - `git log --follow --oneline -- <file>` for the movement history,
   - `git log -S"<symbol>" --oneline` for symbol moves or removals,
   - the diff between measurement base and current base for the exact lines.
4. Record both epochs in the published evidence — authoring base where truth was proven, current base where relevance is judged. Reviewers: a drifted pin is still a required finding, but state the class and the proof. Authors: the minimal correct resolution of an epoch finding is usually to name the verified epoch explicitly in the artifact; re-pin everything to the current base only when the closure condition asks for it or the epoch cannot be proven.
5. Settle count or range disputes with one authoritative enumeration: `git rev-list --count <epoch>..<base> -- <path>` plus `git log --oneline <epoch>..<base> -- <path>`. Note that one commit can touch several files in the table; recount per file, not per table row. Never adopt either side's count — measure it.
6. Digest hygiene during publication is unchanged: compute digests over the exact bytes (strip exactly the one transport-appended line feed when the read path adds one), and treat the digest — not byte counts — as the artifact identity, since character counts and byte counts diverge on non-ASCII text.

### Quick Reference

| Question | Command or check |
| --- | --- |
| Is the token a content digest? | `sha256(source bytes) == token` |
| Is the token a real revision? | `git cat-file -t <token>` |
| Authoritative base? | carrier `revision` field > base marker > `git rev-list -1 --before="<artifact time>" main` |
| Authoring-truth or drift? | re-derive at base; prove with `git log --follow`, `git log -S` |
| Settle a count dispute | `git rev-list --count <a>..<b> -- <path>` |

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --- | --- | --- | --- |
| 1 | Fetch the 64-hex epoch token as a git ref | The token was `sha256` of the requirements source, not an object; fetch and history search both empty | Hash the candidate source first; a content-digest token proves itself by byte match, and the carrier's explicit revision field names the true base |
| 2 | Verify every pin only at the current base | Pins that were exact at authoring read as false defects; one lane produced wrong-class findings until corrected | Classify with two checkpoints: measurement base for truth, current base for relevance; name the class and proof for each failure |
| 3 | Reconstruct the measurement base by proxy checkout when no revision field was found | The proxy tip matched most but not all pins; risk of off-by-days measurement | Prefer `git rev-list -1 --before="<artifact publication time>"`; a publication-preceding tip is deterministic and checkable |
| 4 | Trust a reviewer commit count over the author's (or vice versa) | Both were human counts from different methods; the table they summarized counted files touched by one commit twice | Settle counts mechanically with `git rev-list --count` per path; report the command as the evidence |

## Results & Parameters

- Token classification order: hash-the-source → inspect explicit `revision` field → VCS resolution attempt. Expected output: one of the classes `content-digest`, `explicit-revision`, `vcs-revision`, or `unclassifiable` (stop and report).
- Dual-epoch evidence record per claim: measurement-base result, current-base result, class (`defect` or `drift`), and the command output that proves the class.
- Epoch-resolution for authors: name the proven epoch in the artifact (for example a `source-base` marker carrying the exact revision) rather than re-pinning, unless closure requires re-pinning.
- Distribution note: apply the same source-time discipline to every artifact in the exchange; a mixed-epoch evidence chain (some claims at authoring base, some at current base) must say which epoch each claim binds.

## Verified On

- Multi-round chain-verified plan/review exchanges over a fast-moving automation monorepo: three independent lanes hit the same 64-hex content-digest token; two resolved it definitively (`sha256` byte match against the requirements source; explicit carrier `revision` field proven by an all-pins-exact audit), one used a proxy first and later converged.
- Dual-epoch classification applied across seven review rounds with zero defect-or-drift misclassifications after adoption.
- A reviewer-versus-author commit-count dispute (six versus seven) resolved by `git rev-list --count`; the mechanical count also explained the miss (one commit touched two tracked files).

## References

- Companion entries: review-exchange assessment-order, head-refresh carrier repair, terminal carrier, and terminal manifest construction skills (same corpus) cover carrier-chain mechanics; this entry covers only how an advertised epoch is identified and how pins bind to a base.
- `git rev-list(1)`, `git log --follow` and `git log -S` manual pages.
