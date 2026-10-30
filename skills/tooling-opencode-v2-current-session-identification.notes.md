# Notes: OpenCode v2 Current-Session Identification

Supporting evidence for v1.0.0. Generalized from one verified live session.
Identifiers are intentionally omitted.

## Campaign evidence

- A coordinator directive resumed a single-issue worker lane and ordered a
  completion protocol: learn from the session evidence, rename the session
  title by replacing a status prefix, and report. The rename required the
  exact current title, and no available tool reported it.
- The rename tool accepted an omitted identifier to target "the current
  session", but the new title had to preserve the unchanged remainder of the
  old title, so the old title and id had to be bound before the call.
- Fleet conditions at the time: the session store held hundreds of rows in a
  stale archived transcript export and dozens of concurrently updating live
  rows. Five sibling lanes showed `time_updated` values inside one
  half-minute window, and their titles shared the same prefix pattern
  (`<status>: <issue>-worker (<train>)`).
- Binding procedure that succeeded: snapshot copy of the database with its
  write-ahead-log and shared-memory siblings to a temporary directory;
  candidate narrowing by title pattern; identity confirmation by an exact
  substring of the session's own first user message in `session_message.data`
  (exactly one match, on the candidate id).
- Mutation used the harness session rename tool with the bound identifier.
  Post-write verification read the live store through an `immutable=1` URI
  and returned the new title on the bound id with no other row changed.
- The official API was checked for a self-identification path. It offers
  `session.list`, `session.active`, `session.view`, `session.update`, and a
  rename operation, but no operation that identifies the caller. The activity
  listing returned dozens of rows marked running, nearly all idle lanes.
- A service locator file in the state directory carries the API credential.
  It was read once locally to establish API availability and was screened
  from every artifact, log, and commit. Treat it as secret material.

## Non-evidence

- The same session also established that its assigned issue had been closed
  by a merged pull request from a sibling lane hours before the lane was
  spawned. That part of the evidence is already covered by
  `shared-repo-interruption-yield-to-peer-pr` (v1.2.0) and
  `post-merge-ci-failure-attribution`, so it is not repeated in the main
  skill.
