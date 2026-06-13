---
name: github-issue-forms-cannot-auto-apply-labels-from-fields
description: "GitHub issue *forms* (`.github/ISSUE_TEMPLATE/*.yml`) cannot themselves apply a label from a dropdown/field answer — only the static `labels:` key applies labels, and only unconditionally. To turn a form field (e.g. a `severity` dropdown) into a label you MUST build a consumer Action that parses the rendered issue body. Use when: (1) a planning/triage issue-form proposal adds a dropdown or input whose answer nobody reads — a reviewer NOGOs an inert field, (2) you are tempted to embed the body-parsing `grep` directly in a workflow `run:` block — it is untestable and silently no-ops on a rendering-format mismatch, (3) the consumer triggers on `issues: [opened, edited]` and a plain POST of the label leaves a stale same-family label, (4) you need to bind `${{ github.event.issue.body }}` safely without opening a CWE-94 Actions-injection hole, (5) the issue names a second linkage (an 'audit-section' field) you decline to build and you must scope it out explicitly rather than silently drop it, (6) you must keep the EXACT GitHub body-rendering format honest — a fixture test encodes the assumption but the only true closure is opening one throwaway issue and capturing the real rendered body."
category: architecture
date: 2026-06-12
version: "1.0.0"
user-invocable: false
verification: unverified
tags:
  - github-issue-forms
  - issue-template
  - dropdown-field
  - label-automation
  - inert-field
  - untested-parser
  - workflow-run-grep
  - unit-tested-module
  - fixture-body-test
  - label-reconciliation
  - same-family-label
  - actions-injection
  - cwe-94
  - scope-honesty
  - planning-learning
  - rendered-body-format
---

# GitHub Issue Forms Cannot Auto-Apply Labels From Field Answers

> **Warning:** This workflow has not been validated end-to-end. Treat as a hypothesis until CI confirms. Verification level: `unverified` — this is a PLANNING learning: the plan was written and reviewed across 3 NOGO/GO iterations for ProjectHephaestus issue #1210 but was NOT executed, and no CI has run the proposed code. The fixture test ENCODES the body-rendering assumption; the only true closure is the manual step in "Results & Parameters".

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-06-12 |
| **Objective** | Add planning/triage fields (a `severity` dropdown) to GitHub issue *forms* tied to a label-driven Epic+state workflow on ProjectHephaestus issue #1210 — and make the field actually *do* something, i.e. drive a `severity:*` label, rather than sit inert. |
| **Outcome** | Planning-only. Converged to GO on R2 after two NOGOs (R0: field with no consumer; R1: consumer embedded as an untestable bash `grep`). The accepted shape: a form field is mere documentation until a consumer Action reads the rendered body; that consumer's parsing MUST live in a unit-tested Python module the workflow invokes (`run: pixi run python -m hephaestus.github.<mod>`), so a fixture-body test exercises the exact code path. Not yet executed; no CI. |
| **Verification** | unverified — PLANNING learning. The plan, the form YAML, the parser-module sketch, and the consumer-workflow sketch were written and reviewed across 3 iterations. None of it was run; no test, no CI. Treat every command below as a hypothesis. |
| **Core misconception corrected** | "I'll add a `severity` dropdown to the issue form and it will label the issue." It will NOT. GitHub issue forms only apply labels via the static top-level `labels:` key, unconditionally — there is no per-option / per-answer label mapping. A field answer is inert text in the rendered body until a separate Action parses it. |

## When to Use

- A planning/triage issue-form proposal adds a **dropdown or input whose answer nobody reads**. "A triager *could* read it" is not a consumer. A reviewer will (correctly) NOGO a field that nothing consumes — it re-creates the inert-field anti-pattern.
- You are tempted to put the body-parsing logic as a `grep` for `### <FieldLabel>` directly inside a workflow `run:` block. That code is **not reachable by `pytest`**, so the load-bearing rendering assumption goes untested and a format mismatch **silently applies no label** — the exact "field nobody consumes" failure, re-introduced.
- The consumer Action triggers on `issues: [opened, edited]` and you are about to **POST** the derived label. A plain POST leaves any stale same-family label in place; editing severity major→minor accumulates *both* `severity:major` and `severity:minor`.
- You must bind `${{ github.event.issue.body }}` into the parser without opening an Actions-injection hole (CWE-94).
- The issue names a **second linkage you decline to build** (here: an "audit-section" field). Silently dropping half a named criterion is itself a (minor) requirements-alignment finding — scope it out explicitly with the reason.
- You need to keep the **exact GitHub body-rendering format** honest. A fixture test reduces but does not eliminate the risk that the real rendering differs from your fixtures.

**Don't use when:**

- You want an unconditional, every-issue label — the static `labels:` key in the form YAML already does that. No consumer Action needed.
- The triage signal is naturally human-only and has no downstream automation — then a dropdown for a human to read is fine, and a label is YAGNI. (But say so explicitly; don't ship a label-shaped field that no code reads and call it automation.)

## Verified Workflow

> The steps below are the **proposed** shape that earned GO in planning. They have not been executed.

### Quick Reference

```text
WRONG (NOGO):  form dropdown ─────────────────────────► (nobody reads it)            ← inert field
WRONG (NOGO):  form dropdown ─► workflow run: grep ###  ─► label                     ← untestable, silent no-op
RIGHT (GO):    form dropdown ─► run: python -m pkg.mod ─► parse_severity() ─► reconcile label
                                       ▲
                                       └── exact same code a fixture-body pytest exercises
```

```bash
# The consumer workflow invokes a MODULE, not embedded grep:
#   run: pixi run python -m hephaestus.github.apply_severity_label
# bound safely:
#   env:
#     ISSUE_BODY: ${{ github.event.issue.body }}     # read ONLY via os.environ in Python
#     ISSUE_NUMBER: ${{ github.event.issue.number }} # validate .isdigit() before use
```

### Detailed Steps

1. **Recognise the platform limitation first.** GitHub issue forms apply labels *only* through the static top-level `labels:` key, and *only* unconditionally. There is no "if option X then label Y" in the form schema. A field answer is text in the rendered body, nothing more, until something parses it.

2. **A field needs a consumer or it is inert.** If you add a `severity` dropdown, name the thing that reads it. "A human triager could read it" does not count as a consumer for an automation plan — that is acknowledging a limitation, not fixing it (R0 NOGO).

3. **Put the parser in a unit-tested module — never embedded bash in `run:`.** Extract a pure function plus a thin entry point:

   ```python
   # hephaestus/github/apply_severity_label.py
   SEVERITY_OPTIONS = ("blocker", "major", "minor", "trivial")  # hard-coded allow-list

   def parse_severity(issue_body: str) -> str | None:
       """Return the selected severity from a GitHub-rendered issue-form body.

       Rendered shape assumed: a '### Severity' heading, then blank line(s),
       then the selected option on its own line. '_No response_' → None.
       """
       ...

   def main() -> int:
       import os
       body = os.environ.get("ISSUE_BODY", "")
       number = os.environ.get("ISSUE_NUMBER", "")
       if not number.isdigit():
           return 1
       severity = parse_severity(body)
       reconcile_label(int(number), severity)  # see step 5
       return 0
   ```

   The workflow then runs `pixi run python -m hephaestus.github.apply_severity_label`. Because the grep/regex now lives in `parse_severity`, a fixture-body test runs the **exact** code the workflow runs (R1 NOGO fix).

4. **Write the fixture-body test against faithful rendered bodies.** RED-GREEN: one case per option, `_No response_` placeholder → `None`, blank-line-between-heading-and-value, missing section → `None`, and a stray non-matching first line → `None`. A rendering-format mismatch now **fails a test in CI** instead of silently no-op'ing in production. Mirror `tests/unit/github/` conventions.

5. **Reconcile, don't just POST.** Under an `issues: [opened, edited]` trigger, a plain POST leaves the stale label. The applier must: list current labels → **delete** any same-family (`severity:*`) label that isn't the target → add the target. `None`/`_No response_` → remove all family labels. Idempotent POST ≠ reconciling; an `edited` trigger demands convergence to exactly one (or zero) family labels.

6. **Mirror the repo's module + console-script convention.** Register the entry point in `pyproject.toml [project.scripts]` as `hephaestus.github.<mod>:main` rather than inventing a one-off script, and refresh the editable install (`pixi run dev-install`) so the entry-point integration test resolves it. (ProjectHephaestus learnings: new console scripts need entry-point verification; a pixi env re-solve drops the editable install.)

7. **Keep injection-safe through the refactor (CWE-94).** Bind `${{ github.event.issue.body }}` to an `env:` var; read it ONLY via `os.environ` in Python; match against the hard-coded `SEVERITY_OPTIONS` allow-list; only ever pass CONSTANT label strings to the API; validate the issue number with `.isdigit()` before use. No user text is executed or passed as a label.

8. **Be honest about scope under a MINOR issue.** When the issue names a linkage you decline to build (the "audit-section" field, for which no label vocabulary exists, so it would be inert), scope it out EXPLICITLY in the plan, the form description, and the doc — with the reason. Silently dropping half a named criterion is itself a requirements-alignment finding.

9. **Close the format-assumption loop manually before relying on it.** The fixture test encodes the rendering assumption; if the real rendering differs, the tests pass against a wrong fixture while production no-ops. The only true closure: open one throwaway issue via the real form, `gh issue view <n> --json body`, and confirm `parse_severity` returns the selected value. Add this as an explicit implementation step.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| R0 | Added a `severity` dropdown to the issue form with NO consumer | NOGO: a field nobody reads is inert. "A triager could read it" is not a consumer; acknowledging a limitation ≠ fixing it. GitHub forms apply labels only via the static `labels:` key, unconditionally — never per-answer. | A form field needs a named consumer or it is documentation, not automation. |
| R1 | Added a body-parsing workflow as the consumer, with the parsing as bash `grep` for `### Severity` embedded in the workflow `run:` block | Still NOGO: the load-bearing rendering assumption (dropdown answer renders as `### <FieldLabel>` + blank line + value) was UNVERIFIED, and code in a `run:` block is not reachable by `pytest`, so the grep would silently apply no label on a format mismatch — re-creating the inert-field problem. A reviewer floors to NOGO on an untested risky mechanic with a silent-no-op failure mode. | Extract the parsing to a unit-tested module the workflow invokes (`run: python -m pkg.mod`) so a fixture-body test exercises the EXACT code path. |
| — | POST-only label application under an `issues: [opened, edited]` trigger | Leaves a stale same-family label: editing severity major→minor accumulates both `severity:major` and `severity:minor`. Idempotent POST does not converge. | Reconcile: list current labels → delete same-family non-target → add target; None → remove all family labels. |
| — | Silently dropping the "audit-section" half of the two-part issue criterion | Minor requirements-alignment finding: half a named criterion was dropped without acknowledgement. | State the exclusion AND its reason explicitly (no `audit-section:*` vocabulary exists, so the field would be inert) in plan + form + doc. |
| — | Treating a fixture-body test as full verification of the rendering format | The test encodes the assumption; if real GitHub rendering differs, the test passes against a wrong fixture while production no-ops. A green suite gives false confidence. | A fixture reduces but does not eliminate the unverified-format risk; add a manual "open one real issue, capture `gh issue view --json body`, confirm the parser" step as the true closure. |

## Results & Parameters

### Why a form field cannot self-apply a label

| Mechanism | Applies a label? | Conditional on a field answer? |
|-----------|------------------|--------------------------------|
| Static `labels:` key in the form YAML | Yes | **No** — every issue from the form, unconditionally |
| A dropdown/input field answer | **No** | n/a — it is just rendered text in the body |
| A consumer Action parsing `github.event.issue.body` | Yes | Yes — but only if the parser actually matches the rendered format |

There is no per-option label mapping in the issue-form schema. The field → label step is *always* a separate Action.

### The R2 shape that earned GO (proposed, not executed)

```text
.github/ISSUE_TEMPLATE/<form>.yml          # dropdown id: severity, options = allow-list
        │  (issue opened/edited renders body)
        ▼
.github/workflows/apply-severity-label.yml # on: issues: [opened, edited]
        │  env: ISSUE_BODY, ISSUE_NUMBER (bound from github.event.*)
        │  run: pixi run python -m hephaestus.github.apply_severity_label
        ▼
hephaestus/github/apply_severity_label.py  # parse_severity(body) -> str|None ; reconcile_label()
        ▲
tests/unit/github/test_apply_severity_label.py  # fixture bodies exercise parse_severity directly
```

### Fixture cases the parser test MUST cover

| Fixture | Expected `parse_severity()` |
|---------|------------------------------|
| `### Severity\n\nblocker` (each option) | the option string |
| `### Severity\n\n_No response_` | `None` |
| heading then **multiple** blank lines then value | the value (don't assume exactly one blank line) |
| body with **no** `### Severity` section | `None` |
| stray non-matching first line before the section | the correct value (anchor on the heading, not line 1) |

### Reconciliation logic (converge to exactly one family label)

```python
def reconcile_label(issue_number: int, target: str | None) -> None:
    family = "severity:"
    current = list_labels(issue_number)
    desired = f"{family}{target}" if target else None
    for lbl in current:
        if lbl.startswith(family) and lbl != desired:
            remove_label(issue_number, lbl)      # delete stale same-family
    if desired and desired not in current:
        add_label(issue_number, desired)         # add only a CONSTANT string
    # target is None → all family labels removed above; nothing added.
```

### Injection-safety checklist (CWE-94)

- `${{ github.event.issue.body }}` → bound to `env: ISSUE_BODY`; read ONLY via `os.environ`.
- Never interpolate the body/title into a shell string in the `run:` block.
- Match the parsed value against the hard-coded `SEVERITY_OPTIONS` tuple; reject anything else.
- Only ever pass CONSTANT `severity:*` strings to the labels API.
- Validate `ISSUE_NUMBER` with `.isdigit()` in Python before use.

### STILL-UNCERTAIN (flag for the reviewer)

The EXACT GitHub body-rendering format remains an **assumption** even after the refactor. The fixture test now *encodes* that assumption, so if the real rendering differs the tests pass against a wrong fixture while production no-ops. The ONLY true closure is the manual step: open one throwaway issue via the real form, capture `gh issue view <n> --json body`, and confirm the parser returns the selected value before relying on it. A fixture test reduces but does not eliminate the unverified-format risk; the plan added this manual verification as an explicit implementation step.

### What was grounded during planning (verified-during-planning, not executed)

- Label / path / line claims grounded in live `gh label list`, `ls hephaestus/github/`, the `pyproject.toml` console-script lines, and the existing `auto-label-needs-plan.yml` numeric-validation pattern.
- Followed the repo's `tests/unit/github/` + module + `:main` convention.
- RED-GREEN ordering for the fixture test.

### Related skills

- `architecture-github-labels-as-state-vocabulary` — labels (not free-text) as the source-of-truth state vocabulary; the consumer here writes into that vocabulary, and its Actions-injection hardening mirrors that skill's `issues:opened` workflow.
- `monorepo-subproject-gitignore-and-github-template-gotchas` — adjacent gotchas when issue templates / forms live in a monorepo subproject.

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| ProjectHephaestus | Issue #1210 — planning for issue-form planning/triage fields tied to a label-driven Epic+state workflow | PLANNING ONLY. Converged to GO on R2 after R0 (inert field) and R1 (untestable embedded grep) NOGOs. No code executed, no CI. The fixture test encodes the body-rendering assumption; manual real-issue capture is the outstanding true-closure step. |
