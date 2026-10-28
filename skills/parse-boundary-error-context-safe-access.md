---
name: parse-boundary-error-context-safe-access
license: BSD-3-Clause
description: "Build typed-error context with safe access at fail-closed parse boundaries. The partially parsed fields that triggered the failure are exactly the fields that may be absent, so strict indexing inside the error path turns the intended typed, redacted diagnostic into an opaque KeyError. Use when a typed domain error surfaces as KeyError, or when writing the rejection branch of a record, provenance, or configuration parser."
category: architecture
date: 2026-10-28
version: "1.0.0"
user-invocable: false
verification: verified-local
tags: [error-handling, fail-closed, parse-boundary, keyerror, dict-access, redaction, python, validation]
---

# Parse Boundary: Typed Error Context Needs Safe Access

## Overview

| Field | Value |
|-------|-------|
| Date | 2026-10-28 |
| Objective | Keep a fail-closed parse boundary raising its typed domain error, never a KeyError from the error path itself. |
| Pattern | Collect optional fields from the untrusted source with safe access into a partial map. Prove completeness once. Build the context of every rejection raised before that proof with safe access (`mapping.get(key)`), and reserve strict indexing for the success path after completeness is proven. |
| Outcome | Incomplete or malformed input produces the typed error with whatever safe context exists, such as a redacted role and content identity. The caller sees the domain diagnostic, not a bare KeyError. |
| Verification | verified-local — a boundary test that removed one required provenance role caught the KeyError; after the fix the same test passed and the focused parser and integration suites were green. |

## When to Use

Trigger phrases that should route to this skill:

- "typed error raises KeyError instead"
- "the error path itself crashes"
- "KeyError from a rejection branch"
- "incomplete record crashes the parser's own error handling"
- "typed exception replaced by KeyError"
- "error context built from fields that failed"

Trigger situations:

- A parser collects optional fields from a mapping, then raises a typed error for missing fields and builds that error's context by indexing the same mapping.
- A rejection branch references a field such as an identity or content digest that is only present when the record is well formed.
- A test removes one required field and expects the typed error, but observes KeyError.
- An error contract promises redacted output, and the KeyError bypasses it.

## Verified Workflow

### Quick Reference

```python
fields = {name: raw for name in suffixes if isinstance(raw := data.get(prefix + name), str)}
missing = sorted(set(suffixes) - set(fields))
if missing:
    raise TypedParseError(
        "record is incomplete",
        # Safe access: the missing fields are the failure trigger, so any
        # field may be absent here.
        identity=fields.get("identity"),
    )
# Strict indexing is correct only after completeness is proven.
return Record(identity=fields["identity"], ...)
```

1. Inventory every raise site between field collection and the completeness proof. Each one may run on a partial map.
2. Build error context with safe access at those sites. A `None` context is acceptable when the typed error treats it as absent and omits it from the message.
3. Wrap the remaining model construction in the typed-error translation (`except ValidationError as exc: raise TypedParseError(...) from exc`). That wrap does not protect the earlier raise sites.
4. Add one boundary test per rejection branch that removes a different required field, including the field used for error context. A single malformed-record test cannot distinguish a typed rejection from a KeyError in the error path.
5. Run the focused parser tests and confirm the typed error message still contains no secrets, paths, or payload content.

### Worked Examples

| Example | Symptom | Authority Check | Correct Action |
|---|---|---|---|
| Provenance role parser in a serving runtime | A test that dropped one whole role from component provenance expected the typed role error and observed `KeyError: 'content_identity'` from the incomplete-record raise. | The raise site built its context with `fields["content_identity"]`; the same field was in the missing set. | Build the context with `fields.get("content_identity")`; keep strict indexing on the success path. |
| Identity-mismatch rejection | A malformed revision kind reached a later raise that also indexed the identity field. | The identity field is optional by construction because collection precedes the completeness proof. | Use safe access for the identity at every pre-proof raise site. |

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|-------|----------------|---------------|----------------|
| Wrap only the constructor call | Added `try/except ValidationError` around model construction and treated the boundary as fail closed. | The crash happened earlier, in an incomplete-input raise that built context with strict indexing. | Every raise site over partially parsed fields needs safe access, not only the final constructor wrap. |
| Trust the happy-path test suite | Relied on tests that supply complete records. | Complete records never exercise the rejection branches where the partial map is indexed. | Test each rejection branch with one distinct missing field. |
| Raise with a generic message and no context | Considered dropping the identity from the error entirely. | Callers lose the safe correlation data the error contract promises. | Safe access preserves redacted context; it does not force an empty diagnostic. |

## Results & Parameters

Use these parameters when implementing or reviewing a parse boundary:

```yaml
parse_boundary_contract:
  collection: "safe access into a partial map"
  completeness_proof: "one explicit check that the required field set is present"
  pre_proof_raises: "error context via mapping.get(key); None allowed and omitted"
  post_proof_access: "strict indexing permitted"
  test_matrix: "one boundary test per required field, asserting the typed error type"
  redaction: "error message carries only safe identifiers; no payload, path, or secret"
```

Canonical decision rule:

```text
raise site before the completeness proof -> build context with safe access
raise site after the completeness proof  -> strict indexing is correct
KeyError observed from a typed boundary  -> find the strict index in the error path
```
