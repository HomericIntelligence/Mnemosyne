---
name: cli-validator-fail-closed-tool-policy-separation
description: "Design batch file validators so incomplete inspection fails closed without changing successful helper return types, while CLI output separates tool errors from policy violations. Use when: (1) discovery, stat, read, decode, size, or parse failures can currently look clean, (2) an empty discovered inventory should fail unless narrowly allowed, (3) public list-returning helpers need backward-compatible success behavior, or (4) human and JSON output must expose operational failures separately from policy findings."
category: tooling
date: 2026-08-06
version: "1.0.0"
user-invocable: false
verification: unverified
tags:
  - validator
  - fail-closed
  - cli
  - file-discovery
  - yaml
  - typed-errors
  - policy-violations
  - json-compatibility
  - empty-inventory
  - python
---

# Fail-Closed Batch Validators with Separate Tool and Policy Results

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-08-06 |
| **Objective** | Prevent a batch file validator from reporting clean when target discovery or file inspection is incomplete, without breaking successful public helper returns or established machine-readable fields. |
| **Outcome** | A behavior-first design was produced: private detailed results support CLI aggregation; public list-returning helpers raise a typed exception only when inspection is incomplete; empty inventories are policy violations; and tool errors remain distinct from policy findings. |
| **Verification** | unverified — this workflow was derived from an implementation plan and was not executed end to end in this session. |

## When to Use

- A validator catches file-system, decoding, dependency, or parser failures and returns an empty
  finding list, prints a warning, skips the target, or otherwise permits a false-clean result.
- A CLI accepts multiple files or directories and must report all discoverable failures in one
  run instead of stopping at the first error.
- Existing public helpers return a simple collection such as `list[Violation]` or `list[Path]`
  on success, and changing them to a result object would unnecessarily break callers.
- An empty directory or successfully enumerated target set should be a policy failure by default,
  while an explicit `--allow-empty` option is needed for a narrow workflow.
- JSON consumers depend on legacy fields, but new output must distinguish policy findings from
  operational/tool failures.
- Human output needs stable category labels and separate stdout/stderr channels.

## Proposed Workflow

> **Warning:** This workflow has not been validated end-to-end. Treat it as a hypothesis until
> implementation tests and CI confirm it.

### Quick Reference

```python
class ToolError(NamedTuple):
    target: Path
    code: str
    message: str


class ValidationIncompleteError(RuntimeError):
    def __init__(self, errors: list[ToolError]) -> None:
        self.errors = tuple(errors)
        super().__init__(
            "; ".join(f"{error.target}: {error.message}" for error in errors)
        )


def validate_file(path: Path) -> list[Violation]:
    result = _validate_file_detailed(path)
    if result.tool_errors:
        raise ValidationIncompleteError(result.tool_errors)
    return result.violations
```

The compatibility rule is:

```text
complete inspection + no findings  -> existing empty-list return
complete inspection + findings     -> existing populated-list return
incomplete inspection              -> typed exception from public helper
CLI batch                           -> aggregate policy findings and tool errors
```

### Detailed Steps

1. **Write the result-state matrix before implementation.** Distinguish at least:

   - complete and policy-clean;
   - complete with policy violations;
   - incomplete discovery;
   - incomplete file inspection;
   - successfully enumerated empty inventory.

   Only the first state may produce a clean verdict by default.

2. **Preserve successful public contracts.** Keep existing public helpers returning their
   established list types after complete inspection. Introduce a typed exception containing
   immutable error records for incomplete work. This makes the intentional failure-contract
   change inspectable without forcing every successful caller to consume a new tuple or result
   object.

3. **Add private detailed-result helpers for aggregation.** Use private collection and validation
   result records containing both ordinary findings and tool errors. The CLI calls these private
   helpers so one broken target does not prevent validation of other discovered files. Public
   wrappers call the same helpers and raise when `tool_errors` is nonempty.

4. **Make discovery explicit and fail closed.** For every requested target:

   - call `stat()` once and retain its mode;
   - classify regular files and directories from that mode;
   - reject unsupported file types with a stable code;
   - catch directory enumeration failures;
   - preserve deterministic extension ordering;
   - resolve paths for deduplication and report resolution failures;
   - never convert a failed probe into an empty inventory.

5. **Validate the whole file boundary before applying policy.** In order:

   - verify the parser dependency is available;
   - `stat()` the file and reject it when the size limit is exceeded;
   - read as the required encoding;
   - distinguish read failures from decode failures;
   - parse the document and distinguish syntax errors;
   - reject empty documents;
   - reject an invalid top-level shape;
   - only then run the policy checks.

   Returning zero policy findings is trustworthy only after all of these steps complete.

6. **Use stable machine-readable error codes.** Keep codes independent of exception prose so
   tests, JSON consumers, and operators can rely on them. A representative taxonomy is:

   ```text
   dependency_unavailable
   target_stat_error
   directory_read_error
   unsupported_target
   target_resolve_error
   stat_error
   oversized
   read_error
   decode_error
   yaml_parse
   empty_document
   invalid_document
   ```

   Use distinct discovery-time and validation-time stat codes because their remedies and test
   arrangements differ.

7. **Classify an empty inventory only after successful discovery.** Define:

   ```python
   empty_inventory = not workflow_files and not collection.tool_errors
   ```

   Add an `empty_inventory` policy violation unless `--allow-empty` is present. The flag must
   suppress only that policy finding; it must never suppress missing targets, unreadable
   directories, resolution failures, or file-validation errors.

8. **Aggregate both categories before deriving status.** Continue validating readable files even
   if another target produced a tool error. Derive the CLI result from the union:

   ```python
   exit_code = 1 if tool_errors or policy_violations else 0
   ```

   Never print a success summary while either collection is nonempty.

9. **Evolve JSON additively.** Preserve the established envelope and the exact meaning of legacy
   fields. Add category-specific counts and arrays instead of renaming or repurposing an existing
   count:

   ```json
   {
     "status": "error",
     "exit_code": 1,
     "files_checked": 2,
     "violation_count": 1,
     "policy_violation_count": 1,
     "tool_error_count": 1,
     "policy_violations": [{"code": "checkout_order"}],
     "tool_errors": [{"code": "yaml_parse"}]
   }
   ```

10. **Separate human-output channels by meaning.** Print policy violations to stdout and tool
    errors to stderr. Prefix both with stable labels:

    ```text
    POLICY VIOLATION [<code>]: ...
    TOOL ERROR [<code>]: ...
    ```

11. **Drive the implementation with boundary tests.** Test every code directly through the public
    exception contract and again through the CLI. Monkeypatch `Path.stat`, `Path.glob`,
    `Path.resolve`, and `Path.open` at the narrow target needed for each branch. For a
    validation-time stat failure, pass a directory and fail `stat()` only for the file yielded
    by enumeration so the discovery-time probe still succeeds.

12. **Lock compatibility and mixed-output behavior.** Add tests proving:

    - valid re-exported helpers still return lists;
    - malformed and policy-violating files are both reported in one invocation;
    - human output uses the correct channel for each category;
    - JSON retains the legacy count while adding category data;
    - default empty inventory fails;
    - `--allow-empty` permits only a successfully enumerated empty inventory.

## Verified Workflow

No workflow is verified yet. Promote the proposed workflow only after the implementation's
focused regression suite passes; use `verified-local` for local evidence and `verified-ci`
after CI confirms the exact change.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| ------- | -------------- | ------------- | -------------- |
| Return an empty finding list after an exception | Missing parser dependencies, stat failures, read failures, oversized files, or malformed documents were treated like policy-clean files | The caller could not distinguish completed validation from incomplete work | A clean list is valid only after complete inspection; raise a typed incomplete-validation exception at the public boundary |
| Warn and skip failed targets | Discovery or validation errors were printed while the batch continued and eventually exited successfully | Human-visible warnings do not make an automated gate fail closed | Aggregate stable tool-error records and include them in exit-status calculation |
| Change public helpers to return detailed result tuples | Replaced simple list returns everywhere to expose errors | Successful callers would incur a breaking migration even though only failure behavior needed to change | Keep detailed records private; preserve successful list returns and change only the incomplete-work path |
| Treat no discovered files as success | An empty directory produced zero findings and exit zero | A misconfigured target path or unexpectedly empty checkout could silently disable the gate | Make successfully enumerated emptiness an explicit policy violation |
| Let `--allow-empty` suppress all failures | Used one broad bypass around discovery and validation | The opt-in could hide missing, unreadable, or malformed targets | Suppress only `empty_inventory` after error-free discovery |
| Put every failure into one violations list | Operational failures and policy findings shared one category | Operators could not tell whether content violated policy or the tool lacked enough evidence to decide | Model and render tool errors separately from policy violations |
| Replace the legacy JSON violation count | Reinterpreted the existing field as all failure categories | Existing consumers could observe a silent semantic break | Preserve the old field and meaning; add new counts and arrays |
| Probe targets repeatedly with `is_file()` and `is_dir()` | File type was inferred through multiple convenience-method calls | Multiple filesystem probes can disagree or fail at different times, obscuring which inspection failed | Use one explicit `stat()` result and classify its mode |

## Results & Parameters

### Contract Matrix

| Condition | Public helper | CLI category | Default exit |
| --------- | ------------- | ------------ | ------------ |
| Complete, no policy findings | Existing empty list | None | 0 |
| Complete, policy findings | Existing populated list | Policy violation | 1 |
| Discovery incomplete | Typed exception | Tool error | 1 |
| File inspection incomplete | Typed exception | Tool error | 1 |
| Enumeration complete, inventory empty | Existing empty collection helper result | `empty_inventory` policy violation | 1 |
| Enumeration complete, inventory empty, `--allow-empty` | Existing empty collection helper result | None | 0 |
| Tool error plus `--allow-empty` | Typed exception | Tool error | 1 |

### Minimum Regression Matrix

```yaml
public_contract:
  - valid_collection_returns_list
  - valid_validation_returns_list
  - typed_exception_exposes_all_errors
discovery:
  - target_stat_error
  - directory_read_error
  - unsupported_target
  - target_resolve_error
validation:
  - dependency_unavailable
  - stat_error
  - oversized
  - read_error
  - decode_error
  - yaml_parse
  - empty_document
  - invalid_document
inventory:
  - empty_fails_by_default
  - allow_empty_succeeds
  - allow_empty_does_not_hide_tool_error
output:
  - human_channel_separation
  - json_category_separation
  - legacy_json_fields_preserved
```

### Verification Commands

```bash
<project-test-command> <focused-validator-tests> -v
<project-test-command> <complete-validator-test-module> -v
<project-lint-command> <validator-module> <validator-tests>
<project-typecheck-command> <validator-module> <validator-tests>
```

Expected successful evidence:

- every listed failure boundary has a direct public-helper test and a CLI nonzero-exit test;
- mixed inputs expose both categories in one run;
- the old JSON fields retain their established values;
- no success summary is emitted for a tool error or policy violation.

## Verified On

| Project | Context | Details |
| ------- | ------- | ------- |
| ProjectHephaestus | Proposed hardening of the workflow checkout-order validator | Architecture and behavior-first test matrix supplied; implementation and CI evidence pending. |

## References

- [CLI input-file pre-validation](cli-input-file-prevalidation.md) — adjacent parse-time diagnostics for a single explicit input path.
- [Explicit config paths fail closed](config-explicit-path-fail-closed.md) — adjacent explicit-path versus auto-discovery semantics.
- [Subprocess JSON result validation](tooling-subprocess-json-fail-closed-result-validation.md) — adjacent fail-closed handling for external tool output.
- [Vulnerability scanner evidence validation](vulnerability-scanner-evidence-fail-closed-validation.md) — adjacent separation of report validity from policy classification.
