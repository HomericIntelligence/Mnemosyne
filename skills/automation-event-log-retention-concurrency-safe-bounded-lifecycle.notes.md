# ProjectHephaestus Event-Log Retention Planning Notes

## Scope captured

The supplied objective was to add bounded lifecycle management for the automation loop's
default pipeline JSONL event logs. The proposed controls are a 30-day age limit and a 100-log
count limit, each independently disabled by `0`. Cleanup must support dry-run previews, protect
active logs across concurrent runs, emit warnings for failures, and never affect pipeline routing
or exit status.

No implementation or verification was performed during this `/learn` session. The local
ProjectHephaestus checkout did not contain `event_log_retention.py` or either retention flag when
inspected on 2026-08-06, and its `main` worktree reported that it was behind `origin/main`.
Consequently, all workflow material in the main skill is intentionally marked `unverified`.

## Proposed source ownership

- `hephaestus/automation/loop_runner.py` creates the default path and dispatches
  `run_pipeline()`. It should own the lifecycle context and expose the CLI/config values.
- `hephaestus/automation/pipeline/coordinator_runtime.py` currently performs best-effort event
  appends. It should remain append-only and should not own cleanup.
- `hephaestus/utils/file_lock.py` already exposes a POSIX advisory `file_lock()` context manager,
  `LockUnavailableError`, non-blocking acquisition, and `require_exclusive=True`. Reuse it rather
  than adding a dependency or another lock implementation.
- `hephaestus/automation/pipeline/stages/finished.py` contains the established
  `[dry-run] would remove ...` message convention.

## Proposed files

Create:

- `hephaestus/automation/event_log_retention.py`
- `tests/unit/automation/test_event_log_retention.py`

Modify:

- `hephaestus/automation/loop_runner.py`
- `tests/unit/automation/test_loop_runner.py`
- `tests/unit/automation/pipeline/test_pipeline_flag.py`
- `docs/observability.md`
- `docs/architecture.md`

No dependency, schema migration, or ADR was proposed.

## Proposed public behavior

```python
DEFAULT_EVENT_LOG_RETENTION_DAYS = 30
DEFAULT_EVENT_LOG_RETENTION_COUNT = 100

with event_log_lifecycle(
    config.event_log_path,
    retention_days=cfg.event_log_retention_days,
    retention_count=cfg.event_log_retention_count,
    dry_run=cfg.dry_run,
):
    return run_pipeline(config)
```

Proposed CLI controls:

```text
--event-log-retention-days <non-negative-int>
--event-log-retention-count <non-negative-int>
```

The recognized namespace is proposed as:

```regex
pipeline-events-(?P<timestamp>\d{8}T\d{6}Z)-(?P<pid>[1-9]\d*)\.jsonl
```

The timestamp must also parse as a valid UTC instant. JSON content is deliberately not parsed.

## Proposed test inventory

- age expiry plus exact-cutoff retention;
- oldest-first count enforcement;
- combined age-then-count behavior;
- unrelated names, malformed timestamps/PIDs, directories, and symlinks;
- current and concurrent active-log locks;
- temporary count-cap excess when active logs cannot be deleted;
- dry-run preview without unlink;
- per-file unlink failure warning plus continuation;
- cleanup-lock and current-lock failure remaining nonfatal;
- both limits disabled with zero;
- CLI defaults, custom values, and rejection of negative values;
- lifecycle wrapping `run_pipeline()` for every coordinator exit path.

Proposed focused commands from the supplied design:

```bash
uv run pytest tests/unit/automation/test_loop_runner.py \
  tests/unit/automation/pipeline/test_pipeline_flag.py -v

uv run pytest tests/unit/automation/test_event_log_retention.py -v

uv run pytest \
  tests/unit/automation/test_event_log_retention.py::test_active_log_is_not_removed_by_concurrent_cleanup \
  tests/unit/automation/test_event_log_retention.py::test_only_recognized_regular_logs_are_candidates -v

uv run pytest \
  tests/unit/automation/test_event_log_retention.py::test_unlink_failure_is_logged_and_lifecycle_continues -v
```

These commands were captured as acceptance commands only; they were not run in this session.
