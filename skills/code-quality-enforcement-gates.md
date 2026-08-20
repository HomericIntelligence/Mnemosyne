---
name: code-quality-enforcement-gates
description: "Introduce or tighten code-quality gates without hiding debt or breaking unrelated code. Use for Ruff complexity/annotation rules, mypy strictness, warnings-as-errors, markdownlint thresholds, production asserts/paths, post-remediation audits, reviewer-finding verification, tracking-doc reconciliation, and deprecation documentation invariants."
category: ci-cd
date: 2026-08-05
version: "2.0.0"
license: BSD-3-Clause
user-invocable: false
verification: verified-local
history: code-quality-enforcement-gates.history
tags: [code-quality, quality-gate, mypy, ruff, markdownlint, deprecation, audit, regression]
---

# Code-Quality Enforcement Gates

## Overview

A quality gate is safe when the current tree passes before configuration is tightened, exceptions
are explicit and shrinking, and tests assert behavior rather than exact source text. Verify audit
claims and documentation state against code, live CI, and GitHub before changing either.

Detailed remediation cases are indexed in
[`code-quality-enforcement-gates.notes.md`](code-quality-enforcement-gates.notes.md). The complete
prior source is in [`code-quality-enforcement-gates.history`](code-quality-enforcement-gates.history).

## When to Use

- Enabling a Ruff rule, mypy strictness option, warning-to-error policy, or lower lint threshold.
- Deciding whether to refactor, suppress, or scope a new diagnostic.
- Narrowing a mypy override after part of a tree becomes typed.
- Replacing production assertions or hardcoded temporary paths.
- Auditing whether remediation actually closed every finding.
- A reviewer/audit finding may be stale, pre-existing, or factually wrong.
- Runtime deprecation warnings and multiple documentation insertion points must stay synchronized.

## Verified Workflow

### 1. Establish the clean baseline

Run the proposed rule manually before editing configuration. Capture every current failure and
separate in-scope debt from unrelated pre-existing failures. Do not enable a gate first and then
silence its output globally.

```bash
ruff check <scope> --select <rule>
mypy <scope> --check-untyped-defs
markdownlint-cli2 '<changed-glob>'
pytest <focused-tests>
```

Choose the narrowest scope that covers the intended property. If the repository already has a
selection list or override structure, extend it rather than replacing unrelated settings.

### 2. Fix complexity at the decision boundary

For McCabe/C901 failures, extract coherent decisions or transformations with descriptive names;
keep orchestration visible. Preserve exception ordering, side effects, logging, and early-return
semantics. Re-run the exact rule and focused behavior tests after each extraction. Suppress only
when the complexity is intentional, documented, and a refactor would obscure a stable state machine.

### 3. Tighten typing incrementally

Before enabling `check_untyped_defs`, repair all surfaced diagnostics, including empty collections,
`defaultdict` annotations, and deprecated third-party aliases. Narrow broad test overrides by
proving the newly included directory passes without the override, then list only residual untyped
subtrees.

Mypy does not reliably require explicit `__init__ -> None`; add targeted Ruff `ANN204` for that gap.
Fix constructors and add an AST property guard that examines the intended source scope. Avoid broad
`ANN` enablement unless the repository is ready for its full debt.

### 4. Promote warnings only at zero

Count the targeted warning on representative tests and require zero before converting warning
annotations into build failures. Match the precise deprecation category/message so unrelated
warnings do not become accidental policy. Remove obsolete compatibility paths only after all
callers have migrated.

Keep runtime warnings and documentation synchronized: symbol name, replacement, removal timeline,
and migration example must agree. When docs have multiple insertion points, bound and assert each
section independently; one combined substring assertion can pass when one required block is absent.

### 5. Tune documentation gates intentionally

For duplicate-heading rules such as MD024, prefer sibling-only enforcement when repeated headings in
separate sections are meaningful. Do not blanket-disable the rule. Include the repository’s
changelog/release companions only if they are actual lint inputs and product consumers.

### 6. Assert properties, not prose

Regression tests should prove the behavior the gate protects:

- parse the AST and require the target constructor annotations;
- invoke code and assert warning category/message;
- parse configuration and assert the scoped rule is enabled;
- isolate each documentation section and require its semantic tokens;
- test both positive and negative halves so absence cannot pass vacuously.

Avoid tests that pin comments, whitespace, exact line counts, or whole prose blocks.

### 7. Fix production-quality hazards

Replace assertions used for user/runtime validation with explicit exceptions because `python -O`
removes assertions. Replace shared hardcoded temp paths with a test/runtime-provided temporary
directory to prevent platform failures and parallel collisions. During type migrations, remove or
update all dependent placeholder code; commenting only the declaration leaves invalid uses.

### 8. Coordinate bounded batches

Read all files before editing, identify shared imports/config, and keep each PR to a reviewable set
of related files. Run focused checks on changed paths, then the repository-required suite. Record
pre-existing failures with matching baseline evidence; never disable a rule or hook to make the batch
green.

### 9. Verify findings before remediation

For each audit/reviewer claim, open the named code and reproduce the condition. Compare failing check
names on the PR with the same checks on current main before attributing them to the change. A matching
main failure is pre-existing context, not proof that the PR introduced it.

For a tracking document, verify every checkbox against live issues/PRs and code—not only entries
called out by the bug report. Update status and evidence together. A stale report can name a fix that
already landed or a root cause that was never true.

### 10. Audit the completed remediation

Re-run the original detector, targeted behavior tests, full required gates, and a source search for
suppression markers, obsolete aliases, production asserts, hardcoded paths, or stale docs. Verify
supported runtime versions against actual CI matrices before changing metadata. Report residual
gaps explicitly rather than marking the initiative complete from the absence of one diagnostic.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --- | --- | --- | --- |
| Blanket ignore | Enabled gate then suppressed broadly | Hid existing and future debt | Reach zero first; scope residual exceptions |
| Metric-only extraction | Split code only to lower score | Reordered effects or exceptions | Extract coherent behavior and test equivalence |
| Mypy-only constructor | Assumed mypy covered `__init__` | Return-annotation gap remained | Add targeted ANN204 plus AST property test |
| Early warning promotion | Made residual warnings errors | Existing tests immediately failed | Count and reach zero first |
| Source-string test | Pinned exact implementation text | Harmless refactors broke tests | Assert parsed behavior/property |
| Combined doc assertion | Searched all insertion points together | One missing block still passed | Scope each section independently |
| Production assert | Used `assert` for runtime input | Optimization removed validation | Raise an explicit exception |
| Trusted audit state | Believed checkbox or PR failure | Evidence was stale or pre-existing | Verify code, live GitHub, and main check |

## Results & Parameters

```text
rule/tool/version and exact target scope
baseline command and diagnostic count
fix-versus-suppress disposition for each finding
configuration delta and residual override list
focused positive/negative regression tests
changed-path lint/type/test commands
main-versus-PR check comparison
post-remediation detector count and full required-gate result
remaining gaps with owners/tracking links
```

## Verified On

- Ruff C901/ANN204, mypy, deprecation, Markdown, production-path, and audit-remediation cases through
  2026-08-05.
- Verification remains `verified-local`; case-specific CI status is retained in notes/history.
