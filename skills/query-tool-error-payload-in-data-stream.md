---
name: query-tool-error-payload-in-data-stream
description: "Detect that a query CLI wrote its error payload to the data stream, so a consumer that skips the exit status reads a failure as an empty or zero result. Use when: (1) a helper prints a count, list, or record set parsed from a query tool's standard output, (2) a summary reports zero items while a related command reported an error, (3) a query string is assembled inline and can be malformed, or (4) an inline filter or projection option is used to extract a value."
category: tooling
date: 2026-11-08
version: "1.0.0"
user-invocable: false
tags: [query-cli, exit-status, pipefail, json-errors, empty-result, false-negative, gh-cli, graphql, jq, fail-closed]
---

# Query Tool Error Payload in the Data Stream

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-08 |
| **Objective** | Prevent a failed query from being reported as a valid empty result when the tool writes its error payload to the same stream as its data. |
| **Outcome** | Operational. One queue-state read reported zero entries while the query had failed, and the corrected query showed one entry already waiting. |

A query tool can write an error document to standard output and also exit
nonzero. The error document is usually valid data for the same parser. When a
consumer reads only standard output and ignores the exit status, the parse
succeeds and the answer looks authoritative. The failure becomes an empty
result instead of an error.

## When to Use

- A helper prints a count, list, or record set from a query tool's standard output.
- A summary reports zero items while a related command reported an error or a warning.
- A query or filter document is assembled inline from shell arguments.
- An inline projection option, such as a filter expression, extracts one value.
- A later action starts because the reported set looked empty.

## Verified Workflow

### Quick Reference

Check the exit status before you parse. Treat the payload as untrusted until the
status is zero and the expected outer field exists.

```bash
# Wrong: the parse succeeds on an error document, and the result reads as empty.
tool query --expr "$QUERY" | python3 -c 'print(len(parse(read_stdin())["items"]))'

# Right: fail on a nonzero status, then require the expected field.
set -o pipefail
if ! raw="$(tool query --expr "$QUERY")"; then
  echo "query failed; the result is unknown, not empty" >&2
  exit 1
fi
count="$(printf '%s' "$raw" | python3 -c '
import json, sys
document = json.load(sys.stdin)
if "errors" in document:
    raise SystemExit("query returned errors: " + json.dumps(document["errors"]))
print(len(document["data"]["items"]))
')"
```

### Suggested Approach

1. **Separate the fetch from the parse.** Keep the raw output in a variable or a
   temporary file. Do not put the parse first in a pipeline.
2. **Fail on the exit status.** Use `set -o pipefail` when a pipeline cannot be
   avoided. Without it, the exit status of the last stage replaces the status of
   the query tool.
3. **Require the expected outer field.** Read the known envelope, for example
   `data`, `items`, or `results`. An absent envelope is a failure, not an empty set.
4. **Reject an error member explicitly.** Many tools include an `errors` member
   next to, or instead of, the data member. A nonempty `errors` member makes the
   answer unknown.
5. **Do not read a missing key as zero.** Use a mandatory lookup. A default of
   `0` or `[]` on a missing key hides the same defect again.
6. **Compare the result with an independent signal.** If a related command
   reported an error, a zero result is suspect until the two agree.
7. **Keep the query validated.** Build the query once from a validated template.
   An inline query that is easy to break is easy to fail silently.

Reserve requests for input for a material design choice, such as which failure
policy a caller needs. A defect in the consumer does not need such a request.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Read the parsed result only | Piped the tool into an inline parser and used the parsed value as the count. | The tool wrote an error document to standard output and exited nonzero. The document parsed cleanly, so the missing data key produced a count of zero. | Check the exit status before you parse, and require the expected outer field. |
| Trust one zero result | Reported the empty set and concluded that no work was waiting. | The query string was malformed by an extra brace. The failure was in the request, not in the data. | A zero result after a reported error is untrusted until an independent signal agrees. |
| Rely on the pipeline status | Assumed the pipeline reported the query tool's failure. | A shell pipeline returns the status of its last stage. A successful parser hides a failed query tool. | Use `set -o pipefail`, or separate the fetch from the parse. |
| Default a missing key | Read the count with a default of zero so the helper never raised an error. | A default on a missing key converts every request failure into a valid empty result. | Use a mandatory lookup. Let an absent envelope fail. |

## Results & Parameters

| Parameter | Value | Effect |
| ----------- | ------- | -------- |
| `set -o pipefail` | enabled | A failed stage fails the pipeline. |
| Envelope check | required | An absent data envelope raises instead of reading as empty. |
| Error member check | required | A nonempty errors member makes the result unknown. |
| Missing-key default | none | An absent key raises instead of returning zero. |
| Exit-status policy | fail closed | An unknown result is never reported as an empty result. |

A tool that writes an error document to standard output is the general
condition. The specific tool, endpoint, query, and inline expression only change
the reproduction, not the rule.

The cost of the guard is one extra branch. The cost of the defect is a wrong
decision made from an authoritative-looking zero.