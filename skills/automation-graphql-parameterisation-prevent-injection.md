---
name: automation-graphql-parameterisation-prevent-injection
license: BSD-3-Clause
description: "Safely parameterise GitHub GraphQL calls without query injection or gh CLI file expansion. Use when: (1) binding dynamic strings or integers with gh api graphql, (2) handling agent-generated bodies or other strings that may begin with @, (3) centralising GraphQL argv construction, (4) testing the exact -f versus -F transport contract."
category: tooling
date: 2026-08-07
version: "2.0.0"
user-invocable: false
verification: verified-local
history: automation-graphql-parameterisation-prevent-injection.history
tags:
  - graphql
  - parameterisation
  - injection-prevention
  - gh-api-graphql
  - variable-binding
  - raw-field
  - typed-field
  - file-expansion
  - security
  - github-cli
---

# Safe GitHub GraphQL Parameterisation

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-08-07 |
| **Objective** | Bind dynamic GraphQL variables without interpolating them into the query document and without allowing GitHub CLI to interpret leading-`@` string values as local file references. |
| **Outcome** | Successful locally. A central Python transport now sends every string variable with raw `-f` and every integer variable with typed `-F`; argv regressions cover agent reply bodies and GraphQL integers. |
| **Verification** | `verified-local` — 7,345 tests passed with 83.95% coverage, including leading-`@` regressions; Ruff, mypy, and pre-commit passed. CI and a live GitHub mutation remain pending. |
| **History** | [changelog](./automation-graphql-parameterisation-prevent-injection.history) |

Parameterisation and CLI encoding are separate safety decisions:

1. Put dynamic data in GraphQL variables instead of interpolating it into the query.
2. Choose the GitHub CLI flag from the value's required GraphQL type.

For the common Python boundary `int | str`, use raw `-f` for every string and
typed `-F` only for integers. GitHub CLI's typed-field parser treats a value beginning
with `@` as a file reference; raw-field transport preserves the string verbatim.

## When to Use

- A `gh api graphql` call binds owner, repository, cursor, node ID, commit SHA,
  mutation ID, review body, or other string variables.
- A string may originate in agent output, user input, GitHub data, or any source that
  can legitimately begin with `@`.
- A GraphQL `Int` variable must remain numeric instead of becoming a JSON string.
- Multiple GraphQL call sites share one transport helper and should not duplicate
  encoding policy.
- An existing test only checks that `-F` appears somewhere in argv instead of
  proving the flag associated with each value.

## Verified Workflow

> Verified locally only — CI validation pending.

### Quick Reference

```python
def graphql_argv(query: str, **fields: int | str) -> list[str]:
    argv = ["api", "graphql", "-f", f"query={query}"]
    for key, value in fields.items():
        argv.extend(["-F" if isinstance(value, int) else "-f", f"{key}={value}"])
    return argv
```

```bash
gh api graphql \
  -f 'query=query($owner:String!,$body:String!,$number:Int!){...}' \
  -f owner=HomericIntelligence \
  -f 'body=@/etc/passwd' \
  -F number=7
```

### Detailed Steps

1. **Parameterise the query document.** Declare variables such as
   `$owner: String!`, `$body: String!`, and `$number: Int!`. Never interpolate
   caller-controlled values into GraphQL syntax.

2. **Keep the query document raw.** Pass `query=<document>` with `-f` so the
   document remains a string.

3. **Select the variable flag by the Python value type.** For an `int | str`
   boundary, pass `int` with `-F` and `str` with `-f`. This retains JSON numeric
   conversion for GraphQL `Int` while avoiding typed-field file expansion for
   strings.

4. **Centralise transport construction.** Put this selection in the one helper
   through which all GraphQL calls flow. Do not special-case reply bodies or encode
   selected call sites differently.

5. **Audit every call site's value types.** Search all calls to the transport and
   classify each variable. In the verified ProjectHephaestus case, only PR numbers
   were integers; owner/name, cursors, bodies, thread/review/node IDs, SHAs, and
   generated mutation IDs were strings.

6. **Test exact argv adjacency at the external boundary.** Mock the function that
   invokes `gh`, exercise a real domain path for untrusted text, and assert the flag
   immediately before each `key=value` entry:

   ```python
   body_index = argv.index("body=@/etc/passwd")
   assert argv[body_index - 1] == "-f"
   assert argv[argv.index("number=7") - 1] == "-F"
   ```

7. **Run the focused regression, the owning adapter suite, lint, type checks, and
   repository-wide guards.** A centralized transport change can affect every caller,
   and line-count or architecture budgets may sit outside the focused module.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Raw value interpolation | Insert dynamic values directly into the GraphQL document. | Caller-controlled data can alter query syntax and create an injection surface. | Keep the document static and bind variables separately. |
| Blanket typed fields | Send every GraphQL variable with `-F/--field`. | GitHub CLI interprets values beginning with `@` as local file references; a string such as `@/etc/passwd` is not preserved as text. | Use raw `-f` for strings and reserve `-F` for values that need typed conversion. |
| Blanket raw fields | Send integers and strings alike with `-f/--raw-field`. | GraphQL `Int` variables arrive as strings instead of JSON numbers and can fail type validation. | Keep integer variables on typed `-F`. |
| Call-site body escaping | Special-case only the known agent reply body. | Other strings—cursors, IDs, owner/name, SHAs, or future inputs—still inherit unsafe transport behavior. | Fix the centralized argv builder and audit all callers. |
| Loose argv assertions | Assert only that both `-f` or `-F` appear somewhere. | The test can pass while a particular value is paired with the wrong flag. | Assert the element immediately preceding each exact `key=value`. |

## Results & Parameters

The verified transport contract is:

| Python value | GraphQL use | GitHub CLI flag | Result |
|--------------|-------------|-----------------|--------|
| `str` | `String`, `ID`, `GitObjectID`, cursor | `-f` | Preserved verbatim, including leading `@` |
| `int` | `Int` | `-F` | Converted to a JSON number |
| query document | `query=` parameter | `-f` | Preserved as text |

Verified ProjectHephaestus evidence:

- Issue #2526 / PR #2698 changed the centralized
  `PipelineGitHub._graphql()` transport.
- Two parameterized values, `@/etc/passwd` and `@relative-secret`, were exercised
  through the real thread-reply path and paired with `-f`.
- Repository owner and name were paired with `-f`; PR number `7` remained paired
  with `-F`.
- All seven transport call sites were audited. Only PR numbers required typed
  handling.
- The full local pre-push suite passed: 7,345 passed, 12 skipped, 5 deselected,
  83.95% coverage.
- The first full-suite run exposed an unrelated-to-behaviour integration constraint:
  the transport collaborator has a 400-line architecture budget. Expressing the
  type choice without adding a physical line preserved that invariant.

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| ProjectHephaestus | Issue #2526 / PR #2698 | Centralized GraphQL transport hardening with argv-level leading-`@` regressions |
| ProjectHephaestus | Full local pre-push suite | 7,345 passed, 12 skipped, 5 deselected; 83.95% coverage |
