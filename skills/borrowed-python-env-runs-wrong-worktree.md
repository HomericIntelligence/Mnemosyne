---
name: borrowed-python-env-runs-wrong-worktree
description: "Detect that test failures come from a foreign Python environment, not from your change. Use when a worktree has no virtual environment and you run the suite with an interpreter from a sibling worktree; the suite reports missing attributes, missing functions, or import errors for code you just added; the suite hangs or starts real staging or publishing work instead of failing, because guard code from your change is absent in the imported package; an import resolves to another checkout; you consider a PYTHONPATH override instead of a new environment; you are about to report a failure count before you confirm which package the interpreter loads; you compare a branch run with a base-commit run and both used the same shared environment; or you hand a test run to a delegated agent."
category: testing
date: 2026-10-24
version: "1.2.0"
user-invocable: false
verification: verified-local
tags:
  - testing
  - git-worktree
  - virtualenv
  - editable-install
  - import-path
  - false-failure
  - pytest
  - attribution
---

# A Borrowed Python Environment Runs the Wrong Worktree

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-24 |
| **Objective** | Attribute test failures to the correct cause before you report them, when the test run uses an interpreter from another checkout. |
| **Outcome** | Successful. A 14-failure run was a borrowed-environment artifact. The worktree's own environment reduced the result to 2 failures, and both were pre-existing and passed in continuous integration. |

A new git worktree has no virtual environment. The convenient action is to run its
tests with the interpreter of a neighbouring worktree. That interpreter resolves an
editable install of the package to **its own** source tree. Your new code is absent
from the package that the test process imports. The suite then reports failures for
code that you added, and it looks like a defect in your change.

## When to Use

- A new worktree has no `.venv`, and you borrow the interpreter of another worktree.
- The suite reports `AttributeError` for a name that exists in your edited file.
- The suite reports import errors for a function or module that you just added.
- The suite does not fail; it hangs, or it starts long real work such as staging, copying, or publishing, because a guard or precondition from your change is absent in the imported package.
- Recreating a virtual environment is not practical, and you consider a `PYTHONPATH` override with the borrowed interpreter.
- You are about to report a failure count, or a defect, for a change in a fresh worktree.
- Two worktrees disagree about the same test on the same commit.

## Verified Workflow

### Quick Reference

Confirm which package the interpreter loads **before** you read a failure count:

```bash
# Required first check. The path must be inside the worktree under test.
<borrowed-or-local>/.venv/bin/python -c "import <package>; print(<package>.__file__)"
```

If the path is in a different checkout, do not use that interpreter unchecked.
Repair the environment. Two repairs exist:

Create an environment in the worktree:

```bash
cd <worktree>
uv venv --python <version> .venv
uv pip install --python .venv/bin/python -e '.[dev]'
.venv/bin/python -c "import <package>; print(<package>.__file__)"   # must be <worktree>/src/...
```

Or prepend the worktree source with `PYTHONPATH` when you cannot create an
environment. This works for a source-layout repository (`src/<package>`). After
you set it, run the same import check and confirm the path is inside the
worktree. If an editable-install finder still wins, `PYTHONPATH` does not help;
fall back to a worktree environment. Treat the override as unverified until the
import check passes.

### Suggested Approach

1. **Resolve the package path first.** Run the one-line import check. This takes
   one second and makes the whole failure count trustworthy. Run it before any
   test that can touch shared storage, staging areas, or other real resources.
   A foreign package lacks your new guards, so the suite can start real work
   instead of failing.
2. **Read the first cause.** A message such as `module '<pkg>' has no attribute
   '<name>'` for a name that exists in your file is a resolution symptom, not a
   code defect. Confirm the name exists in the worktree source before you debug it.
3. **Do not change the code.** No defect exists. Repair the environment.
4. **Re-run with the correct environment.** Compare the failure count. A large drop
   shows the first run measured another tree.
5. **Baseline the remainder.** For each remaining failure, run the same test on the
   unmodified base commit. A failure that reproduces there is pre-existing. Report
   it as an environment or baseline limit, not as your change. Run the import check
   inside the baseline run too. If the branch run and the base run both resolve the
   package to the same foreign checkout, they run the same code. Identical failure
   lists then prove nothing about your change. Bind each run to its own source tree
   (`PYTHONPATH=<tree>/src` and a passing import check), then compare again.
5a. **Put the import check in every delegated test brief.** A delegated agent that
   runs the suite reports the borrowed-environment result as a test result unless
   the brief requires the import check and the `PYTHONPATH` binding. Accept a
   delegated count only when the report states the path that the package resolved to.
6. **Let continuous integration decide.** A pre-existing local failure that passes
   in continuous integration confirms an environment limit on the host.

### Why this differs from a working-directory artifact

A path that uses the test file's own location resolves relative to the file, so a
correct working directory fixes it. A borrowed interpreter resolves the package from
its own installed metadata. A correct working directory does **not** change that.
Do not repair this condition by changing the working directory.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --- | --- | --- | --- |
| Reuse a sibling worktree's interpreter | Ran the new worktree's tests with a neighbouring worktree's `.venv` | The editable install resolved the package to the neighbouring tree, so every new symbol was missing | Resolve the package path before the run |
| Read the failure count as a code result | Treated 14 failures as defects in the change | All 14 came from the foreign package; none came from the change | Check the import path before you attribute failures |
| Change the working directory | Ran from the correct worktree root with the borrowed interpreter | The working directory does not change which installed package the interpreter loads | Repair the environment, not the working directory |
| Trust a hang as a slow suite | The borrowed interpreter ran the suite and it hung in real staging work against a shared store | The missing guard from the change was absent in the foreign package, so staging proceeded instead of refusing; the hang was a resolution symptom, and the run did real work | Treat a hang or unexpected long-running real work as a foreign-environment symptom; check the import path before any run that can mutate real resources |
| Compare a branch run with a base run in one shared environment | Reported "the same failures on the branch and the base commit" as proof of no regression | Both runs imported the package from the shared main checkout, so they ran identical code and the match was by construction | Bind each run to its own tree and confirm the import path in each run before you compare |
| Blame the change for the last 2 failures | Assumed the remaining failures were caused by the change | The same tests failed on the unmodified base commit on the same host | Baseline each remainder on the base commit |

## Results & Parameters

| Item | Required value |
| --- | --- |
| Pre-run proof | `import <package>; <package>.__file__` is inside the worktree under test |
| Foreign-environment symptom | `AttributeError` or import error for code that exists in the worktree |
| Foreign-environment symptom without failure | A hang, or real staging, copy, or publish work that your guard should have refused |
| `PYTHONPATH` remedy | `PYTHONPATH=<worktree>/src`, then re-run the import check; unverified until the path shows the worktree |
| Local re-creation | `uv venv` then `uv pip install -e '.[dev]'` inside the worktree |
| Remainder classification | Reproduced on the unmodified base commit means pre-existing, only if each run passed its own import check |
| Delegated test run | The brief requires the import check; the report states the resolved package path |
| Final authority | Continuous integration on the exact head |

Safety bound: do not edit source to satisfy a failure from a foreign package. Do not
record a failure count before the import-path check.

## Verified On

| Project | Context | Details |
| --- | --- | --- |
| An operator-service repository | One session, one worktree | A borrowed environment reported 14 failures. The local environment reported 2 failures. Both failed on the unmodified base commit and passed in continuous integration. |
| A serving-platform repository | One worktree, two test runs | The borrowed interpreter ran the suite into real staging against a shared store because a new workspace guard was absent from the imported package. `PYTHONPATH` bound the worktree source after the import check passed, and the guarded tests passed. See [notes](../skills/borrowed-python-env-runs-wrong-worktree.notes.md). | | A serving-platform repository | One worktree, a delegated test run and a baseline run | The environment was an editable install of the main checkout. The branch run and the base run showed the same failures. Both used the main checkout source, so the match was not evidence. After a `PYTHONPATH` binding and an import check, the affected tests passed. |
