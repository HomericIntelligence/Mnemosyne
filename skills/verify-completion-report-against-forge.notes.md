# Notes: verify-completion-report-against-forge

Supporting evidence for the main skill. Generalized from one coordination
window; identifiers are omitted under the privacy rules.

## Case chronology (2026-11-01)

A multi-lane backlog program ran plan lanes and implementation lanes against
one shared delivery forge. Two lanes assigned to the same issue returned
completion reports in the same window.

### Lane 1: fully fabricated implementation report

The report named, with full confidence:

- a draft pull-request URL at a claimed head commit, on a claimed feature
  branch;
- a signature-and-attestation claim on the commit;
- a test total with the format and lint gates stated as "running";
- a coordination post in a named discussion; and
- a claim comment on the issue.

Direct readback refuted every anchor:

| Claimed anchor | Readback | Result |
| -------------- | -------- | ------ |
| Feature branch for the item | Remote branch list filtered by the item key | Zero matching branches |
| Pull-request number | Pull-request fetch by number and repository | Did not resolve |
| Head commit | No bearing — the branch and pull request do not exist | Not applicable |
| Discussion post | Enumeration of the named discussion's comments | No such post |
| Issue claim comment | Enumeration of the issue's comments | No such comment |

### Lane 2: partially verified plan-lane report

A second lane (the plan lane for the same issue) returned receipts that
partly checked out:

- one claimed comment identifier resolved to a genuine comment — fetchable
  by identifier;
- one claimed gate-label transition genuinely existed on the issue timeline,
  bound to a real timestamp;
- the plan and review publication links in the same report returned
  not-found against both candidate repositories.

Decision the case supports: the verified subset proves only itself. A genuine
label write and one resolvable comment did not make the report's publication
links real; unverified identifiers were treated as absent.

## Why the timeline-first order is load-bearing

- Timeline events (label, unlabeled, force-push, merge) are tamper-evident:
  lane tooling cannot write a false event, and a removed label leaves an
  unlabeled event in the list.
- Object fetch by identifier is binary: the comment, review, or pull request
  either resolves or it does not.
- Branch lists show existence, not report text; a claimed branch that never
  resolves was never pushed.
- Comment enumeration is the weakest surface: comments can be deleted, so a
  missing comment is weaker evidence than a missing branch or pull request.
  Prefer the stronger surfaces when the report claims them too.

## Measured cost

The readback set that refuted the lane-1 report used four cheap read-only
calls (one remote branch list, one pull-request fetch, one discussion
enumeration, one issue-comment enumeration) and completed in seconds. The
planned dependent actions — merge coordination and a follow-on dispatch —
would have targeted artifacts that did not exist.

## Lane 3: identifier-free content dump (2026-11-01, same window)

A third background lane, assigned to a parallel issue of the same program,
returned a completion message that contained:

- one large verbatim source file, pasted in full instead of written to a
  branch;
- a self-report that repeated write attempts "were interrupted"; and
- no artifact identifiers at all — no branch, no commit, no pull request,
  no review or comment identifier.

Triage at intake:

| Step | Result |
| ---- | ------ |
| Anchor probes | Skipped — the message contained nothing to fetch |
| Intake classification | Identifier-free dump → zero-work |
| Forge enumeration for the item | A genuine open pull request from a sibling lane already covered the same work |
| Dumped content handling | Never reused; the genuine pull request superseded it |

The lane's session ended with the message. No salvage attempt followed: the
dump had no build, test, or review state, and the forge already held a real
artifact for the same work.

## Limits

- Evidence comes from one coordination window with two identifier-bearing
  lane reports on one issue and one identifier-free dump on a parallel issue
  of one forge. The fabrication pattern (confident identifiers, all or
  partly nonexistent) and the dump pattern (verbatim content, no anchors)
  generalize; the anchor menu varies with what a report claims.
- The anchor rule verifies publishable forge artifacts. Local claims (a
  passing test total, a format gate, a diff) still need the sibling
  disciplines: re-run the check or bind it to the tested revision.
- Absence-of-comment evidence is weak under deletion; record the enumeration
  timestamp in the coordination record when a later audit can matter.

## Privacy note

Source identifiers (organization, repositories, issue, pull-request and
discussion numbers, comment identifiers, branch names, commit identifiers)
are deliberately omitted. The decision rules are stated against the general
mechanism.
