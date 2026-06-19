---
name: planning-verify-assumptions-before-enforcement-gate
description: "When planning a fix for an audit/security/POLA finding that ends in a doc-config enforcement gate, verify the cited evidence location AND every infrastructure assumption BEFORE designing the gate — issue line-number citations, 'the e2e stack' descriptions, and 'add it to the existing CI/hook' advice are frequently imprecise. Scope the gate's file scan with `git ls-files` (the index) instead of filesystem `rglob` so submodules and gitignored worktrees are excluded for free; confirm the language's test runner is actually wired (a polyglot/meta-repo may have no pytest) and prefer a stdlib `--self-test`; resolve every risk in the plan body (a risk merely listed in a Learnings note does NOT count). Use when: (1) an issue cites a fail-open credential/config (e.g. GF_AUTH_ANONYMOUS_ENABLED, admin/admin) in 'the e2e stack' or by file:line, (2) you are about to scope a fix to docs + e2e while leaving 'real prod' alone, (3) you plan to add a doc-as-gate check (pygrep hook / scripts/check_*.py / CI step) that must catch a PRE-EXISTING finding, (4) the gate would scan a tree that contains submodules, (5) the plan leans on a pytest harness / python-at-hook-stage / regex-proximity assumption that was never confirmed on disk."
category: documentation
date: 2026-06-19
version: "1.1.0"
user-invocable: false
verification: unverified
history: planning-verify-assumptions-before-enforcement-gate.history
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
  - git-ls-files
  - pre-commit-hook
  - pygrep
  - ci-gate
  - self-test
  - resolve-not-list-risks
  - unverified-assumptions
---

# Planning: Verify Assumptions Before Building a Doc-Config Enforcement Gate

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-06-19 |
| **Objective** | Capture the planning discipline surfaced while planning a POLA/security fix for a fail-open Grafana credential finding (anonymous-viewer enabled / `admin/admin` default): how to verify the cited evidence location and every gate-design assumption BEFORE designing a doc-config enforcement gate. Amended after re-planning issue #179 following a NOGO review. |
| **Outcome** | A PLAN (not executed code): disambiguated the real evidence location via grep, scoped the change to docs + e2e (left already-fail-closed prod alone), matched the repo's existing doc-as-gate pattern (pygrep hooks + CI `validate` job), chose a `scripts/check_*.py` over a regex hook for a two-sided assertion, scoped the scan to the git INDEX (`git ls-files`) so submodules drop out for free, made the gate SELF-TESTING via a stdlib `--self-test` (no pytest exists in this meta-repo), tightened the proximity regex to require an admonition token, and RESOLVED each prior risk in the plan body. A few runtime assumptions (git metadata present in CI, `git` on PATH at hook stage) remain reviewer risks. |
| **Verification** | unverified — this is a PLANNING learning. Nothing was executed end-to-end; the gate script was NOT run in CI (no PR run observed). The grep/read facts below were verified by READING the tree this session, but the proposed gate, self-test, and hook were NOT executed. |
| **Category** | documentation / planning |
| **History** | [changelog](./planning-verify-assumptions-before-enforcement-gate.history) |

> **Verification note:** The evidence-location facts (where `GF_AUTH_ANONYMOUS_ENABLED` actually lives, that the Argus prod stack is already fail-closed, that `git ls-files '*.md'` returns only `docs/deployment.md`, that `pixi.toml` has no pytest task and `just test` runs `ctest` + bash) were genuinely verified by grep/read this session. The downstream gate design — the `scripts/check_*.py`, its `--self-test`, the new CI step, the system pre-commit hook — was **planned only**. Treat every "ASSUMPTION" / risk row in Failed Attempts as an open reviewer task.

## When to Use

- Planning a fix for an audit/security/POLA finding whose remedy is a documentation + config change plus a CI/hook enforcement gate.
- The issue describes the evidence imprecisely — "the e2e stack," a bare file:line, or "the compose file" — and there is more than one candidate file in the tree.
- You are about to scope a change to docs + e2e and explicitly leave "real prod" untouched (confirm prod is already safe first).
- You plan to add a doc-as-gate check (pygrep hook, `scripts/check_*.py`, CI step) and must decide regex-vs-python, diff-only-vs-full-tree, and scan scope (this-repo vs submodules).
- The gate would walk a submodule meta-repo: prefer `git ls-files` over `Path.rglob` so the scan never descends into submodule trees or gitignored worktrees.
- You are about to write a `pixi run pytest ...` (or any test-runner) verification command — confirm that runner is actually wired before depending on it; in a polyglot/meta-repo it may not exist.
- You are choosing between extending the repo's existing enforcement pattern and inventing new gate infra.
- A reviewer NOGO'd a prior plan for "acknowledged but unresolved" risks — every risk must be resolved in the body, not merely listed in a notes section.

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

# 3. SCOPE the gate's scan to the git INDEX, NOT a filesystem walk. In a submodule meta-repo
#    Path.rglob("*.md") descends INTO submodules and matches files the repo cannot edit.
git ls-files '*.md'            # -> only docs/deployment.md (the ONE tracked .md), submodules excluded for free
git ls-files '*.yml' '*.yaml'  # -> only docker-compose.e2e.yml
#   git ls-files also excludes gitignored worktrees automatically — no manual SKIP_DIRS list needed.

# 4. Find the repo's EXISTING doc-as-gate pattern; extend it instead of inventing new infra.
grep -nE 'pygrep|language: (pygrep|system)' .pre-commit-config.yaml

# 5. Decide regex-hook vs scripts/check_*.py:
#   single-token presence/absence  -> pygrep regex hook is enough.
#   two-sided proximity assertion ("credential line REQUIRES a warning within N lines") -> Python script.

# 6. CONFIRM the test runner before writing a verification command — do not assume pytest.
grep -nE 'pytest|\[tasks\]' pixi.toml      # this meta-repo has NO pytest task/dep
grep -nE 'test' justfile                     # `just test` runs ctest (C++) + tests/install/*.sh (bash)
#   No Python runner => make the gate SELF-TESTING with a stdlib subcommand instead of a pytest file:
python3 scripts/check_doc_config_gate.py --self-test   # builds temp git repos, asserts exit codes

# 7. TIGHTEN proximity regexes: require an admonition token AND a verb, not a bare verb.
#   BAD : WARN_RE = rotate|change.*password   (matched by "we rotate logs nightly")
#   GOOD: requires (warning|caution|important) AND (rotate|change) near the credential
#   Add an explicit NEGATIVE test: assert a bare "rotate" line does NOT pass the gate.

# 8. Make the gate FULL-TREE over the index (not diff-only) so it catches a PRE-EXISTING finding (#179).

# 9. Tag a DELIBERATE e2e opt-in so the gate can distinguish it from an accidental prod regression.
#   GF_AUTH_ANONYMOUS_ENABLED: "true"   # e2e-only: anonymous viewer for local harness
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

3. **Scope the file scan with `git ls-files`, not filesystem `rglob`.** This is the
   fix for the prior plan's submodule-scope risk. Odysseus references ~14 submodules;
   `Path.rglob("*.md")` walks INTO those trees and matches files the meta-repo cannot
   edit (e.g. `ProjectKeystone`'s `MONITORING.md`/`PRODUCTION.md` contain `admin / admin`;
   its `k8s/grafana.yaml` sets `GF_AUTH_ANONYMOUS_ENABLED`), making the gate go
   red-on-clean-tree on content owned elsewhere. `git ls-files '*.md'` returned ONLY the
   one tracked file (`docs/deployment.md`); `git ls-files '*.yml' '*.yaml'` returned ONLY
   `docker-compose.e2e.yml`. Scanning the index excludes submodules AND gitignored
   worktrees for free — no manual `SKIP_DIRS` list needed.

4. **Match the repo's existing doc-as-gate pattern.** The repo already enforced
   conventions via pygrep hooks in `.pre-commit-config.yaml` plus a `validate`/CI job in
   `.github/workflows/ci.yml`. The plan added ONE CI step and ONE system hook to that
   established pattern rather than inventing new infra.

5. **Pick the gate mechanism by the shape of the assertion.** A single-token
   presence/absence check fits a pygrep regex. A two-sided assertion — "a credential
   line REQUIRES an adjacent warning within N lines" — exceeds a single pygrep regex,
   which justified a Python `scripts/check_*.py`.

6. **Confirm the test runner exists before writing a verification command; prefer a
   stdlib self-test.** The prior (NOGO'd) plan used `pixi run pytest tests/...`, but
   `pixi.toml [tasks]` has no pytest task/dep and `just test` runs `ctest` (C++) plus
   `tests/install/*.sh` (bash) — there is NO Python test runner. The fix makes the gate
   script SELF-TESTING via a stdlib `--self-test` subcommand (builds temp git repos,
   asserts exit codes) invoked from CI and `just lint`. In a polyglot/meta-repo, confirm
   the language's test runner is actually wired before assuming pytest.

7. **Tighten proximity-based doc-gate regexes.** A loose `WARN_RE = rotate|change.*password`
   is satisfied by coincidental nearby text (e.g. "we rotate logs nightly"). Require an
   admonition token (`warning`/`caution`/`important`) AND a rotate/change verb, and add an
   explicit NEGATIVE test case asserting a bare verb does NOT pass.

8. **Scan the full index, not just the diff.** A PRE-EXISTING finding (the exposure
   pre-dated the PR, e.g. issue #179) would be missed by a diff-only gate. A full-tree
   scan over `git ls-files` is required to catch it.

9. **Require an explicit opt-in marker for deliberate e2e relaxations.** An e2e
   anonymous-viewer flag should carry a `# e2e-only:` marker so the gate can distinguish
   a deliberate local-harness opt-in from an accidental prod regression — avoids
   over-broad false positives. Note the marker convention is newly introduced and is
   documented only inline + in the gate's error text (see risks).

10. **Resolve every risk in the plan BODY — listing it in a Learnings note is not enough.**
    The reviewer NOGO downgraded the prior plan because risks it had flagged in its own
    notes were left unfixed in the body. Each surfaced risk must be RESOLVED (changed
    approach + verification) in the plan body, not merely acknowledged.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| ------- | -------------- | ------------- | -------------- |
| Trusting the issue's "the e2e stack" location | Assumed the fail-open flag was in the `e2e/` dir compose files | The flag was actually in the ROOT `docker-compose.e2e.yml:154`; only a grep across ALL compose files revealed it | Disambiguate any vague evidence-location ("the e2e stack" / bare file:line) with grep before planning |
| Scanning the tree with filesystem `Path.rglob("*.md")` | Gate walked the whole working tree to find docs/configs to enforce | In a submodule meta-repo (~14 submodules) `rglob` descends INTO submodule trees and matches files the repo cannot edit (Keystone `MONITORING.md`/`PRODUCTION.md` hold `admin / admin`; its `k8s/grafana.yaml` sets `GF_AUTH_ANONYMOUS_ENABLED`) — gate goes red-on-clean-tree on content owned elsewhere | Scan the git INDEX via `git ls-files '*.md'` (returned only `docs/deployment.md`); it excludes submodules AND gitignored worktrees for free — no manual SKIP_DIRS |
| Referencing a `pixi run pytest` harness in the plan | Plan added a test file and a `pixi run pytest tests/...` verification command | `pixi.toml [tasks]` has no pytest task/dep; `just test` runs `ctest` (C++) + `tests/install/*.sh` (bash) — there is NO Python test runner | Confirm the language's test runner is wired before writing a verification command; in a polyglot/meta-repo prefer a stdlib `--self-test` over assuming pytest |
| Treating an "acknowledged risk" in the Learnings section as resolved | Prior plan flagged risks in its own notes but left them unfixed in the plan body | The reviewer NOGO'd / downgraded precisely because flagged risks were not resolved in the body | Every surfaced risk must be RESOLVED in the body (changed approach + verification), not merely listed |
| Trusted loose proximity regexes | `WARN_RE = rotate\|change.*password` used to assert a warning sits near a credential | A bare verb is trivially satisfied — "we rotate logs nightly" passes the gate by coincidence, a false-negative | Require an admonition token (`warning`/`caution`/`important`) AND a rotate/change verb; add a NEGATIVE test asserting a bare verb does NOT pass |
| Assumed `python3` / `git` resolves at the pre-commit / CI hook stage | Plan used a `language: system` hook that shells out to `python3` and the self-test shells out to `git init` in a tempdir | Other repo hooks use `pygrep` / bash; `python3` and `git`-on-PATH availability at hook stage and `git` metadata presence in CI were never confirmed on this PR | Confirm the interpreter AND `git` are present (and metadata fetched by `actions/checkout`) in the pre-commit/CI environment before depending on them |
| Assumed adding `GF_SECURITY_ADMIN_PASSWORD` to e2e is harmless | Plan injected a real admin password var into the e2e stack | The existing e2e harness/login flow may rely on `admin/admin`; injecting a password could break login expectations | Check what the e2e harness expects for Grafana login before changing its credentials |
| Took prior-learnings skills as accurate prior art | Referenced `python-logging-and-silent-error-patterns`, `doc-config-drift-check`, `security-md-version-sync`, `security-scanning-and-supply-chain-hardening` from the issue | Their on-disk content was NOT opened during planning — they were trusted sight-unseen | Open referenced prior-learnings on disk before building a plan on top of them |

> Every row above is an UNVERIFIED assumption baked into the plan, framed as a reviewer task: confirm the "Lesson Learned" / "verify Y first" column before relying on the gate.

## Results & Parameters

- **Verified evidence locations (read this session):**
  - Fail-open flag: `GF_AUTH_ANONYMOUS_ENABLED: "true"` in ROOT `docker-compose.e2e.yml:154` (NOT in `e2e/` dir files).
  - Prod already fail-closed: `infrastructure/ProjectArgus/docker-compose.yml:133` => `GF_SECURITY_ADMIN_PASSWORD: ${GF_ADMIN_PASSWORD:?...}`.
- **Index-scoped scan (verified):** `git ls-files '*.md'` => only `docs/deployment.md`; `git ls-files '*.yml' '*.yaml'` => only `docker-compose.e2e.yml`. Submodules + gitignored worktrees excluded automatically. Submodule content a naive `rglob` would have matched: `provisioning/ProjectKeystone/docs/MONITORING.md`, `PRODUCTION.md` (`admin / admin`), `k8s/grafana.yaml` (`GF_AUTH_ANONYMOUS_ENABLED`).
- **Test-runner reality (verified):** `pixi.toml [tasks]` has no pytest; `just test` => `ctest` (C++) + `tests/install/*.sh` (bash). Gate is SELF-TESTING via `python3 scripts/check_doc_config_gate.py --self-test` (stdlib only, builds temp git repos), invoked from CI + `just lint`.
- **Scope decision:** docs + e2e only; prod (Argus) left untouched because it was already safe.
- **Enforcement pattern matched:** pygrep hooks in `.pre-commit-config.yaml` + a `validate`/CI job in `.github/workflows/ci.yml`; the plan added one CI step + one system hook to that pattern.
- **Mechanism choice:** single-token presence/absence => pygrep regex hook; two-sided proximity assertion ("credential REQUIRES an adjacent warning within N lines") => Python `scripts/check_*.py`.
- **Proximity regex (tightened):** require an admonition token (`warning`/`caution`/`important`) AND a rotate/change verb; negative test asserts a bare verb (e.g. "we rotate logs nightly") does NOT pass.
- **Scan mode:** full-index (NOT diff-only) — required to catch a pre-existing finding (issue #179) that a diff-only gate would miss.
- **Opt-in marker:** `# e2e-only:` on a deliberate e2e relaxation so the gate distinguishes it from an accidental prod regression. NEW convention — documented only inline + in the gate's error text.
- **Open reviewer tasks (UNVERIFIED):**
  - `git ls-files` needs git metadata present at gate runtime — confirmed locally, but in CI it depends on `actions/checkout` fetching the repo (not run in CI yet). Outside a git work tree, `git rev-parse --show-toplevel` fails.
  - The self-test shells out to `git init`/`git add` in a tempdir; assumes `git` is on PATH in CI and pre-commit envs (true here, not guaranteed universally).
  - The `e2e-only` marker convention is new — a future editor unaware of it could delete the marker, after which the gate would (correctly) fail; the convention is not documented beyond the inline comment + gate error text.
  - e2e login dependence on `admin/admin`; on-disk content of the four referenced prior-learnings skills.
  - End-to-end verification level is **unverified**: the plan was produced and its grep-facts verified, but the gate script was NOT executed in CI (no PR run observed).
