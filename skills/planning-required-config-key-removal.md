---
name: planning-required-config-key-removal
description: "Plan a change that adds a required configuration key and stops a hardcoded default from reaching a check. Use when a plan adds required fields to a config schema, keeps a module constant as a fallback, replaces a literal at trust-decision sites, or a later plan revision adds a helper that fills absent keys."
category: architecture
date: 2026-11-07
version: "1.0.0"
user-invocable: false
verification: verified-local
tags: [planning, config-schema, required-field, hardcoded-default, fail-closed, fallback-seam, acceptance-criteria, plan-revision, review-finding, source-of-truth]
---

# Planning: Required Config Keys Without a Silent Fallback

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-11-07 |
| **Objective** | Keep a plan that moves a hardcoded constant into required configuration from re-introducing the constant through a convenience helper. |
| **Outcome** | Successful: a plan-review loop caught the defect in one round and named the smallest correct alternative. |
| **Verification** | verified-local: one plan-review round on a config-required-field plan found a constructor helper that filled absent keys with the module constant, and required its removal before a GO. |

## When to Use

- A plan adds a required field to a config schema, and one acceptance criterion says that an absent key must fail validation with the key name.
- A plan keeps the old module constant "as the schema default" or "as the fallback".
- A plan replaces a literal at check sites that make a trust decision: account lookup, principal comparison, or path owner comparison.
- A later plan revision adds a helper, a wrapper, or a factory that supplies default values for absent keys, to avoid edits at call sites.
- A review must decide if a plan delivers an enforcement criterion or only the validation half of it.

## Verified Workflow

### Quick Reference

```text
Required key in the schema?  strict field, no default
Absent key at load time?     validation error that names the key
No profile for this context? one named fallback, one note, no block
Call-site churn?             shared test helper, not a production default
Helper fills absent keys?    refuse: it restores the constant and defeats the criterion
```

### Detailed Steps

1. **Keep the schema strict and the fallback separate.** A required field with no default gives the validation criterion. A constant is acceptable only on a path that has no configuration at all, such as a context cluster with no profile file. State that path in the plan and name the outcome it produces: a note, a refusal, or a pass.
2. **Refuse a production helper that supplies absent values.** A constructor wrapper that merges the module constant into a payload when the key is absent makes the wrapper accept what the schema rejects. When the enforcement path calls the wrapper, the enforcement criterion no longer holds, and the constant is again the effective source. The same rule covers a field default: `Field(default=...)` makes a "required" field optional.
3. **Put call-site churn in tests, not in production code.** When many constructors of the schema need the new keys, add one shared test helper and use it at each site. A production seam that exists only to avoid test edits is a defect in the design, not a convenience.
4. **Check that the verification command uses the strict path.** A check that validates a profile through the wrapper proves the wrapper, not the requirement. The criterion-1 command must load the profile with the production loader and expect the field-name error.
5. **Keep the test list and the file table consistent.** When one row says "a missing key fails" and the named test says "the helper fills absent keys", the plan states two opposite behaviours. Resolve it in the same revision.
6. **Use the trust-decision rule for literal replacement.** A site is converted when it resolves an identity or compares against an expected identity. A record, a data row, or a schema literal stays as data. State the rule in the plan so the implementer does not classify sites.
7. **Verify a layer claim with the layer map.** When the plan says a module may import another module "because both are core", read the layer list and the importers. State the measured direction and cite the importers. A direction claim that the gate contradicts invalidates the plan's justification, not the change.
8. **Prefer one name for a shared pattern.** Either import the existing pattern or declare it once. "Use the same name, or a local copy" re-introduces the duplicate that an earlier round removed.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Default the required field with the module constant | `Field(default=CONSTANT)` on a schema field that the criterion says must be required | The default applies, validation passes, and the constant stays the source of truth | A default and a required-field criterion cannot both hold; use a strict field |
| Fallback constructor for old callers | A classmethod that merges the constant into the payload when a key is absent, so existing callers and tests do not change | The enforcement path used the wrapper, so a profile without the key installed and silently enforced the literal; the file table and the named test then described opposite behaviour | Keep the schema strict; move call-site churn into a shared test helper; keep the no-configuration fallback on one named path only |
| Layer claim from intuition | Justified a re-export with "no core module imports that module, so the check stays green" | The layer list ranked the target as core and the importer as service, and an existing core module already imported it | Read the layer map and grep the importers before you write the direction |

## Results & Parameters

- Required field: `name: str = Field(pattern=...)` with no default.
- Enforcement path: the production loader, not a constructor wrapper.
- Test churn: one shared helper for every constructor site.
- No-configuration path: one named branch with a stated outcome.
- Identity sites: convert trust decisions only.
- Layer claims: cite the layer list entry and the importers.