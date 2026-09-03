---
name: architecture-self-exclusion-all-scan-entry-points
license: BSD-3-Clause
description: "When a scanning guard excludes its OWN policy/pattern file so it does not flag itself, that self-skip must be applied at EVERY scan entry point (working-tree, tracked, AND staged/index), not just the ones you happened to notice — a self-skip enforced on some code paths but missing on one is a silent trap. It bites the moment the policy file becomes git-TRACKED (e.g. promoting a gitignored local denylist to a committed project-level denylist): the loader reads the newly-added token from the working tree, the staged blob of the policy file IS that token, and the un-guarded staged path flags the file against its own pattern — so `git add`+commit of the pattern fails the very guard the file feeds. With `--no-verify` banned, the central list can never be populated: a self-lock. Use when: (1) planning to make an optional/local denylist/allowlist/secret-scanner into a committed, centrally-enforced control; (2) a guard script has multiple scan modes (`--staged`/`--tracked`/path args) and only some call a shared self-skip; (3) you add a shared `_is_denylist_file`-style predicate and must audit that every finder path calls it; (4) a plan reviewer flags that a self-exclusion covers `scan_paths()` but not the `--staged` index loop; (5) any guard whose enforced data lives in a file the guard itself scans. Fix: centralize the exclusion in ONE predicate and call it from EVERY entry point; add a test that stages the policy file containing its own token and asserts exit 0. PLANNING learning — the staged-path gap and self-lock were verified against repo source by a plan reviewer; the fix was NOT executed end-to-end in CI."
category: architecture
date: 2026-07-17
version: "1.0.0"
user-invocable: false
tags:
  - planning
  - architecture
  - self-exclusion
  - self-flag
  - scan-entry-point
  - denylist
  - allowlist
  - pre-commit-hook
  - staged-index-scan
  - gitignored-to-tracked
  - no-verify-banned
  - dry
  - shared-predicate
  - pii-guard
  - review-caught
---

# Self-Exclusion Must Cover Every Scan Entry Point, Not Just Some

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-07-17 |
| **Objective** | When a scanning guard skips its own policy/pattern file, apply the self-skip at EVERY scan entry point (working-tree, tracked, staged) so promoting the file from gitignored to git-tracked does not make it self-flag and lock out its own population |
| **Outcome** | ProjectHephaestus issue #2179 plan: a reviewer NOGO'd a revision that added a committed `.heph-project-denylist` and centralized the self-skip in `scan_paths()` but LEFT the `--staged` index loop un-guarded; the re-plan added a shared `_is_denylist_file()` predicate called from all three paths plus a `test_staged_scan_skips_project_denylist_file` regression test |
| **Verification** | verified-in-review (the staged-path gap + self-lock were confirmed against `scripts/check_private_denylist.py` source by a plan reviewer; the fix was not run end-to-end in CI) |

## The trap

`scripts/check_private_denylist.py` (ProjectHephaestus) is a pre-commit guard that
rejects text matching any fixed string in a denylist file. Originally the denylist
lived only in an untracked, gitignored `.heph-private-denylist` — so the guard could
never scan the denylist file itself as a violation (git never sees it), and its
self-skip in `scan_paths()` was, in practice, dead weight.

Issue #2179 asked to make the policy "centrally effective" — add a COMMITTED,
project-level `.heph-project-denylist` so the control is enforced for every
contributor and in CI, not only on machines where an operator created the local file.
The first revised plan did this and centralized the self-skip:

```python
# scan_paths(): correctly skips BOTH denylist files
denylist_paths = {
    (repo_root / DENYLIST_FILENAME).resolve(),
    (repo_root / PROJECT_DENYLIST_FILENAME).resolve(),
}
for path in paths:
    candidate = path if path.is_absolute() else repo_root / path
    if candidate.resolve() in denylist_paths or not candidate.is_file():
        continue
```

But the guard has THREE scan entry points, and the `--staged` one bypasses
`scan_paths()` entirely — it reads index blobs directly:

```python
# main() --staged loop — NO denylist-path exclusion
if args.staged:
    for rel_path in staged_files(repo_root, pathspecs):
        text = staged_text(repo_root, rel_path)
        if text is not None:
            findings.extend(_scan_text("staged", rel_path, text, tokens))
```

The moment the project file becomes TRACKED, this un-guarded path becomes a self-lock:

1. An operator adds a real banned pattern to `.heph-project-denylist` and `git add`s it.
2. `load_denylist()` reads the working tree → the new token is now an active pattern.
3. The staged blob of `.heph-project-denylist` literally CONTAINS that token.
4. The `--staged` loop scans that blob, has no self-skip, and flags the file → exit 1.
5. The pre-commit hook runs `--staged --tracked`, so the commit is rejected.
6. `--no-verify` is banned in the repo — **there is no sanctioned way to ever commit
   a pattern into the central list.** The feature is dead on arrival.

The gitignored→tracked promotion is what activates the latent bug: for a gitignored
file the missing staged-path skip never mattered because the file could never be
staged. Widening the guard's data surface to a tracked file exposed the incomplete
self-exclusion.

## Why the "obvious" tests miss it

The plan already had `test_scan_paths_skips_project_denylist_file` and a
`python3 scripts/check_private_denylist.py --tracked` smoke check. Neither catches the
self-lock: both exercise the working-tree/tracked path (which HAD the skip). The bug
lives only on the `--staged` code path, and only when the policy file's staged blob
contains one of its own tokens. A header-only committed file (no active patterns)
also passes every check — the trap is invisible until someone adds the first real
pattern, i.e. the first time the feature is actually used.

## The fix

Centralize the exclusion in ONE predicate and call it from EVERY entry point (DRY —
a single source of truth for "is this a denylist file"):

```python
def _is_denylist_file(repo_root: Path, path: Path) -> bool:
    """True if *path* is either denylist file (never scanned as a violation)."""
    candidate = path if path.is_absolute() else repo_root / path
    denylist_paths = {
        (repo_root / DENYLIST_FILENAME).resolve(),
        (repo_root / PROJECT_DENYLIST_FILENAME).resolve(),
    }
    return candidate.resolve() in denylist_paths
```

```python
# --staged loop, now guarded by the SAME predicate
if args.staged:
    for rel_path in staged_files(repo_root, pathspecs):
        if _is_denylist_file(repo_root, rel_path):
            continue
        text = staged_text(repo_root, rel_path)
        if text is not None:
            findings.extend(_scan_text("staged", rel_path, text, tokens))
```

And a regression test that proves the previously-broken path exits 0 — staging the
policy file with its own token in the index:

```python
def test_staged_scan_skips_project_denylist_file(tmp_path):
    repo = _init_repo(tmp_path)  # git init
    (repo / ".heph-project-denylist").write_text("BANNED_TOKEN\n", encoding="utf-8")
    subprocess.run(["git", "add", ".heph-project-denylist"], cwd=repo, check=True)
    monkeypatch.setattr(_mod, "get_repo_root", lambda: repo)
    # The staged blob of the denylist file IS the token; must NOT self-flag.
    assert _mod.main(["--staged"]) == 0
```

## When to Use

- Planning to promote an OPTIONAL/LOCAL denylist, allowlist, or secret-scanner pattern
  file into a COMMITTED, centrally-enforced control (the gitignored→tracked promotion).
- A guard script has more than one scan mode (`--staged`/`--tracked`/explicit paths)
  and you must verify a shared self-skip is called on ALL of them, not just one.
- You are introducing a shared `_is_<policy>_file()`-style predicate and need to audit
  that every finder/scan path routes through it (grep the call sites).
- A plan reviewer flags that a self-exclusion covers the working-tree scan but not the
  index/`--staged` loop (or vice versa).
- Any guard whose enforced data lives inside a file the guard itself scans — the file
  must be excluded on every path, or it flags its own contents.
- The repo bans `--no-verify` / hook bypasses: an incomplete self-skip is not a minor
  annoyance but a hard self-lock with no escape hatch.

## Verified Workflow

> **Warning:** This is a PLANNING learning. The staged-path gap and the self-lock
> consequence were confirmed by a plan reviewer reading `scripts/check_private_denylist.py`
> at the cited lines; the shared-predicate fix and the regression test were authored in
> the plan but NOT executed end-to-end in CI. Treat the fix as a hypothesis until a PR
> lands it green.

### Quick Reference

```bash
# 1. Enumerate EVERY scan/finder entry point in the guard (not just the first one).
grep -nE "def scan_|for .* in staged_files|for .* in tracked_files|_scan_text\(" scripts/check_private_denylist.py
# 2. Confirm each entry point routes through the single self-skip predicate.
grep -nE "_is_denylist_file|denylist_paths|skip" scripts/check_private_denylist.py
# 3. Any entry point that calls _scan_text() / reads a blob WITHOUT the predicate is a gap.
# 4. Add a test that STAGES the policy file containing its own token and asserts exit 0:
uv run pytest tests/unit/scripts/test_check_project_denylist.py -k staged_scan_skips -v
```

### Detailed Steps

1. **List all scan entry points.** A guard with `--staged`, `--tracked`, and positional
   paths typically has 2-3 distinct loops. Only some route through a central helper;
   others (often the index/`--staged` loop) read blobs directly and are easy to miss.
2. **Route the self-skip through ONE predicate.** Replace any inline path-set comparison
   with a single `_is_<policy>_file(repo_root, path)` and call it from every loop before
   scanning. This is the DRY fix — the bug was one loop lacking the check the others had.
3. **Reason about the gitignored→tracked transition explicitly.** For a gitignored
   policy file the missing staged skip is latent (the file can never be staged). Adding
   a tracked project-level file activates it. Any plan that "promotes" a local file to
   committed must audit self-exclusion on the staged path specifically.
4. **Add a regression test on the previously-broken path, with a real active token.** A
   header-only/empty policy file passes everything; the test must stage the file WITH one
   of its own patterns and assert exit 0. Mirror the repo's existing git-repo test
   fixture (e.g. `_init_repo` + `git add`).
5. **Do not rely on the working-tree/`--tracked` smoke check.** It exercises the path
   that already had the skip and gives false confidence.
6. **Treat `--no-verify` bans as raising the stakes.** Where hook bypass is forbidden,
   an incomplete self-skip is a hard lock-out, not a warning — escalate it to a blocking
   finding in review.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Centralize the self-skip only in `scan_paths()` | The first #2179 revision added `.heph-project-denylist` and extended the denylist-path set check inside `scan_paths()` (working-tree/`--tracked` path) | The `--staged` loop in `main()` calls `_scan_text()` on index blobs directly, bypassing `scan_paths()` — it had NO self-skip. Staging the tracked project file with its own token would self-flag and, with `--no-verify` banned, lock out ever populating the list | A self-skip must be applied at EVERY scan entry point; extending only the one you first edit leaves a silent gap on the others |
| Rely on `test_scan_paths_skips_project_denylist_file` + a `--tracked` smoke run | The plan asserted the committed file is never flagged, and ran the guard on the repo | Both exercise the working-tree/tracked path that already had the skip; neither touches the `--staged` code path where the bug lives. A header-only committed file also passes because it has no active tokens | The regression test must target the SPECIFIC broken path (`--staged`) with a real active token in the staged blob, not the path that was already correct |
| Assume a gitignored file's missing staged-skip is harmless | The original guard shipped with a `scan_paths()` self-skip and an un-guarded `--staged` loop; it worked because the only denylist file was gitignored | The gap is latent only while the file is untracked. Promoting it to a committed/tracked file activates the self-flag — the change that widens the guard's data surface exposes the incomplete exclusion | When widening a guard to scan a newly-tracked file, re-audit self-exclusion on every path; a dormant gap becomes a live self-lock |

## Results & Parameters

**Point-in-time source anchors (ProjectHephaestus `scripts/check_private_denylist.py`, RE-GREP — line numbers drift).**

- Denylist filename constant + self-skip set: around `check_private_denylist.py:22` and `scan_paths()` at `~:134-137`.
- The un-guarded `--staged` loop: `main()` at `~:183-187` (`for rel_path in staged_files(...): ... _scan_text("staged", ...)`).
- The early-exit that made a missing local file a silent no-op: `main()` at `~:164-165` (`if not tokens: return 0`).
- Pre-commit hook wiring `--staged --tracked`: `.pre-commit-config.yaml:242-252`; CI runs it via `pre-commit run --all-files` in `.github/workflows/_required.yml:181`.

**Grep recipe to find every scan entry point before trusting a single self-skip:**

```bash
grep -nE "def scan_|staged_files|tracked_files|_scan_text\(" scripts/check_private_denylist.py
grep -nE "_is_denylist_file|denylist_paths" scripts/check_private_denylist.py
```

**Generalization.** The pattern is broader than denylists: any guard whose enforced
data lives in a file the guard scans (secret-scanner allowlists, lint-rule pattern
files, banned-identifier lists, config-schema self-references) must exclude that file on
EVERY code path. The failure signature is: "the guard passes until the first real entry
is added to its own committed pattern file, then that commit is rejected by the guard."

**Risks for the reviewer.**

- PLANNING artifact only — no pytest/CI was run for the fix; the self-lock was reasoned
  from source, and the regression test is authored but unexecuted.
- Line numbers are point-in-time; re-grep by content (`staged_files`, `_scan_text`,
  `_is_denylist_file`) at implementation time.
- The generalization to non-denylist guards is inferred from the single #2179 instance,
  not independently verified across other guards.

### Related skills

- `planning-frozen-registry-guard-co-update` — a DIFFERENT guard failure mode: a frozen
  exact-set test whose hard-coded copy drifts from the list it pins (co-update or drop),
  vs. this entry's runtime self-exclusion applied inconsistently across scan paths.
- `gitignored-scratch-dir-regression-guard` — guarding a gitignored dir against becoming
  tracked; shares the gitignored↔tracked boundary theme but guards against tracking, not
  against a tracked policy file self-flagging.
- `architecture-ctx-github-guard-blind-spot` — documenting a static guard's INTENDED
  scope boundary (out-of-scope by design), the opposite polarity of this UNINTENDED gap
  that must be closed.

## Verified On

| Project | Scenario | Status |
|---------|----------|--------|
| ProjectHephaestus | Issue #2179 plan — promote local `.heph-private-denylist` to committed `.heph-project-denylist`; reviewer caught missing `--staged` self-skip → self-lock | verified-in-review — gap confirmed against source by plan reviewer; fix authored in plan, not run in CI |
