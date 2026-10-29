# Notes: http-response-rewrap-double-decode

Privacy-safe supporting evidence for the main entry. Provenance: LLM360/comet
issue #3235 and pull request #3239 (merged as squash commit `20f7f37231`).

## Failure chronology

Every deployed-branch (`prod`) push after the manual bootstrap publication
(2026-09-21) failed the `docs` workflow at the step `Authorize production
source`, with a single swallowed marker
(`::error::Documentation deployment evidence is invalid.`):

| Date | Run | Head |
| ---- | ---- | ---- |
| 2026-10-26 | 40291655345 | ffa6ac6e8c |
| 2026-10-21 | 39689791253 | 69db22968d |
| 2026-10-20 | 39467940975 | 8a7441e788 |
| 2026-10-19 | 39336723118 | 7b6af3e3fb |
| 2026-09-21 | 35632540630 | c8ea5ac241 |

The sibling `CI` workflow was green at the same heads, so this step was the
only red signal on the deployed branch. The 2026-09-21 run failed even before
the gate's pinned identity existed, because even an absent-resource (404)
response body arrives gzip-compressed: the wrapper raised during the read,
before the absence short-circuit could return.

## Local reproduction recipe (read-only)

Executed from a full checkout with a real read-only token (CLI-provided), with
the CI environment simulated: `GITHUB_EVENT_NAME=push`, `GITHUB_REF` set to the
deployed branch ref, `GITHUB_SHA` set to the run head, `GH_TOKEN` and
`GITHUB_TOKEN` set to the same token value. The gate script's internals were
called directly so the swallowed exception escaped.

- Before the repair, the first transport request raised
  `httpx.DecodingError: Error -3 while decompressing data: incorrect header
  check` (direct cause: `zlib.error` from the response-body gzip decoder).
- After the repair, the same sequence completed the full verification (both
  tag objects, the pinned release, the empty asset inventory, the deployed
  ref, a 6-commit first-parent ancestry walk, and every re-read) and returned
  `True`.

## Adjacent-cause exclusion record

Other raise sites in the same gate were checked and excluded with evidence:

- Pinned identity drift: the frozen manifest fields were compared byte for byte
  against the live provider reads (tag objects, messages, release author and
  publication timestamp, release id): all equal.
- Ancestry-walk bound: the first-parent distance from the deployed tip to the
  anchor was 6; the configured history limit is 20000. Not the cause.
- Deadline: roughly 20 sequential GETs inside a 120-second window. Not the
  cause.

## Sweep pattern for every re-wrap site in a codebase

```bash
grep -n "httpx.Response(" src/ scripts/          # httpx reconstruction sites
grep -rn "class .*Transport" src/                # subclasses that may re-wrap
grep -rn "iter_bytes\|iter_raw" src/             # consumption-layer decode points
```

Rule per site: if consumption used a decoding API (`iter_bytes`, `read`, the
plain `Response(..., json=...)` form), the accumulated bytes are decoded; a
reconstructed response must not keep `content-encoding`, `content-length`,
`transfer-encoding`. If consumption used the raw API (`iter_raw`), the
reconstructed response may keep the headers, but the size bound then meters
compressed bytes and must be re-applied after decode to mean anything.

## Review-delivery environment gap (session record)

The repository's async review path (skill-bearing subagents) failed
repeatedly in this session with credential/timeout errors; a trivial no-skill
subagent probe succeeded. The review was therefore executed inline, published
as a clearly-labeled author evidence record, and the merge decision was taken
by the operator. Recorded here as session context for the delivery path; it
does not change any claim in the main entry.
