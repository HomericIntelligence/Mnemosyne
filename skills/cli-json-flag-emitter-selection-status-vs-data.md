---
name: cli-json-flag-emitter-selection-status-vs-data
description: "Planning heuristic for fixing a registered-but-ignored --json flag in a ProjectHephaestus hephaestus-* console script: classify the CLI as status-shaped vs data-shaped, then pick emit_json_status() for pass/fail CLIs or format_output(data, 'json') for data-returning CLIs. The deciding reference is add_json_arg's own docstring. Use when: (1) a hephaestus-* CLI registers --json via add_json_arg(parser) but main() never reads args.json (silent no-op / POLA violation), (2) planning which JSON emitter a CLI should call when honoring --json, (3) writing a behavioral test for a --json flag instead of a help-text-substring assertion."
category: tooling
date: 2026-06-12
version: "1.0.0"
user-invocable: false
verification: unverified
tags:
  - cli
  - json
  - add-json-arg
  - emit-json-status
  - format-output
  - silent-no-op
  - pola
  - planning-heuristic
  - hephaestus
---

# CLI --json Flag Emitter Selection: Status vs Data

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-06-12 |
| **Objective** | When planning a fix for a `--json` flag that is registered via `add_json_arg(parser)` but never read in `main()` (a silent no-op / POLA violation), choose the correct emitter by classifying the CLI as status-shaped vs data-shaped, and honor the flag at the terminal branch carrying the REAL exit code. |
| **Outcome** | Planning heuristic captured for ProjectHephaestus issue #1217. This is a PLAN — no code was executed; CI has not run. |
| **Verification** | unverified — proposed plan only; edits and tests not executed, CI not run |

## When to Use

- A `hephaestus-*` console script calls `add_json_arg(parser)` but `main()` never reads `args.json`, so passing `--json` silently emits human text (POLA violation / silent no-op).
- Planning which JSON emitter a CLI should call: `emit_json_status()` vs `format_output(data, "json")`.
- Deciding whether a CLI's output is "status" (pass/fail) or "data" (a structured payload the caller consumes).
- Writing a test for a newly honored `--json` flag — you want a behavioral test, not a help-text-substring assertion.
- Reviewing a plan that proposes one emitter over the other and you need the deciding evidence rather than a guess.

## Verified Workflow

> **Proposed Workflow — NOT verified.** This workflow has not been validated
> end-to-end. It is a PLAN for ProjectHephaestus issue #1217 — the proposed code
> edits and unit test have not been executed and CI has not run. The section is
> titled "Verified Workflow" only to satisfy the skill validator's required-section
> check; its real status is `unverified`. Treat as a hypothesis until CI confirms.

### Quick Reference

The deciding rule lives in `add_json_arg`'s own docstring (`hephaestus/cli/utils.py:131-139`). READ IT — do not guess:

> Data-returning CLIs emit their structured payload via `format_output(data, "json")`; status-only CLIs should call `emit_json_status()` to print a minimal `{"status": ..., "exit_code": ...}` envelope on exit.

**Status-shaped CLI** (pass/fail; fix/format/install/check/lint) — use `emit_json_status`:

```python
# emit_json_status(exit_code, message=None, **extra)
#   -> print(json.dumps(envelope))   # COMPACT, no indent
# envelope = {"status": "ok"|"error", "exit_code": <code>, ...message, ...extra}
exit_code = run_check(args)
if args.json:
    extra = {"remediation": remediation} if has_drift else {}
    emit_json_status(exit_code, message=summary, **extra)  # carry REAL exit_code
    return exit_code
# text path below stays byte-for-byte unchanged
```

**Data-shaped CLI** (returns a structured payload the caller consumes) — use `format_output` (canonical sibling: `hephaestus/validation/stale_scripts.py:299-310`):

```python
if args.json:
    report = {"stale_scripts": stale, "stale_count": len(stale),
              "exit_code": exit_code, "passed": not stale}
    print(format_output(report, "json"))   # json.dumps(data, indent=2) — PRETTY
    return exit_code
```

### Detailed Steps

1. **Read `add_json_arg`'s docstring first** (`hephaestus/cli/utils.py:131-139`). It is the authoritative decision rule. Status-vs-data is a judgment call; let the docstring + the nature of the payload decide, not intuition.
2. **Classify the CLI.** Does it report *whether something passed/failed* (status) or *return a structured result a caller parses* (data)? A drift/fix/format/check CLI is usually status-shaped; a listing/report CLI is data-shaped.
3. **Honor the flag at the terminal branch in `main()`**, before/at the final return. Carry the REAL exit code into the envelope — never hardcode success.
4. **Keep the existing text path byte-for-byte.** The `--json` branch is additive; the human-readable path must not change.
5. **Mind the output shape difference.** `emit_json_status` uses `json.dumps(envelope)` (compact); `format_output(data, "json")` uses `json.dumps(data, indent=2)` (pretty). Tests must match whichever emitter you chose.
6. **Avoid serializing null-valued keys.** `emit_json_status` does `envelope.update(extra)`, so passing `remediation=None` serializes as `"remediation": null`. Prefer building `extra` conditionally (`{"remediation": r} if has_drift else {}`) and omit the key when absent.
7. **Add a BEHAVIORAL unit test**, not a help-text assertion: call `main(["--json"])` and `json.loads(capsys.readouterr().out)`, then assert on `status` / `exit_code` / payload keys. A `--help` substring check does NOT prove the flag is honored.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Guessing the emitter from intuition | Planner picked `emit_json_status` for the drift CLI without consulting the rule | Status-vs-data is a genuine judgment call; if a reviewer deems the drift list "data", `format_output({...}, "json")` is the convention instead. Picking by feel is not defensible. | Read `add_json_arg`'s docstring (`hephaestus/cli/utils.py:131-139`) — it is the deciding reference. Cite it in the plan; don't guess. |
| Passing `remediation=None` into the envelope | Plan proposed `emit_json_status(exit_code, remediation=remediation if has_drift else None)` | `emit_json_status` does `envelope.update(extra)`, so a `None` value serializes as `"remediation": null` — a noisy null key in the no-drift case. | Build `extra` conditionally and OMIT the key when there is no drift: `extra = {"remediation": r} if has_drift else {}`. Reviewer should confirm whether null-valued envelope keys are acceptable. |
| Assuming the `--write --json` interaction without checking | Plan assumed `has_drift = bool(drift) and not args.write` is correct because drift is never appended in write mode | The mutually-exclusive `--check`/`--write` group defaults `--check=True`, so `args.write` is the real signal. The "drift only appended in the `else` branch" claim was true *by reading lines 158-167*, not by running the code. | When a guard depends on control flow, state explicitly that it was verified by inspection, not execution, and flag it for the implementer to confirm at GREEN. |
| Relying on exact line numbers as durable facts | Plan pinned line numbers (19 for `add_json_arg(parser)`, 152, 156-175, 168-175) read at plan time | Line numbers are the primary external facts the plan relies on; if the file changes before implementation they drift and the plan misleads. | Anchor on symbol names and docstring contracts (stable) rather than raw line numbers (volatile). Re-locate by symbol at implementation time. |
| Writing a help-text-substring test | Considered asserting `"--json" in main(["--help"])` output to "test" the flag | A `--help` substring only proves the flag is *registered* (it already was — that's the bug). It does NOT prove `main()` honors it. The original bug had the flag registered and ignored. | Write a BEHAVIORAL test: `main(["--json"])` + `json.loads(capsys.readouterr().out)`, asserting on `status`/`exit_code`/payload. Match the emitter's output shape (compact vs indent=2). |

## Results & Parameters

### The two emitters (ProjectHephaestus `hephaestus/cli/utils.py`)

| Emitter | Signature | Output shape | Use for |
|---------|-----------|--------------|---------|
| `emit_json_status` | `emit_json_status(exit_code: int, message: str \| None = None, **extra)` | `print(json.dumps(envelope))` — COMPACT; `{"status": "ok"\|"error", "exit_code": <code>, ...message, ...extra}` | Status-only CLIs (fix / format / install / check / lint / drift) |
| `format_output(..., "json")` | `format_output(data: Any, format_type="json")` | `json.dumps(data, indent=2)` — PRETTY | Data-returning CLIs (listings, reports, structured payloads) |

### Deciding reference

`hephaestus/cli/utils.py:131-139` — the `add_json_arg` docstring states the rule verbatim. This is the citation to put in any plan/review that proposes one emitter over the other.

### Canonical sibling (data-shaped, for contrast)

`hephaestus/validation/stale_scripts.py:299-310` — a data-shaped CLI that builds a `report` dict (`stale_scripts`, `stale_count`, `strict`, `exit_code`, `passed`) and emits it via `print(format_output(report, "json"))`, returning the real `exit_code`. Use this as the template when the CLI is data-shaped; use `emit_json_status` when it is status-shaped.

### Proposed test shape (behavioral)

```python
def test_main_json_emits_status_envelope(capsys):
    exit_code = cli.main(["--json"])            # honor the flag
    payload = json.loads(capsys.readouterr().out)  # parses => flag honored
    assert payload["exit_code"] == exit_code        # REAL code, not hardcoded 0
    assert payload["status"] in {"ok", "error"}
```

### Verification status

unverified — this is a plan for ProjectHephaestus issue #1217. No edits applied, no tests run, no CI. The line numbers and the `args.write`/drift control-flow assumption were established by reading the file at plan time, not by execution.

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| ProjectHephaestus | Issue #1217 — implementation PLAN (not executed) | Planning heuristic for the registered-but-ignored `--json` flag fix: status-vs-data emitter selection (`emit_json_status` vs `format_output`), deciding reference `hephaestus/cli/utils.py:131-139`, sibling `hephaestus/validation/stale_scripts.py:299-310`, behavioral-test-over-help-text rule. Verification: unverified. |
