---
name: bisect-pytest-oom-with-ulimit
description: "Diagnose which specific pytest test causes an OOM by capping virtual memory with `ulimit -v` BEFORE invocation, so the OOM-killer reaps only pytest (yielding a MemoryError traceback) instead of the parent shell. Use when: (1) a pytest run kills the shell, freezes WSL, or 'just disappears' with no traceback, (2) you see `exit=137` (SIGKILL) from pytest, (3) tee'd log files end up zero-bytes because the writer was reaped, (4) you suspect a single test allocates excessive memory but can't tell which."
category: debugging
date: 2026-05-15
version: "1.0.0"
user-invocable: false
tags:
  - pytest
  - oom
  - ulimit
  - bisection
  - memory-leak
  - wsl2
  - debugging
  - tracemalloc
---

# Bisect Pytest OOM with ulimit

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-05-15 |
| **Objective** | Identify the specific pytest test that triggers an OOM-killer event so the leak can be fixed |
| **Outcome** | Verified-CI: successfully pinpointed a runaway `while True: print(...); time.sleep(1)` loop (with `time.sleep` mocked) on ProjectHephaestus PR #412 |

## When to Use

- A pytest run kills the shell, freezes WSL2, or "just disappears" with no traceback
- You see `exit=137` (SIGKILL by OOM-killer) from a pytest invocation
- Tee'd log files survive as zero-byte files because the writer was reaped before flush
- You suspect a single unit test allocates excessive memory but cannot identify it
- You need to diagnose a runaway loop, print spam, or unbounded allocation in a unit test

## Verified Workflow

### Quick Reference

```bash
# Phase 1: cap pytest memory BEFORE invocation
ulimit -v 4194304   # 4 GiB virtual memory cap (per pytest process)
ulimit -t 180       # 180 CPU-seconds — kills a runaway tight loop

# Phase 2: bisect at file granularity (-v prints test IDs; last printed = culprit)
pixi run pytest tests/unit/foo/test_a.py --no-cov --cov-fail-under=0 -p no:cacheprovider -v 2>&1 | tee /tmp/diag-a.log

# Phase 3: pinpoint individual test
pixi run pytest tests/unit/foo/test_b.py::TestClass::test_method --no-cov --cov-fail-under=0 -p no:cacheprovider -v 2>&1 | tail -50

# Phase 4: peak-memory profile of the offender
ulimit -v 4194304; ulimit -t 60
/usr/bin/time -v pixi run pytest "<offending-test-id>" --no-cov -p no:cacheprovider -v -s 2>&1 | tail -30
```

### Detailed Steps

1. **Cap memory in the shell BEFORE invoking pytest.** Set `ulimit -v 4194304` (4 GiB virtual memory) and `ulimit -t 180` (CPU-seconds). These inherit into pytest and any subprocess it spawns. When pytest exceeds the cap, Python raises `MemoryError` inside the normal teardown path instead of being SIGKILL'd by the kernel — you get a real traceback.

2. **Bisect at file granularity.** Run each test file alone with `-v` and `tee` the output. The LAST printed test ID before the cap fires is the offender (the test in progress when allocation exceeded the limit). Critical flags:
   - `--no-cov --cov-fail-under=0` — disables `pytest-cov` (often forced via `addopts` in `pyproject.toml`); coverage adds memory pressure that masks the real leak.
   - `-p no:cacheprovider` — prevents pytest from writing `.pytest_cache` which can pollute diagnosis.
   - `-v` — prints each test ID as it runs.

3. **Pinpoint with single-test runs.** Once the file is known, run individual `file::Class::method` IDs with `-v -s` and `tail` the output to see the traceback.

4. **Loop over every collected test (when manual pinpointing is too slow).** Use a while-read loop with `timeout` and a case statement on exit code: `0=PASS`, `124=TIMEOUT`, `137=OOM` (only seen if ulimit not set), other=`FAIL`.

5. **Get a peak-memory profile.** Use `/usr/bin/time -v` and look at `Maximum resident set size (kbytes)` — should match the cap if it OOMed.

6. **Attribute to a line with tracemalloc.** Reproduce the test logic OUTSIDE pytest under `python -X tracemalloc=10`, call `tracemalloc.take_snapshot().statistics('lineno')`, and print the top allocators. The top sites tell you exactly what's leaking.

### Bulk loop snippet

```bash
pixi run pytest <file> --collect-only -q --no-cov --cov-fail-under=0 | grep '::' > /tmp/tests.lst
while read -r t; do
  printf '%s ... ' "$t"
  timeout 30 pixi run pytest "$t" --no-cov --cov-fail-under=0 -p no:cacheprovider -q > /tmp/one.log 2>&1
  case $? in
    0)   echo PASS ;;
    124) echo TIMEOUT ;;
    137) echo OOM ;;        # SIGKILL — only happens if ulimit not set
    *)   echo "FAIL($?)" ;;
  esac
done < /tmp/tests.lst | tee /tmp/per-test.txt
```

### Tracemalloc snippet (OUTSIDE pytest)

```bash
pixi run python -X tracemalloc=10 - <<'PY'
import tracemalloc
tracemalloc.start()
# ... reproduce the test logic ...
cur, peak = tracemalloc.get_traced_memory()
print(f"current={cur/1e6:.1f}MB peak={peak/1e6:.1f}MB")
for s in tracemalloc.take_snapshot().statistics('lineno')[:5]:
    print(s)
PY
```

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Watch terminal | Running `pixi run pytest tests/unit -v` without ulimit, watching which test runs last | OOM-killer reaped the parent shell too; terminal disappeared with no output | Always set `ulimit -v` BEFORE pytest so the kernel kills only pytest |
| Trust tee logs | Piping pytest output to `tee /tmp/diag.log` and reading the file post-mortem | Under WSL2 the buffered file ended up zero bytes — writer was reaped before flush | tee is not OOM-safe; rely on ulimit to keep pytest's own stderr alive |
| Delete suspect tests | Removing tests by deletion before isolating the culprit | Destroyed evidence and made bisection impossible | Always isolate first, fix second; never delete diagnostic targets |
| Reduce parallelism | Lowering `-n` for pytest-xdist | Most projects don't use xdist; serial execution alone doesn't bound peak RSS | Parallelism is orthogonal to a single-test memory leak |
| Rely on `--tb=long` | Hoping pytest's long traceback would show the leak | The traceback is unreachable if the kernel SIGKILLs before Python unwinds | Kernel SIGKILL is uncatchable; convert it to MemoryError via ulimit |

## Results & Parameters

### Configuration

```bash
# Recommended caps for a typical unit-test suite
ulimit -v 4194304   # 4 GiB virtual memory per process (adjust to ~50% of host RAM)
ulimit -t 180       # 180 CPU-seconds per process

# Pytest flags for clean diagnosis
PYTEST_DIAG_FLAGS="--no-cov --cov-fail-under=0 -p no:cacheprovider -v"
```

### Expected Output

- Successful diagnosis: pytest emits a `MemoryError` traceback ending in the offending test's call stack, AND the shell stays alive.
- `/usr/bin/time -v` output's `Maximum resident set size (kbytes)` field equals the `ulimit -v` cap (in KiB) when the cap fired.
- `tracemalloc` top-N output names the source file + line of the dominant allocator (e.g. 27 MB of identical print strings from a `while True: print(...); time.sleep(1)` loop).

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| ProjectHephaestus | PR #412 — pinpointed `tests/unit/github/test_rate_limit.py::TestGhCallRateLimitFromStdout::test_raises_after_exhausting_retries` as the 4 GiB allocator; root cause was a `while True: print(...); time.sleep(1)` loop with `time.sleep` mocked, generating 27 MB of `[INFO] Rate limit resets in 00:59:59` strings | Verified-CI 2026-05-15 |

## References

- [pytest-coverage-fail-under-partial-run-trap](pytest-coverage-fail-under-partial-run-trap.md)
- [ci-pytest-pip-install-pyproject-addopts-trap](ci-pytest-pip-install-pyproject-addopts-trap.md)
- [e2e-claude-cli-pipeline-oom-fixes](e2e-claude-cli-pipeline-oom-fixes.md)
- [Python tracemalloc docs](https://docs.python.org/3/library/tracemalloc.html)
- [Linux ulimit(1)](https://man7.org/linux/man-pages/man1/ulimit.1p.html)
