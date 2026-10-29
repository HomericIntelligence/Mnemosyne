---
name: template-render-variant-review
description: "Review a change to a template that generates an executable script by rendering every conditional variant and checking the rendered output. Use when a pull request edits a Jinja-style template that emits a shell or batch script with conditional blocks, parallel arrays, heredocs, or an exit-status chain, and the reviewer must verify behavior that the template source view cannot show."
category: tooling
date: 2026-10-29
version: "1.0.0"
license: BSD-3-Clause
user-invocable: false
verification: verified-live
tags:
  - code-review
  - template-rendering
  - shell-generation
  - conditional-variants
  - parallel-arrays
  - exit-status
  - jinja
  - review-evidence
---

# Template Render-Variant Review

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-29 |
| **Objective** | Give a reviewer a repeatable method to verify a change to a template that renders an executable script with conditional blocks, when the template source alone cannot show the behavior of each rendered variant. |
| **Outcome** | Successful. Rendering each variant and comparing it with the pre-change render produced the placement, array-parity, and exit-status evidence that a source-only diff could not supply. Each review claim could cite rendered output. |

A template diff shows text. Behavior lives in the rendered output. Template
conditionals and loops select between variants, and a defect can exist in one
rendered variant while the template source and the default render look
correct. Review the rendered artifacts, not the intention recorded in the
template.

## When to Use

Use this skill when all or most of these conditions apply:

- A change edits a template (Jinja2 or similar) that generates a shell,
  batch, or job script.
- The template contains conditional blocks, loops, or parallel arrays that
  expand into positional script content.
- The change inserts or moves blocks whose placement relative to function
  definitions, heredocs, traps, or earlier commands matters.
- The rendered script carries an exit-status chain (status capture variables,
  a final `exit`), or invariants that the change must preserve (trap and
  kill order, permission bits, log redirection, privacy-sensitive paths).
- Source-level tests of the render function exist, but nothing executes or
  parses each runtime variant.

Do not use this skill for a template that renders a static configuration with
no executable semantics, or when integration tests already execute every
variant and the test evidence is available for review.

## Verified Workflow

### Quick Reference

```bash
# For each variant that the change can affect:
# 1. Render the script at the reviewed revision (project render entry point,
#    or a minimal Jinja2 render with the same variables).
# 2. Parse it.
bash -n <rendered-variant.sh>
# 3. Render the pre-change template with the same variables and compare.
diff <old-render> <new-render>
```

### Suggested Approach

Use these steps as decision criteria. Steps that depend on earlier results
keep their order.

1. **Enumerate the variant space.** List each template conditional and each
   input combination that selects a materially different rendered script.
   Name each variant. Restrict the cross-product to the conditionals the
   change touches.
2. **Render every variant at the reviewed revision.** Use the project's own
   render function or a minimal render with identical variables. Keep the
   rendered files as review evidence.
3. **Parse each rendered script.** Use `bash -n` for shell, or the target
   scheduler's parse or dry-run mode when available. A template can be valid
   while one rendered variant is not.
4. **Diff each variant against the pre-change render.** Render the old
   template with identical variables. The delta is the behavioral change.
   Confirm that regions the change did not touch stay byte-identical, in
   particular invariants the change must preserve: trap order, kill order,
   permission bits, log redirection, and privacy-sensitive paths.
5. **Check parallel-array parity.** For arrays that expand positionally,
   count declared elements and referenced elements in every variant. Index
   arithmetic (array lengths, loop bounds, computed offsets) must agree in
   each variant, not only in the default.
6. **Verify insertion placement in the rendered output.** A block inserted
   after a marker in the template can render inside a function body, inside
   a heredoc, or before its inputs exist, depending on the variant. In each
   rendered file, confirm top-level placement, input availability, and
   heredoc containment.
7. **Verify the exit-status chain end to end.** For each rendered variant,
   confirm that the failure path still propagates: status capture
   assignments, `set -e` interplay, the final `exit`, and that no new
   statement after the capture point resets or masks the status.
8. **Record evidence per variant.** Keep render inputs, rendered outputs,
   diffs, and probe results. Write the review so each claim cites rendered
   output.

When a variant cannot be rendered (missing data, secrets, or environment),
review its template slice directly and report the coverage gap. Do not claim
rendered evidence for it.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| 1 | Review the template source diff alone. | The diff showed textual insertions but could not show where a block lands in each rendered variant, for example inside a function body or a heredoc in a non-default variant. | Template source shows text, not placement. Render each variant before you make a placement claim. |
| 2 | Render only the default variant. | The default render parsed and looked correct, but a conditional variant changed parallel-array counts and moved the inserted block relative to earlier helpers. | The default variant is the least likely to fail. Defects collect in conditional combinations. |
| 3 | Trust source-level tests of the render function. | The tests asserted template properties such as string presence. They did not prove shell semantics of any rendered variant: parse failures and exit-status masking stayed invisible. | Tests of the generator do not prove behavior of the generated. Validate the rendered artifacts. |

## Results & Parameters

### Configuration

- Render tooling: the project's own render module, or Jinja2 with the same
  loader, filters, and variables.
- Variant matrix: the minimal cross-product of the conditionals that the
  change touches.
- Per-variant checks: `bash -n` (or the scheduler parse mode), `diff`
  against the pre-change render, positional array-element counts, placement
  anchors (function-definition ends, heredoc markers), and the exit-status
  chain from capture to final `exit`.

### Expected Output

- One rendered file per variant, each parsed cleanly.
- A per-variant delta limited to the intended change, with invariant regions
  byte-identical.
- Equal parallel-array element counts in each variant.
- A review verdict that cites rendered evidence for each behavioral claim.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| A training-stack launch system with job-scheduler batch templates | Review of a pull request that added conditional blocks to a batch-script template with parallel arrays and an exit-status chain. | See [notes.md](../skills/template-render-variant-review.notes.md). |

## References

- [Jinja Template Designer Documentation](https://jinja.palletsprojects.com/en/stable/templates/)
