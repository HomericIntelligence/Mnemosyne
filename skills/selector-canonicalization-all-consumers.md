---
name: selector-canonicalization-all-consumers
description: "Canonicalize friendly selector input at an adapter boundary and route every raw-selector consumer through canonical accessors. Use when aliases, filenames, or shorthand are added above a strict registry or resolver."
category: architecture
date: 2026-11-20
version: "1.0.0"
user-invocable: false
tags:
  - selectors
  - canonicalization
  - adapters
  - registries
  - api-compatibility
  - ambiguity
---

# Canonicalize Selectors for Every Consumer

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-20 |
| **Objective** | Add friendly selector forms without changing a strict lower-level contract or leaving direct consumers on the raw input. |
| **Outcome** | Successful. One adapter-owned interpretation supplies each consumer with the canonical value that it needs. |

## When to Use

Use this skill when all of these conditions apply:

- A CLI, API, or other adapter accepts a selector for an entry in a canonical registry.
- The new input forms include an identifier, filename, alias, or shorthand in addition to the existing canonical form.
- More than one downstream consumer reads the selector or its resolved value.
- Existing public, service, or internal callers depend on strict lower-level validation.

Do not use this rule to add ambient selection, remove an explicit selector, or weaken validation for callers that require a canonical value. Keep those decisions in their own boundary contracts.

## Verified Workflow

### Quick Reference

Canonicalize friendly input in the adapter, not in the shared strict registry. Inventory every raw-selector consumer. Route each one through the narrowest canonical accessor that supplies its needs. Reject unknown and ambiguous input before the operation starts.

### Suggested Approach

1. **Keep the existing authority.** Reuse the registry's declared identities, filenames, paths, and selection rules. Do not construct a canonical identifier by string concatenation or infer it from an unrelated hostname or environment value.
2. **Give the adapter one interpretation.** Add one canonicalization function at the adapter boundary. Exact canonical input keeps its current behavior. Friendly forms resolve only through declared registry data and existing selection authority.
3. **Preserve the lower-level contract.** Let direct registry and service callers keep strict validation. An adapter convenience must not silently become a new global input contract.
4. **Inventory consumers before editing.** Search for reads of the raw field, not only calls to the primary resolver. Include operation-target construction, path-only lookups, diagnostics, metadata, and secondary helpers.
5. **Select the narrowest canonical view.** Give each consumer only what it needs:
   - a fully resolved operation target when the operation needs credentials, endpoints, or other bound state;
   - a canonical registered path when a consumer needs only the path;
   - a canonical identity when a consumer needs only metadata.
6. **Avoid unrelated side effects.** When full target resolution acquires credentials, opens sockets, or initializes service identity, use a lazy path-only or identity-only accessor backed by the same canonicalizer. Do not make a simple lookup pay for full operation setup.
7. **Fail before effects.** Reject an unknown or ambiguous friendly form before credentials, connections, mutations, or host selection. Name the valid corrections or viable candidates. Never select the first match.
8. **Test the consumer boundary.** Use behavior tests for every accepted form, each direct consumer, strict legacy callers, unknown input, ambiguous input, and side-effect-free narrow accessors.

A single canonicalization function does not require eager resolution or global caching. Add memoization only when repeated work or consistency requirements justify it.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Primary resolver only | The initial plan canonicalized the selector inside the main operation-target resolver. | Review found that direct consumers still read the raw field and would reject or misinterpret friendly input. | Inventory every raw-value consumer and route it through a canonical accessor. |
| One resolved-value shape | The initial design had no path-only canonical accessor for direct path consumers. | Those consumers either stayed on raw input or needed full target resolution with unrelated credential, connection, and service-identity effects. | Add a lazy path-only accessor backed by the same canonicalizer. |

## Results & Parameters

### Decision Table

| Condition | Required behavior |
| --------- | ----------------- |
| Exact registered path or other existing canonical form | Preserve current validation and compatibility behavior. |
| Unique declared identifier, filename, or alias | Resolve to the same canonical entry through the adapter. |
| Shorthand with existing selection authority | Reuse that authority; do not synthesize a new identifier. |
| Unknown shorthand | Refuse before side effects and name useful corrections. |
| Multiple viable entries | Refuse before side effects and name the ambiguity. |
| Existing strict lower-level caller | Keep its current contract unchanged. |
| Consumer needs only a path or identity | Use a narrow canonical accessor without full operation setup. |

### Expected Output

- All accepted friendly forms produce the same canonical entry as the existing exact form.
- No downstream consumer interprets the raw alias independently.
- Direct strict callers see no new accepted input forms.
- Unknown and ambiguous inputs produce deterministic, actionable errors before operation effects.
- Path-only and identity-only consumers do not trigger unrelated credential, socket, or service-identity setup.
- Behavior tests cover direct consumers and failure branches, not only the primary resolution path.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Administrative CLI (privacy-generalized) | Friendly registry selectors above a strict path registry | Behavior tests and independent implementation review passed. Proprietary identifiers are omitted. |
