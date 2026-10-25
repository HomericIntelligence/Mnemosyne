# Notes: pr-review-carrier-prepublication-enumeration

Supporting session evidence (privacy-safe summary; repository names, pull-request
numbers, review identifiers, and commit identifiers withheld). Observations are from one
review drive on a private forge.

## Case: the same-identity fork

- One bounded review exchange allows several independent coordinator lanes under one
  forge identity. A lane in this drive completed independent round-1 reviews of a pull
  request, reduced and rendered a round-1 state carrier, and published it.
- Within the same hour, a second lane had already published its own round-1 carrier on
  the same artifact, answered its findings with an author fix, and published an
  author-response: its chain was at awaiting-reviewer when the second lane's carrier
  landed roughly fifteen minutes later.
- The second lane had verified labels and merge state but had not enumerated review
  records before publication. Both carriers are immutable, so the fork could not be
  unwritten.
- Recovery posture that worked: the second lane stopped all of its publication, label,
  and thread writes on the artifact; its distinct findings were checked against the new
  branch head and handed to the live chain as admissible round additions; the live lane
  later fixed those findings, so the fork had no remaining correctness consequence.
- Two more observations from the same window:
  - A rendered NO-GO label delivery was withheld by the fail-closed helper because the
    branch head had advanced minutes before; re-checking the remote head immediately
    before each write is the working defense.
  - A wrong-form API call (`-f body=@path`; the literal path became the review body)
    produced one junk review during the second lane's carrier publication; the
    void-repair skill covers that record repair.

## What enumeration would have caught

- The first lane's carrier body carried the exchange marker and identity in its first
  hundred bytes, and its author-response named the same exchange. A body scan over the
  paginated review list before reduction would have produced the stop decision in one
  command.
- Labels alone were not a signal: the artifact's single state label said NO-GO, which is
  consistent with both "unreviewed" and "a live exchange in flight".

## Encoded rule

- Enumerate review records before any first carrier publication on an artifact; treat
  any live chain as exclusive regardless of identity matching; stop, contribute
  findings, and let the live chain's refresh mechanics own the artifact's next rounds.
