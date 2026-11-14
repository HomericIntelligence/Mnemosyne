# Session Notes: CLI Deep Audit and Fix

## Source Context

| Field | Value |
| ------- | ------- |
| **Project** | ProjectScylla (`/home/<user>/Scylla2`) |
| **Branch** | `consolidate-run-command` |
| **File Audited** | `scripts/manage_experiment.py` |
| **Commit** | `554bfac fix(cli): Deep audit fixes for manage_experiment.py` |
| **Date** | 2026-02-24 |

## Audit Dimensions Covered (7 of 8)

The audit covered 7 of the 8 dimensions listed in SKILL.md:

1. **Bugs** — Found 1: `default=3600` in argparse competing with YAML config timeout
2. **Dead code** — Found 1: unused `pathlib` import removed
3. **Duplication** — Found 1: `MODEL_ALIASES` dict defined inline inside `resolve_model()`; extracted to module level
4. **Validation placement** — Found 1: path existence check inside `ThreadPoolExecutor` lambda moved before pool creation
5. **Error messaging** — 2 improvements: added missing path in `ArgumentTypeError`; clarified batch-failure message
6. **Exception safety** — Found 1: bare `raise RuntimeError(...)` changed to `raise RuntimeError(...) from e`
7. **Test coverage gaps** — Found: all existing timeout tests passed `--timeout` explicitly; no test exercised the fallback (omitting the flag)

Dimension **8 (argparse resolution)** overlaps significantly with dimension 1 (bugs) — the `default=3600` issue was the concrete instance of a broken argparse resolution pattern.

## Key Observation: Override Tests vs Fallback Tests

A recurring blind spot in the test suite was **asymmetric coverage**:

- Tests would verify "if I pass `--timeout 120`, the run uses 120 seconds" ✅
- But no test verified "if I omit `--timeout`, the YAML config value is used" ❌

This pattern means the config-layer fallback can silently break without failing any test. The fix
is to always write **both** variants whenever a CLI flag has a corresponding config-layer default:

```python
def test_timeout_override():
    # Pass --timeout explicitly; assert override wins
    ...

def test_timeout_fallback():
    # Omit --timeout; assert YAML/config default flows through
    ...
```

## Specific Code Changes (ProjectScylla)

### `scripts/manage_experiment.py`

```python
# Before: argparse default competed with config layer
parser.add_argument("--timeout", type=int, default=3600,
                    help="Per-subtest timeout in seconds")

# After: None sentinel; config layer sets actual default
parser.add_argument("--timeout", type=int, default=None,
                    help="Per-subtest timeout in seconds (default: from config or 3600)")
```

```python
# Before: MODEL_ALIASES inside function
def resolve_model(alias: str) -> str:
    MODEL_ALIASES = {"sonnet": "claude-sonnet-4-6", ...}
    ...

# After: module-level constant
MODEL_ALIASES: dict[str, str] = {
    "sonnet": "claude-sonnet-4-6",
    "opus": "claude-opus-4-6",
    "haiku": "claude-haiku-4-5-20251001",
}

def resolve_model(alias: str) -> str:
    ...
```

### `tests/unit/cli/test_manage_experiment.py`

12 new tests added covering:
- `test_model_aliases_constant` — validates MODEL_ALIASES keys/values directly
- `test_timeout_fallback_uses_config` — omits `--timeout`; asserts config value used
- `test_timeout_override_wins` — passes `--timeout`; asserts override wins
- `test_missing_config_file_exits_with_error` — asserts `SystemExit` with non-zero code
- `test_batch_validation_before_threadpool` — asserts validation errors surface before any thread starts
- ... (7 additional tests for other dimensions)

## Files in This Session

- `scripts/manage_experiment.py` — production changes
- `tests/unit/cli/test_manage_experiment.py` — test changes (+12 tests)
