---
name: testing-date-bomb-hardcoded-timestamp-future-failure
description: "Identifies and fixes 'date bomb' tests — time-dependent assertions using hardcoded epochs or calendar dates that pass when written but fail after a fixed window elapses. Use when: (1) a test suddenly fails in CI with no code changes, (2) reviewing tests that reference specific calendar dates or hardcoded Unix timestamps, (3) a test asserts a parsed time value is within N seconds of a literal constant."
category: testing
date: 2026-05-10
version: "1.0.0"
user-invocable: false
verification: verified-ci
tags: []
---

# Testing: Date Bomb — Hardcoded Timestamp Future Failure

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-05-10 |
| **Objective** | Fix a CI test that suddenly began failing weeks after it was written, with no code changes |
| **Outcome** | PR #367 merged green; test is now temporally reflexive and will not rot |
| **Verification** | verified-ci |

## When to Use

- A test was passing in CI for weeks or months and suddenly fails with no code changes
- A test asserts time or date relationships against hardcoded epochs or specific calendar dates
- Reviewing tests that mention specific calendar dates ("May 8", "2026-05-09") in fixtures or assertions
- Pre-commit review of date-related tests for time-dependent assertions using literal constants
- A test error mentions a large delta between `now` and an expected timestamp

## Verified Workflow

### Quick Reference

```python
# BAD — date bomb (passes today, fails after the fixed window passes)
def test_parses_date_qualified_form():
    parsed = parse_date_string("May 8, 5pm")
    expected_epoch = 1778284800  # May 8, 2026 5pm UTC — hardcoded!
    assert abs(parsed - expected_epoch) < 86400  # 24h tolerance

# GOOD — dynamic future date (temporally reflexive)
from datetime import datetime, timedelta, timezone

def test_parses_date_qualified_form():
    now = datetime.now(timezone.utc)
    future = now + timedelta(days=2)
    input_str = future.strftime("%B %-d, %-I%p").lower()  # e.g., "may 12, 4pm"
    expected_epoch = future.timestamp()
    parsed = parse_date_string(input_str)
    assert abs(parsed - expected_epoch) < 86400
```

### Detailed Steps

1. **Identify the date bomb** — Look for hardcoded Unix timestamps or string literals referencing specific dates in test fixtures, `assert` statements, or helper constants. Grep for patterns like `178\d{7}`, `assert abs(parsed -`, or strings like `"May \d"` in test files.

2. **Understand the parser under test** — Determine what relative reference point the parser uses (e.g., "next occurrence of May 8" anchored to `now`). The test's expected value must be derived from the same anchor.

3. **Generate input and expected value from `now`** — Pick an offset (e.g., `now + timedelta(days=2)`) that stays consistently in the "future" window the parser expects. Format the offset as the input string using the same format the parser accepts.

4. **Assert against the same dynamic value** — The assertion `abs(parsed - expected_epoch) < 86400` is now valid indefinitely because both sides come from `datetime.now()` in the same test run.

5. **Verify no other tests in the file share the same hardcoded constant** — Search for the literal epoch value across the test file; fix every occurrence in the same PR.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| 1 | Hardcode timestamp `1778284800` ("May 8, 2026 5pm UTC") with 24-hour tolerance | Test passed initially. After ~2 days, `now` drifted past the 24-hour window and the assertion failed. The "date bomb" detonated as time advanced. | Hardcoded timestamps in time-dependent tests have an implicit expiration date. They are time bombs. |
| 2 | Increase tolerance from 24 hours to 7 days | Defers the failure by ~5 days but does not eliminate it; tests still rot over time and require periodic manual updates | Tolerance widening is a band-aid. The correct fix is to make the test temporally reflexive — generate the input *and* the expected value from `now()` so they always match regardless of when the test runs. |

## Results & Parameters

**Root cause (PR #367, HomericIntelligence/ProjectHephaestus):**

File: `tests/unit/github/test_rate_limit.py`
Test: `TestDetectClaudeUsageCap::test_parses_date_qualified_form`

The test hardcoded the input string `"May 8, 5pm"` along with epoch `1778284800` and asserted the parsed result was within 86400 seconds. This worked the day it was written but detonated once the system clock moved more than 24 hours past May 8, 2026 5pm UTC.

**Detection grep patterns:**
```bash
# Find hardcoded Unix timestamps in test files (2025–2027 range)
grep -rn "17[6-9][0-9]\{7\}\|18[0-2][0-9]\{7\}" tests/

# Find 24h/7d tolerance assertions
grep -rn "abs(.*parsed.*-.*[0-9]\{10\})" tests/

# Find calendar date literals in test strings
grep -rn '"[A-Z][a-z]* [0-9]\{1,2\},\? [0-9]\{1,2\}[ap]m"' tests/
```

**Template for any relative-date parser test:**
```python
from datetime import datetime, timedelta, timezone

def test_parses_<unit>_relative():
    now = datetime.now(timezone.utc)
    target = now + timedelta(<offset>)
    input_str = target.strftime("<format>")
    expected = target.timestamp()
    parsed = parse_date_string(input_str)
    assert abs(parsed - expected) < <tolerance_seconds>
```

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| ProjectHephaestus | PR #367 — test_rate_limit.py hardcoded epoch | verified-ci, merged green |
