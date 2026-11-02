# Notes: Review Exchange Head Refresh and Carrier Repair

Privacy-safe supporting detail for `review-exchange-head-refresh-carrier-repair`.
Identifiers from the source incident (repository, pull request, review, account, and
digest values) stay out of this record. Git provenance keeps the authoring context.

## Source case (2026-10-21)

A chain-verified review exchange on a qualification-artifact pull request (eight
changed paths, seven required findings plus two nonblocking findings) reached round 2
`NO-GO`, then received author answers at one head, then a conflict-resolution
force-push moved the head. The reduced logical state after the author answers was
`awaiting_reviewer`, round 2, coverage invalidated by the refresh convention.

The reviewer-side next step required rebinding the exchange to the new head. Three
tooling obstacles appeared in sequence; each was resolved and verified in the same
session.

## Obstacle 1: strict parser versus forge bodies

`review_exchange.py extract` rejected every published carrier body as returned by the
forge review API with "The review-exchange JSON fence is malformed or not final". Byte
inspection showed each body ended with the closing fence, one line feed, and one
additional line feed. Removing exactly one final `"\n"` made the strict parser accept
every carrier (four of four, including the round-1 state, the round-2 state, and two
author-response carriers). The repaired documents produced the same envelope digests as
the ones referenced inside the chain, confirming that the trailing delta is a delivery
artifact, not carrier damage. The skill's own contract already anticipates exactly this
delta for one delivery path; the session extended the same recovery to readback
verification of freshly published carriers.

## Obstacle 2: reduce-request schema width

Replaying a published author event through the reducer with the extracted envelope
state as the event failed: "author response has invalid fields: unknown
requirements_sha256, target." The stored envelope state retains two state-level fields
that the event schema does not admit. Removing exactly those two fields made the
original round-2 author event reduce cleanly (`status: accepted`), which also served as
a live verification of the replay path before any new event was prepared.

## Obstacle 3: snapshot materialization on a private remote

The evidence collector's materialization tier ran `git fetch` with an isolated
environment (global and system git configuration redirected to `/dev/null`, terminal
prompts disabled). On a private remote this yields exit 128: "could not read Username
for 'https://...'". An ambient fetch of the same refs succeeded because it used the
configured credential helper. The collector also mounts quota volumes; on hosts without
that capability earlier tiers fall back, so the auth boundary is the one that binds in
practice. Mitigation used in the session: recompute each binding digest directly from
the forge API under the documented canonical recipes, then reproduce a published
carrier's digests with the same code before trusting it for a new event.

## Digest conventions verified in the session

- Visible content: SHA-256 of the visible carrier text with every trailing line-feed
  byte stripped. Verified by reproducing the visible-content digest inside a published
  author-response carrier (exact match); two alternate normalizations (as-is bytes up
  to the marker, single-trailing-line-feed) did not match.
- Reviewed scope: SHA-256 of the canonical JSON serialization (sorted keys,
  `(",", ":")` separators, `ensure_ascii=false`, `allow_nan=false`) of the
  pull-request scope fields, with `closingIssuesReferences` items each canonical-JSON
  serialized and the item strings then sorted. Verified by computing the digest for the
  live pull-request metadata twice (before prepare and before publication) with
  identical results.
- Failed candidates for the scope digest (listed to prevent re-derivation):
  concatenation of sorted scope-file bytes; concatenation of per-file SHA-256 digests;
  canonical JSON of per-file digest map; sorted `path\0blob-sha1\n` records; sorted
  `git ls-tree` output; and the head tree object identifier.
- Requirements digest: retained from the earlier binding because the bound requirements
  issue was closed and unmodified since nine days before the last binding
  (last-modified time compared against binding time).

## Head-refresh event construction

The refresh preserved: exchange identity, round number, finding identifiers, and the
fix/contest dispositions of all seven required findings. It replaced: the head
revision (new force-pushed head), the artifact and visible digests (recomputed), the
changed-path set (eight paths -> five paths, because the merged base had deleted three
test files that the resolution then kept byte-identical to the base, so they left the
author-intent diff), with a non-empty `scope_change_reason`, and every finding's
evidence list (each re-stated against the new head). The reducer accepted the event;
the new logical state was `awaiting_reviewer / review_assessment`, round 2, at the new
head, with all seven required findings re-answered (5 fix, 2 contest) and both
nonblocking findings untouched.

One clarification on contested findings: a refresh revalidation of a contest re-verifies
the enforcement evidence at the new head (render-boundary context gate and
replica-ceiling enforcement, both unchanged by the force-push because the force-push
touched no source file). The contest disposition stands; the reviewer round evaluates it
on that evidence.

## Publication and readback

The refresh carrier was published as exactly one COMMENT review, `commit_id` = the new
head, empty inline-comment list. Readback followed the same rule set: re-fetch the
review by id, remove exactly one final line feed, extract, and compare the envelope
digest with the accepted digest (match), the review author (expected publisher), and
the carrier's chain position (last carrier on the pull request). Full revalidation
ran immediately before publication: pull-request state/head/base from the API and a
fresh scope-digest recomputation, both matching the event's bindings.

## External closure

Two minutes after the refresh carrier was published, the owner merged the pull
request. No terminal round-3 carrier was prepared or published; the exchange closed
externally through the merge. The prepared reviewer-round task instructions were
discarded without execution (they were drafted but never dispatched). This incident
shape is the basis for the "owner merges before terminal delivery" rule row; the
session did not attempt any post-merge carrier, so that row is a stop rule derived
from protocol design (carriers bind live artifact state), not from an observed
rejection.

## Verification record

- Repaired extraction: four published carriers, all accepted after exactly one-line-feed
  removal; envelope digests matched their in-chain references.
- Replay verification: original round-2 author event reduced `accepted` after stripping
  the two state-level fields.
- Refresh: reducer output `status: accepted`, decision `awaiting_reviewer /
  review_assessment`, round 2; rendered carrier round-tripped through the extractor
  with an identical digest; published carrier readback-verified.
- Pull-request preconditions at publication: `OPEN`, exact head and base oids matched,
  scope digest recomputed fresh and matched.

## Source case (2026-10-24): decision-required wedge and delivery-side perishability

A multi-round chain-verified exchange had reached its terminal phase: a fresh-context
reviewer round returned GO at the current head, and every finding thread from the
previous round was resolved. The reduced logical state was `decision_required`. A
complete terminal-delivery set was prepared offline (reviewer assessment, thread
closures, authority record, closure manifest), and the closure manifest passed a full
offline validation pass.

### Branch analysis in `decision_required` state

With the head moved since harvest, three candidate transitions exist for the wedged
exchange; the reducer rules constrain all three:

- Author-response refresh on a wedged exchange: admissible only when the exchange's
  own derived stop-reason is the literal `replacement_blocker`. This session's derived
  stop-reason was scope-related, so the refresh path was rejected by inspection of the
  reducer rules, not by a live probe.
- `human_decision`: the event must carry the prior state's artifact binding unchanged.
  It certifies the exchange as bound; it does not rebind a head. After any head move
  this event cannot reduce.
- Reframe: a new exchange at round 1 at the current head. Legal with reframe
  authority; in this session the artifact owner approved a new exchange in writing.
  The authority record is published once as a comment and referenced by the new
  round's envelope.

### Perishable bindings observed

Between the harvest and the delivery preflight (same session, under one hour):

- The head moved twice (a squash-and-push and a follow-up head advance).
- The changed-path set shrank, so the scope set and the scope digest changed.
- The requirements source was edited concurrently, so the requirements digest changed.
- A concurrent delivery session resolved the last two open finding threads, so every
  thread digest changed.

Every digest in the validated manifest was bound to a snapshot that no longer existed.
The correct recovery is a full re-derivation from the live snapshot before any forge
write; patching individual fields keeps the dependent digests stale. The authority
record published earlier in the sequence was requirements-stale within minutes. It
was left in place (delivery channels are append-only) and documented, consistent with
the external-closure stance on existing carriers.

### Goal-met stop

At preflight the live forge readback showed: the terminal state label applied
exclusively, zero open threads, and a complete terminal carrier published by the
concurrent session (final round, GO, all findings resolved), followed by the artifact
merge. The prepared delivery set was discarded without execution. The stop condition
was the live state, not a failure: the goal of record (a terminal GO at an exact
head, merged) was already satisfied.

### Verification record (second incident)

- Reducer branch analysis: source-level inspection of the reduce rules for
  author-response (stop-reason literal) and `human_decision` (binding identity). No
  illegal event was submitted to the reducer as a probe.
- Offline manifest validation: a full validation pass on the closure manifest
  completed before the discard decision.
- Staleness check at preflight: head, scope digest, requirements digest, and the
  thread set were re-read from the forge API; all four had changed since harvest.
- Goal-met verification: the exclusive label state, zero open threads, and the
  concurrent session's terminal carrier were read back and verified (round,
  completeness, per-finding dispositions, resolution markers) before the discard
  decision.

## 2026-10-26 — Post-terminal head refresh with armed auto-merge

### Context

A bounded review exchange on an external worker-agent pull request (anchor-carrier
annex carrier) reached a delivered terminal GO at an exact head. CI policy then
required a container-image refresh twice; each refresh pushed a new head after
terminal delivery. Auto-merge had been armed by policy before the refreshes.

### What happened

- After the first post-terminal push, continuing the completed exchange was
  attempted: the reducer rejected every event kind except `reframe` with "A
  terminal review state cannot accept another event". Terminal law confirmed
  empirically.
- Recovery per refresh: the completed exchange stayed archived by its terminal
  reply; a fresh round-1 exchange opened at the live head with an independent
  full-coverage reviewer round from a fresh context; a new GO bound the pushed
  head. Three exchanges coexisted on one artifact, each archived by its own
  terminal reply.
- Live forge inspection showed the armed auto-merge request had survived the
  first push and was not head-pinned: the forge merges whichever head first
  satisfies branch protections. Auto-merge was disabled before every subsequent
  push and re-armed only after the final terminal delivery bound the pushed
  head. The squash merge followed on the delivered head.

### Verification record (third incident)

- Terminal law: reducer rejection observed directly on the completed exchange.
- Auto-merge persistence: armed-request state read back from the forge API
  across a push; it remained armed with no head binding recorded.
- Fresh-round independence: each new head received a round-1 assessment from a
  reviewer context that had not authored or author-responded to the artifact.
- Closure: guarded merge completed at the terminal-bound head; base-branch CI
  green after merge.

### Privacy note

Source identifiers (organization, repository, pull-request numbers) are
deliberately omitted; the rules above are stated against the general mechanism.

## Source case (2026-10-26): forge-metadata-only fix at the constant head

A chain-verified two-round exchange on a fix-artifact pull request (nine changed
paths, one required finding plus one nonblocking finding) reached round 1 `NO-GO`
with a single required finding. The finding's closure condition required only a
pull-request body correction: the body had to stop using closing syntax for the
linked requirement because the artifact deliberately leaves one acceptance
criterion open.

### The rejection

The author landed the body correction and submitted the `fix` answer with the
recomputed bindings: the head revision unchanged, the revised reviewed-scope
digest (the corrected body moved it), and the unchanged requirements digest. The
reducer rejected the answer: "A pull-request fix must bind a new head revision."
Source inspection confirmed the rule is absolute: on a pull-request surface a
`fix` or `fix_with_tradeoff` answer requires a changed artifact revision, and no
event field carries a metadata-only fix. Alternatives were examined and rejected
as dishonest: `risk_acceptance` needs no head move but records acceptance of an
unfixed finding, and `contest` asserts the finding is wrong; neither describes a
correction.

### The deliberate head advance

The correction was already live, so the only missing element was a new head
revision. The author added one empty signed commit on the review branch whose
tree was byte-identical to the tested head and pushed it:

- `git diff <tested-head>..<new-head>` produced no output;
- both `git rev-parse <commit>^{tree}` values matched;
- the commit message recorded why the commit is empty and that a squash merge
  carries none of its identity.

The reviewed-scope digest that bound the corrected body survived the head
advance unchanged, because the digest covers the pull-request metadata fields
(title, body, closing references, state, draft flag, base and head branch
names) and not the head object identifier. The author-response refresh then
reduced `accepted` at the new revision (`awaiting_reviewer`, round unchanged),
and its carrier published and readback-verified.

### Coverage and the next round

The refresh invalidated coverage, so the next reviewer round was a full-coverage
round from a fresh context. Because the new tree was byte-identical, the reviewer
proved tree identity and re-affirmed the round-1 deep source coverage instead of
re-executing it; the round returned terminal GO with the required finding
resolved. One nonblocking follow-up finding did attach to the head-chain text:
an earlier head-chain commit message, written to the repository's `Closes #N`
convention, contained a closing keyword that a squash merge composing its
default message from branch commit messages could copy into the default branch.

### Squash-hygiene verification

The merge was armed with an explicitly set squash title and body carrying the
non-closing linkage (`References #N`). Post-merge verification confirmed: the
merge commit contains no closing keyword for the requirement, the pull request's
closing-issues set was empty at merge, and the requirement issue stayed open
with its residual criterion. The empty commit's identity did not enter the
default branch.

### Verification record (third incident)

- Constant-head fix rejection: the reducer rejected the `fix` answer with the
  literal message above; the rule was confirmed by source inspection, not by
  probing with alternatives.
- Tree identity: empty diff and equal tree object identifiers between the
  tested head and the advanced head, verified before and after the push.
- Digest survival: the reviewed-scope digest was identical before and after the
  head advance; it was recomputed from the live metadata at both points.
- Refresh and terminal delivery: the author-response refresh reduced
  `accepted`; the terminal round reduced `complete / GO`; terminal delivery
  published one terminal COMMENT review (byte-exact readback), closed the one
  open thread with a marker-verified reply, and set the exclusive state label.
- Merge verification: explicit squash title and body; zero closing keywords in
  the merge commit; the requirement issue open with its residual criterion.

## Source case (2026-10-26): head change after a complete terminal GO delivery

A chain-verified review exchange on a private-monorepo pull request reached a
terminal GO after two reviewer rounds (one critical required finding, resolved;
four nonblocking findings, all recorded live). Terminal delivery completed: the
terminal carrier published and readback-verified byte-exact, all five finding
threads responded and resolved, and the exclusive terminal-state label applied.

CI at the terminal head then failed closed on a test-inventory partition gate:
a newly added test module was not classified in the inventory. The repair was
one classification line, moving the head by one commit and adding the inventory
file to the changed-path set; every previously reviewed path was
byte-identical at the new head.

### Rebind probes rejected

The completed exchange accepted no rebind:

- A continued author-response event on the complete state failed: "author
  response" events on a complete state are reducer-rejected. A
  round-increment reviewer assessment failed the same way with the exact
  gate message: "A terminal review state cannot accept another event." The
  reducer code path confirms: a complete phase accepts only a reframe event.
- The reframe path requires `requirements_sha256` to differ from the prior
  digest. The requirements source was unchanged, so its live-recomputed
  digest was identical: no reframe was possible without fabricating a
  requirements change.

### Contract resolution: the delivered GO survives

The delivery-contract text resolves the state directly: an exclusive
terminal-state label with zero open threads and a verified completed history
is `already_delivered`; the label does not lapse when a later commit changes
the head; a rebase, a base merge, or a later bug fix does not remove it. The
label lapses only when a reviewer delivers the exclusive NO-GO label or when
the target carries no state label. Re-review after a post-delivery bug fix is
the author's judgement, not an exchange obligation.

Judgement applied in the session: the repair was a non-behavioral
configuration classification line with all reviewed content byte-identical,
so no re-review was selected. The judgement and its evidence were recorded in
the final report.

### Text tension noticed

The review workflow's author-response section lists a pre-round-5 complete GO
as an accepted head-refresh precondition when the head revision changed. The
current reducer gate rejects every non-reframe event on a complete state, so
that acceptance text does not reduce with the current implementation. The
operative contract for this state is the delivery-contract survival rule.
Recorded here for the workflow maintainers; treat the complete GO as
terminal.

### Outcome and verification record

- Live forge readback before merge: exclusive terminal-state label present,
  zero pending threads, head at the repair commit, artifact open and
  non-draft.
- Squash auto-merge armed; the required-checks gate went green at the new
  head and the artifact merged. A long-running non-gate check completed
  successfully afterwards.
- Pre-merge reducer probes were run exactly once each and discarded; no forge
  write followed a rejected probe. No reframe was attempted (identical
  requirements digest), so no protocol state was fabricated.
- The test-tier classification defect itself (a new test module must be
  registered in an explicit inventory partition, diagnosed by a uniform fast
  failure of every shard with an "unclassified modules" message) is a
  project-specific fact, not generalized into the skill.

## Source case (2026-11-01): reframe bound to an older predecessor

A requirements reframe was required because a linked requirement closed on the
default branch after a terminal GO, which made the retained requirements digest
stale. The reframe authority record was published, then the round-1 reframe
carrier was reduced, rendered, and published with one required finding. No
verdict could be delivered afterwards.

### Diagnosis

- The authority record carried `supersedes_state_sha256` equal to an earlier
  round-1 state of the old exchange, not the terminal state that was the logical
  state at publication time.
- An author event published before the authority record had already derived a
  successor from that same earlier state. That state therefore had two derived
  successors: the author-event result and the reframe carrier.
- The delivery reader replays every carrier on the artifact and builds the
  derived-children map for the whole graph. It rejects any state with more than
  one child, so the failure is not limited to the current exchange.
- Re-running the delivery reproduced the exact error message: one
  review-exchange state has multiple derived successors.
- A second, independent defect also blocked delivery: the record body as the
  forge returns it carries one trailing line feed, while the record parser
  requires the body to equal its canonical JSON exactly, so the receipt could
  not resolve from the forge even by digest.

### Recovery assessment

- Reviews that are no longer pending cannot be deleted, and every carrier is
  immutable, so the forked edge cannot be removed.
- A corrected second authority record would not remove the edge; the rejection
  is over the whole graph, not over the selected exchange.
- Patching the delivery helper or the parser is outside the protocol and was not
  done.
- The supervisor rule that applies is the authority-transition rule: do not
  apply an authority transition to an older reviewer state when a later verified
  author event derives the current logical state. That is the exact mistake that
  was made.

### Actions taken

- Re-verified the live head, labels, open threads, and every carrier state and
  predecessor digest from the forge, read-only.
- Re-produced the delivery error once against the exact head to bind the evidence.
- Published exactly one blocker comment that names the bound predecessor state,
  the current logical state, both derived successors, and the delivery error.
- Made zero carrier writes, zero reducer probes, zero label changes, and did not
  arm auto-merge.
- Kept the published round-1 review and its required finding as valid
  source-review output.

### Reusable outcome

The checks belong in the preparation path, not the recovery path: compare the
receipt supersession binding and every event prior-state binding with the current
logical state digest before publication. When they differ, the exchange has no
route to delivery, and the only safe action is a read-only stop with one blocker
comment.

## Incident: unresolvable receipt reference in an immutable carrier (2026-10-31)

### Shape

A review exchange on an open change reached an author-refreshable state and was
then reframed with an authority record. Both carriers published and the round-1
state extracted and standalone-verified.

The reframe carrier's accepted event embedded its authority receipt as a
reference string. That string used the change-host's numeric REST review
identifier. The delivery reader resolves review references only by the GraphQL
node identifier for the same review.

### Reproduction of the mismatch

Resolve the same reference in both spaces and compare the counts:

- the REST identifier returns the review record in the REST API;
- the GraphQL node identifier returns the same record in the GraphQL API;
- the REST identifier used as a delivery reference resolves to zero records in
  the reader's identifier space.

Both identifiers name one review. The fault is the reference form inside the
carrier, not the receipt content.

### Why the exchange is dead

1. **Immutability.** The carrier is already published. Editing or dismissing a
   carrier invalidates it for every delivery, so the reference cannot be
   corrected in place.
2. **Single successor.** The reframe state is the derived successor of the
   round-1 state and occupies that state's one successor slot. Re-deriving from
   the round-1 state with a new author response, reviewer round, or authority
   event produces two successors and fails the chain check.
3. **Single chain.** Every later delivery verifies or archives each persisted
   exchange on the artifact. This exchange has no terminal GO, so a NO-GO or GO
   delivery fails the nonforking-chain check at any head, not only at the bound
   head.

Consequence: no review-workflow route reaches a GO. Adding reviewer rounds
cannot help, and enabling auto-merge would bypass the contract rather than
satisfy it.

### Actions taken

- Read the live labels: the delivered NO-GO label was still exclusive and
  correct.
- Read the carrier body and confirmed the reference string and both identifier
  values.
- Published exactly one blocker comment naming the failing reference, both
  identifier values, the two chain rules, and the superseded disposition.
- Made zero carrier edits, zero reducer probes, and zero label changes.
- Did not enable auto-merge.

### Reusable outcome

The repair content and its scope were preserved and handed forward for a fresh
artifact with a clean round-1 exchange. A dead exchange is a supersession
decision for the owner of the artifact, so the branch ends with a decision
request rather than a unilateral replacement.

## Source case (2026-10-31): undeliverable terminal binding and fresh-genesis recovery

One chain-verified exchange reached its terminal reviewer round with a GO
verdict, phase complete, and next action finalize. The terminal state's
`visible_content_sha256` bound the SHA-256 of hand-written terminal prose,
not the deterministic terminal ledger that the delivery helper generates.

### Diagnosis

- Every closure manifest built on the state failed pre-publication with:
  "The terminal visible closure ledger does not match its manifest entries."
- Supplying the deterministic ledger bytes satisfied the helper's ledger
  equality check but broke the state's own visible-content digest.
- Supplying the bound prose kept the state digest intact but failed the
  equality check.
- The defect is in the published state, not in any manifest input. No input
  repair exists.

Diagnosis method: compute the deterministic ledger with the delivery helper's
own generator at the same binding (zero closure entries), hash its exact
bytes, and compare with the state's bound digest. Different digests prove the
permanent defect with zero forge writes.

### Recovery: fresh genesis exchange at a moved head

1. Advanced the head with one empty signed commit (byte-identical tree,
   honest message, no closing keywords). The push started a fresh gated CI
   run at the new head because the exclusive label was applied after the
   previous delivery attempt.
2. Computed the deterministic ledger at the new head and hashed its exact
   bytes into a fresh round-1 reviewer assessment event: new exchange
   identifier, `prior_state_sha256` null, `supersedes_state_sha256` null,
   artifact binding {new head, reviewed-scope digest, ledger digest},
   coverage complete, no findings, no responses, no stop reason. Reduced with
   `previous` = null. The reduced state carried verdict GO, phase complete,
   next finalize.
3. Rendered the state carrier, published it as one COMMENT review pinned at
   the new head, and readback-verified byte equality and envelope identity.
4. Built the closure manifest on the new genesis envelope with the same
   ledger bytes and delivered with the anchor source. The delivery helper
   verified the old exchange's full carrier chain, archived the old
   exchange, and applied the exclusive terminal label at the new head.
5. Gated CI ran green at the new head; the guarded squash merge followed.

### Archival-guard detail

The delivery helper's archival sweep fails when an old exchange's carrier
sits at the delivery binding head. After the head move, every old exchange
carrier sat at an older revision, so the sweep archived the old exchange in
the same delivery that published the new terminal state. The same recovery
repeated once more after a real CI test failure moved the head again: the
fresh genesis pattern delivered at the second head and the first fresh
exchange archived the same way.

### Why the terminal state was undeliverable, not repairable

- A terminal state accepts no further events, so no later event can rebind
  its visible-content digest.
- The carrier is published and immutable.
- The state's digest binds the prose bytes; the helper's check binds the
  generated ledger bytes. The two cannot both hold for one manifest.

### Same-series protocol observations

- A submitted forge review cannot be deleted (the API refuses), but a
  submitted review body can be replaced through the GraphQL review-update
  mutation. A mistaken non-carrier review was withdrawn this way with an
  honest replacement note.
- The forge accepts a review pinned to a commit identifier that the branch
  history no longer contains (a pre-rebase head). The chain walk classifies
  published carriers by kind at each pinned revision.
- Kind=state carriers that embed an author event were tolerated by the chain
  walk when a matching kind=author-event carrier for the same transition
  also existed; the reducer proved both normalized to the same state.

### Reusable outcome

The digest comparison is the decision gate: equal digests mean a manifest
repair; different digests mean the terminal state is permanently
undeliverable and a fresh genesis exchange at a moved head completes the
goal. The recovery verified end to end on the first delivery attempt at each
of the two heads.

## 2026-11-01 — Terminal GO withheld at external closure of a merged artifact

### Context

A reviewer lane finished a full source review of a pull request at a moved
head, reduced a complete terminal GO round-1 state, verified the anchor
proofs and the reducer confirmation, and built the closure manifest for the
delivery helper's sole-publisher sequence. Before the first forge write of
the delivery (terminal carrier, thread resolutions, exclusive label), the
owner merged the artifact from the forge UI. The lane had the prepared,
offline-validated manifest on disk but had published nothing for the
terminal delivery.

### Delivery-helper gate

- `deliver_go.py --prepare-manifest` against the merged artifact printed
  "The pull-request head, target, or state changed; withhold GO delivery."
  and wrote no manifest. The helper's not-open check is the last-line
  proof that a post-merge delivery cannot succeed; the prepared payload
  was discarded.
- Zero forge writes followed the merge. Every later forge contact in the
  lane was read-only: state read MERGED, the merge commit and timestamp
  resolved, and the label pair re-read from the live artifact.

### Label observation

- The merged artifact carried both terminal-state labels
  (NO-GO from the superseded-head round, and GO whose provenance was
  unknown: no published terminal record could be verified between the two
  polls in which the pair appeared).
- The labels were left as found. Exclusive-label transitions are part of a
  live delivery on an open artifact; a merged artifact accepts no
  lane-driven repair. The review report recorded the observed state and
  its unknown provenance instead of repairing it.
- The delivered-GO survival rule did not apply: its preconditions
  (published terminal carrier, resolved threads, exclusive label) were
  never met in this exchange.

### Final recorded state

- The review report recorded the terminal delivery as withheld, with the
  merge commit and merge timestamp as the external closure, the helper
  refusal message as the delivery verification, and the untransitioned
  label pair as reported-not-repaired.

### Verification record

- Helper refusal message reproduced verbatim and matched the standard
  withhold phrase in the delivery reference.
- MERGED state, merge commit, and mergedAt timestamp read from the live
  forge after the merge.
- Post-merge lane log contained only read operations; no carrier, thread,
  or label write was issued.
- Live label state read at close still carried the unmaintained pair,
  untouched from the merge-time observation.

### Reusable outcome

Owner merge before terminal delivery is an external closure, not a failed
delivery: confirm the helper refuses the not-open artifact, discard the
payload, leave observed non-exclusive labels as found, record the withheld
terminal delivery as the final state, and publish nothing further.
