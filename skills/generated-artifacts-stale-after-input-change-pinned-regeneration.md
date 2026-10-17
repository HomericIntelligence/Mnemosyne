---
name: generated-artifacts-stale-after-input-change-pinned-regeneration
license: BSD-3-Clause
description: "Regenerate byte-checked generated artifacts with CI-pinned tool versions after any input-content change, renames included. Use when artifact freshness gates fail after a green-test merge, or when freshness checks fail only on a dev host."
category: ci-cd
date: 2026-10-16
version: "1.0.0"
user-invocable: false
verification: verified-local
tags:
  - generated-artifacts
  - freshness-gate
  - byte-exact-check
  - input-digest
  - rename
  - version-skew
  - pinned-dependencies
  - regeneration
  - ci-repair
  - matplotlib
---

# Checked-in Generated Artifacts Go Stale After Input Changes: Regenerate With CI-Pinned Tools

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-16 |
| **Objective** | Keep byte-exact CI freshness gates green after a change alters any input of checked-in generated artifacts. A repository-wide identifier rename changed the content of a hashed index input, so every artifact that embeds an input digest went stale while the full test suite stayed green. |
| **Outcome** | Successful: all freshness steps were enumerated from the workflow up front, every drifted tree was regenerated in a dependency-pinned environment (41 files, digest-only diff), and all seven CI check steps exited 0 locally in the pinned environment. |
| **Verification** | verified-local — all CI check invocations re-run and green in the pinned environment; the repair PR gate was still pending at capture time. |

## When to Use

- A repository checks in generated artifacts (audit summaries, coverage files, rendered figures, ledgers, lockfiles) and CI re-renders them and compares the bytes as a required step (a `--check` or freshness gate).
- Any merged change alters the content of an input those artifacts fingerprint. A pure identifier rename inside a hashed input file is a content change: it shifts the input digest and fans out into every artifact that embeds input bindings, with zero data or metric changes.
- CI fails at an artifact freshness step after a merge whose tests were all green. Test suites usually do not exercise artifact gates, so a green test run proves nothing about artifact freshness.
- A local freshness check fails on the dev host but the tree looks correct. Suspect tool version skew before you believe drift: renderer output bytes depend on installed library versions.
- A report generator emits one file per CLI invocation from an expensive deterministic build, so a full regeneration loops for hours.
- You are about to "fix" embedded digests or hashes by hand. Never hand-edit generator-owned bytes.

## Verified Workflow

Byte-exact checks make artifact freshness a function of two things: input content and tool
versions. Control both.

### Quick Reference

```bash
# 1. Enumerate EVERY freshness step in the workflow before fixing any of them.
grep -nE '\-\-check' .github/workflows/*.yml

# 2. Build a pinned regeneration environment from the requirements CI installs.
python3 -m venv /tmp/regen-venv
/tmp/regen-venv/bin/pip install -r <requirements-file-ci-installs>
/tmp/regen-venv/bin/python -c "import <renderer>; print(<renderer>.__version__)"  # == CI pin

# 3. Per owned tree: regenerate (no --check), then re-run the EXACT CI command.
PYTHONPATH=. /tmp/regen-venv/bin/python scripts/<generator> <ci-args>
PYTHONPATH=. /tmp/regen-venv/bin/python scripts/<generator> <ci-args> --check   # exit 0

# 4. Audit the diff: only digest/string propagation is allowed, never metric changes.
git diff --stat
git diff | grep -oE '[0-9a-f]{12}' | sort -u   # the input-digest substitution
```

### Suggested Approach

1. **Enumerate the complete freshness surface first.** CI evaluates the workflow in order and
   stops at the first stale step, so the failure log shows only one stale tree at a time. Read
   the workflow file and list every step that re-renders or re-checks checked-in artifacts. In
   the capture case the first failing step hid several more stale trees behind it.

2. **Regenerate with CI-pinned tool versions.** Renderer output bytes are a function of the
   installed libraries: a newer plotting library renders PNG or SVG bytes that differ from the
   checked-in ones even for identical inputs. Build a throwaway virtual environment from the
   same pinned requirements the CI install step uses, and confirm each renderer version equals
   the CI pin before regenerating. Text formats (JSON, CSV, Markdown dumps) are usually
   version-independent; rendered formats (PNG, SVG) are not.

3. **Do not trust dev-host check results in either direction.** A failed freshness check under
   newer local tools can be pure skew — false staleness — and a passed check under non-pinned
   tools proves nothing about CI. Diagnosis rule: run the check in the pinned environment; a
   failure that disappears there was skew, and a tree that regenerates byte-identical there was
   never stale. This A/B prevented three spurious "repairs" in the capture case.

4. **Repair every stale tree in one pass.** For each owned tree, run the documented
   regeneration form (the same command without `--check`) and immediately re-run the exact CI
   check invocation to exit 0. Then audit the diff: content propagated from the input change
   (digest strings, renamed paths) is expected; any metric, row, or threshold change is not.

5. **Use the single-pass builder behind `--check` for multi-stream reports.** When the CLI
   renders one file per invocation against an expensive deterministic build, the `--check` path
   typically proves a single-process alternative exists: it regenerates every stream in memory
   from one load. Drive that builder API once (load inputs once, render and write each stream)
   instead of looping the CLI. In the capture case this avoided repeating an expensive input
   load dozens of times; independent invocations can also be parallelized when no shared state
   exists.

6. **Deliver as a scoped follow-up PR.** Commit only the regenerated artifact trees, with the
   root cause (which input changed and how its digest propagates) in the commit and PR body.
   Do not include unrelated work.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Trusted a green test run as gate-complete | Merged a rename PR after the full test suite passed on its head | Master CI failed at the first artifact freshness step after the merge; tests never exercised the byte-exact gates | A green test suite says nothing about artifact freshness; enumerate and run the workflow freshness steps before merging input-touching changes |
| Repaired only the step CI reported | Regenerated the one tree the failing step named | That step went green and the next freshness step failed on different trees | CI stops at the first stale step; inventory all freshness steps from the workflow and repair them in one pass |
| Regenerated with unpinned local tools | Ran the checks and renderers under a newer local plotting library than the CI pin | Unrelated checks failed locally on trees that were never stale, and bytes rendered under the wrong version would have failed CI after commit | Regenerate and verify in an environment pinned from the CI install step; treat dev-host-only check failures as suspected skew and A/B before editing |
| Looped the report CLI once per stream | Ran the audit renderer 45 times, once per report stream | Every invocation rebuilt the same expensive intermediate result (several minutes each), serializing into hours | Drive the single-pass builder the `--check` path uses: one load, render all streams, verify with the stock check |

## Results & Parameters

### Configuration

```yaml
inventory:  # before fixing anything, list every freshness step
  command: grep -nE '\-\-check' .github/workflows/*.yml
pinned_regen_env:
  source: the requirements files the CI install step uses
  rule: renderer versions must equal the CI pins (renderer PNG/SVG bytes are version-dependent)
regeneration:
  per_tree:
    - run the documented generator without --check, using the CI argument line
    - re-run the exact CI check invocation; require exit 0
  multi_stream_reports:
    rule: never loop the CLI once per stream against an expensive deterministic build
    action: drive the single-pass builder behind --check (one load, all streams), or parallelize independent runs
diff_rule: only digest or renamed-string propagation allowed; metric values must be unchanged
delivery: scoped follow-up PR containing only the regenerated artifact trees
```

### Expected Output

- Every workflow freshness step exits 0 in the pinned environment.
- The diff is limited to content propagated from the input change (digest strings, renamed
  paths); metrics, rows, and thresholds are unchanged.
- No test files change.
- The commit and PR body name the input change and the propagation class.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Python benchmark-telemetry repository with checked-in audit reports, coverage trees, and rendered figure assets | A repository-wide identifier rename (thousands of substitutions) merged green; master CI then failed at the model-data-audit freshness step | The rename changed a hashed index input; its new digest invalidated every artifact embedding input bindings. Enumerated seven freshness steps from the workflow; regenerated the audit summary and all coverage trees in an environment pinned to the CI renderer stack (41 files, a single digest substitution across the diff); all seven steps exit 0 locally. See [generated-artifacts-stale-after-input-change-pinned-regeneration.notes.md](generated-artifacts-stale-after-input-change-pinned-regeneration.notes.md) for the propagation mechanics and timings. |

## References

- [uv-lock-stale-after-constraint-regenerate-verify-marker](uv-lock-stale-after-constraint-regenerate-verify-marker.md) — the single-lockfile case: regenerate resolver-owned output after a declared-metadata change, never hand-edit
- [ci-cd-pixi-lock-version-skew-regeneration](ci-cd-pixi-lock-version-skew-regeneration.md) — regenerate with the CI-pinned binary because the writer version determines output format
- [rename-propagation-unexercised-paths-break-later](rename-propagation-unexercised-paths-break-later.md) — the rename inverse: unexercised consumers break later (paths), while here correct consumers stay green and the artifact fingerprints break (content)
- [logical-model-family-rename-with-storage-exceptions](logical-model-family-rename-with-storage-exceptions.md) — the rename discipline that this freshness repair complements
- [pr-ci-failure-triage-preexisting-vs-introduced](pr-ci-failure-triage-preexisting-vs-introduced.md) — classification discipline for red checks before fixing
