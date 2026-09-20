---
name: myrmidon-research-grounding-swarm-with-counterfactual-track
license: BSD-3-Clause
description: "Ground a speculative premise in cited science, optionally using independent research and counterfactual tracks before synthesizing the requested deliverable."
category: architecture
date: 2026-05-30
version: "1.1.0"
user-invocable: false
verification: verified-local
tags: [myrmidon, swarm, parallel-agents, l0-commander, opus, research-grounding, counterfactual-track, evidence-file-per-dimension, feasibility-tagging, citations, synthesis-agent, creative-premise, science-grounding, wave-dispatch]
---

# Myrmidon Research-Grounding Swarm with Counterfactual Track

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-05-30 |
| **Objective** | Ground a speculative premise ("AI simulating the Planck-constant reaction in real time on a handheld device for ultra-precise measurement of reality", plus follow-on invented computing concepts) in real, cited science using a Myrmidon Opus swarm — pure research, no narrative content injected |
| **Outcome** | Successful: swarm ran end-to-end this session; ~47 single-purpose Opus research briefings + 1 synthesis (`00-SYNTHESIS.md`) produced, all files present on disk under `Story/Research/` |
| **Verification** | verified-local |
| **Concrete example** | Sci-fi premise grounding 2026-05-30: ~47 cited briefings, one Opus agent per research dimension, plus a parallel "assume Heisenberg uncertainty principle is false" counterfactual track, converging in one synthesis agent |

## When to Use

- A speculative premise needs scientific grounding and explicit uncertainty.
- A counterfactual physical assumption should be separated from established science.
- Independent research dimensions can use separate evidence notes before synthesis.

## Verified Workflow

### Quick Reference

Clarify the scientific claim and requested deliverable, gather relevant sources, distinguish
established findings from speculation, and synthesize the result. Use direct research for compact
work. Consider independent agents when supported and useful; unavailable delegation need not
block research. Complete narrative integration too when the user requested it.

### Research and synthesis

- Preserve the premise's meaning and correct unit or category errors, such as confusing the
  Planck constant with Planck length. Quoting the exact premise can help when wording matters.
- Divide work by coherent questions. One dimension per agent was useful in the recorded case;
  combine related questions when that improves reasoning and avoids duplicated research.
- Choose models and concurrency from task needs and current host limits. The historical Opus
  selection and five-agent wave size below are observations, not universal requirements.
- Give each independent writer a distinct output path to prevent collisions. Incorporate user
  steering through available coordination tools and reconcile partial results with current scope.
- Label consequential claims by evidence strength. Cite primary sources and distinguish a
  scientific result from engineering feasibility or speculative extrapolation.
- Add a counterfactual track when it answers the user's question. Identify which conclusions
  depend on the changed assumption and which constraints remain independently supported.
- Synthesize available findings, compare disagreements, and investigate material gaps. Missing
  optional briefings do not prevent useful independent work; explain unresolved uncertainty.

### Suggested research prompt

```text
Research <QUESTION> for the user's premise <PREMISE>.
Distinguish established results, frontier research, and speculation. Correct misconceptions
that affect the answer and cite primary sources for consequential claims.
Write a concise evidence note to <OUTPUT_PATH>. Include findings, uncertainty, and sources;
use tags or tables when they help comparison. Continue through the assigned question.
```

### Suggested counterfactual prompt

```text
Examine <QUESTION> under the explicit fictional assumption <ASSUMPTION>.
Separate real-world evidence from consequences inferred under that assumption.
Identify independent limits that remain. Record findings at <DISTINCT_OUTPUT_PATH>.
```

### Suggested synthesis prompt

```text
Synthesize the available research notes for <REQUESTED_OUTCOME>.
Reconcile conflicting claims using their sources and uncertainty. A table of shared limits
or feasibility levels may help. Follow up on material gaps when possible and explain those
that remain. Complete any requested narrative or thematic integration after the evidence
supports it; keep fictional assumptions distinct from scientific claims.
```

### Output paths and progress

A pattern such as `Story/Research/NN-topic.md`, `NN-h0-topic.md` for a counterfactual,
and `00-SYNTHESIS.md` for synthesis made the recorded campaign easy to inspect. Use the
project's existing organization when applicable. Prefer completion notifications and bounded
artifact reads to large transcript dumps; consult a focused transcript segment if needed to
diagnose missing or inconsistent results.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Combining two topics into one agent | Researched dark matter + dark energy in a single agent/file | User explicitly wanted them split; combined output had lower focus/recall per topic | Default to one dimension per agent; split on request immediately via NEW filenames |
| `cd` then bare `ls` for inventory | Ran `cd Story/Research` in one Bash call, then `ls` in a later call | `cd` does not persist across Bash tool calls; the bare `ls` resolved against an unexpected cwd | Use ABSOLUTE paths for inventory checks (or rely on the working dir already being the Research dir) |
| Trusting the premise's wording | Took "smaller than the Planck constant" / "fields slightly larger than the planck constant" at face value | Conflates the Planck CONSTANT (action, J·s) with the Planck LENGTH — a unit/category error | Bake "correct the premise's misconceptions" into EVERY agent prompt; flag unit/category errors up front |
| Reading sub-agent JSONL transcripts via shell | `cat`/`grep` the agent transcript output files to check progress | Context overflow — transcripts are huge | Prefer completion notifications and artifact inventory; use bounded transcript excerpts only when needed |
| Collision-prone replacement filenames | Re-scoped an agent reusing an in-flight agent's filename | Replacement agent would overwrite / race the in-flight one | Give every follow-up/replacement agent a DISTINCT filename (06 → 06a/06b, NN-h0-*) |
| Mixing narrative into research synthesis | Tempted to weave thematic/story integration into the synthesis | User asked to DEFER thematic integration; mixing pollutes the pure evidence corpus | Respect the requested research-only scope; include integration when the user requests it |

## Results & Parameters

### Session (2026-05-30 — speculative premise grounding)

| Metric | Value |
| ------- | ------- |
| Research dimensions | ~46 (one Opus agent each) |
| Counterfactual-track agents | included in total (NN-h0-* siblings for core dimensions) |
| Synthesis agents | 1 (Opus, reads ALL evidence files) |
| Total Opus agents | ~47 research + 1 synthesis |
| Output per agent | one cited briefing, ~1800-2500 words |
| Output path convention | `Story/Research/NN-topic.md`, `Story/Research/NN-h0-topic.md` |
| Synthesis output | `Story/Research/00-SYNTHESIS.md` |
| Dispatch | background async, waves of <= 5 (Myrmidon cap) |
| Narrative injected | none — pure research |

### Tag Schemes (preserve through synthesis)

| Track | Tags |
| ----- | ---- |
| Science feasibility | `[ESTABLISHED]` / `[FRONTIER]` / `[SPECULATIVE]` / `[FRINGE]` |
| Engineering readiness | `[SHIPPING-NOW]` / `[LAB-PROTOTYPE]` / `[FAR-FUTURE]` |
| Counterfactual | `[REAL-PHYSICS]` / `[CONSEQUENCE-IF-PREMISE-TRUE]` / `[SPECULATIVE]` |

### Suggested briefing structure

A summary, evidence with source references, and unresolved questions are usually sufficient.
Length and headings can follow the user's deliverable. Preserve distinctions between scientific
support and counterfactual conclusions when combining notes.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Story / Research | Speculative sci-fi premise grounding, 2026-05-30 | ~47 cited Opus briefings + 1 synthesis under `Story/Research/`; real-physics + counterfactual (Heisenberg-false) tracks; verified-local (files present on disk; not CI-tested) |

## References

- [myrmidon-one-agent-per-item-portfolio-research-pattern.md](myrmidon-one-agent-per-item-portfolio-research-pattern.md) — Sibling pattern: one agent per item for portfolio/due-diligence research (this skill applies the same granularity rule to research dimensions and adds a counterfactual track + feasibility tagging)
- [parallel-agent-research-and-swarm-orchestration.md](parallel-agent-research-and-swarm-orchestration.md) — General Myrmidon swarm orchestration (wave limits, agent tiers, L0 commander)
- [swarm-agent-status-misread-as-premature-exit.md](swarm-agent-status-misread-as-premature-exit.md) — Handling agent status misreads during wave execution
