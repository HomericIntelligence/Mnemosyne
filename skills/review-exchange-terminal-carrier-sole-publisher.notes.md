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

## Incident chronology (2026-10-28)

A documentation program ran under fleet automation: several automation
sessions under one account published on the same pull requests.

1. One pull request carried a foreign round-1 exchange whose only finding had
   been adjudicated and resolved in-tree. During branch maintenance, a
   sibling session posted two distinct terminal GO state carriers over one
   parent state, accompanied by empty carrier bodies. The persisted chain
   forked: one state had multiple derived successors.
2. Helper terminal delivery at the refreshed head failed closed: the guards
   require one nonforking chain and reject any state with multiple derived
   successors. Review dismissal is rejected as an invalid carrier, and the
   forge exposes no review deletion, so no carrier-level repair existed. A
   reframe was not available either: the exchange requirements had not
   changed.
3. A cross-session coordination note prescribed the same recovery that the
   graph analysis had indicated: close the pull request as superseded and
   open one replacement from the same branch and head with one publisher.
   The closure comment and the replacement body carried the fork record, the
   per-finding in-tree resolution table of the old exchange, and the
   unchanged verification results.
4. On the replacement pull request, a sibling session's delivery landed
   seconds before this session's prepared delivery. Replaying the persisted
   carriers classified the rejection as preemption, not a wedge: exactly one
   terminal GO envelope bound the exact live head. This session extracted
   the sibling carrier and audited it byte-for-byte against its own prepared
   manifest — requirement digest, reviewed-scope digest, artifact revision,
   anchor annex base and head, and the single-round complete-GO event
   structure. Every value matched, so this session posted a handoff note,
   applied the terminal state label exactly once, and armed auto-merge.
5. On a later, clean pull request with no foreign carriers, the same
   manifest-construction route delivered on the first attempt: the helper
   published the terminal review and applied the terminal state label
   itself, and auto-merge completed.

## Why the fork classification matters

The fork is a property of the persisted carrier set, not of the delivery
input. No manifest repair exists, so every retry fails identically, and the
standard exits do not apply: a void repair edits one's own carrier, but the
duplicate carriers here were a sibling's records, and voiding one successor
of a forked parent leaves the chain forked by definition; a reframe requires
a real requirements change, which did not exist. Closing the pull request as
superseded resets the persisted carrier set because a new pull request
starts an empty chain, while the branch and head — and therefore every
in-tree finding resolution — carry over unchanged.

## Additional limits

- The close-and-replace recovery was exercised once, under an explicit
  cross-session coordination note and a sole-publisher agreement. Without
  that agreement, two sessions can open competing replacements and re-fork.
- The audit-acceptance path applies only when the sibling uses identical
  tooling and the audit covers every binding field. A partial audit turns
  acceptance into trust.
- The empty carrier bodies that accompanied the duplicate carriers were
  immutable and stayed in place as part of the fork record.
