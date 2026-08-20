# Parallel Agent Swarm Dispatch Notes

Supporting cases for
[`parallel-agent-swarm-dispatch-patterns.md`](parallel-agent-swarm-dispatch-patterns.md).

## Case Index

| Case | Source | Verification | Material result |
| --- | --- | --- | --- |
| Prompt guardrails and ownership | [Immutable source](https://github.com/HomericIntelligence/Mnemosyne/blob/e7f342098c41f3d5fda1bf7c7fedf754abdaaad2/skills/parallel-agent-swarm-dispatch-patterns.md) | verified-local | Reduced stalls with bounded scope, executable directives, and explicit files |
| Hot-file bundling and phase gate | [Immutable source](https://github.com/HomericIntelligence/Mnemosyne/blob/e7f342098c41f3d5fda1bf7c7fedf754abdaaad2/skills/parallel-agent-swarm-dispatch-patterns.md) | verified-local | Avoided fan-out conflicts and prevented consumers from using malformed artifacts |
| Audit remediation swarm | [Immutable source](https://github.com/HomericIntelligence/Mnemosyne/blob/e7f342098c41f3d5fda1bf7c7fedf754abdaaad2/skills/parallel-agent-swarm-dispatch-patterns.md) | verified-local | One thematic issue and isolated PR per owner with coordinator verification |
| Dependency-chain executor | [Immutable source](https://github.com/HomericIntelligence/Mnemosyne/blob/e7f342098c41f3d5fda1bf7c7fedf754abdaaad2/skills/parallel-agent-swarm-dispatch-patterns.md) | verified-ci | Replaced concurrent polling with one sequential state machine |
| Gate-loop early exit | [Immutable source](https://github.com/HomericIntelligence/Mnemosyne/blob/e7f342098c41f3d5fda1bf7c7fedf754abdaaad2/skills/parallel-agent-swarm-dispatch-patterns.md) | verified-ci | Hard cap, explicit success branch, continuation directive, and absolute completion rule |

## Detailed Observations

The superseded source records campaign-specific stall rates, executor counts, time estimates, issue
numbers, and prompt transcripts. Those values explain the rules but are not universal defaults.
Current capacity, task complexity, and host delegation support determine wave size and routing.

The dependency-gate incidents were semantic prompt failures: the executor interpreted “wait until
ready” as the complete assignment. Successful prompts separated the gate from Step 1 and repeated
the real terminal condition at the end. The reusable main retains that structure without copying
the original transcripts.

The audit-remediation case also showed that fabricated identifiers often arise when a prompt demands
a closing keyword before the coordinator has created an issue. The coordinator must create or verify
the tracking issue first, then provide its exact number.

## Provenance

- Superseded main SHA-256: `d0fa0bc5e245c09de1b52ecc0e0a19495bb67b32710d2b488c2a395de0eb2562`
- Issue #3335 base: `e7f342098c41f3d5fda1bf7c7fedf754abdaaad2`
- Old/new version: `1.4.0` → `2.0.0`
