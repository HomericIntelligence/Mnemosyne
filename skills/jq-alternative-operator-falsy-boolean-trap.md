---
name: jq-alternative-operator-falsy-boolean-trap
description: "jq's // alternative operator silently drops boolean false values, treating
  them as falsy (like null). Use when: (1) jq serialization of a boolean field returns
  empty instead of 'false', (2) a bats/bash test asserting a JSON boolean key is absent
  in output, (3) .field // empty or .field // 'default' unexpectedly skips false values."
category: debugging
date: 2026-05-09
version: "1.0.0"
user-invocable: false
verification: verified-ci
tags: [jq, bash, boolean, serialization, bats, json, falsy, alternative-operator]
---

# jq Alternative Operator Falsy Boolean Trap

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-05-09 |
| **Objective** | Serialize a boolean field from a jq filter without silently dropping `false` |
| **Outcome** | Success — replaced `//` with explicit `if-then-else`; bats test passed in CI |
| **Verification** | verified-ci |

## When to Use

- A jq expression using `.field // empty` or `.field // "default"` returns empty when the field is `false`
- A bats or bash test asserting a JSON boolean key (e.g., `"convergence"`) is missing from output despite the field existing
- You are serializing a boolean jq field to a bash string and getting unexpected empty output
- CI fails on a JSON assertion that worked when the value was `true` but breaks when the value is `false`

## Verified Workflow

### Quick Reference

```bash
# WRONG — silently drops false:
value=$(echo '{"converged": false}' | jq -r '.converged // empty')
echo "$value"   # prints nothing

# CORRECT — explicit null-check:
value=$(echo '{"converged": false}' | jq -r '.converged | if . == null then "" else tostring end')
echo "$value"   # prints: false

# CORRECT alternative — use // false to default only for null/missing:
value=$(echo '{"converged": false}' | jq -r '.converged // false | tostring')
echo "$value"   # prints: false
```

### Detailed Steps

1. **Identify the pattern**: Look for any jq expression that uses `//` on a field that could hold a boolean. The `//` operator in jq is an "alternative" operator (like Perl's `||`) that triggers on `null`, `false`, AND missing keys — not just `null`.

2. **Replace with explicit null guard**: Change `.field // empty` or `.field // "default"` to:
   ```jq
   .field | if . == null then "" else tostring end
   ```
   This preserves `false` as the string `"false"` and `true` as `"true"`.

3. **If you only want to guard against null/missing** (not false), use:
   ```jq
   .field // false | tostring
   ```
   This substitutes `null`/missing with `false`, then serializes both `true` and `false` correctly.

4. **Update tests** to assert the string `"false"` is present in output, not absent.

5. **Verify with bats**: Run the affected bats test to confirm it passes.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| `.converged // empty` | Used jq alternative operator to skip null | `false` is falsy in jq — `//` triggers on `false` too, returning empty string | Never use `//` with boolean fields; use `if . == null` instead |
| `.converged // "false"` | Tried to default to string "false" | Same root cause — `//` replaces `false` with the alternative, so output is always `"false"` even when `.converged` is `true` | The alternative operator is wrong for booleans; use `tostring` with a null guard |
| `.converged | tostring` | Direct tostring without null check | Works for booleans but crashes if field is missing (null input to tostring in strict mode) | Add `// null` guard before `tostring` or use `if . == null then "" else tostring end` |

## Results & Parameters

**Root cause:** jq's `//` operator is defined as: return left side unless it is `false` or `null`, in which case return right side. This traces to Perl's `||` semantics. Unlike most JSON tools, jq treats `false` and `null` as equivalent "alternatives" for `//`.

**jq manual quote (1.6+):** "The operator `//` produces its left-hand side if it is not `false` or `null`, and otherwise produces its right-hand side."

**Correct patterns by use case:**

```jq
# Serialize boolean to string (null-safe):
.converged | if . == null then "" else tostring end

# Serialize boolean with a specific fallback for null/missing:
(.converged // false) | tostring

# Guard in a larger object construction:
{convergence: (.converged | if . == null then null else tostring end)}
```

**Verified on:** Myrmidons PR #623 (2026-05-09). Test `tests/integration/test_verify_convergence.bats:318` was failing because the apply script used `.converged // empty`. Replaced with `if . == null then "" else tostring end`; bats test passed in CI.

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| HomericIntelligence/Myrmidons | PR #623 convergence serialization bug | `tests/integration/test_verify_convergence.bats:318` |
