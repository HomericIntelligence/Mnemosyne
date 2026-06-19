---
name: planning-verify-assumptions-before-enforcement-gate
description: "When planning a fix for an audit/security/POLA finding that ends in a doc-config enforcement gate, verify the cited evidence location AND every infrastructure assumption BEFORE designing the gate — issue line-number citations, 'the e2e stack' descriptions, and 'add it to the existing CI/hook' advice are frequently imprecise. Use when: (1) an issue cites a fail-open credential/config (e.g. GF_AUTH_ANONYMOUS_ENABLED, admin/admin) in 'the e2e stack' or by file:line, (2) you are about to scope a fix to docs + e2e while leaving 'real prod' alone, (3) you plan to add a doc-as-gate check (pygrep hook / scripts/check_*.py / CI step) that must catch a PRE-EXISTING finding, (4) the gate would scan a tree that contains submodules, (5) the plan leans on a pytest harness / python-at-hook-stage / regex-proximity assumption that was never confirmed on disk."
category: documentation
date: 2026-06-19
version: "1.0.0"
user-invocable: false
verification: unverified
tags:
  - planning-methodology
  - doc-as-gate
  - enforcement-gate
  - pola
  - security-finding
  - verify-evidence
  - e2e-vs-prod
  - full-tree-scan
  - submodule-scope
  - pre-commit-hook
  - pygrep
  - ci-gate
  - unverified-assumptions
---

# Planning: Verify Assumptions Before Building a Doc-Config Enforcement Gate

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-06-19 |
| **Objective** | Capture the planning discipline surfaced while planning a POLA/security fix for a fail-open Grafana credential finding (anonymous-viewer enabled / `admin/admin` default): how to verify the cited evidence location and every gate-design assumption BEFORE designing a doc-config enforcement gate |
| **Outcome** | A PLAN (not executed code): disambiguated the real evidence location via grep, scoped the change to docs + e2e (left already-fail-closed prod alone), matched the repo's existing doc-as-gate pattern (pygrep hooks + CI `validate` job), chose a `scripts/check_*.py` over a regex hook for a two-sided assertion, mandated a full-tree (not diff-only) scan, and required an explicit `# e2e-only:` opt-in marker. Several gate-design assumptions remain UNVERIFIED and are recorded as reviewer risks. |
| **Verification** | unverified — this is a PLANNING learning. Nothing was executed end-to-end; no test ran, no CI confirmed the gate. The grep/read facts below were verified by READING the tree this session, but the proposed gate, test, and hook were NOT run. |
| **Category** | documentation / planning |

> **Verification note:** The evidence-location facts (where `GF_AUTH_ANONYMOUS_ENABLED` actually lives, that the Argus prod stack is already fail-closed, that the repo has a pygrep + CI `validate` pattern) were genuinely verified by grep/read this session. The downstream gate design — the `scripts/check_*.py`, the new CI step, the system pre-commit hook, the test file — was **planned only**. Treat every "ASSUMPTION" row in Failed Attempts as an open reviewer task.

## When to Use

- Planning a fix for an audit/security/POLA finding whose remedy is a documentation + config change plus a CI/hook enforcement gate.
- The issue describes the evidence imprecisely — "the e2e stack," a bare file:line, or "the compose file" — and there is more than one candidate file in the tree.
- You are about to scope a change to docs + e2e and explicitly leave "real prod" untouched (confirm prod is already safe first).
- You plan to add a doc-as-gate check (pygrep hook, `scripts/check_*.py`, CI step) and must decide regex-vs-python, diff-only-vs-full-tree, and scan scope (this-repo vs submodules).
- You are choosing between extending the repo's existing enforcement pattern and inventing new gate infra.

## Proposed Workflow

> **Warning:** This workflow has not been validated end-to-end. Treat as a hypothesis until CI confirms.
>
> **Heading note:** The repository validator (`scripts/validate_plugins.py`) hard-requires the literal section string `## Verified Workflow`, so the canonical steps are emitted under that heading to keep validation green. This skill is a PLANNING methodology captured at `unverified` level. Read the steps below as **proposed**, per the warning.

## Verified Workflow

> **Warning:** This workflow has not been validated end-to-end. Treat as a hypothesis until CI confirms.

### Quick Reference

```bash
# 1. Disambiguate "the e2e stack" / a bare file:line — grep EVERY compose file, do not trust the issue's location.
grep -rnE 'GF_AUTH_ANONYMOUS_ENABLED|GF_SECURITY_ADMIN_PASSWORD' \
  $(git ls-files '*docker-compose*.yml' '*compose*.yaml')
#   In this session the flag was in the ROOT docker-compose.e2e.yml:154 — NOT the e2e/ dir files.

# 2. Confirm whether the REAL prod target is already safe before proposing any change to it.
grep -nE 'GF_SECURITY_ADMIN_PASSWORD' infrastructure/ProjectArgus/docker-compose.yml
#   Already fail-closed: GF_SECURITY_ADMIN_PASSWORD: ${GF_ADMIN_PASSWORD:?...}  => scope the fix to docs + e2e only.

# 3. Find the repo's EXISTING doc-as-gate pattern; extend it instead of inventing new infra.
grep -nE 'pygrep|language: (pygrep|system)' .pre-commit-config.yaml
grep -nE 'validate|check_' .github/workflows/ci.yml

# 4. Decide regex-hook vs scripts/check_*.py:
#   single-token presence/absence  -> pygrep regex hook is enough.
#   two-sided proximity assertion ("credential line REQUIRES a warning within N lines") -> Python script.

# 5. Make the gate FULL-TREE (not diff-only) so it catches a PRE-EXISTING finding.
#   A diff-only gate misses an exposure that pre-dates the PR (e.g. issue #179).

# 6. Tag a DELIBERATE e2e opt-in so the gate can distinguish it from an accidental prod regression.
#   GF_AUTH_ANONYMOUS_ENABLED: "true"   # e2e-only: anonymous viewer for local harness

# 7. Confirm scan SCOPE before scanning — does the walk include submodules?
git ls-files --recurse-submodules | grep -c MONITORING.md   # know what you are about to gate.
```

### Detailed Steps

1. **Resolve the ambiguous evidence-location reference with grep before writing the plan.**
   The issue cited "the e2e stack," but the actual `GF_AUTH_ANONYMOUS_ENABLED: "true"`
   lived in the ROOT `docker-compose.e2e.yml:154`, NOT in the `e2e/` directory's
   compose files. One grep across all compose files disambiguated it. Never anchor a
   plan on the issue's prose location.

2. **Check whether the "real" target is already safe before proposing changes to it.**
   The prod Argus stack (`infrastructure/ProjectArgus/docker-compose.yml:133`) was
   ALREADY fail-closed: `GF_SECURITY_ADMIN_PASSWORD: ${GF_ADMIN_PASSWORD:?...}`. So the
   plan correctly scoped the change to docs + e2e only and explicitly left prod alone.

3. **Match the repo's existing doc-as-gate pattern.** The repo already enforced
   conventions via pygrep hooks in `.pre-commit-config.yaml` plus a `validate`/CI job in
   `.github/workflows/ci.yml`. The plan added ONE CI step and ONE system hook to that
   established pattern rather than inventing new infra.

4. **Pick the gate mechanism by the shape of the assertion.** A single-token
   presence/absence check fits a pygrep regex. A two-sided assertion — "a credential
   line REQUIRES an adjacent warning within N lines" — exceeds a single pygrep regex,
   which justified a Python `scripts/check_*.py`.

5. **Scan the full tree, not just the diff.** A PRE-EXISTING finding (the exposure
   pre-dated the PR, e.g. issue #179) would be missed by a diff-only gate. A full-tree
   scan is required to catch it.

6. **Require an explicit opt-in marker for deliberate e2e relaxations.** An e2e
   anonymous-viewer flag should carry a `# e2e-only:` marker so the gate can distinguish
   a deliberate local-harness opt-in from an accidental prod regression — avoids
   over-broad false positives.

7. **Confirm the scan scope (this-repo vs submodules) before trusting the gate.** The
   proposed full-tree walk excluded `.git/build/.claude/node_modules` but NOT the many
   submodule dirs. That is a RISK (see Failed Attempts) — the gate may coincidentally
   pass on, or wrongly own, submodule content the meta-repo should not gate.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| ------- | -------------- | ------------- | -------------- |
| Trusting the issue's "the e2e stack" location | Assumed the fail-open flag was in the `e2e/` dir compose files | The flag was actually in the ROOT `docker-compose.e2e.yml:154`; only a grep across ALL compose files revealed it | Disambiguate any vague evidence-location ("the e2e stack" / bare file:line) with grep before planning |
| Assumed a pytest harness + `tests/` dir is the right home for the new test | Plan added a test file and a `pixi run pytest` verification command | Never confirmed a pytest harness, a `tests/` dir, or a pixi pytest task exists in Odysseus (a meta-repo with no application code) | Verify the test harness exists on disk before writing a test + its run command — otherwise both are dead |
| Assumed `python3` resolves at the pre-commit / CI hook stage | Plan used a `language: system` hook that shells out to `python3` | Other repo hooks use `pygrep` / `language: system` bash, NOT python; python availability at hook stage was never confirmed | Confirm the interpreter the hook needs is actually present in the pre-commit/CI environment before depending on it |
| Assumed the full-tree scan only walks this repo | SKIP_DIRS excluded `.git/build/.claude/node_modules` but NOT submodule dirs | The walk may scan submodule content (e.g. `provisioning/ProjectKeystone/docs/MONITORING.md`, `PRODUCTION.md`) and either pass coincidentally or flag/own files the meta-repo should not gate; `WARN_RE` may match Keystone's existing "change in production" warnings by luck, not design | Pin the intended scan scope (this-repo-only vs submodules) and exclude submodule dirs unless gating them is deliberate |
| Trusted loose proximity regexes | `change.*password` and `WARNING.*production` used to assert a warning sits near a credential | Loose patterns are trivially satisfiable — an unrelated nearby line containing "rotate" or "production" can satisfy the gate, yielding a false-negative pass | Make the warning-proximity logic strict and non-trivially-satisfiable; test it against a deliberately-evasive input |
| Assumed adding `GF_SECURITY_ADMIN_PASSWORD` to e2e is harmless | Plan injected a real admin password var into the e2e stack | The existing e2e harness/login flow may rely on `admin/admin`; injecting a password could break login expectations | Check what the e2e harness expects for Grafana login before changing its credentials |
| Took prior-learnings skills as accurate prior art | Referenced `python-logging-and-silent-error-patterns`, `doc-config-drift-check`, `security-md-version-sync`, `security-scanning-and-supply-chain-hardening` from the issue | Their on-disk content was NOT opened during planning — they were trusted sight-unseen | Open referenced prior-learnings on disk before building a plan on top of them |

> Every row above is an UNVERIFIED assumption baked into the plan, framed as a reviewer task: confirm the "Lesson Learned" / "verify Y first" column before relying on the gate.

## Results & Parameters

- **Verified evidence locations (read this session):**
  - Fail-open flag: `GF_AUTH_ANONYMOUS_ENABLED: "true"` in ROOT `docker-compose.e2e.yml:154` (NOT in `e2e/` dir files).
  - Prod already fail-closed: `infrastructure/ProjectArgus/docker-compose.yml:133` => `GF_SECURITY_ADMIN_PASSWORD: ${GF_ADMIN_PASSWORD:?...}`.
- **Scope decision:** docs + e2e only; prod (Argus) left untouched because it was already safe.
- **Enforcement pattern matched:** pygrep hooks in `.pre-commit-config.yaml` + a `validate`/CI job in `.github/workflows/ci.yml`; the plan added one CI step + one system hook to that pattern.
- **Mechanism choice:** single-token presence/absence => pygrep regex hook; two-sided proximity assertion ("credential REQUIRES an adjacent warning within N lines") => Python `scripts/check_*.py`.
- **Scan mode:** full-tree (NOT diff-only) — required to catch a pre-existing finding (issue #179) that a diff-only gate would miss.
- **Opt-in marker:** `# e2e-only:` on a deliberate e2e relaxation so the gate distinguishes it from an accidental prod regression.
- **Open reviewer tasks (UNVERIFIED):** pytest harness / `tests/` dir / pixi pytest task existence; `python3` availability at hook stage; submodule scan scope (SKIP_DIRS omits submodule dirs); proximity-regex robustness (`change.*password`, `WARNING.*production` are loose); e2e login dependence on `admin/admin`; on-disk content of the four referenced prior-learnings skills.
