---
name: codeql-exclude-vendored-deps-false-criticals
description: "GitHub CodeQL (and Trivy) analyze the vendored third-party dependency tree that CMake FetchContent / Conan fetch under build/**/_deps/, so upstream findings (e.g. cpp/use-after-free critical, cpp/world-writable-file-creation high) get reported AGAINST your repo — creating false urgency and burying real first-party alerts. Teaches how to detect vendored alerts by location path and how to exclude the build tree via a codeql-config.yml paths-ignore wired into every codeql-action/init step. Use when: (1) CodeQL/Trivy reports a critical/high in C++ code you did not write, (2) an alert path contains build/**/_deps/ or *-src, (3) triage is swamped by upstream nats.c/cista findings, (4) you need to stop scanning vendored deps without silencing first-party findings."
category: ci-cd
date: 2026-07-16
version: "1.0.0"
verification: verified-local
tags: []
---

# CodeQL — Exclude Vendored `_deps/` To Kill False Criticals

## Overview

\| Field \| Value \|
\|-------\|-------\|
\| **Date** \| 2026-07-16 \|
\| **Objective** \| Stop GitHub CodeQL (and Trivy) from reporting upstream vendored-dependency findings against first-party C++ repos, where they surface as false `critical`/`high` alerts and bury real findings \|
\| **Outcome** \| `.github/codeql/codeql-config.yml` with `paths-ignore: build/**` + `**/_deps/**` wired into every `codeql-action/init` step across Keystone, Nestor, Agamemnon \|
\| **Verification** \| verified-local — fix applied and PRs opened with auto-merge armed (Keystone#614, Nestor#132, Agamemnon#455); the CI gates and the post-merge CodeQL re-scan have NOT yet been observed green, so this is not verified-ci \|

## When to Use

Use this skill when a C++ (or mixed C++/Python) repo builds its dependencies with
CMake **FetchContent** or **Conan**, and GitHub code scanning reports alerts that
point at third-party source rather than your own code. Concrete triggers:

- A CodeQL alert with severity **critical** (`cpp/use-after-free`) or **high**
  (`cpp/world-writable-file-creation`) that you cannot trace to first-party code.
- Any alert whose `most_recent_instance.location.path` contains `build/**/_deps/`
  or a `*-src` directory (e.g. `nats_c-src`, `natsc-src`, `cista-src`).
- Code-scanning triage is dominated by upstream findings (measured: Keystone 115
  of 313 alerts vendored = 37%, Agamemnon 32 of 36 = 89%, Nestor 34 of 46 = 74%).
- You want to exclude the vendored build tree **without** suppressing genuine
  first-party findings.

## Verified Workflow

The vendored dependency code lives in the build tree at analysis time. CMake
FetchContent / Conan fetch it under `build/**/_deps/` (Conan output dirs are
`build/release` / `build/debug`). CodeQL analyzes whatever source is present, so
those upstream findings are attributed to **your** repo. The fix is to exclude
the build tree from analysis and wire that config into every `init` step.

### Step 1 — Confirm the alert is vendored, not first-party

Never trust the severity at face value. Split open alerts by location path first:

```bash
gh api --paginate "repos/<owner>/<repo>/code-scanning/alerts?state=open&per_page=100" \
  | jq -s 'add' > alerts.json

# how many alerts are vendored (in the build/_deps tree)?
jq '[.[] | select(.most_recent_instance.location.path | test("build/.*/_deps/"))] | length' alerts.json

# the scary "critical" ones are usually upstream:
jq -r '.[] | select(.rule.id=="cpp/use-after-free") | .most_recent_instance.location.path' alerts.json
# -> build/release/_deps/nats_c-src/src/jsm.c   == upstream nats.c, NOT your bug
```

### Step 2 — Add a CodeQL config that ignores the build tree

Create `.github/codeql/codeql-config.yml`:

```yaml
name: "Repo CodeQL config"
paths-ignore:
  - build/**
  - "**/_deps/**"
```

`build/**` also covers Conan output dirs (`build/release`, `build/debug`);
`**/_deps/**` covers FetchContent trees nested anywhere.

### Step 3 — Reference the config from EVERY `init` step

A repo can have multiple `codeql-action/init` steps — one per language. Add
`config-file:` to all of them:

```yaml
- uses: github/codeql-action/init@<pinned-sha>
  with:
    languages: cpp   # (or c-cpp / python)
    queries: security-and-quality
    config-file: ./.github/codeql/codeql-config.yml
```

The CodeQL workflow file location varies per repo — grep to find it:

```bash
grep -rl "codeql-action/init" .github/workflows/
# Keystone -> _required.yml (separate c-cpp AND python inits)
# Nestor   -> codeql.yml
# Agamemnon-> sanitizers.yml
```

### Quick Reference

```bash
# 1. pull all open alerts
gh api --paginate "repos/<owner>/<repo>/code-scanning/alerts?state=open&per_page=100" \
  | jq -s 'add' > alerts.json
# 2. count vendored alerts
jq '[.[] | select(.most_recent_instance.location.path | test("build/.*/_deps/"))] | length' alerts.json
# 3. list paths of the "critical" use-after-free (usually upstream)
jq -r '.[] | select(.rule.id=="cpp/use-after-free") | .most_recent_instance.location.path' alerts.json
# 4. find every workflow with a CodeQL init to wire config-file into
grep -rl "codeql-action/init" .github/workflows/
```

```yaml
# .github/codeql/codeql-config.yml
name: "Repo CodeQL config"
paths-ignore:
  - build/**
  - "**/_deps/**"
```

**Key wiring notes:**

1. A repo may have MULTIPLE `init` steps (one per language); add `config-file`
   to ALL of them. Keystone had separate `c-cpp` and `python` inits in `_required.yml`.
2. Workflow file location varies (`_required.yml`, `codeql.yml`, `sanitizers.yml`)
   — grep for `codeql-action/init` to locate them.
3. `build/**` also covers Conan output dirs (`build/release` / `build/debug`).
4. Effect is only observable on the NEXT CodeQL run after merge — `paths-ignore`
   filters at analysis time, so existing alerts do not disappear until re-scan.

## Failed Attempts

\| Attempt \| What Was Tried \| Why It Failed \| Lesson Learned \|
\|---------\|----------------\|---------------\|----------------\|
\| 1 \| Read the alert severity at face value — treat `cpp/use-after-free (critical)` as a first-party bug \| The path was `build/**/_deps/nats_c-src/...` — upstream nats.c, not our code \| ALWAYS check `.most_recent_instance.location.path` before believing a 'critical' \|
\| 2 \| File one GitHub issue per vendored alert \| Would create dozens of issues for upstream code we do not maintain \| Cluster into ONE 'CodeQL scans vendored _deps' config issue per repo instead \|
\| 3 \| Add `config-file` to only the first `init` step \| The second language's analysis still scanned `_deps/` \| Add `config-file` to every `codeql-action/init` in the workflow \|

## Results & Parameters

**The exclusion config** — `.github/codeql/codeql-config.yml`:

```yaml
name: "Repo CodeQL config"
paths-ignore:
  - build/**
  - "**/_deps/**"
```

**Detection one-liners:**

```bash
gh api --paginate "repos/<owner>/<repo>/code-scanning/alerts?state=open&per_page=100" \
  | jq -s 'add' > alerts.json
jq '[.[] | select(.most_recent_instance.location.path | test("build/.*/_deps/"))] | length' alerts.json
jq -r '.[] | select(.rule.id=="cpp/use-after-free") | .most_recent_instance.location.path' alerts.json
```

**Measured vendored ratios (real repos, 2026-07-16):**

\| Repo \| Vendored alerts \| Total alerts \| Ratio \|
\|------\|-----------------\|--------------\|-------\|
\| Keystone \| 115 \| 313 \| 37% \|
\| Agamemnon \| 32 \| 36 \| 89% \|
\| Nestor \| 34 \| 46 \| 74% \|

**Applied via PRs:** Keystone#614, Nestor#132, Agamemnon#455. Charybdis already
tracked the same idea as its #127.

**Markdown authoring caveat (this skill's own file):** escape any literal `|`
inside a table cell as `\|` (markdownlint MD056), and run
`npx --yes markdownlint-cli2 --config .markdownlint.yaml skills/codeql-exclude-vendored-deps-false-criticals.md`
locally before commit.
