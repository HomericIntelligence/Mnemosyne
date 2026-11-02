---
name: architecture-migration-freeze-import-debt-baseline
license: BSD-3-Clause
description: "Freeze legacy direct imports during a partial runtime migration with an AST-derived exact consumer/module allowlist and matching ADR policy, and retire each frozen pair by moving the depended-on code down one layer. Use when: (1) an accepted ADR describes a completed abstraction but source still uses legacy provider modules, (2) compatibility imports must remain temporarily without allowing the exception to expand, (3) line-oriented grep would miss nested or function-local imports, (4) documentation must distinguish invocation, response parsing/validation, compatibility exports, and provider-specific failure diagnostics, (5) a policy file must list every allowed upward import edge and the same change pays down one or more edges."
category: architecture
date: 2026-07-20
version: "1.1.0"
user-invocable: false
verification: unverified
tags:
  - adr
  - architecture-boundary
  - ast
  - compatibility-shim
  - direct-import
  - migration-debt
  - regression-guard
  - runtime-abstraction
---

# Freeze Partial-Migration Import Debt

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-07-20 (amended 2026-11-01: retirement by extraction) |
| **Objective** | Reconcile an ADR with a partial provider-runtime migration while preventing the remaining direct-import exception from silently expanding. |
| **Outcome** | Proposed an exact AST-derived consumer/module baseline, automation-only path invariant, and normalized ADR-policy assertion. The Hephaestus source inventory was confirmed read-only, but the documentation and test changes were not implemented. A later amendment adds the retirement path: move the depended-on code down one layer, then delete the allowlist pair. |
| **Verification** | unverified — the baseline guard was observed in source; the retirement path comes from one reviewed change whose CI was not observed. |

This pattern is narrower than a general library/product boundary and broader
than a symbol-scoped exemption. It applies when a migration has multiple
legitimate legacy consumers that must remain temporarily, but every new
consumer must be rejected until explicitly justified.

## When to Use

- An accepted ADR says all call sites use a new abstraction, while the current
  source still imports one or more legacy compatibility modules.
- Completing the migration would exceed the focused issue's scope, but merely
  weakening the ADR would leave an open-ended exception.
- The exception has several distinct reasons: provider invocation, response
  parsing or validation, compatibility exports, or provider-specific failure
  diagnostics.
- Imports can occur inside functions or through relative and absolute forms,
  so a line-oriented grep is incomplete.
- You need removals to update both source and policy instead of leaving stale
  allowlist entries that normalize obsolete debt.
- A policy file lists every permitted layer-crossing import edge, and the same
  change removes one or more edges without breaking the guard.
- An upper-layer module imports a lower-layer module only for one cohesive
  group of actions, so the lower module can own that group instead.

Do not use this pattern to authorize new legacy dependencies. For a single
pure symbol imported from a normally forbidden module, prefer the narrower
`symbol-scoped-import-exemptions` skill. For the product-to-library dependency
direction and lean base import surface, use
`library-product-import-boundary-enforcement-test` alongside this pattern.

## Proposed Workflow

> **Warning:** This workflow has not been validated end-to-end. Treat as a hypothesis until CI confirms.

### Quick Reference

| Goal | Mechanism | Required property |
|------|-----------|-------------------|
| Describe reality | Inspect the new runtime and every legacy shim | Never cite a facade or capability that is not present on disk |
| Freeze debt | `frozenset[(relative_consumer, legacy_module)]` | Exact pair equality, not counts or module-only membership |
| Find all imports | `ast.parse` plus `ast.walk` | Covers nested/function-local and supported relative/absolute forms |
| Keep scope one-way | Resolve every approved consumer beneath the product root | The existing reverse-boundary guard remains authoritative |
| Couple policy to code | Normalize the complete normative ADR sentence and a source-derived summary | Documentation must cover every approved reason, including diagnostics-only consumers |
| Retire debt | Remove the source import and baseline pair together | Equality fails on both undocumented additions and stale removals |
| Retire by extraction | Move the depended-on code down one layer, then delete the `(consumer, module)` pair | Re-exporting the module from its new home keeps the edge and leaves the pair valid |

### Detailed Steps

1. **Verify the actual migration state before editing the ADR.** Read the
   provider-neutral runtime entry points, the legacy invocation/parser module,
   compatibility shims, and representative consumers. Confirm which providers
   the new runtime truly executes and whether any facade named by the ADR is
   tracked on disk. Describe the architecture as partial when the direct runner
   rejects a provider still handled by a legacy module.

2. **Inventory exact consumer/module pairs with the AST.** Store paths relative
   to the product-layer root so the baseline is reviewable and portable. Walk
   the whole tree with `ast.walk`, not only `tree.body`, because function-local
   imports are still dependency edges.

   ```python
   import ast
   from pathlib import Path

   PRODUCT_ROOT = Path("pkg/product")
   LEGACY_MODULES = frozenset({"legacy_invoke", "legacy_models", "legacy_timeouts"})

   def legacy_targets(node: ast.Import | ast.ImportFrom) -> set[str]:
       if isinstance(node, ast.Import):
           return {
               target
               for alias in node.names
               for target in LEGACY_MODULES
               if alias.name in {target, f"pkg.product.{target}"}
           }

       module = node.module or ""
       if module in LEGACY_MODULES:
           return {module}
       if module.startswith("pkg.product."):
           target = module.removeprefix("pkg.product.").split(".", 1)[0]
           return {target} if target in LEGACY_MODULES else set()
       if module == "pkg.product" or (node.level and not module):
           return {alias.name for alias in node.names if alias.name in LEGACY_MODULES}
       return set()

   def collect_direct_imports() -> frozenset[tuple[str, str]]:
       pairs: set[tuple[str, str]] = set()
       for source in sorted(PRODUCT_ROOT.rglob("*.py")):
           relative = source.relative_to(PRODUCT_ROOT).as_posix()
           tree = ast.parse(source.read_text(encoding="utf-8"), filename=str(source))
           for node in ast.walk(tree):
               if isinstance(node, (ast.Import, ast.ImportFrom)):
                   pairs.update((relative, target) for target in legacy_targets(node))
       return frozenset(pairs)
   ```

3. **Freeze exact pairs, not aggregate counts.** A count of 30 can stay green if
   one approved consumer disappears while a new unapproved consumer appears.
   Exact equality detects additions and removals:

   ```python
   actual = collect_direct_imports()
   assert actual == APPROVED_DIRECT_IMPORTS, (
       f"added={sorted(actual - APPROVED_DIRECT_IMPORTS)}, "
       f"removed={sorted(APPROVED_DIRECT_IMPORTS - actual)}"
   )
   ```

   Derive prose counts from `APPROVED_DIRECT_IMPORTS` with `Counter`; do not
   maintain a second independent numeric baseline.

4. **Constrain every exception to the intended product layer.** Resolve each
   approved relative path beneath the product root and require it to be an
   existing file. This protects the exception list from naming a library-layer
   consumer. Keep the existing reverse-boundary guard as a separate test: the
   legacy-debt baseline limits imports *within* the product layer, while the
   boundary guard forbids library code from importing the product layer.

5. **Write the ADR policy as a complete normative sentence.** State all of the
   following together:

   - New call sites use the provider-neutral runtime.
   - Frozen direct imports may remain only for their enumerated reasons.
   - Compatibility shims are migration debt, not endorsed architecture.
   - No new consumer/module pair may be added.
   - A migrated pair leaves source and baseline in the same change.
   - Modules with zero approved consumers are named explicitly when their zero
     is part of the policy.

   Include provider-specific failure formatting if even one approved consumer
   imports only a diagnostic helper. Omitting that clause creates a POLA bug:
   the allowlist passes while the prose still says that consumer is forbidden.

6. **Assert the complete policy and source-derived summary in the test.** Use a
   whitespace normalizer so Markdown wrapping can change without weakening the
   content assertion:

   ```python
   def normalize(text: str) -> str:
       return " ".join(text.split())

   adr = normalize(ADR_PATH.read_text(encoding="utf-8"))
   assert normalize(DECISION_POLICY) in adr
   assert normalize(baseline_summary()) in adr
   ```

   Assert the whole normative paragraph, not isolated keywords. Keyword checks
   can pass when the words occur in contradictory or non-normative sections.

7. **Use a documentation-first RED/GREEN sequence.** Add the guard against the
   current source before amending the ADR. The source-baseline assertion should
   pass and the complete-policy assertion should fail. Then update Context,
   Decision, implementation anchors, and Consequences and rerun the focused
   ADR, import-surface, and reverse-boundary suites.

8. **Keep rollback and completion explicit.** The guard is safe to revert
   without runtime migration because it changes only documentation and
   validation. The preferred forward path is still to remove legacy imports;
   each completed migration shrinks the exact baseline. Never expand the list
   merely to make a failing test green.

9. **Retire an edge by moving code down, not by forwarding it.** An upward
   import is a real dependency. Use these rules to remove it without a
   follow-on cycle:

   - Move the whole depended-on unit to a lower module that both sides can
     import. Do not re-export it from the old module; a re-export keeps the
     same import edge, and some layer guards count module re-exports as edges.
   - A layer guard can count `__init__` re-exports as edges, so add a new lower
     module instead of expanding a package `__init__`.
   - Move one cohesive group of actions per step. Leave unrelated actions in
     place, even when they share a file.
   - Update the policy file and the exact pair baseline in the same commit.
     Split consumers of a moved symbol one at a time so the guard never has an
     unrecorded edge.
   - Replace test patches that target the old import site with patches on the
     new site. A patch on a stale site passes while the moved code runs
     unpatched.

## Verified Workflow

_Not applicable._ This skill was captured from a planning and review session
and is `unverified`: the ADR and regression guard were not changed, the focused
tests were not run, and CI was not observed. The actionable methodology is
therefore kept under **Proposed Workflow** above. This placeholder exists
because the repository validator requires the literal `## Verified Workflow`
heading; it does not make a verification claim.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Treat the accepted ADR as current reality | The ADR prohibited all direct legacy imports and named a future unified facade as the implementation direction | The source still had many legacy imports, and the named facade was not present on disk | Reconcile accepted prose against tracked code before citing implementation anchors |
| Describe only invocation and response parsing | The first exception wording covered consumers that invoke Claude or parse its responses | A diagnostics-only consumer imported `describe_claude_failure`; the baseline passed while the prose still contradicted that consumer | Enumerate every behavioral reason represented by the approved importers, including provider-specific failure diagnostics |
| Freeze only aggregate counts | Record totals such as 16 invocation imports and 14 model imports | An unapproved addition can replace an approved removal without changing the totals | Freeze exact `(consumer path, legacy module)` pairs; derive counts only for prose |
| Use line-oriented grep | Search import text with prefixes | Grep can miss nested/function-local imports and mishandle relative or aliased forms | Parse every Python file and use `ast.walk` over `Import` and `ImportFrom` nodes |
| Complete the whole runtime migration inside a documentation-boundary issue | Replace all legacy imports and introduce a unified facade | The change expands into constructor injection, test-patch migration, provider behavior, and orchestration risk | For a focused reconciliation, freeze existing debt and track the full facade migration separately |
| Allow stale baseline entries after migration | Treat the allowlist as a maximum rather than exact state | Removed debt remains documented as acceptable and can be reintroduced silently | Exact equality must reject both additions and removals; update source and baseline together |
| Retire an upward edge by re-exporting the moved symbol from the old module | Keep `from new_module import helper` inside the old upper module for compatibility | The consumer still imports the upper module, so the frozen pair stays valid and the reported debt is unchanged | Move the unit to a lower module and delete the pair in the same change; do not keep a forwarding shim |
| Freeze a specific function after its module already holds a whole action family | Add an exemption for one call when the lower module only needs a group of actions | The exemption hides that the code belongs in a lower layer and leaves a permanent, narrow exception | When the dependency is one cohesive group of actions, extract the group to a lower module and shrink the baseline instead of adding an exemption |
| Retarget only the source after moving a symbol | Patch the old import site in tests and trust the green result | The patch targets a name the moved code no longer reads, so the test passes without exercising the stub | Retarget each patch, mock, and monkeypatch boundary to the new import site in the same change |

## Results & Parameters

The motivating ProjectHephaestus issue #2233 plan was reviewed and refined, but
not implemented during this learning session. A read-only AST scan on
2026-07-20 confirmed the proposed current-source inventory:

| Parameter | Observed / proposed value | Notes |
|-----------|---------------------------|-------|
| Product root | `hephaestus/automation/` | Exceptions remain automation-only |
| Legacy modules | `claude_invoke`, `claude_models`, `claude_timeouts` | The latter two are compatibility shims over `agent_config` |
| Exact consumer/module pairs | 30 | Frozen membership is the normative test input |
| Distinct consumer files | 18 | A file importing two legacy modules contributes two pairs |
| `claude_invoke` pairs | 16 | Includes a diagnostics-only consumer |
| `claude_models` pairs | 14 | Compatibility-export consumers |
| `claude_timeouts` pairs | 0 | State the zero explicitly so no consumer is implicitly approved |
| Runtime state | Direct runner executes Codex and Pi; Claude remains on the legacy invocation path | Do not document a completed provider-neutral facade |
| Verification level | unverified | Inventory observed locally; proposed guard, ADR edit, focused tests, and CI are pending |

Proposed focused verification for the Hephaestus example:

```bash
uv run pytest tests/unit/validation/test_adr_0005_direct_import_policy.py -v --override-ini=addopts=
uv run pytest tests/unit/validation/test_automation_boundary.py tests/unit/validation/test_import_surface.py -v --override-ini=addopts=
uv run pytest tests/unit/validation/test_adr_0005_direct_import_policy.py tests/unit/docs/test_adr_records.py -v --override-ini=addopts=
```

Promote this skill to `verified-local` only after the ADR and guard are
implemented and all focused commands pass. Promote it to `verified-ci` only
after the corresponding PR's CI succeeds.

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| ProjectHephaestus | Issue #2233 implementation planning and review | Read-only source inventory confirmed on 2026-07-20; no implementation PR, focused test run, or CI result was available. |
| An isolated service-restructuring checkout | Upward service-to-command-layer edges, 2026-11-01 | One change moved a cohesive action group out of the command-layer module into a new lower module, updated the layer-policy file, and retargeted the affected test patches. CI was not observed in the learning session, so no verification claim is made. |
