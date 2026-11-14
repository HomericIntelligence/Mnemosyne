---
name: ci-transient-flake-and-environment-failures
license: BSD-3-Clause
description: "Use when: (1) a CI job fails non-deterministically and re-running resolves it, (2) a provider-side 5xx makes a supported rerun unavailable, (3) CI passes locally but fails in GitHub Actions, (4) a CI health check wrongly requires developer-local resources, (5) dependency installation hangs before tests start, or a stuck run ignores a normal cancel, (6) a test that asserts rendered CLI help flips between green and red on the same commit because it inherits the terminal width, or (7) a test fixture reads a real host path or host record as input, so the result changes between hosts, between runs, or when unrelated work changes that path."
category: ci-cd
date: 2026-06-17
version: "1.6.0"
user-invocable: false
verification: verified-ci
tags:
  - ci
  - github-actions
  - transient
  - flake
  - trivy
  - lychee
  - link-check
  - lycheeignore
  - reproduction
  - podman
  - pixi
  - uid
  - tty
  - doctor
  - git-hooks
  - ci-guard
  - environment-detection
  - playwright
  - pip-install
  - dependency-install
  - runner-hang
  - gh-run-rerun
  - terminal-width
  - columns
  - cli-help
  - rich
  - typer
history-source: "https://github.com/HomericIntelligence/Mnemosyne/blob/1956c91d76867bc2e484eaf573a57051855186f8/skills/ci-transient-flake-and-environment-failures.history"
history-cleanup-date: "2026-09-20"
---

# CI Transient Flake and Environment Failures

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-06-17 |
| **Objective** | Diagnose and resolve CI failures that are transient network flakes, environment-only, developer-local health checks, or dependency-install hangs before tests start - without reaching for banned suppressions. |
| **Outcome** | Verified across ProjectAgamemnon (#368), ProjectOdyssey (#5347), ProjectOdyssey local repro, ProjectMyrmidons (#350), and Metrics Service (#897/#904). |
| **Verification** | verified-ci |
| **History** | Previous versions archived in [prior Git source](https://github.com/HomericIntelligence/Mnemosyne/blob/1956c91d76867bc2e484eaf573a57051855186f8/skills/ci-transient-flake-and-environment-failures.history) |

## When to Use

- A GitHub Actions job fails non-deterministically and a fresh run (rerun or new push) resolves it with zero code change. Common signatures:
  - **Trivy install flake**: `aquasecurity/trivy info found version: X.Y.Z` immediately followed by `##[error]Process completed with exit code 1.`, with the prior `pip-audit` (or equivalent) step clean.
  - **Lychee link-check flake**: HTTP 403 on `claude.ai` / `platform.claude.com` / `code.claude.com` (bot-blocking), or `os error 104` (connection reset) on `contributor-covenant.org` and similar community sites.
- Tests pass locally 100% but fail consistently in CI, and you need to replicate the three CI conditions (cold pixi cache + UID mismatch + no-TTY) simultaneously.
- A doctor / health-check / preflight script (`scripts/doctor.sh`, `just doctor`) exits 1 in CI because it validates developer-local resources (`.git/hooks/`, SSH keys, local config) absent on GHA runners.
- A GitHub job API response shows a dependency-install step such as `Install Playwright Chromium for browser smoke tests`, `Install backend coverage dependencies`, `Install backend runtime and test dependencies`, or `Install focused regression dependencies` remains `in_progress` far beyond the latest green baseline while the test step is still pending.
- A job log and the retry endpoint both report a provider-side 5xx, or a provider-managed analysis reports that it cannot be rerun.
- A proposed retry workaround hides a failing required check with `|| true` or `continue-on-error`.
  Preserve the result and diagnose the failure under the repository's actual CI policy.
- The same commit fails one node in one run and passes the same node in the next run,
  and the node asserts on rendered CLI help or any other text a renderer wraps to the
  terminal width.
- The same head passes on a developer machine and fails on a runner, and a rerun
  fails again with the same message. A test fixture likely reads a path or a record
  that only that host has, so the input is host state instead of test state. Use
  **C3** below.

## Verified Workflow

### Quick Reference

```bash
# --- Transient flake: retry only through a supported provider operation ---
unset GITHUB_TOKEN GH_TOKEN                       # let gh use runner auth chain
gh run rerun <RUN_ID> --repo "$ORG/$REPO" --failed
# If the provider rejects rerun or returns 5xx: preserve the head SHA, record
# the outage, and wait for provider recovery or a legitimate source update.

# --- Lychee bot-403 / reset: add regex patterns to .lycheeignore ---
cat >> .lycheeignore << 'EOF'
claude\.ai
platform\.claude\.com
code\.claude\.com
contributor-covenant\.org
EOF

# --- Reproduce CI-only failure locally: all 3 conditions at once ---
podman compose down -v                            # cold pixi cache
USER_ID=1001 GROUP_ID=1001 podman compose up -d   # CI runner UID (image build UID is 1000)
USER_ID=1001 GROUP_ID=1001 podman compose exec -T <service> bash -c \
  "cd /workspace && <test command>"               # -T = no TTY

# --- Doctor script: guard developer-local checks in CI ---
if [[ "${CI:-}" == "true" ]]; then
    warn "<check name> skipped in CI" "<reason: dev-local only>"
    return
fi

# --- Dependency-install hang before tests start ---
gh api repos/<user>/<repo>/actions/jobs/<job_id> \
  --jq '{status:.status,steps:[.steps[]|{name,status,started_at,completed_at}]}'

# Compare against a latest green main/PR job before deciding whether to wait.
gh api repos/<user>/<repo>/actions/runs/<main_run_id>/jobs \
  --jq '.jobs[] | select(.name=="tests-frontend") | {status,conclusion,started_at,completed_at,steps}'

# If the install path invokes optional OS package work but the runner already has deps:
npx --no-install playwright install chromium

# If the same install path passed elsewhere and this run is stuck:
gh run cancel <run_id> --repo <owner/repo>
gh run rerun <run_id> --repo <owner/repo>

# If the cancel is accepted but the run stays in_progress, the runner is not answering:
gh api -X POST repos/<user>/<repo>/actions/runs/<run_id>/force-cancel
gh run rerun <run_id> --repo <owner/repo> --failed   # only after status is completed; keeps the passed jobs
```

### Detailed Steps

#### A. Transient Trivy install.sh exit-1

1. **Match the signature exactly.** The trivy install step's log MUST end with the `found version` line (no download bar, no checksum, no tar-extraction error) followed within ~0.4s by the runner error:

   ```text
   ##[group]Run TRIVY_VERSION=0.58.1
   TRIVY_VERSION=0.58.1
   curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh \
     | sh -s -- -b /usr/local/bin "v${TRIVY_VERSION}"
   trivy --version
   shell: /usr/bin/bash -e {0}
   ##[endgroup]
   aquasecurity/trivy info checking GitHub for tag 'v0.58.1'
   aquasecurity/trivy info found version: 0.58.1 for v0.58.1/Linux/64bit
   ##[error]Process completed with exit code 1.
   ```

   If the log includes a progress bar, checksum-mismatch, or extraction error, this is NOT the same flake — investigate normally.
2. **Confirm the prior step passed.** A clean `pip-audit` immediately before rules out a job-wide environment issue.
3. **Rerun the failed jobs.** `gh run rerun <RUN_ID> --failed`. Unset `GITHUB_TOKEN`/`GH_TOKEN` if your shell has a PAT lacking `actions:write`.
4. **Classify a rejected retry separately.** If the retry endpoint returns a provider-side 5xx, retry only a bounded number of times. If the provider explicitly marks the job non-rerunnable, preserve the head SHA and record the outage; do not create an empty commit or otherwise rewrite branch history solely to force another run.
5. **Investigate persistent failures or new evidence.** A small number of supported reruns may
   distinguish a transient failure. Choose the next step from the logs; two reruns are an
   example budget, not proof of a particular cause.
6. **Durable follow-up (separate issue, don't block the PR):** replace curl-pipe-to-sh with the official action, which has retry semantics:

   ```yaml
   - name: Run Trivy
     uses: aquasecurity/trivy-action@v<X>
     with:
       scan-type: fs
       format: sarif
       output: trivy-results.sarif
   ```

#### B. Lychee link-check bot-403 / connection reset

1. **Identify the failing URLs** in the CI log:

   ```text
   [ERROR] https://claude.ai/code — Status 403 (Forbidden)
   [ERROR] https://contributor-covenant.org/... — Connection reset (os error 104)
   ```

2. **Classify each failure**:

   | Failure Type | URL Pattern | Root Cause | Action |
   |-------------|-------------|------------|--------|
   | HTTP 403 | `claude.ai`, `platform.claude.com`, `code.claude.com` | Anthropic URLs return 403 to automated bots (lychee user-agent) | Add to `.lycheeignore` |
   | Connection reset (os error 104) | `contributor-covenant.org` | Intermittent server reset; site valid but unreliable from CI | Add to `.lycheeignore` |

3. **Add regex patterns to `.lycheeignore`** (project root). Patterns are regular expressions, not globs; escape literal dots with `\.`; a pattern matches any URL containing the substring; `#` starts a comment:

   ```text
   # Ignore Claude/Anthropic URLs that return 403 to bots (valid URLs)
   claude\.ai
   platform\.claude\.com
   code\.claude\.com

   # Ignore external sites that intermittently reset connections (os error 104)
   contributor-covenant\.org
   ```

4. **Verify** — push to trigger CI, or run locally:

   ```bash
   lychee --config .lychee.toml "**/*.md" --exclude-path .pixi
   # or: pixi run lychee "**/*.md"
   ```

   `.lycheeignore` is read automatically by lychee — no explicit `.lychee.toml` reference needed.

#### C. Reproduce CI-only test failures locally

1. **Identify the three CI-specific conditions** that differ from local:
   - **Cold pixi cache**: CI creates fresh named volumes every run; locally volumes persist.
   - **UID mismatch**: CI runner typically uses UID 1001; container image is built with UID 1000.
   - **No TTY**: CI uses `podman compose exec -T` (the `-T` flag disables TTY).
2. **Confirm exact values from your CI config:**

   ```bash
   grep -r "USER_ID\|GROUP_ID\|uid\|user:" .github/workflows/
   grep -r "exec -T\|compose exec" .github/workflows/ justfile
   ```

3. **Delete all named volumes** (`podman compose down -v`), **start with CI UID** (`USER_ID=1001 GROUP_ID=1001 podman compose up -d`), then **run the failing test with `-T`**.
4. **If still not reproducing**, add CI env vars (`CI=true GITHUB_ACTIONS=true`) and check runner resource limits / filesystem (overlay vs native).
5. **Read the FULL stack trace**, not just the summary. `execution crashed` is a symptom; the real cause (permission error from UID mismatch, missing cache dir, segfault) is in the trace. `fortify_fail_abort` / `__fortify_fail` points to a buffer overflow or permission violation.

#### C2. Terminal-width-dependent assertion in a CLI help test

A test that asserts an option name appears in rendered CLI help can flip between
green and red on the *same commit*. The renderer wraps its help panel to the
terminal width, and the test runner takes that width from the environment, which
differs between a developer shell and a CI runner.

1. **Prove the flip is environmental before you change code.** Compare two runs
   of the same commit, not two commits:

   ```bash
   # Same SHA, different conclusions on one node = environment, not a regression.
   gh api "repos/<user>/<repo>/actions/runs?branch=<branch>&per_page=10" \
     --jq '[.workflow_runs[]|select(.name=="<workflow>")][0:3][]|"\(.id) \(.head_sha[0:8])"'
   gh api "repos/<user>/<repo>/actions/runs/<run-id>/jobs?per_page=100" \
     --jq '"failed=\([.jobs[]|select(.conclusion=="failure")|.name]|join(" | "))"'
   ```

2. **Reproduce the width locally.** Pin the width the runner would have seen. A
   very small width makes the renderer put one character per line, so a
   contiguous option name never appears:

   ```bash
   COLUMNS=1 python -m pytest tests/<test_file>.py::<test_name> -q   # expected: fail
   COLUMNS=80 python -m pytest tests/<test_file>.py::<test_name> -q  # expected: pass
   ```

3. **Fix the measurement, not the message.** Pin the width the assertion reads,
   in the test itself, so the check is about the option name and not the host:

   ```python
   def test_<name>(<fixture>, monkeypatch):
       # The renderer wraps to the terminal width; a narrow terminal hides the
       # option name, so pin the width this assertion is about.
       monkeypatch.setenv("COLUMNS", "80")
       result = <fixture>.invoke(["<verb>"])
       assert result.exit_code != 0
       assert "--<option>" in result.output
   ```

4. **Confirm the assertion still fails on the defect.** Revert the fix in a
   scratch copy and re-run at `COLUMNS=1`. A test that passes both before and
   after proves nothing about the reported failure.

5. **Do not** widen the renderer, strip ANSI from the output, or assert on the
   command object instead of the rendered text. Those hide a genuine help-output
   regression, which is the behaviour the test exists to protect.

#### C3. Fixture that reads real host state as an input

A fixture can build its subject, then read a path outside the test root. The
result then depends on what that host holds at that moment, so a rerun cannot
fix it. This is a wrong input, not a flake.

1. **Confirm the head first.** A checkout behind the head produces false passes:
   `git rev-parse HEAD` must equal the head that failed.
2. **Print what the fixture writes, instead of reading the helper source:**

   ```python
   path = make_context(...).artifact(...).weights_path   # field under test
   print("input:", path, "inside test root:", path.is_relative_to(tmp_path))
   ```

   A path outside the test root is host state. Do not accept it as input.
3. **Stage the input under the test root**, and assert that precondition in the
   fixture so a drift to a host path fails loudly:

   ```python
   staged = tmp_path / "weights"          # test-owned, mode 0700
   staged.mkdir(mode=0o700)
   write_fixture_record(staged / "manifest.json")
   ctx = replace_artifact(ctx, weights_path=staged)
   ```

4. **Fix the input, not the assertion.** Filtering the unexpected event kind or
   rerunning the job hides the host dependency; the next release run reports a
   different count from the same input.
5. **Prove the fix with the host path absent or unreadable**, then run the node
   again.

> **C2** is the same rule for terminal width: pin the input in the test.

#### D. Doctor/health-check script CI guard

1. **Identify the failing `check_*()` function** referencing developer-local artifacts (`.git/hooks/`, `~/.ssh/`, pre-commit install state).
2. **Understand the CI context.** GitHub Actions sets `CI=true` on all runners. `${CI:-}` safely handles set and unset cases under `set -u`.
3. **Add the guard at the TOP of the check function**, before any file-existence tests:

   ```bash
   check_hooks() {
       section "Check N: Git hooks"

       local hook_src="${REPO_ROOT}/hooks/pre-commit"
       local hook_dst="${REPO_ROOT}/.git/hooks/pre-commit"

       if [[ ! -f "$hook_src" ]]; then
           warn "hooks/pre-commit source not found in repo"
           return
       fi

       # In CI there is no .git/hooks directory; skip this check.
       if [[ "${CI:-}" == "true" ]]; then
           warn "pre-commit hook check skipped in CI" "hooks are installed by developers locally"
           return
       fi

       if [[ ! -f "$hook_dst" ]]; then
           fail "pre-commit hook not installed" "Run: just install-hooks"
       elif [[ ! -x "$hook_dst" ]]; then
           fail "pre-commit hook not executable" "Run: chmod +x .git/hooks/pre-commit"
       else
           pass "pre-commit hook installed and executable"
       fi
   }
   ```

4. **Use `warn` not `pass`** for the skip message so CI logs show the check was intentionally skipped.
5. **Test locally** that the guard doesn't suppress the check in a normal shell, then **verify in CI** the job exits 0.

   Categories of checks needing CI guards: git hooks, SSH infrastructure, local config files, pre-commit install state, GPG signing setup, editor/IDE config.

#### E. Dependency-install step hangs before tests start

1. **Use the job API, not just logs.** In-progress jobs may return unavailable log
   blobs, but `gh api repos/<user>/<repo>/actions/jobs/<job_id>` still reports
   each step's `status`, `started_at`, and `completed_at`. If the test step is
   pending, do not debug the tests yet.

2. **Compare against a recent green baseline.** Pull the same job from the latest
   green main or sibling PR run. A dependency-install step running for 10-15 minutes
   when the baseline is seconds is a runner/install hang, not slow tests.

3. **Simplify optional install work when the command is the variable.** For
   Playwright, `playwright install --with-deps chromium` can enter an apt/system
   dependency path that is not needed when the runner image already has system
   dependencies. Prefer `playwright install chromium` (or `npx --no-install
   playwright install chromium`) only after verifying the browser smoke tests still
   pass in fresh CI.

4. **Cancel and rerun proven transient install hangs.** If identical dependency
   install paths passed on main, sibling jobs, or a subsequent PR attempt, cancel the
   stuck run and rerun it on a fresh runner instead of waiting indefinitely.

5. **Force-cancel when the cancel is ignored.** A hung runner step can accept
   `gh run cancel` and still stay `in_progress`. Poll the run for about a minute. If
   it does not reach `completed`, call the force-cancel endpoint
   (`POST /repos/<user>/<repo>/actions/runs/<run_id>/force-cancel`). A rerun is
   refused while the run is still active. After the run is `completed` with
   conclusion `cancelled`, use `gh run rerun --failed`. It keeps the jobs that
   already passed and reruns only the cancelled and failed ones.

6. **Prevent the next hang with bounded steps.** GitHub waits for the job limit
   (360 minutes by default) when a step has no timeout.
   - Give each package-install step a step `timeout-minutes` (about 10).
   - Run the package commands in a loop of 3 attempts. Put each attempt under
     `timeout` (for example 120 s for an index update and 300 s for an install)
     with `--kill-after` so a process that ignores TERM is still ended. Sleep a
     few seconds between attempts. Print a clear error and exit 1 after the third
     failure. Keep the commands in an `if A && B; then` list so `set -e` does not
     end the loop on the first failed attempt.
   - Give each test job a `timeout-minutes` of about two to three times the
     longest real run, taken from the run history. Do not guess. If a job has no
     full run in the history, leave it and record the gap.
   - Keep the tests that guard the workflow structural: assert that the timeout
     key and the retry loop exist, not their numbers.

7. **Only edit code/tests after reproduction.** If the rerun reaches the test step
   and fails deterministically with logs, treat that as a real code/test failure.
   Until then, classify the problem as pre-test infrastructure.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Add `\|\| true` / `continue-on-error: true` to silence a flake | Suppress the failing Trivy or link-check step | Org-wide `forbid-suppressions` / `forbid-continue-on-error` guards reject the diff at lint time | Suppressions are policy-banned; never reach for them to mask a flake |
| Pin Trivy to a different version (thinking it was yanked) | Changed `0.58.1` → `0.57.x` | The same install.sh exit-1 reproduces on a fresh run; reverting then succeeds on rerun | The curl-pipe-to-sh transport is the variable, not the version. Don't churn version numbers. |
| Read `install.sh` source to find the failure path | Source-dived the upstream script | It writes nothing to stderr before exit 1; no log evidence to investigate | Without log evidence, source-diving is speculative — rerun first, investigate only if reruns reproduce |
| `--exclude-all-private` lychee flag | Tried excluding private/localhost URLs | Only skips private IP ranges and localhost, not bot-blocked external URLs | Use targeted `.lycheeignore` regex for external 403s |
| `accept = [403]` in `.lychee.toml` | Globally accept 403 status | Too broad — would hide real broken links returning 403 | Prefer `.lycheeignore` for targeted exclusion; reserve `--accept` for codes you globally trust |
| Wait for intermittent resets to clear | Assumed `contributor-covenant.org` resets were transient | Resets consistently enough in CI to block every run | Add unreliable external gates to `.lycheeignore`; don't rely on their availability |
| Declare crash "non-reproducible locally" with warm cache + UID 1000 | 10 parallel agents ran the test locally; all passed | Warm cache + matching UID + TTY don't replicate CI | Never declare "passes locally" without identical conditions; replicate ALL three at once |
| Fix one CI condition at a time | Tried only cold cache, or only UID mismatch | Each condition alone may not trigger the crash; all three together are required | Replicate cold cache + UID mismatch + no-TTY simultaneously |
| Conclude "non-deterministic JIT flakiness" from the summary line | Read only `execution crashed`, not the full trace | The real cause (permission error) was in the stack trace | Always read the complete stack trace before forming a hypothesis |
| Fetch live logs for an in-progress install step | Tried to read logs while the job was still running | GitHub returned unavailable log blobs; the test step had not started | Use the job API step list to identify the stuck in-progress step and pending test steps |
| Debug tests before dependency install completed | Treated the failing check as a test failure | The test command never ran, so editing tests or assertions could not affect the failure | Classify pre-test dependency-install hangs separately from deterministic test failures |
| Keep `playwright install --with-deps chromium` after a long CI hang | Waited on the apt/system dependency path even though the runner baseline installed browsers in seconds | The optional `--with-deps` path was the variable and could hang before browser smoke tests started | If runner system deps are already adequate, install the pinned browser only and verify fresh CI |
| Wait indefinitely on Python dependency install hangs | Assumed enough time would eventually produce logs | The same install path passed on a fresh runner attempt; the stuck attempt consumed CI time without new evidence | After proving a pre-test install hang is transient, cancel and rerun on a fresh runner |
| Cancel a hung run once and wait | Ran `gh run cancel` and waited for the run to end | The runner was not answering, so the run stayed `in_progress` for hours and a rerun was refused | Poll for about a minute, then use the force-cancel endpoint, then `gh run rerun --failed` |
| Rely on the default job timeout for an install step | Left the step and the job without a timeout | A stuck package install held the job for hours and blocked required checks | Add a step timeout, a bounded retry loop, and a job timeout from the run history |
| Create an empty commit when a provider-managed job cannot rerun | Tried to force a new analysis without a source change | It changes implementation-branch history without fixing the provider outage, and some provider-managed scans reject reruns entirely | Preserve the SHA; use only supported reruns, then wait for recovery or a legitimate update |
| Filter an unexpected event in the assertion when a fixture reads host state | Kept the host path and ignored the event kind it produced | The next release run failed the same node, because the host record changed again | Fix the input, not the assertion: stage the record under the test root (C3) |

## Results & Parameters

### Trivy flake — resolution commands

```bash
unset GITHUB_TOKEN GH_TOKEN
gh run rerun <RUN_ID> --repo "$ORG/$REPO" --failed
# If rerun is rejected or returns a provider 5xx, preserve the SHA and report
# the outage instead of creating an empty retrigger commit.
```

Signature features: job shell is `bash -e`; the `found version` line is the last informational line; the `##[error]` appears <0.4s later; no trivy/curl/sh error message; the prior dep-scanner step exited 0.

### Lychee — `.lycheeignore` entries

```text
claude\.ai
platform\.claude\.com
code\.claude\.com
contributor-covenant\.org
```

| Pattern | Matches |
|---------|---------|
| `claude\.ai` | Any URL containing `claude.ai` |
| `platform\.claude\.com` | `https://platform.claude.com/...` |
| `contributor-covenant\.org` | Any `contributor-covenant.org` URL |

### CI environment conditions (Podman + pixi)

```bash
USER_ID=1001   # CI runner UID (image build UID is 1000)
GROUP_ID=1001  # CI runner GID
# Named pixi-cache volumes are fresh each run; compose exec uses -T (no TTY)
```

| Condition | Local Default | CI Default | Replicate Locally |
|-----------|--------------|-----------|-------------------|
| Pixi cache | Warm (persistent) | Cold (fresh) | `podman compose down -v` |
| Container UID | 1000 | 1001 | `USER_ID=1001 GROUP_ID=1001 podman compose up -d` |
| TTY | Present | None (`-T`) | `podman compose exec -T` |
| CI env vars | Unset | `CI=true`, `GITHUB_ACTIONS=true` | Add to exec command |

Expected: a previously "non-reproducible" crash reproduces 100% deterministically; the full trace reveals the real root cause.

### Doctor CI guard — environment reference

```bash
CI=true            # set automatically on all GitHub Actions runners
${CI:-}            # empty string if unset (safe under set -u)
if [[ "${CI:-}" == "true" ]]; then ...  # skip developer-local checks
```

`.git/hooks/` is absent on: GitHub Actions runners (all OS), GitLab shallow clones, any `git clone --depth=1` / `actions/checkout`, Docker-copied repos. It IS present after `pre-commit install`, on full clones, or in CI jobs that explicitly run `pre-commit install`.

### Dependency-install hang - Metrics Service facts

| Fact | Detail |
|------|--------|
| Playwright install hang | PR #897 first CI attempt had `Install Playwright Chromium for browser smoke tests` stuck for 15+ minutes while the latest green `master` baseline completed the same job in seconds |
| Durable frontend fix | Replaced `playwright install --with-deps chromium` with `playwright install chromium`; fresh CI installed in about 12 seconds and browser smoke passed |
| Python coverage install hang | Original Dependabot PR #890 had coverage dependency install hang before tests; canceling and rerunning produced a green second attempt |
| Backend dependency install hangs | PR #904 attempt 1 had backend dependency-install jobs stuck before tests; canceling and rerunning produced a green second attempt |
| Ignored cancel | A package install step on a hosted runner stayed stuck for hours; the normal cancel was accepted and ignored. The force-cancel call ended the run, and `gh run rerun --failed` then passed in minutes while the jobs that had already passed stayed green |
| Classification rule | When the stuck step is dependency installation and test steps are pending, do not edit tests until a fresh run reaches the test command and fails deterministically |

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| ProjectAgamemnon | 2026-05-11 — PR #368 final fix-up cycle | Trivy depscan install exit-1 unblocked by a fresh rerun / push; no code change to the install step |
| ProjectOdyssey | 2026-05-03 — PR #5347/#5348 link-check session | `claude.ai` (403) and `contributor-covenant.org` (os error 104) fixed by `.lycheeignore` entries |
| ProjectOdyssey | Reproducing `fortify_fail_abort` crash declared non-reproducible in `jit-fortify-buffer-overflow.md` | Cold cache + UID 1001 + `-T` flag combined triggered the crash 100% deterministically |
| ProjectMyrmidons | PR #350 | `scripts/doctor.sh` Check 4 failed `just doctor --skip-connectivity` in CI; `${CI:-}` guard fixed it |
| Metrics Service | PRs #897/#904, 2026-06-17 | Playwright `--with-deps` install hang resolved by browser-only install; Python dependency-install hangs cleared by cancel/rerun after API step-state polling showed tests had not started |
| Comet | Two consecutive release runs, 2026-10-28 and 2026-10-29, same node | A warns-once render test read an artifact path in the real production data tree. The record there loaded on the author host and raised on the runner, so the node failed with an unexpected extra event (`assert 2 == 1`). A first fix filtered the unexpected event kind in the assertion; the next release run failed the same node again. Local proof: the fixture path resolved outside the test root and its record loaded correctly at that moment. Fix: stage a sealed tree under the test root. |
