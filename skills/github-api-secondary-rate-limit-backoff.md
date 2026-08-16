---
name: github-api-secondary-rate-limit-backoff
license: BSD-3-Clause
description: 'Fix rate-limit message phrasings that no regex matches falling through
  to the wrong retry path in rate_limit.py. Use when GitHub secondary rate limit
  messages fall through to the generic 1s/2s/4s transient retry path with no useful
  log output, OR when a Claude CLI session-limit 429 (e.g. "You''ve hit your session
  limit · resets 4:20am" with NO parenthesized timezone) is not matched by
  RATE_LIMIT_RE or CLAUDE_USAGE_CAP_RE so the quota-reset resolver returns None and
  the implement phase hard-fails instead of waiting for the reset — instead of being
  identified and routed through the proper rate-limit backoff path.

  '
category: debugging
date: 2026-06-13
version: 1.1.0
history: github-api-secondary-rate-limit-backoff.history
user-invocable: false
tags:
- github-api
- rate-limit
- secondary-rate-limit
- session-limit
- claude-cli
- quota-reset
- regex-phrasing-gap
- detection-consolidation
- backoff
- retry
- hephaestus
---
# Skill: github-api-secondary-rate-limit-backoff

## Overview

| Field | Value |
| ------- | ------- |
| Date | 2026-06-07 |
| Project | ProjectHephaestus |
| Objective | Correctly detect and handle GitHub secondary rate limit errors with proper exponential backoff instead of falling through to the generic 1s/2s/4s transient retry path |
| Outcome | 10 new unit tests; PR #1092 filed (CI pending at capture time) |
| PR | HomericIntelligence/ProjectHephaestus#1092 |
| Verification | verified-local |

## When to Use

Use this skill when:
- GitHub API calls fail with `"You have exceeded a secondary rate limit. Please wait a few minutes before you try again."` but the retry log shows generic `"gh call failed (attempt N), retrying in Ns"` with 1s/2s/4s waits
- `detect_rate_limit()` returns `False` for secondary rate limit messages
- A Claude CLI session-limit 429 (`result: "You've hit your session limit · resets 4:20am"` with **NO** parenthesized timezone) is not matched by `RATE_LIMIT_RE` or `CLAUDE_USAGE_CAP_RE`, the quota-reset resolver returns `None`, the `wait_until(reset_epoch)` branch is skipped, and the implement phase **hard-fails** the issue instead of waiting for the reset
- A rate-limit detector exists in more than one place (e.g. `_claude_quota_reset_epoch`, `scan_quota_reset`, inline detect pairs) and a new phrasing has to be patched in N places — a sign detection must be consolidated into one resolver
- You need to add a new rate-limit signal type that has no reset epoch (unlike primary REST or GraphQL limits)
- Writing tests that mock `time` and need to distinguish rate-limit sleeps from per-thread throttle sleeps

**Trigger symptoms in logs**:
```
ERROR   stderr: gh: You have exceeded a secondary rate limit. Please wait a few minutes...
WARNING github_api: gh call failed (attempt 1), retrying in 1s
WARNING github_api: gh call failed (attempt 2), retrying in 2s
WARNING github_api: gh call failed (attempt 3), retrying in 4s
```

**Expected log output after fix**:
```
WARNING github_api: GitHub secondary rate limit hit (attempt 1), waiting before retry
WARNING github_api: Rate limited but no reset time, waiting 15s
```

## Root Cause: Missing Regex in detect_rate_limit()

`hephaestus/github/rate_limit.py` contains two regexes that cover primary rate limits:
- `RATE_LIMIT_RE`: matches `"Limit reached.*resets TIME (TZ)"` — REST primary limits
- `GRAPHQL_RATE_LIMIT_RE`: matches `"API rate limit exceeded"` — GraphQL primary limits

Secondary rate limit messages look like:
```
You have exceeded a secondary rate limit. Please wait a few minutes before you try again.
```

Neither regex matches this text. Therefore `detect_rate_limit()` returns `False`, `_extract_reset_epoch()` returns `None`, and `_gh_call_impl` falls through to the generic transient error branch which uses `wait_seconds = 2**attempt` (1s, 2s, 4s...).

The secondary rate limit also has **no reset epoch** in the error message — the primary rate-limit path's `_extract_reset_epoch()` has nothing to parse. This means secondary limits must be handled as a separate detection path, not by augmenting `detect_rate_limit()`.

## Root Cause (same shape): Claude session-limit 429 with no timezone

The Claude CLI emits a session-limit 429 as a `result` field with **NO** parenthesized timezone:

```text
result: "You've hit your session limit · resets 4:20am"
```

In `hephaestus/github/rate_limit.py`:
- `RATE_LIMIT_RE` requires `Limit reached` **plus** a `(tz)` group.
- `CLAUDE_USAGE_CAP_RE` requires a **mandatory** `\((?P<tz>...)\)`.

Neither matches the tz-less session-limit phrasing. So the quota-reset resolver
returned `None`, the `wait_until(reset_epoch)` branch was skipped, and the
implement phase **hard-failed** the issue instead of waiting for the 4:20am
reset.

Detection note: `api_error_status` / the literal `429` are never inspected —
detection is purely text/regex on the `result` field. The subtype can be
`"success"` while `is_error: true`; the error must still be treated as an error
via `is_error` (the code already does this). This is the **same root-cause
shape** as the secondary-rate-limit gap above: a phrasing that no regex matches
falls through to the wrong path.

### The fix

Add `CLAUDE_SESSION_LIMIT_RE` + `detect_session_limit(text)` to `rate_limit.py`.
The regex makes the `(tz)` **OPTIONAL**: it matches `(hit|reached) your session
limit` with an optional `resets <time>` and an optional `(tz)`.

- When a reset time is present, parse via the existing
  `parse_reset_epoch(time, tz_or_empty)` — it defaults tz to
  `America/Los_Angeles` and rolls to tomorrow if the time is already past.
- When the message matches but has **no parseable reset time**, return the `0`
  "rate-limited, reset unknown" **sentinel**. Callers must back off, not treat
  `0` as "no limit" — preserve the `is not None` chaining everywhere (a `0`
  reset is still a real limit; only `None` means "no limit detected").

### Consolidation: one resolver, all call sites

The broader lesson. There were **four** separate copies of quota detection:

- `_claude_quota_reset_epoch` in `_implement_phase.py`
- `scan_quota_reset` in `claude_invoke.py`
- inline detect pairs in `client.py` and `follow_up.py`

Fixing a phrasing gap in one place left the others broken. The fix added a
**single common resolver** `resolve_quota_reset_epoch(*texts)` in
`rate_limit.py` that runs all three detectors (`detect_rate_limit`,
`detect_claude_usage_cap`, `detect_session_limit`) and is exported. Every
agent-invocation call site now delegates to it (`_claude_quota_reset_epoch`,
`scan_quota_reset`, the `follow_up` `is_error` guard).

**Lesson**: cross-cutting "is this output a rate limit?" detection MUST live in
ONE resolver that all call sites route through — otherwise a new phrasing must
be patched in N places and some get missed.

**Deliberate exception**: `client.py`'s narrow `detect_claude_usage_cap` was
intentionally left as-is. It raises the typed `ClaudeUsageCapError` for
gh-surfaced caps and must **NOT** also catch GitHub rate limits / session limits
routed through the gh subprocess wrapper. So "route everything through the
resolver" has one deliberate exception where a typed-exception path needs the
narrow detector.

## Verified Workflow

### Quick Reference

```
1. Add SECONDARY_RATE_LIMIT_RE + detect_secondary_rate_limit() to rate_limit.py
2. Add base_wait_seconds param to _handle_rate_limit_attempt() in github_api.py
3. In _gh_call_impl(), detect secondary rate limit BEFORE generic transient path
4. Route to _handle_rate_limit_attempt(reset_epoch=0, base_wait_seconds=15)
5. In tests mocking time: filter sleep calls >= 1s to skip throttle sub-second sleeps
```

### Step 1: Add regex and detector to rate_limit.py

In `hephaestus/github/rate_limit.py`, add after the existing `GRAPHQL_RATE_LIMIT_RE`:

```python
SECONDARY_RATE_LIMIT_RE = re.compile(
    r"exceeded a secondary rate limit",
    re.IGNORECASE,
)

def detect_secondary_rate_limit(text: str) -> bool:
    """Return True if text contains a GitHub secondary rate-limit message."""
    return bool(SECONDARY_RATE_LIMIT_RE.search(text))
```

**Why a separate function**: `detect_rate_limit()` feeds into `_extract_reset_epoch()`. Secondary limits have no reset epoch, so they must not be conflated with primary limits.

### Step 2: Add base_wait_seconds to _handle_rate_limit_attempt()

In `hephaestus/automation/github_api.py`, update `_handle_rate_limit_attempt`:

```python
def _handle_rate_limit_attempt(
    *,
    reset_epoch: int,
    attempt: int,
    max_retries: int,
    retry_on_rate_limit: bool,
    cause: BaseException,
    base_wait_seconds: int = 60,  # NEW parameter; existing callers get 60s default
) -> None:
    ...
    wait_seconds = min(base_wait_seconds * (2**attempt), 300)  # was: 60 * (2**attempt)
```

The `base_wait_seconds=60` default preserves existing primary rate-limit behavior.

### Step 3: Detect secondary rate limit in _gh_call_impl()

In `_gh_call_impl`, locate the existing `_is_non_transient_error` check. Immediately after that (and **before** the generic `wait_seconds = 2**attempt` fallback path), add:

```python
# Check for secondary rate limit — must come before generic transient fallback
stdout_text = e.stdout if e.stdout else ""
stderr_text = e.stderr if e.stderr else ""
if detect_secondary_rate_limit(stderr_text) or detect_secondary_rate_limit(stdout_text):
    logger.warning(
        "GitHub secondary rate limit hit (attempt %s), waiting before retry",
        attempt + 1,
    )
    _handle_rate_limit_attempt(
        reset_epoch=0,
        attempt=attempt,
        max_retries=max_retries,
        retry_on_rate_limit=retry_on_rate_limit,
        cause=e,
        base_wait_seconds=15,
    )
    continue
```

**Why check both stderr AND stdout**: GraphQL API errors can appear on stdout in the `errors` JSON field, not stderr.

**Why `reset_epoch=0`**: Secondary rate limits have no reset epoch in the message. `_handle_rate_limit_attempt` already handles `reset_epoch=0` gracefully (logs "no reset time").

### Resulting backoff sequence

| Attempt | Wait (base_wait_seconds=15) |
| --------- | ----------------------------- |
| 1 | 15s |
| 2 | 30s |
| 3 | 60s |
| 4 | 120s |
| 5 | 240s |
| 6+ | 300s (capped) |

### Step 4: Test pattern for mocking time module

```python
@patch("hephaestus.automation.github_api.time")
@patch("hephaestus.automation.github_api.run")
def test_secondary_rate_limit_retries_with_15s_base_backoff(self, mock_run, mock_time):
    mock_run.side_effect = [
        subprocess.CalledProcessError(1, "gh", stderr="exceeded a secondary rate limit"),
        subprocess.CalledProcessError(1, "gh", stderr="exceeded a secondary rate limit"),
        MagicMock(stdout='{"ok": true}', returncode=0),
    ]

    result = gh_call(["gh", "api", "/repos/foo/bar"])

    # Filter out sub-second throttle sleeps when asserting wait times:
    sleep_calls = [c[0][0] for c in mock_time.sleep.call_args_list if c[0][0] >= 1]
    assert sleep_calls[0] == 15   # not 1s (generic 2**0)
    assert sleep_calls[1] == 30   # not 2s (generic 2**1)
```

**Critical**: When mocking the `time` module, the per-thread throttle (`_gh_throttle_wait`) also calls `time.sleep` with sub-second values. Always filter `>= 1` to isolate rate-limit sleeps from throttle sleeps in assertions.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Standalone sleep+continue | Call `time.sleep(15 * 2**attempt)` then `continue` directly in the except branch | Bypasses `retry_on_rate_limit=False` check; raises generic `RuntimeError` on exhaustion instead of `GitHubRateLimitError` | Always route through `_handle_rate_limit_attempt` to preserve error semantics |
| Augment detect_rate_limit() | Return True for secondary messages from existing `detect_rate_limit()` | Secondary limits have no reset epoch; `_extract_reset_epoch()` returns None causing same fallback | Handle secondary limits as a separate detection path, not via primary rate-limit detector |
| Mandatory-timezone regex | Add a session-limit regex with a required `\((?P<tz>...)\)` group like `CLAUDE_USAGE_CAP_RE` | The session-limit phrasing has NO `(tz)`, so the mandatory group never matched and the message still fell through | Make the `(tz)` OPTIONAL and default it (to `America/Los_Angeles`) when absent |
| Patch detection only in _implement_phase | Add `detect_session_limit` only to `_claude_quota_reset_epoch` in `_implement_phase.py` | Planner / plan-reviewer / follow-up call sites (`scan_quota_reset`, `follow_up` is_error guard) still hard-failed on the same phrasing | Consolidate all detectors into one `resolve_quota_reset_epoch(*texts)` resolver that every call site routes through |

## Results & Parameters

### Key constants

| Parameter | Value | Rationale |
| ----------- | ------- | ----------- |
| `base_wait_seconds` for secondary | 15 | Secondary limits typically clear faster than primary; 15s keeps first retry fast while exponential climb absorbs failures |
| `base_wait_seconds` for primary | 60 (default unchanged) | Preserves existing behavior |
| Max cap | 300s | Prevents runaway waits regardless of attempt count |

### Import required in github_api.py

```python
from hephaestus.github.rate_limit import (
    detect_rate_limit,
    detect_secondary_rate_limit,  # NEW
    _extract_reset_epoch,
)
```

### Session-limit detector + resolver (v1.1.0)

| Parameter | Value | Rationale |
| ----------- | ------- | ----------- |
| `CLAUDE_SESSION_LIMIT_RE` shape | `(hit\|reached) your session limit`, optional `resets <time>`, optional `(tz)` | The session-limit phrasing has no `(tz)`; making it optional lets the same regex match both tz-bearing and tz-less variants |
| Reset-time parse | `parse_reset_epoch(time, tz_or_empty)` | Defaults tz to `America/Los_Angeles`; rolls to tomorrow if the time is already past |
| No-reset-time return | `0` sentinel ("rate-limited, reset unknown") | Callers must back off; `0` is a real limit. Only `None` means "no limit" — preserve `is not None` chaining everywhere |
| Common resolver | `resolve_quota_reset_epoch(*texts)` | Runs `detect_rate_limit`, `detect_claude_usage_cap`, `detect_session_limit`; exported and used by every agent-invocation call site |

**Call sites consolidated onto `resolve_quota_reset_epoch`:**

- `_claude_quota_reset_epoch` (`_implement_phase.py`)
- `scan_quota_reset` (`claude_invoke.py`)
- the `follow_up` `is_error` guard (`follow_up.py`)

**Deliberate exception (NOT consolidated):** `client.py`'s narrow
`detect_claude_usage_cap` stays as-is — it raises the typed
`ClaudeUsageCapError` for gh-surfaced caps and must not catch GitHub/session
limits routed through the gh subprocess wrapper.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| ProjectHephaestus | PR #1092 — secondary rate limit detection and backoff | 10 new unit tests pass locally; CI pending at capture time |
| ProjectHephaestus | PR #1326 / issue #1321 — Claude session-limit 429 (tz-less) detection + resolver consolidation | verified-local: `detect_session_limit` + `resolve_quota_reset_epoch` verified at runtime against the literal message; 103 rate-limit + follow-up unit tests pass locally; CI pending at capture |
