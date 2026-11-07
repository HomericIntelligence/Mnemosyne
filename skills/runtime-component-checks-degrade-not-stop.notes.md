# Notes: Runtime Component Checks Degrade, They Do Not Stop

Supporting evidence for `runtime-component-checks-degrade-not-stop.md`. The main entry carries the
decision rules; these notes carry the source rule text, the generalizations, and the boundaries
against near entries.

## Source rule (generalized)

The source is a repository agent contract. Its new section states, in generalized form:

- After a component has launched, no check may stop the whole component, end its allocation, or
  mark it unhealthy. This covers identity records, digests, manifests, mode bits, release or context
  drift, and the state of another component.
- Each component starts independently of the others.
- A peer that is not up is a normal state. Wait, retry, and report degraded.
- A post-launch check that can stop, end an allocation, or mark unhealthy a running component is
  allowed only where an owner-approved issue or the contract names it.
- Request-time authentication, authorization, and input rejection stay fail-closed. A refused
  request is not a stopped component.
- Pre-launch trust-boundary checks stay: authentication, secrets, and paths that can write outside
  the lane.
- The rule does not cover recovery. A recovery step may refuse to restore a component that it cannot
  verify, where an owner-approved issue names that refusal.
- Records of identity and digests are for traceability. Log them.

## Generalization decisions

| Source detail | General form used in the entry |
| --- | --- |
| Repository-specific contract section and component names | "the repository agent contract", "a component" |
| Named modules, services, hosts, and issue identifiers | Removed. "an owner-approved issue or the contract" |
| Incident dates and log excerpts | Removed. Only the failure shape is kept |
| Internal paths | Removed. "paths that can write outside the lane" |

## Why the timing, not the intent, is the classifier

The word "fail closed" appears on both sides of this rule. The distinction that decides the outcome
is **when** the check runs:

- Before launch, refusing has no serving cost: nothing is up yet, and a refusal prevents a bad
  component from ever serving.
- After launch, refusing has an availability cost: work that was being served stops, and a restart
  repeats the same refusal.

That is why the same verification (for example of an identity record) can be correct before launch
and a defect after launch.

## Boundary against near entries

| Entry | Different intent | Why this entry is separate |
| --- | --- | --- |
| `service-startup-precondition-bootstrap-deadlock` | A first-start artifact whose only producer is the same service | That entry is about a first-start dependency cycle. This one forbids a stop for checks that run after start. |
| `supervised-restart-stale-worker-state-guard` | A startup state-cleanliness guard poisoning supervised restarts | That entry keeps the launch refusal and narrows its scope. This one moves post-launch checks out of the launch path entirely. |
| `observability-readiness-closed-status-local-alert-recovery` | Health and readiness must agree on degradation | That entry describes how to report degraded. This one decides that degradation, not a stop, is the required reaction. |
| `architecture-import-time-assert-anti-pattern` | An assert that can be stripped by an interpreter mode | Timing of evaluation, not component availability. |

## Failure modes observed in the source family

- A post-launch comparison of durable records stopped a serving component, and supervision restarted
  it into the same comparison, producing a restart loop.
- Independent components acquired a startup order because one refused to start while another was
  absent.
- The request path already refused the affected requests correctly; the extra process-level refusal
  added no protection and removed availability.

## Checkpoint the entry proposes

Grep a component for exits and health transitions reachable only after start. Accept a hit only when
its code comment names the authorizing issue. Reject a hit whose comment says only "fail closed".

## Verified On

| Project | Context | Details |
| --- | --- | --- |
| Comet | Repository agent contract, 2026-11 | The rule is stated for all components, not one service. The contract is the authority; the evidence is the contract text above. |

## Privacy review

This notes file records no person, account, organization, internal path, host, URL, repository
name, issue identifier, or proprietary source. It paraphrases the rule and the failure shapes only.