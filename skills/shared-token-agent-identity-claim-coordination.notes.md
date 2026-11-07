# Notes: Shared-Token Agent Identity and Claim Coordination

Supporting evidence for `shared-token-agent-identity-claim-coordination`. Identifiers
are withheld under the privacy policy; the case below describes an anonymized
repository contract.

## Evidence basis

A policy-bearing repository that runs many parallel automated agent lanes adopted a
coordination contract with these properties:

1. **Shared credential, one displayed author.** All agent lanes authenticate to the
   forge through one token. Every issue comment and discussion post from every lane
   shows the same author. Attribution by forge metadata was impossible.
2. **Content-carried identity.** The contract requires one unique, stable agent name
   per task, kept for the task life, prefixed in brackets to each issue comment and
   discussion post.
3. **Claim protocol.** On epic start, the lane posts `[<name>] claiming #N - next
   step: <step>` in an applicable coordination thread; creating a new discussion is
   reserved for work that has no applicable thread.
4. **Hold protocol.** `[DECISION-NEEDED]` posts freeze a path until an operator
   answers.
5. **Completion behavior.** A lane whose task is already delivered does not start new
   work: it attempts a durable learning step, retitles when the session is its own,
   reports the final disposition, and stops.
6. **Public-record discipline.** Explicit prohibition of PII, credentials, and secrets
   in posts; posts keep a goal-then-result structure and stay short.

## Decision branches this evidence adds beyond existing entries

- The swarm orchestration entry formalizes exclusive file ownership and reviewer
  assignment, but assumes attribution is possible. This entry covers the degradation
  case where the forge shows one author and identity must live in the content.
- The general stop-and-report pattern gets a concrete completion order for
  already-delivered lanes: gather evidence, durable-learning step, retitle, report,
  stop.
- Thread reuse is stated as a first-read requirement (search before create), which
  keeps claims visible and prevents duplicate-lane scatter.

## Second evidence case: a gated and already-scoped request (2026-11-01)

A lane received an operator request with two broad halves: remove one synchronization
primitive everywhere, and change where a runtime keeps its state. Read-only discovery
found this state:

1. A design issue recorded both halves as accepted decisions.
2. The implementation issue was open, unassigned, and had no comments. Its body named a
   gate: work starts only after the design issue passes its planning stage.
3. The design issue was still in its design stage, so the gate had not passed.

The lane posted one identity-prefixed claim in the reused fleet thread, with the
precondition evidence, a hold statement, and a decision request. It started no
implementation and created no discussion. One earlier lane had already started the
code work behind the same gate; the claim rule did not stop that, because the lane
never read the gate text.

The decision value this case adds: a claim post does not lift a gate. Read the tracking
issue and the state of the issue that owns the precondition before the claim. Claim the
smallest step the recorded decision allows, not a fresh inventory of the whole request.

## Third evidence case: pull-request swarm under one login

A coordinator ran a swarm of lanes that opened, reviewed, and merged pull requests as
one forge user on one scheduler user. Observed failures: a push after a delivered GO
made the tool treat the GO as stale; a comment during review changed the requirements
digest and blocked GO delivery; a reviewer withheld delivery after being told to skip
labels; a secondary rate limit appeared with quota left; agents repeated blocked
reports while waiting on queued jobs; and a full sub-agent cap stalled fan-out. The
rules in the "Swarm of Pull-Request Lanes" section are the generalized fixes.

## Verification limits

- `verified-local`: the contract text is on the shared branch of a single repository;
  no cross-repository fleet run is recorded yet.
- The claim and hold markers are conventions. Their adoption by every lane is a fleet
  commitment, not a technical guarantee; lanes outside the contract can still collide.
