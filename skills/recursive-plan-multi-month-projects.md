---
name: recursive-plan-multi-month-projects
description: 'Recursive plan-file structure for multi-month research/engineering projects where the plan itself is composed of mini-plans, each composed of sub-plans, and downstream artifacts (issue bodies, code, docs) cite stable §-numbered subsection IDs that survive plan growth and reordering. Use when: (1) scoping a research project that will run for >1 month and span multiple sessions/PRs, (2) the plan must serve as a navigable reference (read non-linearly) rather than a one-shot input to execution, (3) downstream artifacts will cite §-numbers from the plan and refactoring the plan must not break those cites, (4) the same plan will be referenced by future agents (sub-agents, future Claude sessions, human collaborators) who need to jump to specific subsections, (5) a single planning session must produce 5+ independent deliverables (scoping docs, epic body, child issue bodies, GitHub-filing pass, commit pass).'
category: documentation
date: 2026-05-12
version: 1.0.0
user-invocable: false
verification: verified-local
tags: [planning, plan-structure, recursive, multi-month, scoping, research-project, stable-ids, reading-guide, multi-pass, execution-model, divergence-escalation]
---

# Recursive Plan Structure for Multi-Month Projects

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-05-12 |
| **Objective** | Define a recursive plan-file structure that serves as a long-lived navigable reference across multiple execution sessions, with stable §-numbered subsection IDs that downstream artifacts can cite without breaking when sibling sections are added or reordered. |
| **Outcome** | Verified end-to-end on a 25-issue research-project backlog (Predictive-Coding-in-Mojo Phase 0 scoping); produced two merged PRs (5 scoping docs + 25 issue bodies), one epic, and 25 child issues, all citing back into the plan by stable §-IDs. |
| **Verification** | verified-local — used end-to-end in a single session; not yet validated across multiple distinct projects. |
| **Source** | mvillmow/Random Predictive-Coding-in-Mojo Phase 0 scoping (PRs #2, #3; epic #4; child issues #5-#29) |

This skill captures a **structural pattern** for the plan file itself, not a workflow for
executing a plan. The pattern is recursive: the top-level Approach is an N-pass plan; each pass
is a mini-plan with numbered steps; each step that produces an artifact has its own
per-section plan. Subsection IDs (`§4.3.2`) are stable across plan growth so downstream
artifacts (issue bodies, code, docs, future sessions) can cite them durably.

## When to Use

- Scoping a research or engineering project that will run for **>1 month** and span **multiple sessions / PRs**
- The plan must serve as a **navigable reference** (read non-linearly), not just a one-shot input to a single execution session
- **Downstream artifacts** (issue bodies, code, docs, follow-up plans) will cite §-numbers from the plan, and refactoring the plan must not break those cites
- The same plan will be **referenced by future agents** (sub-agents, future Claude sessions, human collaborators) who need to jump to specific subsections without reading the whole document
- A single planning session must produce **5+ independent deliverables** (e.g., scoping docs, epic body, child issue bodies, GitHub-filing pass, commit pass)
- The execution session needs an **explicit divergence-escalation register** so it knows when to surface decisions back to the user instead of pressing on with implicit judgment

### When NOT to Use

- One-shot tasks where the plan is read once and discarded → use a flat plan instead
- Tasks where the deliverable IS itself the plan → use the deliverable's own structure, not this meta-structure
- Tasks under ~5 deliverables → the recursive overhead exceeds the navigation benefit

## Verified Workflow

### Quick Reference

```markdown
# Plan: <one-line goal>

> **Reading guide.** This plan is recursive: the top-level Approach is an N-pass plan (§3);
> each pass is a mini-plan with numbered steps (§3.1 – §3.N); each step that produces an
> artifact has its own per-section plan (§4 – §10). §11 is the verification plan. §12 tracks
> open risks.
>
> The execution session can read top-down or jump to any subsection by ID. Subsection IDs
> are stable: do not renumber existing §s when adding new siblings — append.

## §1 Context
## §2 Material discoveries from <prior phase>
## §3 Approach for the execution session
  ### §3.0 Per-artifact review loop (applies to every artifact)
  ### §3.1 Pass 1 — <description>
  ### §3.2 Pass 2 — <description>
  ...
## §4 Per-section plan: <artifact 1>
  ### §4.1 <subsection>
  ### §4.2 <subsection>
  ### §4.3 <subsection>
  #### §4.3.2 <sub-subsection>
  ...
## §5 Per-section plan: <artifact 2>
...
## §11 Verification plan
## §12 Open risks and decision points the execution session may need to re-surface
```

Greppable §-prefix invariant:

```bash
# All cites resolve cleanly
grep -RhoE '§[0-9]+(\.[0-9]+)*' . | sort -u
# Compare against the plan's defined IDs:
grep -oE '^#+ §[0-9]+(\.[0-9]+)*' plan.md | awk '{print $2}' | sort -u
```

### Step 1: Open with a "Reading Guide"

Most plans assume top-down reading. A recursive plan does not. The first paragraph of the
file MUST explicitly say:

1. "This plan is recursive."
2. The reader can jump to any subsection by ID.
3. Subsection IDs are stable — do not renumber when adding siblings, append.

This single paragraph converts the document from a script into a reference work. Without it,
readers (human or agent) default to top-down execution and miss the navigability affordance.

### Step 2: Encode the §-ID into every heading

Every subsection gets a stable ID like `§4.3.2`, encoded **in the heading text itself**:

```markdown
### §4.3.2 ALGORITHM.md → Per-layer-type rules → Conv strategy A
```

Do NOT rely on document order to define IDs. Order changes when sections are added or
reorganized; IDs must not.

The `§` (section sign) prefix has two properties:

- **Greppable** — `grep -oE '§[0-9]+(\.[0-9]+)*'` extracts every cite from any artifact
- **Visually distinct** from regular markdown headings, so readers spot citations immediately

Cites take the form `notes/foo.md → §4.3.2`, which remains valid as the plan grows because
§4.3.2 is encoded in the heading, not derived from position.

### Step 3: Structure execution as N numbered passes

When the plan covers N independent deliverables, structure the execution model as numbered
passes under §3:

```markdown
## §3 Approach for the execution session

### §3.0 Per-artifact review loop (applies to every artifact)
  Auto-review via sub-agents after each artifact; integrate feedback before moving on.
  Reserve human input for DECISIONS, not AUDITS.

### §3.1 Pass 1 — Write 5 scoping docs
### §3.2 Pass 2 — Compose epic body referencing §1-§5 of each scoping doc
### §3.3 Pass 3 — Write 25 child-issue bodies, each citing back to scoping docs
### §3.4 Pass 4 — File epic and children to GitHub
### §3.5 Pass 5 — Commit + PR
```

Each pass:

- Is its own mini-plan with numbered steps (§3.1.1, §3.1.2, ...)
- Produces its own artifact
- Gets its own commit/review cycle
- Can be executed in a separate session if needed (the §-IDs persist across sessions)

### Step 4: Pre-write a per-artifact plan under §4-§10

Each deliverable gets a per-section plan **before execution begins**. The execution agent
should never re-derive structure mid-pass.

```markdown
## §4 Per-section plan: DEPENDENCY_NOTES.md
### §4.1 Header
### §4.2 Distribution & manifest section
### §4.3 Public API surface section
  #### §4.3.1 Tensor types
  #### §4.3.2 Layer-type registry
### §4.4 Known incompatibilities
### §4.5 Citations table
```

This is the recursive payoff: §4 is itself a plan, §4.3 is itself a plan, §4.3.2 is itself a
plan. The execution session reads top-down within a pass and knows exactly what each
subsection should contain.

### Step 5: Build a divergence-escalation register at §12

§12 "Open risks and decision points the execution session may need to re-surface" is the
explicit register of items the execution agent MUST surface to the user if hit, e.g.:

```markdown
## §12 Open risks and decision points

### §12.4 PC-12 (CIFAR PC AlexNet) refutation
If you encounter the Han et al. 2022 result claiming PC-AlexNet matches BP-AlexNet on
CIFAR-100 but cannot reproduce within 2 percentage points: STOP. Surface to user. Do not
silently de-scope the comparison.

### §12.5 Mojo nightly breaking change in `Tensor.dim`
If the execution session lands during a Mojo nightly that has removed Tensor.dim: surface
the API change before fixing in-place; the fix likely cascades through 4 of the 5 scoping
docs.
```

This converts implicit "use judgment" into explicit "stop and ask if you hit X." Without §12,
the execution agent silently makes scope decisions the user would have wanted to weigh in on.

### Step 6: Insert auto-review loops, not human pauses

Originally the plan had explicit "pause for user review" markers between Pass 1 steps. The
user pushed back: *"don't pause for review, just update the plan to run the review using
sub-agents and integrate the feedback."*

The fix: §3.0 defines a **per-artifact review loop** — sub-agent reviews each artifact, the
main agent integrates feedback, then proceeds. Human pauses are reserved for §12 escalations
(actual decisions), not for correctness checks (audits).

This is critical: a plan that pauses every step burns the user's attention budget on things
sub-agents can validate. Keep human attention on §12 items only.

### Step 7: Append-only ID discipline

When adding new sections after initial scoping:

- **DO** append a new sibling: §4.6, §4.7, ...
- **DO NOT** renumber §4.3 → §4.4 to make room — every cite to §4.3 in every downstream
  artifact would silently break
- If a section becomes obsolete, mark it `### §4.3 [SUPERSEDED → see §4.7]` rather than
  deleting

This is the same invariant as URL permalinks: you can deprecate but you cannot recycle.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Initial flat plan | Wrote a flat plan with linear sections (§1, §2, §3...) and no per-artifact sub-plans | User explicitly requested "each section is itself a detailed plan, and each sub-section again is a detailed plan" — the flat plan could not be navigated non-linearly and downstream artifacts had no stable IDs to cite | Recursive plans must be recursive **from the start**; retrofitting requires a full rewrite. Decide on recursive-vs-flat in the first 5 minutes of plan-drafting, before writing any §1 content. |
| Pause-for-user-review at every step | Original plan had explicit "PAUSE: wait for user review" markers between Pass 1 steps (Pass 1.1 → pause → Pass 1.2 → pause → ...) | User said "don't pause for review, just update the plan to run the review using sub-agents and integrate the feedback" — the pauses burned user attention on things sub-agents could validate | Insert auto review-loops (§3.0 per-artifact review via sub-agents) instead of human pauses for correctness checks. Reserve human input for **decisions** (§12 escalations), not **audits** (correctness checks). |
| Order-derived IDs | Early drafts derived §-numbers from heading order (first ## under §4 was §4.1, second was §4.2, etc.) without writing the ID into the heading text | When a new subsection was inserted between §4.2 and §4.3, every downstream cite to §4.3+ silently broke — the IDs had been ambient, not explicit | Encode the §-ID into the heading **text** (`### §4.3.2 ALGORITHM.md → ...`), never derive it from position. Treat IDs as permalinks — append-only, never renumber. |
| Implicit divergence handling | Initial plan trusted the execution agent to "use judgment" when assumptions failed (e.g., a paper's claim couldn't be reproduced) | The execution agent silently de-scoped the comparison and the user only discovered it during PR review, after the work had been committed | Build §12 as an explicit divergence-escalation register listing **named** open risks. Each entry says "if X happens, STOP and surface to user." Removes ambiguity about when judgment ends and escalation begins. |

## Results & Parameters

### Recommended skeleton

```markdown
# Plan: <one-line goal>

> **Reading guide.** This plan is recursive: the top-level Approach is an N-pass plan
> (§3); each pass is a mini-plan with numbered steps (§3.1 – §3.N); each step that
> produces an artifact has its own per-section plan (§4 – §10). §11 is the verification
> plan. §12 tracks open risks. The execution session can read top-down or jump to any
> subsection by ID. Subsection IDs are stable — append, never renumber.

## §1 Context
  ### §1.1 Background
  ### §1.2 Prior work / inputs to this plan

## §2 Material discoveries from <prior phase>
  ### §2.1 What changed since the last plan
  ### §2.2 New constraints

## §3 Approach for the execution session
  ### §3.0 Per-artifact review loop (applies to every artifact in §3.1-§3.N)
  ### §3.1 Pass 1 — <description of artifact 1>
  ### §3.2 Pass 2 — <description of artifact 2>
  ...
  ### §3.N Pass N — <description of artifact N>

## §4 Per-section plan: <artifact 1>
  ### §4.1 <subsection>
  ### §4.2 <subsection>
  #### §4.2.1 <sub-subsection>
  #### §4.2.2 <sub-subsection>

## §5 Per-section plan: <artifact 2>
  ### §5.1 ...
  ...

## §6-§10 Per-section plans for additional artifacts

## §11 Verification plan
  ### §11.1 What "done" looks like for each artifact
  ### §11.2 Cross-artifact consistency checks (e.g., every cite resolves)

## §12 Open risks and decision points the execution session may need to re-surface
  ### §12.1 <named risk>: if <condition>, STOP and surface to user
  ### §12.2 <named risk>: ...
  ...
```

### Layout invariants

| Invariant | Rule | Why |
|-----------|------|-----|
| Reading guide at top | First paragraph after H1 says "this plan is recursive" + "jump to any §-ID" + "IDs stable" | Tells readers (human + agent) the document is a reference, not a script |
| §-ID in heading text | Every heading includes `§N.M.K` literally, e.g., `### §4.3.2 Foo` | Cites resolve by string match, not by position; reorderings don't break cites |
| Append-only IDs | Never renumber existing §s; deprecate via `[SUPERSEDED → §X.Y]` | Every downstream cite is a permalink |
| §3 = execution passes | Numbered passes §3.1...§3.N, each producing one artifact | Maps execution model to plan structure 1:1 |
| §3.0 = review loop | Auto-review via sub-agents between artifacts | Reserves human attention for §12 escalations only |
| §4-§10 = per-artifact plans | Each artifact has its own pre-written outline | Execution agent doesn't re-derive structure mid-pass |
| §11 = verification | Cross-artifact consistency checks (cites resolve, IDs stable) | Catches plan-level drift |
| §12 = escalation register | Named open risks with "STOP and surface" triggers | Converts implicit judgment into explicit escalation |

### Cite-resolution check

After execution, verify every §-cite in every downstream artifact resolves to a heading in
the plan:

```bash
# Extract every cite from every artifact
grep -RhoE '§[0-9]+(\.[0-9]+)*' artifacts/ | sort -u > cites.txt

# Extract every defined ID from the plan
grep -oE '§[0-9]+(\.[0-9]+)*' plan.md | sort -u > defined.txt

# Cites that don't resolve = bugs
comm -23 cites.txt defined.txt
```

If `comm -23` is non-empty, either an artifact cites a §-ID that was never created, or a §-ID
was renumbered (violating the append-only invariant) and downstream cites were not updated.
Both are bugs.

### Sizing heuristics

| Project size | Use this pattern? |
|--------------|-------------------|
| 1-4 deliverables | NO — flat plan is sufficient; recursive overhead exceeds benefit |
| 5-15 deliverables, single session | OPTIONAL — flat with sub-bullets often works; recursive helps if you want navigability |
| 5+ deliverables, multi-session | YES — stable IDs and per-artifact sub-plans pay off across sessions |
| 25+ deliverables, multi-month | YES — the §-ID permalink discipline is the only thing that keeps cites stable as the plan grows |

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| mvillmow/Random | Predictive-Coding-in-Mojo Phase 0 scoping; produced PR #2 (5 scoping docs) + PR #3 (25 issue bodies) + epic #4 + child issues #5-#29 | Plan file at `~/.claude/plans/master-prompt-predictive-coding-majestic-harp.md`. All 25 child issues cite back into the 5 scoping docs by `§N.M` IDs; no cites broke during 5-pass execution. Auto-review loop at §3.0 caught 3 cite typos before commit. §12 surfaced 1 open risk (PC-12 refutation) that the user weighed in on before it was silently de-scoped. |
