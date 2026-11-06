# Supporting evidence: request opt-out capture contract

This file holds the session detail behind the main skill. It is not part of
normal retrieval.

## Source shape

The source system had three layers:

| Layer | Behavior |
| ------- | -------- |
| A header parser in a small module | Returned a boolean, and raised one error for any value other than the six listed values. The error message named the header and the values. |
| A request handler | Read the full header list for the marker, refused more than one copy, and parsed the single value. The refusal happened before generation, metering, and the store factory. |
| A header filter | Listed the marker with the headers that the proxy consumes and never forwards. |
| A per-request store | Wrote a trace directory only when the marker was false. The trace held request bytes, response bytes, and a metadata file. The access event was written on every path through one event builder. |

## The path that cannot opt out

A batch runner built its forwarding headers from a job record. The set held
the user identity, the batch identity, the workload label, and the scheduling
priority. The runner had no user header path, so it could not send the marker.
The access event and the trace were therefore written for each batch request.

The documentation states this as a limitation. The alternative, adding the
marker to the runner header set, is a code change with its own test needs.

## Documentation placement

- One new owner page held the value table, the rejection rules, the examples,
  and the limits.
- The user guide kept one short item and linked to the owner page.
- The component page that owns the capture gained one paragraph and a link.
- The documentation index table and the site navigation both listed the page.

## Verification commands

| Command | Result |
| ------- | -------- |
| `uv run --locked --extra dev mkdocs build --strict` | Pass. The build printed one informational line for an unrelated page that this change did not touch. |
| `rg -n "<marker-header>" docs/` | Confirmed one owner page plus the linked summaries. |

## Editorial notes

- The value table and the rejection rules appear one time. The other pages
  link to them.
- The page named four items that continue: metering, the access event,
  upstream processing, and the header strip. Naming the continuing items is
  what prevents a false promise of full anonymity.