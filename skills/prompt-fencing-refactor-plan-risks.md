---
name: prompt-fencing-refactor-plan-risks
description: "Planning-stage risk checklist for refactoring prompt builders that fence untrusted GitHub content. Use when: (1) extracting repeated nonce/fence/notice plumbing into a shared helper, (2) reviewing a prompt refactor that must preserve one nonce per rendered prompt, (3) moving _fence_untrusted/_UNTRUSTED_NOTICE usage behind a helper without weakening injection defenses, (4) adding or re-exporting prompt helper APIs from hephaestus.automation.prompts."
category: architecture
date: 2026-06-26
version: "1.0.0"
user-invocable: false
verification: unverified
tags:
  - prompt-builders
  - prompt-fencing
  - untrusted-content
  - nonce
  - secrets-token-hex
  - refactoring
  - planning
  - reviewer-risks
  - parser-sensitive-tests
  - projecthephaestus
---

# Prompt Fencing Refactor Plan Risks

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-06-26 |
| **Objective** | Capture the planning risks from ProjectHephaestus issue #1399: add a shared prompt-scoped fencing helper in `hephaestus/automation/prompts/_shared.py` so prompt builders stop repeating `secrets.token_hex(8).upper()`, `_fence_untrusted(...)`, and `_UNTRUSTED_NOTICE` plumbing. |
| **Outcome** | Plan produced only. The refactor was not executed in this learning capture, and none of the cited grep results, line numbers, prompt contracts, or test locations were independently re-verified here. |
| **Verification** | unverified - planning artifact only; no ProjectHephaestus code was edited or tested. |

This is the prompt-security specialization of the broader DRY/refactor planning
skills. Reach for `dry-refactoring-plan-assumption-audit` for generic DRY
consolidation risks and `refactor-extraction-plan-unverified-assumptions` for
single-module extraction with re-exports. Use this skill when the refactor touches
prompt fencing, nonce scope, or parser-sensitive rendered prompt text.

## When to Use

- Planning or reviewing a refactor that centralizes prompt fencing for untrusted
  issue bodies, PR diffs, review comments, or plan text.
- A plan proposes a `FencedContent`/`fence_content()` helper that generates a
  prompt nonce and returns fenced blocks plus `_UNTRUSTED_NOTICE`.
- Multiple prompt builders must still render exactly one nonce per prompt, even
  when they include several fenced untrusted sections.
- Lower-level prompt helpers keep a `nonce` parameter for compatibility while
  top-level builders switch to a shared helper and pass `fenced.nonce`.
- The plan re-exports a prompt helper from `hephaestus.automation.prompts.__init__`
  and claims public API compatibility.
- The acceptance criteria depend on parser-sensitive prompt output, not just helper
  unit behavior.

## Proposed Workflow

> **Warning:** This workflow has not been validated end-to-end. Treat as a
> hypothesis until CI confirms. The source plan was not executed, and this skill
> records reviewer risks and verification commands to run before trusting it.

### Quick Reference

```bash
# Run from the ProjectHephaestus repo root before implementing or approving.

# 1. Rebuild the evidence instead of trusting the plan's copied grep output.
rg -n "secrets\\.token_hex|_fence_untrusted|_UNTRUSTED_NOTICE" \
  hephaestus/automation/prompts/planning.py \
  hephaestus/automation/prompts/implementation.py \
  hephaestus/automation/prompts/address_review.py \
  hephaestus/automation/prompts/pr_review.py

# 2. Locate lower-level helpers that must remain signature-compatible.
rg -n "def build_unaddressed_directive|def _build_context_block" \
  hephaestus/automation/prompts tests

# 3. Verify public export expectations before adding/re-exporting names.
rg -n "__all__|from hephaestus\\.automation\\.prompts import|FencedContent|fence_content" \
  hephaestus/automation/prompts tests

# 4. After the refactor, prove duplication is gone from the intended files only.
rg -n "secrets\\.token_hex\\(8\\)\\.upper\\(\\)|_fence_untrusted\\(|_UNTRUSTED_NOTICE" \
  hephaestus/automation/prompts/planning.py \
  hephaestus/automation/prompts/implementation.py \
  hephaestus/automation/prompts/address_review.py \
  hephaestus/automation/prompts/pr_review.py

# 5. Run helper and rendered-prompt behavioral tests together.
pytest \
  tests/unit/automation/prompts/test_shared.py \
  tests/unit/automation/test_prompts.py \
  tests/unit/automation/test_prompt_terseness.py
```

### Detailed Steps

1. **Re-verify every plan premise against the current tree.** The #1399 plan
   claimed specific `rg` results for `import secrets`, `secrets.token_hex`,
   `_UNTRUSTED_NOTICE`, `_fence_untrusted`, re-export sites, and test locations.
   Treat those as hints. Re-run the searches on the implementation branch before
   writing code, and cite fresh paths/lines in the PR body.

2. **Make nonce scope the central invariant.** The helper can reduce duplication
   only if every top-level prompt builder still uses exactly one nonce for the
   rendered prompt. If a builder fences multiple untrusted inputs, all nonce-delimited
   blocks in that rendered prompt must share the same nonce. Tests should count or
   monkeypatch nonce generation at the top-level builder, not only assert that the
   helper returns a string.

3. **Preserve the prompt-injection boundary, not just string shape.** Every untrusted
   GitHub payload must remain inside `_fence_untrusted(..., nonce)` output and the
   rendered prompt must still include `_UNTRUSTED_NOTICE`. A helper-only test can pass
   while a prompt builder accidentally drops the notice or embeds one payload raw.
   Compare actual rendered prompt output for planning, implementation, PR review,
   and address review.

4. **Keep lower-level nonce helpers compatible.** `build_unaddressed_directive(threads, nonce)`
   and `_build_context_block(..., nonce)` are intended to keep their signatures. The
   top-level builder should pass `fenced.nonce`; the lower-level helper should not
   start generating its own nonce. Add direct regression coverage for the address-review
   path because it is the easiest place to accidentally create a second nonce.

5. **Treat `__all__`/re-export work as public API.** If `FencedContent` and
   `fence_content()` are exported from `prompts/__init__.py`, verify the package's
   existing export pattern and tests before changing it. Missing an `__all__` entry
   breaks import-style callers; over-exporting private helpers broadens the public
   surface without review.

6. **Test parser-sensitive rendered prompts, not only helper mechanics.** The plan's
   riskiest claim is behavioral equivalence. Existing tests in
   `tests/unit/automation/test_prompts.py` and `test_prompt_terseness.py` are more
   important than a new `test_shared.py` if they compare the real prompt strings that
   downstream parsers/review loops consume.

## Verified Workflow

No verified workflow exists for this learning yet. The heading is retained only
because `scripts/validate_plugins.py` currently requires `## Verified Workflow`
in every flat skill file. Use the `## Proposed Workflow` section above; do not
treat this as a verified implementation recipe.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Trust copied grep evidence from the plan | Accepted claimed `rg` results for `secrets.token_hex`, `_UNTRUSTED_NOTICE`, `_fence_untrusted`, exact line numbers, and test locations | The learning request did not independently verify the ProjectHephaestus tree; line numbers and import sites can drift before implementation | Re-run every search on the current branch and cite fresh paths/lines before coding or approving |
| Unit-test only the new helper | Added `test_shared.py` for `FencedContent`/`fence_content()` and assumed prompt behavior was covered | A helper can return correct fields while a prompt builder uses two nonces, drops `_UNTRUSTED_NOTICE`, or embeds one untrusted payload raw | Add rendered-prompt tests for each affected builder and keep existing behavioral tests in the verification set |
| Treat nonce generation as a local detail | Moved `secrets.token_hex(8).upper()` behind a factory without asserting top-level nonce scope | Multiple helper calls inside one prompt can silently generate multiple nonces, breaking nonce-delimited fence contracts | Assert exactly one nonce per rendered prompt and ensure all fenced blocks in that prompt use `fenced.nonce` |
| Assume lower-level helper signatures are safe by intent | Planned to pass `fenced.nonce` to `build_unaddressed_directive(threads, nonce)` and `_build_context_block(..., nonce)` without targeted address-review coverage | The address-review path has nested helper calls and can accidentally start generating or expecting a different nonce | Keep signatures unchanged and add direct address-review regression tests around the rendered output |
| Re-export without auditing the package surface | Added helper names to `prompts/__init__.py` because the plan said to re-export them | `__all__` or import-style tests may require exact names; exposing private helper internals can create accidental API | Inspect current `__init__.py` export style and tests before changing the public surface |
| Declare the duplication audit empty without scoping it | Ran a broad or stale grep and called duplication removed | A broad grep may flag `_shared.py` intentionally, while a narrow grep may miss one affected builder | Scope the final grep to `planning.py`, `implementation.py`, `address_review.py`, and `pr_review.py`, and make the expected hits/zero-hits explicit |

## Results & Parameters

### Plan Context Preserved

- Objective: add a shared prompt-scoped fencing helper in
  `hephaestus/automation/prompts/_shared.py`.
- Proposed design: frozen `FencedContent` helper plus `fence_content()` factory.
- Nonce rule: one nonce per prompt builder; pass `fenced.nonce` into lower-level
  helpers that already accept a nonce.
- Public API plan: re-export the helper from `hephaestus.automation.prompts.__init__`.
- Affected prompt modules named in the plan: `planning.py`, `implementation.py`,
  `address_review.py`, and `pr_review.py`.
- Tests named in the plan: new `tests/unit/automation/prompts/test_shared.py`,
  existing `tests/unit/automation/test_prompts.py`, and
  `tests/unit/automation/test_prompt_terseness.py`.
- Lower-level helpers intended to remain signature-compatible:
  `build_unaddressed_directive(threads, nonce)` and `_build_context_block(..., nonce)`.

### Most Uncertain Assumptions

1. The existing prompt builders all share the same nonce lifecycle and can use one
   factory result without changing rendered output.
2. The current lower-level helper signatures are exactly as the plan states and
   no caller relies on generating a nonce inside them.
3. The package export surface can add `FencedContent` and `fence_content()` without
   breaking `__all__`, lazy imports, or downstream import expectations.
4. Existing behavioral tests compare enough parser-sensitive prompt output to catch
   notice ordering, fence delimiter, and nonce regressions.
5. The duplication audit grep is scoped to the intended prompt-builder files and
   will not be fooled by legitimate helper definitions in `_shared.py`.

### External Sources, Files, And APIs Not Verified Here

- The plan's claimed `rg` output for `import secrets`, `secrets.token_hex`,
  `_UNTRUSTED_NOTICE`, `_fence_untrusted`, exact line numbers, and test locations.
- Current contents of `hephaestus/automation/prompts/_shared.py`,
  `planning.py`, `implementation.py`, `address_review.py`, `pr_review.py`, and
  `prompts/__init__.py`.
- Current parser-sensitive prompt contracts asserted by
  `tests/unit/automation/test_prompts.py` and `test_prompt_terseness.py`.
- The exact behavior and expected delimiter format of `_fence_untrusted(...)`.
- The public import/export contract for `hephaestus.automation.prompts`.
- The stdlib `secrets.token_hex(8).upper()` behavior is stable, but whether tests
  monkeypatch it or assert exact nonce text in this repo was not verified here.

### Reviewer-Risk Focus

```text
Prompt fencing refactor review checklist

- [ ] Every rendered prompt still uses exactly one nonce.
- [ ] Every untrusted GitHub payload remains inside nonce-delimited fenced blocks.
- [ ] `_UNTRUSTED_NOTICE` still appears in each prompt that includes untrusted content.
- [ ] `build_unaddressed_directive(threads, nonce)` and `_build_context_block(..., nonce)`
      keep behavior and do not generate their own nonce.
- [ ] `FencedContent` / `fence_content()` exports match the package's public API policy.
- [ ] Tests compare actual rendered prompt output, not just helper return values.
- [ ] The final duplication-audit grep is empty for the intended prompt-builder files.
```

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| ProjectHephaestus | Issue #1399 implementation-plan learning capture | Planning-only; unverified. The plan was summarized into this skill, but the ProjectHephaestus code, tests, line numbers, and grep evidence were not independently checked in this request. |
