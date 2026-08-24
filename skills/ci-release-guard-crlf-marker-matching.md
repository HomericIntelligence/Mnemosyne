---
name: ci-release-guard-crlf-marker-matching
license: BSD-3-Clause
description: "A whole-line fixed-string guard (`grep -Fqx needle`) that validates a marker embedded in externally-stored text (a GitHub Release body fetched back through the API) yields FALSE REFUSALS when the stored text uses CRLF line endings — GitHub may persist CRLF even when your writer sent LF, so the marker line ends `-->\\r` and never equals an LF-only needle. Strip carriage returns BEFORE the match: `printf '%s\\n' \"$BODY\" | tr -d '\\r' | grep -Fqx \"$MARKER\"`. Use when: (1) a release/publish workflow's unsafe-retry guard refuses a re-dispatch with 'lacks provenance' even though PyPI, artifacts, attestations, and the marker itself are all intact, (2) you write any guard that matches an exact line inside text fetched from GitHub (release/issue/PR bodies, API JSON string fields), (3) you are tempted to trust exit status alone when probing CLI capabilities — pre-2.31 git ECHOES unknown flags with exit 0, so output shape must be asserted too, (4) auditing existing `-Fqx`/`-Fx` guards for line-ending sensitivity."
category: ci-cd
date: 2026-08-23
version: "1.0.0"
user-invocable: false
verification: verified-ci
tags:
  - release-workflow
  - unsafe-retry-guard
  - crlf
  - grep-Fqx
  - whole-line-match
  - provenance-marker
  - github-release-body
  - capability-probe
  - output-strict-probe
  - hephaestus
---

# CI: Release Guard vs CRLF Bodies (Strip CR Before Whole-Line Marker Matches)

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-08-23 |
| **Objective** | Recover a refused v0.10.4 release re-dispatch (Hephaestus Release run 32661118992: "Existing published release lacks immutable source provenance") whose source-sha marker WAS present in the immutable GitHub Release body. |
| **Outcome** | Success — root cause was CRLF storage of the release body defeating `grep -Fqx` whole-line matching against an LF-only needle; fix strips `\r` before both marker matches (PR HomericIntelligence/Hephaestus#2819, merged). Reproduced against the live body bytes: old guard no-match, fixed guard match. Post-fix dispatch run 32664443843 passed the previously-failing guard end-to-end. |
| **Verification** | verified-ci (fix merged to main via required-gate PR #2819; live Release dispatch succeeded through the patched guard) |

## When to Use

Apply this pattern when a **guard that matches an exact line in externally-stored text** changes verdict on line endings you do not control:

- A release/publish workflow's retry/provenance guard fetches a GitHub Release body back through the API and does `printf '%s\n' "$BODY" | grep -Fqx "$MARKER"` — and it FAILS while every substantive artifact (PyPI deployment, assets, attestations) is intact.
- You store a nonce/hash marker via one writer (e.g. `softprops/action-gh-release`, release-notes APIs) and validate it via another reader; GitHub may normalize or store the body with `\r\n`.
- You audit existing `-Fqx`/`-Fx`/`==`-line guards over API-fetched text for line-ending sensitivity.
- Related trap surfaced by the same incident: a **capability probe that trusts exit status alone** is unsound — `git rev-parse --path-format=absolute --show-toplevel` on pre-2.31 git ECHOES the unknown flag as an extra stdout line and exits 0, so both "supported" and "unsupported" hosts can return rc=0 depending on context. Assert output SHAPE (exactly one line equal to the expected value), not just rc.

**Key trigger:** the marker is visibly present in the stored text (even byte-inspectable via `od -c`) but a whole-line match returns false — suspect a trailing `\r`.

## Verified Workflow

> Verification level: **verified-ci**. Fix merged through the Hephaestus required-gate lane (PR #2819); live Release dispatch 32664443843 passed the patched guard.

### Quick Reference

```bash
# WRONG — LF-only needle vs possibly-CRLF stored body:
printf '%s\n' "$RELEASE_BODY" | grep -Fqx "$MARKER"

# RIGHT — strip CRs before the whole-line match:
printf '%s\n' "$RELEASE_BODY" | tr -d '\r' | grep -Fqx "$MARKER"
```

```bash
# Prove which side is lying, byte-level (v0.10.4 case: '-->' followed by \r \n):
gh api "repos/<org>/<repo>/releases/tags/vX.Y.Z" --jq '.body' | head -c 200 | od -c | head

# Reproduce old-vs-fixed against the LIVE body:
SHA=$(git rev-parse origin/main^{commit})
M="<!-- hephaestus-source-sha:${SHA} -->"
B=$(gh api "repos/<org>/<repo>/releases/tags/vX.Y.Z" --jq '.body')
printf '%s\n' "$B" | grep -Fqx "$M"            && echo OLD=match || echo OLD=no-match
printf '%s\n' "$B" | tr -d '\r' | grep -Fqx "$M" && echo FIXED=match || echo FIXED=no-match
```

```bash
# Capability probes must assert OUTPUT SHAPE, not exit status alone:
# pre-2.31 git echoes unknown flags with rc=0, so rc-only probes lie BOTH ways.
probe=$(git rev-parse --path-format=absolute --show-toplevel 2>/dev/null)
[ "$(git rev-parse --path-format=absolute --show-toplevel 2>/dev/null | wc -l)" -eq 1 ] \
  && [ "$probe" = "$EXPECTED_ABSOLUTE_TOPLEVEL" ]
```

### Detailed Steps

1. **Treat externally-stored text as having hostile line endings.** Any guard matching an exact line inside a GitHub Release/issue/PR body must normalize CRs first: `tr -d '\r'` before `grep -Fqx`. The writer's LF is not a contract — v0.10.4's body was stored fully CRLF (verified with `od -c`: `--> \r \n`), so the whole-line needle `<!-- hephaestus-source-sha:<sha> -->` never equaled the stored line. This silently inverted the unsafe-retry guard: a routine re-dispatch of a FULLY PUBLISHED release was refused, blocking even the built-in docs-only recovery path.

2. **Patch EVERY whole-line match site over the same text, not just the one that failed.** In Hephaestus `release.yml` two independent sites matched the marker (the resolve-step provenance check and the draft-finalize step); fixing only the observed failure leaves a latent twin. Grep the workflow for `-Fqx`/`-Fx` over fetched bodies and fix each with the same `tr -d '\r' |` prefix, with a comment citing the incident.

3. **Reproduce old-vs-fixed against live bytes before shipping.** The two-command reproduction (old guard no-match / fixed guard match against the real API body) converts a plausible theory into proof, and doubles as the regression narrative in the PR. Include the failing run ID, the successful historical run, and the post-fix dispatch ID so reviewers can audit the chain: 32661118992 (refused) → #2819 → 32664443843 (passed).

4. **Capability probes need output-shape assertions, not just exit codes.** The same incident session found `git rev-parse --unknown-flag --show-toplevel` returning rc=0 on git 2.30 (flag echoed into stdout), making rc-only probes claim support on incapable hosts AND fail inside non-repo cwds on capable ones. Probe from a known repo, require exactly one stdout line equal to the expected absolute value. (See `tests/conftest.py::require_git_path_format` in Hephaestus for the pattern.)

5. **Distinguish this from whitespace-wrapping false failures.** The sibling failure mode — multi-word substring checks broken by line-wrapping — needs `\s+`→space collapsing (see `testing-doc-guard-markdown-linewrap-substring`). Whole-line EXISTENCE guards have the opposite requirement: keep the line intact but normalize its endings. Choosing the wrong normalization weakens the guard (line-collapsing would let a marker buried mid-paragraph match).

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Trust the writer's line endings | Guard assumed `action-gh-release` stores the `body:` it was given verbatim as LF lines | v0.10.4's stored body was fully CRLF (`od -c` shows `--> \r \n`), so `-Fqx` never matched; the release was complete but the retry guard refused recovery | Externally-stored text must be CR-normalized before exact-line matching; writer-side formatting is not part of the reader's contract |
| Exit-status-only capability probe | `_git_supports_path_format()` returned `rc == 0` from a non-repo cwd, then `rc == 0` inside a repo | First form fails everywhere (`--show-toplevel` needs a repo); second succeeds on git 2.30 because unknown flags are ECHOED with rc=0 — probe claimed support on incapable hosts, silently skipping 16 tests suite-wide | Assert output shape (single stdout line == expected absolute path), not exit code; probe from a real repository |
| Fix only the observed match site | Patching the resolve-step provenance check initially left the draft-finalize `-Fqx` untouched | Same body, same CR exposure, second latent refusal | Sweep ALL exact-line matches over the same stored text in the same change |

## Results & Parameters

**The one load-bearing pipe:**

```bash
printf '%s\n' "$STORED_BODY" | tr -d '\r' | grep -Fqx "$MARKER"
```

**Byte-level triage one-liner (is it CRLF?):**

```bash
gh api "repos/$REPO/releases/tags/$TAG" --jq '.body' | head -c 200 | od -c | grep -m1 '\\r'
```

**Generalization (the durable, reusable rule):** Guards that match exact lines in text retrieved from external systems (GitHub bodies, issue timelines, third-party APIs) must normalize transport-introduced line endings before comparing — `tr -d '\r'` for whole-line fixed-string matches. Corollary: CLI capability probes must assert output shape, because tools differ on whether unknown flags error, warn-and-continue, or echo. Both failures share one root discipline: **never let a comparison's verdict rest on bytes you don't own** — normalize first, then assert the invariant you actually care about. Cross-reference `testing-doc-guard-markdown-linewrap-substring` for the wrapping analogue and `gha-release-package-workflow-patterns` for `$GITHUB_OUTPUT` escaping (a different byte-mangling layer entirely).

## Verified On

| Repository | Issue / PR | What was applied |
| ------------ | ------------ | ------------------ |
| HomericIntelligence/Hephaestus | failed dispatch run 32661118992 → PR #2819 (merged) → validation dispatch 32664443843 (success) | `release.yml`: `tr -d '\r' |` added before both source-sha marker `-Fqx` matches with incident comments; reproduced no-match→match against the live v0.10.4 body; post-fix dispatch passed the guard and correctly skipped republish of the already-published version |

## Tags

`#release-workflow` `#unsafe-retry-guard` `#crlf` `#grep-Fqx` `#whole-line-match` `#provenance-marker` `#github-release-body` `#capability-probe` `#output-strict-probe` `#hephaestus`
