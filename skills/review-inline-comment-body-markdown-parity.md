---
name: review-inline-comment-body-markdown-parity
description: "Validate every inline review-comment body with the same strict Markdown parser that the delivery helper applies, before handing the batch to a carrier publisher. Use when: (1) you prepare inline finding comments for a review carrier and the carrier itself already parses, (2) a publish or delivery attempt rejects a comment body as an open HTML block or an open code fence, (3) comment bodies contain path or identifier placeholders written with angle brackets, such as a generic user-home or session-file placeholder, (4) you must decide whether a passing carrier extraction proves the inline batch is publishable, or (5) you need a bounded pre-publication check that costs no forge write."
category: ci-cd
date: 2026-11-02
version: "1.0.0"
user-invocable: false
tags: [pull-request, code-review, markdown, validation, fail-closed, inline-comments]
---

# Validate Inline Comment Bodies with the Carrier Parser

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-02 |
| **Objective** | Catch an unpublishable inline comment batch before any forge write, by applying the delivery helper's own strict Markdown parser to each comment body. |
| **Outcome** | Operational. A carrier body parsed clean and its extraction succeeded, yet the delivery helper rejected the batch at pre-publication validation because two comment bodies contained bare angle-bracket placeholders. Wrapping each placeholder in inline code spans cleared the rejection with no change to the finding identities, the state envelope, or the visible content. The write attempt failed closed with zero forge mutation. |

## When to Use

- You prepared inline finding comments for a pull request review carrier.
- The carrier or visible content parses, and you are tempted to conclude the whole batch is valid.
- A helper rejects a comment body with an open HTML block or open code fence error.
- Comment bodies quote path or identifier placeholders that use angle brackets.
- You want a bounded pre-publication check that makes no forge write.

## Verified Workflow

### Quick Reference

Parse each comment body with the same parser the helper uses, before publication:

```bash
python3 - <<'PY'
import json, sys
sys.path.insert(0, "<review-exchange-skill>/scripts")
import review_exchange

for comment in json.load(open("<inline-comments>.json")):
    try:
        review_exchange.top_level_markdown_lines(comment["body"], require_closed=True)
        print("OK  ", comment["path"], comment["line"])
    except review_exchange.ProtocolError as error:
        print("FAIL", comment["path"], comment["line"], "->", error)
PY
```

An inline comment body is valid only when this call succeeds. A carrier extraction that
succeeds proves the carrier and visible content, not the comment bodies.

### Suggested Approach

1. **Identify the parsers.** A review carrier, its visible content, and each inline
   comment body are validated by separate call sites. A green check on one says
   nothing about the others. Treat "the carrier extracted" as evidence about the
   carrier only.
2. **Parse every body with the helper's own function.** Do not write a regex that
   approximates the rule. Call the same strict Markdown validator the helper calls,
   with its closed-block requirement enabled. This keeps the check honest when the
   parser changes.
3. **Find the real cause, not the symptom.** The open-HTML-block rejection is caused
   by a bare angle-bracket placeholder, because a Markdown parser reads it as an
   unclosed inline HTML tag. The same failure class appears with an unclosed code
   fence. Both are body-formatting defects, not content defects.
4. **Repair with the smallest edit that changes no identity.** Wrap each placeholder
   in inline code spans. Keep the finding text, the finding identifier, the location,
   the visible content, and the state envelope unchanged. A body fix must not force a
   new reduce pass or a new visible-content digest.
5. **Re-parse after the edit.** Confirm every body passes before the next publication
   attempt. Rebuild only the comment list, not the state.
6. **Classify the rejection correctly.** A pre-publication input rejection is safe:
   fix the input and resubmit. Confirm the forge shows no partial mutation, then retry.
   Do not treat it as a carrier-history structural rejection.
7. **When the helper is unavailable,** still apply the invariant: no comment body may
   contain a bare angle-bracket placeholder or an unclosed code fence. Wrap
   placeholders in code spans. State the check as a manual review step.

### Diagnostics

| Rejection text | Cause | Repair |
| ---------------- | ------- | -------- |
| `The Markdown body contains an open HTML block.` | A bare `<placeholder>` is read as an unclosed inline HTML tag. | Wrap the placeholder in inline code spans. |
| `The Markdown body contains an open code fence.` | An odd number of fence openers, or an opener without its closer. | Close every fence. |
| Marker is not a top-level line or is in an open block | A finding marker sits inside an unclosed block. | Close the block so the marker is the final top-level line. |

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ------------ |
| Validate the carrier only | Confirmed that carrier extraction and visible-content parsing both succeeded, then handed the batch to the delivery helper | Extraction and visible parsing use different validators than the inline comment bodies; the helper rejected the batch at pre-publication validation | A passing carrier check is not evidence about the comment bodies. Parse each body with the helper's own validator. |
| Repair by rewriting the finding prose | Considered shortening the sentences that held the placeholders | Changes finding text and risks changing identities for a formatting defect | Repair the formatting only. Wrap the placeholder in a code span and keep the text and identifiers unchanged. |

## Results & Parameters

### Configuration

Bare placeholders that a strict Markdown validator rejects, and their accepted forms:

| Form | Result |
| ------ | -------- |
| `/home/<user>` | Rejected: open HTML block |
| `` `/home/<user>` `` | Accepted |
| `<session>.jsonl.tmp` | Rejected: open HTML block |
| `` `<session>.jsonl.tmp` `` | Accepted |
| Unclosed triple-backtick fence | Rejected: open code fence |
| Closed fence | Accepted |

### Expected Output

- One line per comment body, marked OK or FAIL with its path and line.
- Zero FAIL lines before you hand the batch to the publisher.

## Verified On

| Project | Context | Details |
| -------- | --------- | ------- |
| Internal review tooling | Terminal pull-request review delivery | A pre-publication rejection with no forge mutation, a code-span repair, and a successful retry. See [notes](review-inline-comment-body-markdown-parity.notes.md). |

## References

- [Review exchange terminal manifest construction](review-exchange-terminal-manifest-construction.md)
- [Review exchange terminal carrier sole publisher](review-exchange-terminal-carrier-sole-publisher.md)