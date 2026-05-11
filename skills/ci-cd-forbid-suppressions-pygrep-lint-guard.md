---
name: ci-cd-forbid-suppressions-pygrep-lint-guard
description: "Pygrep pre-commit hook + matching CI job that rejects `|| true` and `continue-on-error: true` suppressions in committed source. Use when: (1) auditing a codebase for silent-failure workarounds, (2) a CI build mysteriously passes despite an obvious tool failure, (3) adding a regression guard so a refactored idiom cannot return, (4) refactoring `cmd || true` into explicit `if`-guards across multiple files, (5) deciding whether a `|| true` is masking a real failure (Bucket A) or guarding legitimate teardown (Bucket B), (6) widening a regex after an agent feedback loop discovers a missed control-flow boundary, (7) reviewing a sweep PR that converted `continue-on-error: true` to `if ! cmd; then echo \"::warning::...\"; fi` — that's Bucket F, the advisory anti-pattern, also forbidden, (8) auditing CI for tool-level suppression flags (`--exit-code 0`, `--exit-zero`, `--no-fail`) that mimic `continue-on-error: true`'s effect at the tool layer, (9) a CI tool runs but its findings (CVEs, leaked secrets, format diffs, type errors) never gate the merge — fix the policy by making the tool fail-fast and allowlisting specific findings with tracked issues."
category: ci-cd
date: 2026-05-11
version: "2.0.0"
user-invocable: false
verification: verified-ci
history: ci-cd-forbid-suppressions-pygrep-lint-guard.history
tags:
  - pre-commit
  - pygrep
  - silent-failures
  - lint-guard
  - or-true
  - continue-on-error
  - github-actions
  - regression-prevention
  - workaround-removal
  - bucket-classification
---
# Forbid-Suppressions Pygrep Lint Guard

| Attribute | Value |
| ----------- | ------- |
| **Date** | 2026-05-11 |
| **Objective** | Eliminate `\|\| true` and `continue-on-error: true` suppressions ecosystem-wide and add a regression guard that prevents the pattern from returning. |
| **Outcome** | 16 PRs across 15 repos — ~198 occurrences refactored. Lint guard ported to every repo. Memory `feedback_no_silent_failures` added. |
| **Verification** | verified-ci — guard is live in 16 PRs; regex passes pre-commit on all 15 repos; meta-repo CI job `forbid-suppressions` passed on the merged Odysseus PR #280; the regex-widening follow-up PR #281 was opened with the same job on it. |
| **PR (initial)** | HomericIntelligence/Odysseus#280 (merged) |
| **PR (regex widening)** | HomericIntelligence/Odysseus#281 |
| **Submodule PRs** | 14 (one per repo) — see Results table below. |

## Overview

A silent-failure idiom — `cmd || true` in shell/YAML/Dockerfile/justfile/HCL,
or `continue-on-error: true` in GitHub Actions — is a high-leverage way to
mask a real bug. When the underlying tool starts failing, the suppressed step
still reports green, and the failure surfaces somewhere down the line as an
empty file, missing artifact, or absent metric.

This skill captures the verified pattern for **(a)** removing every existing
instance ecosystem-wide and **(b)** installing a `pygrep` pre-commit hook
plus a matching GitHub Actions job that rejects the idiom on every future
commit. The guard is deployed in 15 repos and gated on the meta-repo CI.

## When to Use This Skill

- Auditing a codebase for silent-failure workarounds
- A CI build mysteriously passes despite an obvious tool failure
- Adding a regression guard so a refactored idiom cannot return
- Refactoring `cmd || true` into explicit `if`-guards across multiple files
- Deciding whether a `|| true` is masking a real failure (Bucket A) or
  guarding legitimate teardown (Bucket B)
- Widening a regex after an agent feedback loop discovers a missed
  control-flow boundary
- A user reports "this CI step is always green but the underlying tool
  obviously fails sometimes"
- A pattern like `goose --version || true` has masked a real failure
  (refer to `ci-cd-achaean-fleet-ci-cascade-patterns` v2.0.0 for the
  historical incident)
- You're considering adding a new `|| true` and want to know why you
  shouldn't

## Verified Workflow

### 1. The pre-commit hook (copy-paste ready)

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: forbid-or-true
        name: "forbid silent-failure workaround in shell/YAML/Dockerfile/justfile/HCL"
        description: >
          Rejects the `or-true` idiom (and its whitespace variants) in shell,
          YAML, Dockerfile, justfile, and HCL sources.
        language: pygrep
        entry: '^(?!\s*#).*\|\|\s*true(\s*$|\s*[#);&|])'
        files: \.(sh|bash|yml|yaml|hcl)$|(^|/)Dockerfile[^/]*$|(^|/)[Jj]ustfile$
        types: [text]
        pass_filenames: true

      - id: forbid-continue-on-error
        name: "forbid continue-on-error workflow opt-out"
        language: pygrep
        entry: '^\s*continue-on-error:\s*true\s*$'
        files: ^\.github/workflows/.*\.ya?ml$
        pass_filenames: true
```

Key field notes:

- `language: pygrep` — zero-script regex hook
- The leading `^(?!\s*#)` exempts comment lines so the runbook can quote the
  idiom verbatim for teaching
- The trailing `(\s*$|\s*[#);&|])` requires a control-flow boundary so
  literal documentation prose containing the phrase in backticks is not
  matched
- `files:` covers `.sh`, `.bash`, `.yml`, `.yaml`, `.hcl`, any `Dockerfile*`,
  and any `justfile` / `Justfile`

### 2. The matching CI job for `.github/workflows/_required.yml`

```yaml
  forbid-suppressions:
    name: forbid-suppressions
    runs-on: ubuntu-latest
    timeout-minutes: 5
    steps:
      - uses: actions/checkout@v4

      - name: "Reject silent-failure workaround in shell/YAML/Dockerfile/justfile/HCL"
        run: |
          # Scans top-level sources only — submodules carry their own copy
          # of this guard. Matches the forbidden idiom at any control-flow
          # boundary. See docs/runbooks/no-silent-failures.md.
          set -euo pipefail
          mapfile -t files < <(git ls-files \
            -- \
            '*.sh' '*.bash' '*.yml' '*.yaml' '*.hcl' \
            'Dockerfile*' '**/Dockerfile*' \
            'justfile' '**/justfile' 'Justfile' '**/Justfile')
          # Skip the runbook (documents the rule and quotes the idiom) and
          # this workflow file itself (heredoc would otherwise self-match).
          declare -a scan_files=()
          for f in "${files[@]}"; do
            case "$f" in
              docs/runbooks/no-silent-failures.md) continue ;;
              .github/workflows/_required.yml) continue ;;
            esac
            scan_files+=("$f")
          done
          if [ "${#scan_files[@]}" -eq 0 ]; then
            echo "No files to scan"
            exit 0
          fi
          if grep -nP '^(?!\s*#).*\|\|\s*true(\s*$|\s*[#);&|])' "${scan_files[@]}"; then
            echo ""
            echo '::error::Found silent-failure workarounds above. Refactor per docs/runbooks/no-silent-failures.md.'
            exit 1
          fi
          echo 'OK: no silent-failure workarounds found'

      - name: "Reject continue-on-error workflow opt-out"
        run: |
          set -euo pipefail
          mapfile -t files < <(git ls-files -- '.github/workflows/*.yml' '.github/workflows/*.yaml')
          if [ "${#files[@]}" -eq 0 ]; then
            echo "No workflow files"
            exit 0
          fi
          if grep -nE '^[[:space:]]*continue-on-error:[[:space:]]*true[[:space:]]*$' "${files[@]}"; then
            echo ""
            echo '::error::Found "continue-on-error: true" above. Fix the root cause per docs/runbooks/no-silent-failures.md.'
            exit 1
          fi
          echo 'OK: no "continue-on-error: true" found'
```

**Critical**: the first grep must use `-nP` (PCRE) because the regex uses
negative lookbehind for the comment skip. ERE (`-nE`) does not support
lookbehind. Standard GNU grep on `ubuntu-latest` runners is built with PCRE
support. The second grep (continue-on-error) is a flat anchored match, so
`-nE` works there.

### 3. Bucket A–E classification framework

When refactoring an existing `|| true`, classify it first; the canonical
fix depends on the bucket.

| Bucket | Pattern | Canonical fix |
|---|---|---|
| A — Masks a real failure | `cmd && check_pass ... \|\| true` | `if cmd; then check_pass ...; fi` |
| B — Best-effort cleanup | `kill ... 2>/dev/null \|\| true` | `if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then kill "$pid" 2>/dev/null \|\| echo "warn: ..." >&2; fi` |
| C — `((counter++)) \|\| true` | counter increment under `set -e` | `counter=$((counter + 1))` |
| D — Pipeline-tail suppression | `cmd \| grep \| head \|\| true` | Capture once: `_out=$(cmd) \|\| _out=''; printf '%s\n' "$_out" \| grep ... \| head -1 \|\| printf ''` |
| D-count — `grep -c \|\| true` | empty-input count fallback | `awk '/pattern/{n++} END{print n+0}'` (always exits 0) |
| E — `continue-on-error: true` | workflow step opt-out | Capture rc explicitly. **Note (v2.0.0):** the prior recommendation `if ! cmd; then echo "::warning::..."; fi` is now forbidden — see Bucket F. Prefer making the tool fail-fast and allowlisting unfixable findings with a tracking issue. |
| F — Advisory `::warning::` annotation wrapping a tool's exit | `if ! pip-audit; then echo "::warning::..."; fi`, `tool` + warning fallback, or `tool --exit-code 0` / `--exit-zero` | bare `tool` (default exit-on-findings) OR `tool --strict`; for legitimately unfixable findings, allowlist the specific finding with an inline-comment tracking issue + planned review date. NEVER use double-pipe true, `continue-on-error: true`, or `::warning::` to wrap the tool's exit. |

#### Bucket F — worked example

```yaml
# WRONG — Bucket F: advisory wrapper hides real findings
- run: |
    if ! pip-audit; then
        echo "::warning::pip-audit found vulnerabilities"
    fi

# WRONG — Bucket F: tool-level opt-out flag
- run: gitleaks detect --source . --exit-code 0    # the --exit-code 0 IS the suppression
- run: trivy fs --exit-code 0 .                     # same
- run: bandit --exit-zero                           # same

# RIGHT — fail-fast, real findings block the PR
- run: pip-audit                                    # default: exit 1 on findings
- run: gitleaks detect --source .
- run: trivy fs --exit-code 1 .

# RIGHT — when a finding genuinely can't be fixed in this PR:
- run: |
    # Baseline runner-image CVEs allowlisted per issue #N (review YYYY-MM-DD).
    # Each --ignore-vuln below corresponds to a finding in #N; revisit after
    # ubuntu-latest base image refreshes.
    pip-audit \
      --ignore-vuln GHSA-XXXX-XXXX-XXXX \
      --ignore-vuln GHSA-YYYY-YYYY-YYYY
```

### 4. Operational lessons from the 2026-05-10/2026-05-11 ecosystem sweep

**The first CI run after removing a suppression will fail. That is success — not regression.**

Confirmed cases:

- **HomericIntelligence/ProjectNestor#75**: removing `clang-tidy ... \|\| true` exposed a GCC↔clang cross-tooling issue — GCC-generated `compile_commands.json` contains `-Wduplicated-branches` and other GCC-only `-W` flags that clang-tidy errors on as `clang-diagnostic-unknown-warning-option`. Fix: `--extra-arg-before=-Wno-unknown-warning-option`.
- **HomericIntelligence/Myrmidons#712**: flipping `pip-audit` to fail-fast surfaced **37 baseline-runner-image CVEs** across 15 packages (pip, setuptools, jinja2, twisted, urllib3, cryptography, requests, etc.) that had accumulated silently. Allowlisted via `--ignore-vuln` with tracking issue #713 (review 2026-08-08).
- **HomericIntelligence/AchaeanFleet#656**: `pip-audit --require aider-chat \|\| echo "::warning::..."` had been a complete no-op for weeks — argparse silently ambiguated `--require` to `--requirement` (file path mode), so pip-audit was exiting immediately with no audit. Removing the wrapper revealed the broken invocation AND **57 CVEs** in aider-chat's transitive deps once the flag was fixed. Allowlisted with issue #655.
- **HomericIntelligence/ProjectOdyssey#5387**: flipping `mojo-format` from advisory to fail-fast revealed **37 test files** needed reformatting (missing blank line between imports and first function) — the advisory wrapper had been silently hiding these. Fix: ran `mojo format` inside dev container, committed the regen.
- **HomericIntelligence/ProjectCharybdis#221**: removing `gitleaks detect ... \|\| true` revealed a self-inflicted false positive — the script extracted the gitleaks tarball *into the workspace*, and the tarball's README contains a sample sidekiq secret (`cafebabe:deadbeef`) that gitleaks then "found" in the repo. Fix: extract to `mktemp -d`.
- **HomericIntelligence/ProjectCharybdis#221** (second case): removing `conan audit . \|\| true` revealed the step had been broken since added — `conan audit` requires a subcommand (`scan`/`list`/`provider`), so the call was failing silently. Removed the redundant step; Trivy already scans `conan.lock` offline.

Diagnose the failure, **fix the root cause**. Never re-introduce the suppression as a "temporary" workaround.

**Update meta-tests that pin to the literal suppression syntax BEFORE running the sweep.**

Some test suites have regression-guard tests that assert on the *exact string* of a known suppression — e.g.:

```python
def test_npm_audit_is_non_blocking():
    assert "continue-on-error: true" in step_text
```

When the sweep replaces `continue-on-error: true` with a different form preserving the same property (in-script `AUDIT_EXIT=$?` capture, or now-also-forbidden `if !` + `::warning::` wrapper), these tests fail even though the *property* is preserved.

**Fix the meta-test before the sweep, not after.** Broaden the assertion from syntax to property. Confirmed cases:

- **HomericIntelligence/ProjectScylla#1968**: `tests/unit/ci/test_npm_audit_step.py::test_npm_audit_is_non_blocking` was pinned to `continue-on-error: true`. Broadened to accept either `continue-on-error: true` OR `\|\| AUDIT_EXIT=$?` + `AUDIT_EXIT:-0`.
- **HomericIntelligence/ProjectOdyssey#5385**: `tests/smoke/test_pre_commit_workflow_properties.py` and `.github/workflows/workflow-smoke-test.yml` both pinned to literal `continue-on-error: true` for the mojo-format step. Broadened to assert "the step is non-blocking" via property check.

To find these before refactoring:

```bash
grep -rn "continue-on-error\|or-true\|::warning::" tests/ \
  --include="*.py" --include="*.sh" --include="*.bash"
```

With the v2.0.0 Bucket F clarification, ALL such meta-tests should assert the underlying tool runs fail-fast (rather than asserting any suppression syntax is present).

**Lint guards must self-exempt.**

A pygrep hook or CI grep step that catches a pattern *will catch itself* if the hook's `entry:` literal, error message, or YAML metadata contains the pattern.

Symptoms:
- CI fails on a fresh PR with an error pointing at the hook's own `_required.yml` line.
- Pre-commit fires on the hook's own description.

Two complementary fixes (use both):

1. **Pre-commit hook**: add an `exclude:` regex to the hook stanza pointing at the workflow file containing the matching CI grep step:
   ```yaml
   - id: forbid-advisory-warnings
     ...
     files: ^\.github/workflows/.*\.ya?ml$
     exclude: ^\.github/workflows/_required\.yml$
   ```
2. **CI grep step**: build a `scan_files` array in shell that explicitly skips the workflow file containing the rule and any runbook that documents the pattern:
   ```bash
   declare -a scan_files=()
   for f in "${files[@]}"; do
     case "$f" in
       .github/workflows/_required.yml) continue ;;
       docs/runbooks/no-silent-failures.md) continue ;;
     esac
     scan_files+=("$f")
   done
   ```

The pre-commit `exclude:` only skips the file from the hook's per-file invocation; it doesn't help the CI step. Conversely, the CI shell skip doesn't help the local pre-commit run. Use both.

### Quick Reference

```bash
# Find all violations in current repo (matches the same regex as the hook):
grep -rnP '^(?!\s*#).*\|\|\s*true(\s*$|\s*[#);&|])' \
  --include="*.sh" --include="*.bash" --include="*.yml" --include="*.yaml" \
  --include="*.hcl" --include="Dockerfile*" --include="justfile" --include="Justfile" \
  . 2>/dev/null | grep -v "/\.git/"

# Verify the hook is wired up:
pre-commit run --all-files
```

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---|---|---|---|
| 1 | Initial regex `\|\|\s*true(\s*$\|\s+#)` only matched EOL and trailing `#` | Missed `$(cmd \|\| true)`, `cmd \|\| true; next`, `cmd \|\| true && next` — Argus refactor agent (HomericIntelligence/ProjectArgus#500) flagged 7 pre-existing instances in same-repo helper scripts that the narrow regex couldn't see | Widen to `^(?!\s*#).*\|\|\s*true(\s*$\|\s*[#);&\|])` and exempt comment lines via negative-lookahead |
| 2 | Tried `\|\|\s*true\b` (any word-boundary) | False-positives on documentation comments quoting the idiom inside backticks | Need explicit control-flow boundary characters `[#);&\|]`, plus the comment-line exemption |
| 3 | Used `grep -nE` (ERE) in the CI job | ERE doesn't support negative-lookbehind/lookahead | Switch CI grep to `grep -nP` (PCRE); standard GNU grep on ubuntu-latest runners supports PCRE |
| 4 | Considered allowlist via `# noqa: silent-fail` comment | Per user directive "I don't ever want workarounds like this added", no escape hatch should exist | Documented allowlist syntax in runbook as theoretical-only; hook has no syntax for it |
| 5 | Test-helper `\|\| true` previously labeled "intentional" in Myrmidons CLAUDE.md | User directive rejects "intentional suppression" as a valid label | Refactor to captured-rc pattern: `_rc=0; cmd \|\| _rc=$?; : $((_rc))` — preserves "don't assert on rc" semantics while making the value observable for debugging |
| 6 | Inline `entry:` script in `.pre-commit-config.yaml` containing `\|\| true` | Inline shell can't be cleanly refactored without escaping nightmares | Extract to standalone `scripts/check-*.sh` so `set +e`/`awk` patterns can be applied (used in ProjectOdyssey PR #5385) |
| 7 (v2.0.0) | Refactored `continue-on-error: true` to `if ! cmd; then echo "::warning::..."; fi` per the v1.0.0 documented Bucket E pattern | Functionally identical to `continue-on-error: true` — the CI step still passes when the tool finds a real issue. Found 14 instances across 7 repos after the sweep. | v2.0.0 adds Bucket F: the `::warning::` advisory wrapper is also forbidden. Tools must be fail-fast; legitimate non-blocking annotations use plain `echo "WARN:"` to stdout. |
| 8 (v2.0.0) | Used tool-level opt-out flags (`gitleaks --exit-code 0`, `trivy --exit-code 0`, `bandit --exit-zero`, `pip-audit` with no flags but inside an `if !` wrapper) | These are the same suppression spelled at the tool layer. The CI step passes despite real findings. | Treat tool-level exit-suppression flags as equivalent to `continue-on-error: true`. The runbook explicitly lists `--exit-code 0`, `--exit-zero`, `--no-fail` as forbidden. |
| 9 (v2.0.0) | Allowed advisory `::warning::` for "external service unreachable" (e.g., schemastore.org outage on `check-jsonschema` schema fetch) | Network-bound fallback isn't actually needed — `check-jsonschema --builtin-schema vendor.github-workflows` is network-free and equally correct. Removed the outage scenario entirely. | Prefer network-free alternatives over advisory wrappers. The `--builtin-schema` flag bundles the GitHub Actions schema offline; no curl or outage handling required. |
| 10 (v2.0.0) | Added a new pygrep hook for `::warning::` but didn't exempt the workflow file containing the matching CI grep step | The hook fired on its own definition (`name:`, `entry:`, error message strings all contain `::warning::` literally). Lint check failed on a fresh PR. | Self-exempt every lint guard via BOTH the pre-commit `exclude:` regex AND the CI step's `scan_files` array. |
| 11 (v2.0.0) | A pip-audit step in a CI workflow had been a complete no-op for weeks because argparse silently ambiguated `--require aider-chat` to `--requirement` (file path mode) — file `aider-chat` didn't exist, pip-audit exited 2, wrapper swallowed it | The `\|\| echo "::warning::..."` wrapper made the broken step look advisory rather than broken. No audit had actually run. | Once the wrapper is removed, real findings (or in this case, the broken invocation) become visible immediately. Always check the actual invocation produces audit output after flipping to fail-fast. |

## Results & Parameters

### Runbook structure

Each repo carries a copy of `docs/runbooks/no-silent-failures.md` (or
equivalent path) that documents the rule, lists the buckets, and shows
the canonical fix for each. The runbook is exempted from the scanner so
it can quote the idiom verbatim.

### Ecosystem rollout pattern

One PR per repo, dispatched in parallel via a Myrmidon swarm. Each agent:

1. Adds the pre-commit hook to `.pre-commit-config.yaml`
2. Adds the matching CI job to `.github/workflows/_required.yml`
   (or the repo's equivalent required workflow)
3. Refactors every existing `|| true` and `continue-on-error: true`
   instance per the bucket classification
4. Opens a PR with auto-merge enabled

### PRs

| Repo | PR | Refactors |
|---|---|---|
| HomericIntelligence/Odysseus | #280 (merged) | 40 + lint guard |
| HomericIntelligence/Odysseus | #281 (auto-merge queued) | Regex widening follow-up |
| HomericIntelligence/ProjectProteus | #137 (merged) | 0 + 2 continue-on-error + lint guard |
| HomericIntelligence/ProjectAgamemnon | #367 | 5 |
| HomericIntelligence/ProjectNestor | #75 | 2 + 2 continue-on-error |
| HomericIntelligence/AchaeanFleet | #654 (merged) | 21 |
| HomericIntelligence/ProjectArgus | #500 | 3 + 1 continue-on-error (FOUND THE REGEX GAP) |
| HomericIntelligence/ProjectHermes | #613 (merged) | 1 + lint guard |
| HomericIntelligence/Myrmidons | #711 | 22 |
| HomericIntelligence/ProjectKeystone | #549 | 27 + 10 continue-on-error |
| HomericIntelligence/ProjectTelemachy | #239 (merged) | 2 + 2 continue-on-error |
| HomericIntelligence/ProjectOdyssey | #5385 | 41 + 4 continue-on-error |
| HomericIntelligence/ProjectScylla | #1968 | 32 + 3 continue-on-error |
| HomericIntelligence/ProjectHephaestus | #403 | 13 + 1 continue-on-error |
| HomericIntelligence/ProjectMnemosyne | #1652 (merged) | 1 + 1 continue-on-error |
| HomericIntelligence/ProjectCharybdis | #221 | 4 |

### Phase 2 — Bucket F sweep (2026-05-11)

After v2.0.0 added Bucket F, a follow-up sweep refactored every `if ! cmd; then echo "::warning::..."; fi` and tool-level exit-suppression flag across the ecosystem.

| Repo | PR | Sites refactored | Notes |
|---|---|---|---|
| HomericIntelligence/Odysseus | #282 (merged) | 1 (gitleaks) + lint rule + runbook Bucket F | Meta-repo policy + guard |
| HomericIntelligence/ProjectNestor | #76 (open) | 2 (schema-fetch, pixi.lock fallback) | Required rebase after #75 merged |
| HomericIntelligence/AchaeanFleet | #656 (merged) | 3 (pip-audit + compose-exec + shell-test coverage) | 57 CVEs allowlisted, issue #655 |
| HomericIntelligence/ProjectHephaestus | #405 (merged) | 2 (schema-fetch, pixi.lock info) | Built-in schema, no network fallback |
| HomericIntelligence/Myrmidons | #712 (open) | 2 (pip-audit + apply.sh wrapper) | 37 baseline-runner CVEs, issue #713 |
| HomericIntelligence/ProjectKeystone | #550 (open) | 2 (pip-audit + benchmark) | Real fix on benchmark step |
| HomericIntelligence/ProjectOdyssey | #5387 (merged) | 9 (pip install ×2, pip-audit, mojo-format, semgrep ×2, pixi.lock, podman cp) | 13 CVEs allowlisted, issue #5386; 37 mojo-format files regen'd; meta-tests updated |

## Verified On

| Project | Context | Details |
|---|---|---|
| Odysseus meta-repo | 2026-05-10 ecosystem-wide silent-failure removal | See HomericIntelligence/Odysseus#280, #281 |
| All 14 HomericIntelligence submodules | Same date — Myrmidon swarm dispatched 14 parallel agents | One PR per repo, all `--squash` auto-merge |

## Key Takeaway

The combined pre-commit + CI guard is the right structural fix for a
recurring anti-pattern: pre-commit catches the developer locally,
CI catches anyone who skipped hooks, and the matching regex on both sides
guarantees there's no drift. When the regex needs to widen (Attempt 1
above), a single follow-up PR widens both copies simultaneously — the
runbook quotes the regex so anyone touching it sees both halves at once.
