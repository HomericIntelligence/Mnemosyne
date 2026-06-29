---
name: testing-autouse-default-patch-for-new-batched-call
description: "When you add a NEW external call (e.g. a new batched GraphQL fetch) inside a function that MANY existing unit tests already mock at a DIFFERENT seam, keep the existing tests green without editing each one by (a) making the new helper fault-tolerant (return {}/[] on any exception) and (b) adding ONE module-scoped autouse fixture that default-patches the new call (and any new side-effect write) to a no-op. Use when: (1) a function under test gains a new fetch/write that pre-existing tests do not patch; (2) ~N existing tests would otherwise hit the network or real I/O through the new seam; (3) you switched a gh JSON projection from --jq newline output to full --json + json.loads and must update mock payloads from newline strings to JSON arrays."
category: testing
date: 2026-06-29
version: "1.0.0"
user-invocable: false
verification: verified-local
tags:
  - pytest
  - autouse-fixture
  - mock-seam
  - new-dependency
  - fault-tolerant-helper
  - graphql-batch
  - json-projection
  - default-patch
  - existing-tests-green
  - unittest-mock
---

# Testing: Autouse Default-Patch for a New Batched Call

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-06-29 |
| **Objective** | Add a new external call (batched GraphQL fetch) + a new side-effect write inside a heavily-tested function without editing every pre-existing test |
| **Outcome** | Successful — all automation unit tests stay green; only the directly-exercising test file gains one fixture |
| **Verification** | verified-local — 2217 automation unit tests pass locally; CI pending on PR #1670 |

## When to Use

- You are adding a NEW external call (network, GraphQL, subprocess, file write) INSIDE a
  function that many existing unit tests already exercise.
- Those existing tests mock a DIFFERENT seam (e.g. they patch a labels fetch) and do NOT
  patch your new call — so without intervention the new call hits the real network/I/O.
- You do not want to touch ~N pre-existing tests one-by-one (high churn, error-prone).
- You changed a `gh` JSON projection from `--jq` newline output to full `--json` +
  `json.loads`, and existing mock payloads are now the wrong shape.

## Verified Workflow

Two complementary techniques. Apply BOTH — they cover different test files.

### Quick Reference

```python
# Technique 1 — make the NEW helper fault-tolerant by design.
# Tests in OTHER files that stub _gh_call / get_repo_root / get_repo_info in a way
# that makes the real call fail stay green automatically: the helper swallows the
# error and returns the empty default, which the caller treats as "signal unknown".
def fetch_all_issue_titles_graphql(...) -> dict[int, str]:
    try:
        ...  # real batched GraphQL fetch
    except Exception as exc:  # noqa: BLE001 — must be non-fatal
        logger.warning("title fetch failed, treating as unknown: %s", exc)
        return {}  # safe empty default ({} / [])


# Technique 2 — in the ONE test file that directly exercises the modified function,
# add a module-scoped autouse fixture that default-patches the new call to a no-op
# AND patches any new side-effect write to a no-op. Tests that exercise the NEW
# behavior override these with their own patch(...) context managers.
@pytest.fixture(autouse=True)
def _default_patch_new_seams():
    with (
        patch("hephaestus.automation.planner_state.fetch_all_issue_titles_graphql",
              return_value={}),
        patch("hephaestus.automation.planner_state.skip_epics"),  # no-op the new write
    ):
        yield
```

### Detailed Steps

1. **Identify every seam the function now touches.** Any NEW external call is a NEW mock
   seam — it is independent of seams existing tests already patch. Do NOT assume the old
   tests cover it.
   ```bash
   grep -rn "fetch_all_issue_titles_graphql\|skip_epics" tests/unit/automation/
   ```
2. **Make the new helper non-fatal.** Wrap the real fetch in `try/except`, log a warning,
   return a safe empty default (`{}` / `[]`). This keeps OTHER test files green untouched —
   they stub `_gh_call`/`get_repo_root`/`get_repo_info` so the real call no-ops/raises, and
   the helper swallows it, so the caller treats it as "signal unknown."
3. **Add one autouse default-patch fixture** in the test file that directly drives the
   modified function. Patch the new fetch to its empty default and any new write to a no-op.
   Scope it to the module (the test file), not session-wide.
4. **Override per-test for new behavior.** Tests that specifically assert the new fetch /
   write behavior open their own `patch(...)` context managers, which take precedence over
   the autouse defaults.
5. **If you changed the JSON projection,** update the mock payloads accordingly (see
   Results & Parameters) and add a test asserting the `--json` field list.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Patch the new call in every existing test individually | Edited ~6 pre-existing tests to add a `patch(...)` for the new fetch | High churn, error-prone, easy to miss one and let it hit the network | Use ONE module-scoped autouse default-patch fixture instead of N per-test edits |
| Assume existing tests still pass because they patch the labels fetch | Added the new titles fetch and ran the suite expecting green | WRONG — the new titles fetch is a SEPARATE seam those tests never patched, so it hit the real path | Any NEW external call is a NEW mock seam; either default-patch it (autouse) or make the helper fault-tolerant |
| Leave old mock payloads as newline strings after switching to `json.loads` | Kept mocks returning `"12\n7\n10\n"` after the projection became `--json number,labels,title` | `json.loads("12\n7\n10\n")` fails / yields the wrong shape — tests break or silently misparse | Update mock payloads to JSON arrays AND add a test asserting the `--json` field list as a cheap projection-regression guard |

## Results & Parameters

**Concrete context (ProjectHephaestus, HomericIntelligence/ProjectHephaestus, PR #1670):**
`PlannerStateManager.filter` in `hephaestus/automation/planner_state.py` already had ~6
tests patching `fetch_all_issue_labels_graphql`. Adding a new `fetch_all_issue_titles_graphql`
call plus a `skip_epics` write would have hit the real network in those tests.

- **Technique 1** — the titles helper returns `{}` on any failure, so the other test files
  (`tests/unit/automation/test_planner_loop.py`, `test_planner_main.py`) that only patch
  labels stayed green untouched.
- **Technique 2** — `tests/unit/automation/test_planner_state.py` gained a module-scoped
  `@pytest.fixture(autouse=True)` defaulting titles to `{}` and `skip_epics` to a no-op,
  avoiding edits to the ~6 pre-existing tests.

**JSON projection migration (the related fact):** when you change a `gh` projection from
`--jq`-newline output to full JSON, you MUST update existing mock payloads:

```python
# BEFORE — newline string consumed by --jq:
mock_run.return_value = "12\n7\n10\n"

# AFTER — full JSON parsed with json.loads(... ), projection: --json number,labels,title
mock_run.return_value = json.dumps([
    {"number": 12, "labels": [{"name": "bug"}], "title": "Fix the thing"},
    {"number": 7,  "labels": [],                "title": "Another"},
    {"number": 10, "labels": [{"name": "epic"}], "title": "Big epic"},
])

# Cheap regression guard against silent projection drift:
def test_projection_requests_expected_json_fields(mock_run):
    ...  # call the function
    args = mock_run.call_args[0][0]
    assert "--json" in args
    assert args[args.index("--json") + 1] == "number,labels,title"
```

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| ProjectHephaestus | PR #1670 — add `fetch_all_issue_titles_graphql` + `skip_epics` to `PlannerStateManager.filter` | verified-local — 2217 automation unit tests pass locally; CI pending |
