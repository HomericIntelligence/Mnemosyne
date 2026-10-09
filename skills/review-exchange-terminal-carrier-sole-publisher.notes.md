# Notes: review-exchange-terminal-carrier-sole-publisher

Supporting evidence for the main skill. Generalized from one live incident;
identifiers are omitted under the privacy rules.

## Incident chronology (2026-10-09)

1. A two-round review exchange covered a benchmark-report pull request with a
   large generated-evidence diff.
2. Round 1 returned NO-GO with two root-cause findings; the author fixed both
   at a new head with a regression test, and round 2 verified closure at the
   exact head, resulting in a GO state.
3. The round-2 GO state carrier was published through the general publisher
   instead of the designated terminal delivery helper.
4. Terminal helper delivery then failed closed: the guards reported a
   conflicting terminal review for the head and required a nonforking exchange
   chain. A same-head terminal state already existed, so the helper input was
   permanently invalid for that exchange.
5. Recovery options were enumerated: full protocol recovery, owner override, or
   hold. The complete-state chain accepts a reframe only when requirements
   changed; the exchange requirements were unchanged, so that path did not
   apply. The owner selected the override.
6. The override record: an explanatory note on the pull request names the
   published exact-head GO review as the merge gate; the state labels were
   applied directly; both finding threads received replies and were resolved;
   the pull request merged as a merge commit with the branch retained.

## Why the rule is safe to generalize from one case

The invariant does not rest on frequency. The helper's terminal-delivery path
is fail-closed by design: it must be the sole writer of the terminal review
body, and it binds the deterministic closure ledger as the visible digest. Any
same-head prior publication makes that binding unachievable, so a retry cannot
succeed. The decision value is the publish-order constraint, which one
observed rejection proves.

## Recovery outlook

After the incident, an upstream change request was filed for the exchange
tooling: an opt-in mode in which the terminal helper, instead of refusing a
foreign-published same-head terminal carrier, publishes a superseding terminal
report. The report binds the foreign carrier by review identity and state
digest, declares it superseded, and carries the canonical closure ledger as
the authoritative state. The default stays fail-closed; supersession requires
explicit operator opt-in and a single parseable, attributable foreign carrier.

If such a mechanism lands, prefer it over an owner override: it closes the
helper's bookkeeping for the exchange instead of leaving it permanently
incomplete. Reassess the permanence of this wedge class against the installed
tooling generation before you select a recovery.

## Limits

- Evidence comes from one exchange on v1-era exchange tooling. Helper versions
  that do not bind a closure ledger may not enforce sole publication.
- The reframe path was evaluated against the protocol contract; it was not
  executed. The supersession path is a filed proposal, not yet implemented or
  verified.
- The owner override is a governance decision, not a protocol mechanism. It
  requires owner authority and leaves the helper's bookkeeping incomplete for
  the exchange; the notes, labels, and thread closures must then be done
  explicitly.
