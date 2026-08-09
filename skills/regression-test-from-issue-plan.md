---
name: regression-test-from-issue-plan
description: "Recover missing regression tests from issue plans and choose the lowest test tier that proves the real boundary. Use when: (1) an issue references a test that should exist as a harness, (2) a bug fix landed without its named regression, (3) issue comments contain hand-computed expected values, (4) a parser consumes external-tool output whose producer semantics must be exercised without mocks."
category: testing
date: 2026-07-20
version: "1.1.1"
user-invocable: false
verification: unverified
history: regression-test-from-issue-plan.history
tags:
  - regression-testing
  - issue-plan
  - integration-testing
  - git
  - porcelain
  - pytest
---
# Regression Tests from Issue Plans

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-07-20 |
| **Objective** | Recover regression tests specified in issue plans and prove behavior at the real boundary when mocks cannot establish the producer contract |
| **Outcome** | The original Mojo workflow was verified in ProjectOdyssey; the new real-Git type-change integration pattern is planning-only and has not been executed |
| **Verification** | unverified — proposed Git integration workflow pending local and CI validation |
| **History** | [changelog](./regression-test-from-issue-plan.history) |

## When to Use

- Issue description says "test X will serve as the regression harness" but test X does not exist in the codebase
- A bug fix is already merged to main but the paired regression test is missing
- Issue comments contain hand-computed expected values for specific inputs
- Issue cross-references another issue that planned a test (e.g. "follow-up from #NNNN")
- `grep -r "test_<name>" tests/` returns no matches for a test the issue expects to exist
- Existing unit tests inject synthetic subprocess output, but the regression depends on the
  external tool producing a particular status, mode, quoting, or record shape
- A Git parser accepts a porcelain-v1 status pair, but no test creates the corresponding real
  repository transition and follows it through parsing, selection, and staging

## Verified Workflow

> **Scope:** This section is the original ProjectOdyssey workflow, verified by PR #4868. The
> real-Git extension is separated under Proposed Workflow because it has not been executed.

### Quick Reference

```bash
# 1. Find what test name the issue expects
gh issue view <N> | grep "test_"
gh issue view <N> --comments | grep -A5 "test_"

# 2. Check if test exists
grep -r "test_<name>" tests/

# 3. Check if the fix is already in source
git log --oneline -- <file> | head -5

# 4. Read the plan for expected values
gh issue view <REFERENCED_ISSUE> --comments

# 5. Count tests in target file (≤10 per file)
grep -c "^fn test_" tests/path/to/test_file_part2.mojo

# 6. Validate pre-commit before commit
SKIP=mojo-format pixi run pre-commit run --files <file>
```

### Detailed Steps

1. **Read the issue** — `gh issue view <N>` — note exact test name mentioned
2. **Search for the test** — `grep -r "test_<name>" tests/` confirms it is missing
3. **Check fix status** — `git log --oneline -- shared/core/<file>.mojo | head -5`
4. **Read the referenced issue plan** — `gh issue view <REFERENCED> --comments` for expected values
5. **Find the right part file** — count tests with `grep -c "^fn test_"` per file, pick one with room
6. **Write the test** — use hand-computed expected values from the plan; manually set strides if testing stride logic
7. **Add to main()** — append the call in the appropriate section
8. **Validate** — `SKIP=mojo-format pixi run pre-commit run --files <file>`
9. **Commit and PR** — `git add <file> && git commit -m "test(scope): add <name> regression test"`

### Key insight: `_get_float64` vs stride-based indexing

When `as_contiguous()` uses `_get_float64(i)` with a flat index, it reads `index * dtype_size` from
memory — ignoring strides entirely. This means manually mutating `_strides` changes what
`is_contiguous()` reports but does NOT change the flat memory layout. The non-contiguous branch of
`as_contiguous()` that uses stride arithmetic will reorder values; the flat-copy branch preserves them.
Know which branch is exercised before computing expected values.

## Proposed Workflow

> **Warning:** The real-Git type-change extension has not been validated end-to-end. It is based
> on a reviewed implementation plan. Treat it as a hypothesis until local tests and CI confirm
> it.

### Quick Reference

```bash
# Inspect implementation and synthetic coverage first
rg -n "porcelain|type.change" <source-dir> tests

# Run the real-producer integration test without repository-wide addopts
uv run pytest tests/integration/test_<feature>_integration.py \
  --override-ini="addopts=" -v --strict-markers
```

### Real external-output boundary subcase

When the code parses output from Git or another external tool, a mocked string proves only that
the parser accepts a string chosen by the test author. It does not prove the tool produces that
record for the filesystem transition at issue. Add one narrow integration test that owns the
whole producer-to-consumer chain:

1. Create an isolated temporary repository and remove inherited repository-scoping variables
   such as `GIT_DIR`, `GIT_WORK_TREE`, `GIT_INDEX_FILE`, and `GIT_COMMON_DIR`.
2. Configure only what the fixture requires. For a file-to-symlink transition, enable
   `core.symlinks=true`, commit a regular file baseline with test-local identity and hooks
   disabled, then replace the tracked file with a symlink.
3. Call the production status reader. Do not mock porcelain output. Assert the exact
   NUL-delimited record, including the significant leading space in the worktree-only status
   pair: `" T path/to/file\0"`.
4. Pass that real record through the production parser, path allowlist/selection logic, and
   staging helper in sequence. This proves the integration seam instead of merely re-testing
   each helper separately.
5. Ask Git for independent index evidence with
   `git diff --cached --name-status`; expect `T\tpath/to/file\n`.
6. Keep malformed-record and unsupported-status-pair rejection tests at the unit tier. The
   integration test complements those tests; it does not replace them.
7. Mark the test `integration` and POSIX-only, with an explicit Windows skip, because genuine
   file-to-symlink behavior depends on real symlink semantics.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Search for test by exact name | `grep -r "test_contiguous_stride_correct_values" tests/` | Returned no matches — test never existed | Absence of a test is exactly the bug to fix |
| Checked existing branch for the fix | Expected `4088-fix-as-contiguous` branch to contain the test | Branch had a different change (pre-commit hook), not the regression test | Branch names can be misleading; use `git diff main..<branch> -- <file>` to confirm |
| Considered adding to original test file | `test_utility.mojo` seemed consistent with issue plan | File had 43 tests — far exceeds the ≤10 fn test_ limit | Always count tests before adding; use numbered part files |
| Assumed the fix still needed implementing | Expected the source fix to be missing | Fix was already in `shape.mojo` from a prior commit | Check `git log` for the source file first — fix and test can land separately |
| Treat synthetic porcelain records as full boundary coverage | Existing unit tests directly supplied accepted and rejected status pairs | They prove parser policy but cannot prove real Git emits the accepted pair for the intended filesystem transition or that the path reaches the index | Preserve unit rejection coverage and add one real-producer integration path from repository mutation through staged-index evidence |

## Results & Parameters

**Test template for stride-based bug regression (Mojo)**:

```mojo
fn test_contiguous_stride_correct_values() raises:
    """Regression test: as_contiguous() must use stride-based indexing.

    For shape [2, 3] with strides [1, 2] (column-major), the stride-based
    source offsets produce:
      Output[0,0] = src[0*1 + 0*2] = src[0] = 0.0
      Output[0,1] = src[0*1 + 1*2] = src[2] = 2.0
      Output[0,2] = src[0*1 + 2*2] = src[4] = 4.0
      Output[1,0] = src[1*1 + 0*2] = src[1] = 1.0
      Output[1,1] = src[1*1 + 1*2] = src[3] = 3.0
      Output[1,2] = src[1*1 + 2*2] = src[5] = 5.0
    Flat output: [0.0, 2.0, 4.0, 1.0, 3.0, 5.0]
    """
    var shape = List[Int]()
    shape.append(2)
    shape.append(3)
    var a = arange(0.0, 6.0, 1.0, DType.float32)
    var b = a.reshape(shape)

    # Manually set column-major strides to simulate non-contiguous view
    b._strides[0] = 1
    b._strides[1] = 2

    assert_false(b.is_contiguous(), "Column-major tensor should not be contiguous")
    var c = as_contiguous(b)
    assert_true(c.is_contiguous(), "as_contiguous() result should be contiguous")

    assert_almost_equal(c._get_float64(0), 0.0, 1e-6, "c[0,0] should be 0.0")
    assert_almost_equal(c._get_float64(1), 2.0, 1e-6, "c[0,1] should be 2.0")
    assert_almost_equal(c._get_float64(2), 4.0, 1e-6, "c[0,2] should be 4.0")
    assert_almost_equal(c._get_float64(3), 1.0, 1e-6, "c[1,0] should be 1.0")
    assert_almost_equal(c._get_float64(4), 3.0, 1e-6, "c[1,1] should be 3.0")
    assert_almost_equal(c._get_float64(5), 5.0, 1e-6, "c[1,2] should be 5.0")
```

**Test file constraint**: ≤10 `fn test_` functions per `.mojo` file. Check with:

```bash
grep -c "^fn test_" tests/path/to/file.mojo
```

**Strides for common shapes**:

| Shape | Row-major (contiguous) | Column-major (non-contiguous) |
| ------- | ------------------------ | ------------------------------- |
| (2, 3) | `[3, 1]` | `[1, 2]` |
| (3, 4) | `[4, 1]` | `[1, 3]` |
| (2, 3, 4) | `[12, 4, 1]` | `[1, 2, 6]` |

**Proposed real-Git type-change fixture (Python/pytest)**:

```python
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = [
    pytest.mark.integration,
    pytest.mark.requires_posix,
    pytest.mark.skipif(
        sys.platform == "win32",
        reason="Real file-to-symlink Git type changes require POSIX symlink semantics",
    ),
]


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )


def test_real_type_change_reaches_the_index(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "core.symlinks", "true")

    relative_path = "src/type-changed.py"
    tracked_path = repo / relative_path
    tracked_path.parent.mkdir()
    tracked_path.write_text("regular file\n", encoding="utf-8")
    _git(repo, "add", "--", relative_path)
    _git(
        repo,
        "-c", "user.name=Integration Test",
        "-c", "user.email=integration-test.invalid",
        "-c", "core.hooksPath=/dev/null",
        "commit", "--no-gpg-sign", "-qm", "test: add baseline",
    )

    tracked_path.unlink()
    tracked_path.symlink_to("replacement.py")

    porcelain = production_read_status(repo, git_timeout=10)
    assert porcelain == f" T {relative_path}\0"
    entries = production_parse_status(porcelain)
    paths = production_select_paths(entries, allowed_paths=(relative_path,))
    production_stage_paths(paths, repo, git_timeout=10)

    staged = _git(repo, "diff", "--cached", "--name-status")
    assert staged.stdout == f"T\t{relative_path}\n"
```

Before initializing the repository, clear inherited Git environment variables in a fixture or
with `monkeypatch.delenv(..., raising=False)`. Replace the `production_*` placeholders with the
actual public or intentionally-tested internal helpers. Keep `git_timeout=10` explicit so a hung
subprocess fails promptly.

**Expected observations**:

| Check | Expected value |
|-------|----------------|
| Worktree porcelain-v1 record | `" T src/type-changed.py\\0"` |
| Parsed entry | `((" T", "src/type-changed.py"),)` |
| Selected staging mode | add the explicit path; no update-only paths |
| Cached name-status | `"T\\tsrc/type-changed.py\\n"` |
| Platform scope | POSIX symlink semantics; skip Windows |

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| ProjectOdyssey | Issue #4088, PR #4868 | [notes.md](../references/notes.md) |
| ProjectHephaestus | Planned integration regression for real Git porcelain-v1 file-to-symlink type changes | unverified — implementation and CI validation pending |
