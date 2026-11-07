---
name: source-literal-census-profile-enforced
license: BSD-3-Clause
description: "Count and freeze every source literal of a configuration value before you convert it to profile-enforced configuration. Use when a plan turns a hard-coded identity, name, path, or limit into a declared configuration field and an acceptance criterion says that no module must resolve the value from a literal; also when the repository already carries schema-level literal types (Literal, StrEnum, a closed grant table) that must restate the value."
category: architecture
date: 2026-11-07
version: "1.0.0"
user-invocable: false
verification: unverified
tags:
  - planning
  - configuration
  - profile
  - literal-census
  - frozen-baseline
  - schema-pin
  - acceptance-criterion
  - testability
  - exemption-rationale
  - silent-scope-inflation
  - guard-conversion
  - constant-home
  - import-layers
---

# Source Literal Census Before Profile-Enforced Configuration

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-07 |
| **Objective** | Plan a change that moves one hard-coded value (a required account, group, path, or limit) into a declared configuration field, and make the acceptance criterion "no module resolves the value from a literal" testable and honest |
| **Outcome** | Four plan revisions were rejected in review until the plan carried a measured literal census, one disposition per literal class, and one outcome per guard. The revised plan converged. |
| **Verification** | unverified — plan only; no conversion was implemented and no frozen census test was run |

## When to Use

Apply this skill when any condition holds:

- A plan turns a module constant into a declared configuration field, and one acceptance criterion
  requires that no source module resolves the value from a literal while configuration is active.
- A rough measurement of the literal appears in the issue ("a literal in five other modules"), and
  the plan must decide which sites to convert.
- The repository already restates the value in schema-level literal positions: a `Literal[...]`
  annotation, a string-valued enum, a closed grant table, or a SQL predicate over such a column.
- A guard function must gain a value that was a constant. A guard is called on a request path, or a
  test seam or fixture builds the object under test.

## Verified Workflow

> **Warning:** This workflow has not been validated end-to-end. It comes from plan reviews only.
> Treat it as a hypothesis until a conversion lands and its frozen census test runs in CI.

### Quick Reference

```bash
# 1. Measure before you plan. Count string constants, exact and substring, per file.
python3 - <<'PY'
import ast
from pathlib import Path
exact = {}
partial = {}
for path in sorted(Path("src").rglob("*.py")):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if node.value == "TARGET.VALUE":
                exact[str(path)] = exact.get(str(path), 0) + 1
            elif "TARGET.VALUE" in node.value:
                partial[str(path)] = partial.get(str(path), 0) + 1
print("exact", sum(exact.values()), "in", len(exact), "files")
print("partial", sum(partial.values()), "in", len(partial), "files")
PY
# 2. Split the exact hits into running comparisons, data rows, and schema pins.
grep -rn '"TARGET.VALUE"' src/ | sed 's/:.*//' | sort | uniq -c | sort -rn
```

### Detailed Steps

1. **Count before you plan.** Use an `ast` walk, not `grep`, and record two numbers per file: exact
   string constants and constants that only contain the value as a substring. Report both counts and
   the file count. A `grep` line count mixes code, messages, docstrings, and tests, and an issue
   never reports the substring class. A review will reject a census that cannot be reproduced.
2. **Classify every exact hit into one of four classes, and name the line of each:**
   - **running comparison** — the value is compared or resolved at a guard, check, or request path;
   - **data row** — the value is a field of a policy, grant, or vocabulary table;
   - **schema pin** — the value is required by a literal type: a `Literal[...]` annotation, an enum
     member, or a column predicate that a migration seeds;
   - **inert** — a default evaluated at class-definition time, a test seam, or an audit-attribution
     constant.
3. **Convert only the running comparisons that hold or receive a configuration object.** A
   comparison inside a context-free helper (a principal-to-ID selector, a numeric resolver) has no
   configuration in scope. A conversion there changes behavior for every caller and is not the
   issue's requirement. Name it exempt with the reason, not with a silent omission.
4. **Name the schema pins once, and state the consequence in one rule.** The value cannot come from
   configuration while a literal type forbids other values, so a configured value that differs is a
   hard refusal at the running guard. Write this as one sentence of the rule. Do not claim the site
   is "converted" and also that the value is "validated at schema level": those two statements give
   different behavior, and a reviewer will find the gap.
5. **Add a frozen census test as the acceptance evidence.** The test walks the source and asserts
   both maps (exact and substring) against one table that holds every file. Converted files get an
   expected post-change count, including `0`; every other file is frozen at its measured count. A
   test that lets a converted module hold or drop any literal cannot prove the criterion.
6. **Never test a prohibition with a source scan without a per-file table.** The repository may
   forbid such scans for other rules. Check the repository contract first. When the same test file
   already validates behavior, keep the census next to it, and keep the runtime tests as the proof
   of the refusal messages.
7. **Decide where the constant lives by the import layers.** When the value must be a schema default
   and the schema module is in a higher layer than an existing core holder, the constant lives in
   the core module and the schema module imports it. The reverse edge fails an import-layer gate.
   Keep exactly one constant per value and delete every re-export.
8. **Give each guard one read and one outcome for an absent configuration.** The binder loads the
   configuration once and holds the value beside its other derived attributes; the request-path
   guard compares a held value and reads no file. State what happens when the configuration is
   absent: one refusal at bind or command entry, or one typed finding at the install check. Do not
   let a guard that runs per request gain an unbounded file read and an untyped error.
9. **Update every fixture that omits the new required field, and name those tests in the plan.** A
   required field breaks every construction site and every fixture profile, including fixtures of
   clusters that have no shipped profile. List the tests, and say which directory the fixture
   supplies.
10. **Remove plan-only checks.** If an issue scope names one behavior (a configured value that
    differs from the deployment contract), do not add a second check (host presence of the value)
    with no scope item. A reviewer reads the added check as scope inflation.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| ------- | ---------------- | --------------- | -------------- |
| Cite the issue count as the census | The plan reused the issue count of literal files | The issue counted a few named modules; an `ast` walk found hundreds of exact constants in more than twenty files, and a review rejected the count as wrong | Measure with an `ast` walk and report exact and substring counts per file |
| Convert every literal | One design converted the running comparisons, the policy-table rows, the type annotations, and the document messages | The table rows and the annotations cannot read configuration, the conversion of a context-free resolver changes behavior for all callers, and the frozen count could not tell "converted" from "dropped" | Classify every hit; convert running comparisons; name the other classes exempt with a reason |
| Move the constant next to the schema | The constant moved into a higher-layer schema module and a core module imported it | The import-layer gate forbids a core module from importing a higher layer, and the plan's claim about the module's imports was false | Put the constant in the core module; let the schema import it; delete the re-exports |
| Keep a fallback that fabricates a configuration object | When no configuration file existed for a test cluster, the check built a default object from a module constant | The fabricated default turned a missing value into a pass-by-default, the refused behavior the issue supersedes, and it hid the required-field break in the lanes that used that cluster | One outcome for an absent configuration: one typed refusal that names the path and the absent keys |
| Let the request-path guard load the configuration | The guard function called the loader on each call | The guard runs per request, and it had no stated outcome when the file was absent | Load once at bind, hold the value, and compare on the request path |
| Add a host-presence check for the new value | The plan added a second refusal for a value with no host account | No issue scope item names it, and the existing contract already bounds the value | Add only the check the scope names; remove the extra refusal |

## Results & Parameters

### Configuration

```yaml
literal_conversion:
  measure: ast_walk            # exact and substring, per file
  convert: running_comparison  # only where a configuration object is in scope
  exempt_classes: [data_row, schema_pin, inert]
  evidence: frozen_census_test # per-file exact and substring table
  guard_read: once_at_bind     # request path compares a held value
  absent_configuration: typed_refusal # one outcome, no fabricated default
```

### Expected Output

- A census table with, for each file, the exact and substring counts before and after the change.
- One sentence that states what the configured value cannot be, and where the refusal happens.
- A frozen census test that fails when any file drifts in either count.
- A guard table with one read point and one absent-configuration outcome per guard.

## Verified On

| Project | Context | Details |
| ------- | --------- | ------- |
| (planning session, 2026-11) | Plan review of a change that moved a required account and group into a declared profile | `unverified` — the plan converged after four revisions; no conversion landed in this session |

## References

- [Verify issue premises before implementing](planning-verify-issue-premise-before-implementing.md)
- [Frozen registry guard co-update](planning-frozen-registry-guard-co-update.md)
- [Consolidate duplicated silent defaults](pola-consolidate-duplicated-silent-default-resolver.md)