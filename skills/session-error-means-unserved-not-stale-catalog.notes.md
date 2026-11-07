# Notes: session-error-means-unserved-not-stale-catalog

Supporting evidence for [session-error-means-unserved-not-stale-catalog](session-error-means-unserved-not-stale-catalog.md).
Current rules stay in the main skill. This file holds the execution evidence.

## Privacy check

This file is a generalized record. It holds no person, account, organization,
repository, host, path, issue, or product identifier. It holds no proprietary
source. The commands and values are the generic form of what was run.

## Provenance

- Lesson date: 2026-11-07.
- Source: one agent session that diagnosed a reported model-list fault. The
  reporter said one session showed its model list as unavailable while the
  current session used the same list.
- Evidence: session records, publisher output, the serving endpoint, and one
  real turn after the repair.

## Reported symptom

The reporter described the fault as an unavailable model list. The stored
session record named one model entry. A sibling session in the same project
named a different entry and worked.

```text
failing session record: { model: <entry-a>, provider: <provider> }
working session record: { model: <entry-b>, provider: <provider> }
```

Both providers resolved to the same endpoint and the same credential, so a
per-session configuration fault was ruled out.

## The three states

The release inventory declared 14 entries. The serving endpoint answered 2. The
published status record reported a live count for each entry.

```text
declared:  14
served:     2
live > 0:   2
live == 0: 12
```

The publisher marked every entry with a zero live count as not selectable and
gave it a compatibility status word. The member list held only the selectable
entries, so it returned 2 of 14. This is not a cap. Run the publisher and count
what it registers before you suspect truncation.

## Decisive proof

One minimal request per suspect entry, through the serving endpoint:

```text
<entry> -> 404 {"error":{"code":"model_not_found", ... "not in the current serving set" ...}}
```

The refusal named the serving set. This proved the entry was not served, and no
catalog change could have made it serve.

## Repair and verification

The failing session was pointed at a served entry. The selection endpoint
accepted the value, but an earlier failed turn state still read as failure. One
real turn then returned a succeeded state.

Order of checks that separates a repair from a change:

1. read the stored model and confirm the new value;
2. send one real turn;
3. read the session outcome and require a succeeded state.

## Mutating probe on a live session

To confirm that the selection endpoint accepts an unserved entry, a down entry
was sent to the live session. The endpoint accepted it and the next turn failed
with a not-served error, which reproduced the reported symptom exactly.

This probe changed the user session. Restore it and re-verify, or use a scratch
session. The endpoint accepted an entry that the host does not list, so a
selection command is not a validity check.

## Relationship to the visibility-gate rule

A related entry teaches how to keep a degraded entry selectable. That rule
assumes the backend is served and the user must still reach it. In this case no
backend was live, so hiding the entry was correct and the fix belonged to the
session. Decide from the serving probe, not from the word shown in the list.