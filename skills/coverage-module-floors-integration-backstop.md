---
name: coverage-module-floors-integration-backstop
description: "Enforce per-module coverage floors and integration tests for omitted modules. Use when: (1) aggregate coverage gates hide under-tested critical modules, (2) some modules are omitted from measurement (live orchestration, TTY), (3) need end-to-end backstop without false negatives."
category: testing
date: 2026-05-28
version: "1.0.0"
user-invocable: false
verification: verified-ci
tags: ["coverage", "testing", "module-floors", "integration-tests", "cobertura"]
---

# Coverage Module Floors + Integration Backstop

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-05-28 |
| **Objective** | Prevent aggregate coverage gates from masking under-tested modules; add end-to-end integration tests for omitted modules without false negatives from live CLI/TTY |
| **Outcome** | Implemented per-module floor enforcement (schema.py: 80%) + 16 integration tests for 10 omitted orchestration modules + guard test preventing silent allowlist growth |
| **Verification** | verified-ci (PR #643 auto-merged; all 36 new tests passing; per-module floor enforcement working end-to-end) |

## When to Use

- **Scenario 1**: Aggregate coverage passes (83%) but critical modules are under 60% (e.g., schema.py @ 56%)
- **Scenario 2**: Some modules intentionally omitted from coverage (live orchestration, external CLI, TTY interactions)
- **Scenario 3**: Need to verify omitted modules are still tested end-to-end without false negatives
- **Scenario 4**: Want to freeze the list of excluded modules and prevent silent growth

## Verified Workflow

### Quick Reference

```bash
# 1. Create coverage.toml with per-module thresholds (relative paths matching Cobertura XML)
cat > coverage.toml << 'EOF'
[module_floors]
"validation/schema.py" = 80

[omit_allowlist]
modules = [
  "agents", "automation", "ci", "cli", "config", "datasets",
  "discovery", "forensics", "github", "nats"
]
EOF

# 2. Parse Cobertura XML to extract per-file branch/line rates
# (ripgrep to find coverage.xml, parse class/method elements)
python -c "from hephaestus.ci.coverage import parse_module_coverage; \
  rates = parse_module_coverage('coverage.xml'); \
  print(f'schema.py: {rates.get(\"validation/schema.py\", {})}%')"

# 3. Integrate per-module floor check in main()
python -m hephaestus.ci.coverage --check-per-module-floors --config coverage.toml

# 4. Add unit tests for missing branches in critical modules
# Tests: resolve_schema fallback, schema-load errors, verbose output, --json

# 5. Create integration tests for omitted modules (importability + script smoke)
# test_orchestration_smoke.py: 16 tests (2 per omitted module)
# - importability: from hephaestus.module import submodule (no TTY)
# - script smoke: python -m hephaestus.module.script --help (exit 0)

# 6. Create guard test to freeze omit-list
# test_omit_allowlist.py: assert the 10-module set hasn't grown

# 7. Verify all tests pass and per-module enforcement working
pytest tests/unit -v --tb=short
```

### Detailed Steps

1. **Identify under-tested modules** masked by aggregate gates
   - Run coverage with aggregate report: `pytest --cov=hephaestus --cov-report=term-missing`
   - Search for modules with coverage < 70% (or your threshold)
   - Identify which are critical (validation logic, config parsing, etc.)

2. **Create coverage.toml with per-module thresholds**
   ```toml
   [module_floors]
   "validation/schema.py" = 80  # Relative path matching Cobertura XML format
   ```
   **CRITICAL**: Use relative paths (e.g., `validation/schema.py`) NOT full package paths (e.g., `hephaestus/validation/schema.py`). Cobertura XML reports paths relative to project root.

3. **Parse Cobertura XML to extract per-file coverage rates**
   - Cobertura XML already contains `<class name="...">` elements with `branch-rate` and `line-rate` attributes
   - Use `parse_module_coverage(coverage_xml_path)` to extract rates per file
   - Returns dict: `{"validation/schema.py": {"branch_rate": 0.56, "line_rate": 0.72}}`

4. **Integrate per-module floor check in main()**
   - Add check after aggregate gate passes
   - Read coverage.toml for per-module thresholds
   - Compare actual rates against configured floors
   - Fail loudly with clear message if any floor is breached: `"Module validation/schema.py: 56.0% branch rate < 80% floor"`
   - Exit with code 1 on failure

5. **Add unit tests for missing coverage in critical modules**
   - Identify uncovered branches in schema.py (e.g., resolve_schema fallback path, error handling)
   - Write 4-5 new tests: resolve_schema fallback, schema-load errors, verbose output, --json flag
   - Verify: new tests bring module to 80%+ coverage

6. **Create integration tests for omitted modules** (importability + script smoke)
   - Create `test_orchestration_smoke.py` with 16 tests (2 per omitted module)
   - **Tier 1 - Importability**: `from hephaestus.module import submodule` (no TTY, no live CLI)
   - **Tier 2 - Script smoke**: `subprocess.run(["python", "-m", "hephaestus.module.script", "--help"])` (exit 0)
   - Do NOT run scripts end-to-end (live TTY causes hangs); use `--help` only
   - Omitted modules: agents, automation, ci, cli, config, datasets, discovery, forensics, github, nats

7. **Create allowlist guard test**
   - File: `test_omit_allowlist.py`
   - Assert: the set of omitted modules has not grown
   - Rationale: silent growth of exclusions masks coverage drift
   - Example: `assert OMIT_ALLOWLIST == {"agents", "automation", "ci", ...}`

8. **Update existing coverage tests with isolated config**
   - Issue: test_coverage.py loads repo-level coverage.toml which has per-module floors
   - Solution: create `empty_config` pytest fixture that provides isolated coverage config
   - Apply fixture to all coverage tests to avoid test interference

9. **Verify end-to-end**
   - All 36 new tests pass (4 unit + 16 smoke + 12 coverage/allowlist)
   - Aggregate coverage unchanged (should stay ~82-83%)
   - Per-module enforcement verified: set floor=99% and verify exit code 1
   - No regressions in existing tests

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|---|---|---|
| Full package paths in coverage.toml | `"hephaestus/validation/schema.py"` | Cobertura XML reports relative paths `"validation/schema.py"`; path mismatch skipped floor check silently | Always match config paths to exact XML format; relative paths are canonical in coverage reports; test config by setting floor=99% and verifying it fails |
| test_coverage.py using repo config | Tests loaded repo-level coverage.toml with per-module floors | Test failures due to interference with actual thresholds; floors didn't match test scenario | Isolate test config with empty_config fixture; never let repo config leak into unit tests; parameterize fixtures by scenario |
| Full script execution in smoke tests | Tried `subprocess.run(["python", "-m", "hephaestus.agents.script"])` end-to-end | Live CLI interactions hang subprocess; test timeouts without capturing output | Use --help flag only for script smoke tests; importability tests sufficient for live modules; avoid TTY-dependent code paths in subprocess |
| Unguarded omit-list growth | Allowed omit_allowlist to grow without tracking | Silent growth of excluded modules over time; no visibility into what's omitted; coverage drift undetected | Create dedicated guard test that freezes module set; treat allowlist as a breaking change requiring explicit test update; document each exclusion with rationale |

## Results & Parameters

### Test Results
- **Total new tests**: 36 (4 schema.py unit + 16 orchestration smoke + 12 coverage/allowlist)
- **Aggregate coverage**: 82.87% (meets 80% gate)
- **Per-module enforcement**: verified working (floor=99% correctly exits 1)
- **Regressions**: none; all existing tests pass

### Configuration (coverage.toml)
```toml
[module_floors]
"validation/schema.py" = 80

[omit_allowlist]
modules = [
  "agents",
  "automation", 
  "ci",
  "cli",
  "config",
  "datasets",
  "discovery",
  "forensics",
  "github",
  "nats"
]
```

### Schema.py Unit Tests Added
1. **resolve_schema fallback**: Test missing schema → uses default resolution logic
2. **schema-load errors**: Test file not found, invalid YAML, malformed schema
3. **verbose output**: Test `--verbose` flag adds debug logging
4. **--json flag**: Test JSON schema output format is valid

### Orchestration Smoke Tests (16 total)
**Pattern**: 2 tests per omitted module
- `test_<module>_importable`: `from hephaestus.<module> import ...`
- `test_<module>_script_help`: `python -m hephaestus.<module>.script --help`

**Modules**: agents, automation, ci, cli, config, datasets, discovery, forensics, github, nats

### Omit-Allowlist Guard Test
```python
def test_omit_allowlist_frozen():
    """Prevent silent growth of coverage exclusions."""
    assert OMIT_ALLOWLIST == {
        "agents", "automation", "ci", "cli", "config",
        "datasets", "discovery", "forensics", "github", "nats"
    }
```

### Cobertura XML Path Format Reference
```xml
<classes>
  <class name="hephaestus.validation.schema" filename="validation/schema.py" branch-rate="0.56" line-rate="0.72">
    <!-- branch-rate and line-rate are decimals 0.0-1.0, multiply by 100 for percentage -->
  </class>
</classes>
```

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| ProjectHephaestus | Issue #623: Per-module coverage floor + orchestration backstop | PR #643; all 36 tests passing; CI verified; auto-merged |
