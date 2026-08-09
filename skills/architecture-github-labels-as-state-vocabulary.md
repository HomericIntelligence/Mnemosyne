---
name: architecture-github-labels-as-state-vocabulary
description: "Use mutually-exclusive `state:*` GitHub labels as the single source of truth for pipeline state, with deterministic disjoint mutations and strict fail-closed reads. Use when: (1) automation gates work on fragile free-text verdicts, (2) multiple components must read one durable GitHub state signal identically, (3) state swaps must remain one canonical `gh issue edit`, (4) duplicate, shuffled, malformed, unavailable, or contradictory labels must not authorize progress, (5) batched GraphQL reads need an unavailable sentinel plus strict per-item fallback, (6) post-mutation confirmation and retries must fail closed without compensating writes."
category: architecture
date: 2026-08-07
version: "1.4.0"
user-invocable: false
verification: verified-local
history: architecture-github-labels-as-state-vocabulary.history
tags:
  - github-labels
  - state-vocabulary
  - state-machine
  - plan-review
  - go-nogo-gate
  - free-text-fragile
  - structured-state
  - self-healing-backfill
  - actions-injection
  - org-provisioning
  - gh-issue-edit
  - mutually-exclusive-labels
  - source-of-truth
  - shared-gate-divergence
  - replan-transition
  - unexecuted-edge
  - stuck-closed-gate
  - state-transition-audit
  - atomic-label-swap
  - swap-not-bare-add
  - combined-edit-primitive
  - mutually-exclusive-invariant
  - deterministic-label-mutation
  - disjoint-add-remove
  - fail-closed-readback
  - exclusive-state-reader
  - idempotent-retry
  - strict-label-payload
  - graphql-unavailable-sentinel
  - rest-fallback
  - tri-state-cache
  - authorization-read
---

# Architecture: GitHub Labels as State Vocabulary (Not Free-Text Comments)

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-08-07 |
| **Objective** | Replace fragile regex-parsing of free-text comment bodies (e.g. `Verdict: GO/NOGO`) with mutually-exclusive `state:*` GitHub labels as the single source of truth for per-issue pipeline state — eliminates "comment unparseable → issue permanently stuck" and "planner and implementer disagree → infinite loop" failure modes |
| **Outcome** | Pattern executed end-to-end on 2026-05-29 in HomericIntelligence/ProjectHephaestus PR #707; 911 automation tests pass locally, ruff + mypy clean. Three labels (`state:needs-plan`, `state:plan-no-go`, `state:plan-go`) defined, idempotent provisioner CLI shipped, `issues:opened` workflow auto-tags new issues, reviewer applies-and-removes opposites, implementer trusts the terminal label absolutely. One-time comment-scan backfill self-heals legacy issues. |
| **Verification** | verified-local — the original label-state pattern passed 911 automation tests plus ruff and mypy locally in ProjectHephaestus PR #707. **The v1.1.0 through v1.4.0 additions are design-stage / unverified**: the re-plan edge, atomic-swap refinement, deterministic normalization, strict payload parsing, GraphQL unavailable sentinels, per-issue fallback, exclusive readers, readback ownership, and retry recovery are specified but were not implemented or executed in the sessions that captured them. |
| **Live observation that motivated this** | 320 "no parseable Verdict" WARNINGs across an org-wide automation run, plus wasteful re-planning of already-approved issues because the latest comment's verdict line had drifted from the regex contract |

## When to Use

- An automated pipeline gates per-issue work on a regex-parsed verdict from the **latest** comment body, and you have observed unparseable comments that permanently block forward progress
- You are building a planner+reviewer+implementer pipeline where **all three components must read the same gate signal** and you want the signal to be cheap to query and impossible to misparse
- You see logs like `Issue #N: no parseable Verdict line in plan-review comment — defaulting to NOGO` more than a handful of times across one loop iteration
- You want a `gh issue list --label state:plan-go` style cheap query to drive ranking, dashboards, or per-state batching
- You need a **state vocabulary** that survives prompt/contract evolution: changing the LLM's verdict-line format must not invalidate already-approved issues
- You are migrating an existing pipeline and need a **one-time fallback** that promotes a parseable verdict from existing comments into a label, so the migration self-heals without manual relabeling
- You suspect a **shared-gate divergence bug** where two pipeline components read different signals: e.g. the planner sees "plan comment exists → skip" while the implementer sees "review unparseable → defer" → the issue cycles forever
- You are wiring an `on: issues: opened` Action that tags new issues with `state:needs-plan` and need to harden it against the GitHub Actions script-injection class
- You need to provision the labels across an org so the first reviewer write doesn't race against a missing label name
- Your labels-first gate deliberately returns False under a rejection label (e.g. `state:plan-no-go`), and a re-plan / retry cycle **never converges** — it exhausts a per-cycle budget and fails instead of re-entering the fresh state. This is usually a **documented-but-unexecuted state-transition edge** (see Failed Attempt #9)
- You are about to implement a `state:*` transition and your GitHub accessor only exposes **separate `add_labels` / `remove_labels`** methods — you need the transition to be a mutually-exclusive **swap** (add one, remove the siblings) done as **one atomic `gh issue edit`**, so add a combined `edit_labels(add=[...], remove=[...])` primitive rather than emitting two calls (see Failed Attempt #10). A naive "add the fresh label back" fix leaves the rejection label in place and transiently violates the one-label invariant.
- Equivalent label mutations produce different argv, dry-run diagnostics, or logs because callers supply duplicates or permutations. Canonicalize once, before provisioning, logging, or transport.
- A reader reports GO merely because the GO label is present, even when NO-GO is also present. Interpret each state family as a set and accept only an exact singleton; contradictory or malformed reads fail closed.
- A state writer returns success immediately after `gh issue edit`. The transition owner must perform a fresh exclusive readback, while generic label helpers remain state-family agnostic.
- A batched GraphQL label fetch maps missing aliases, malformed nodes, or response errors to `[]`, making unavailable state indistinguishable from a successfully read empty collection and preventing a strict per-item fallback.
- A `check=False` GitHub call is parsed without checking its return code, or a label parser silently ignores malformed siblings in an otherwise plausible payload. Authorization must reject the entire read.
- Tests or compatibility callers can inject raw issue payloads behind an adapter. Every authoritative gate and post-mutation confirmation must re-parse that payload strictly at its own boundary.

**Don't use when:**

- The pipeline state is naturally ephemeral (in-memory only, no persistence across loop iterations) — overkill
- The state machine has more than ~5 states and lots of transitions — labels become noisy; use a JSON state file in the repo or a real DB
- You only need a single boolean and `gh pr review --approve` already encodes it natively
- The repo is a personal scratch project with no org-wide automation — KISS, just leave comments

## Verified Workflow

### Quick Reference

```bash
# ── The 3 mutually-exclusive labels (the entire vocabulary) ──
#
#   state:needs-plan   — set by issues:opened workflow (or no state label = needs-plan)
#   state:plan-no-go   — set per NOGO review iteration
#   state:plan-go      — terminal: implementer trusts this absolutely, never re-plans
#
# Only ONE of the three may be set on an issue at any time.

# ── Reviewer transition (NOGO this iteration) ──
gh issue edit <N> \
    --repo <owner>/<repo> \
    --add-label state:plan-no-go \
    --remove-label state:needs-plan \
    --remove-label state:plan-go

# ── Reviewer transition (GO — terminal) ──
gh issue edit <N> \
    --repo <owner>/<repo> \
    --add-label state:plan-go \
    --remove-label state:needs-plan \
    --remove-label state:plan-no-go

# ── Implementer read (cheap, no comment fetch needed) ──
if gh issue view <N> --json labels --jq '.labels[].name' | grep -qx 'state:plan-go'; then
    proceed_to_implementation
else
    defer
fi

# ── One-time self-healing backfill (run when no state label is set) ──
if no_state_label_present && latest_plan_review_comment_parseable_as_GO; then
    apply state:plan-go   # promote legacy comment verdict → label
elif no_state_label_present && latest_plan_review_comment_parseable_as_NOGO; then
    apply state:plan-no-go
fi
# Subsequent runs short-circuit on the label — no re-parsing.

# ── Org-wide idempotent provisioning ──
for color_pair in "state:needs-plan:fbca04" "state:plan-no-go:d73a4a" "state:plan-go:0e8a16"; do
    name="${color_pair%:*}"; color="${color_pair##*:}"
    gh label create --force "$name" --color "$color" --repo "$ORG/$REPO"
done
```

### Detailed Steps

1. **Define the vocabulary as a small, mutually-exclusive set**:
   - Three labels is the sweet spot for a plan-review gate: one initial state, one rejection state, one terminal acceptance state.
   - Use the `state:` prefix as a namespace to keep them grouped and to make `gh issue list --label state:*` queries trivial.
   - Pick distinct colors so the GitHub UI also tells the story (yellow=needs-plan, red=plan-no-go, green=plan-go).

2. **Pick the source of truth and commit to it**:
   - The label is authoritative. The comment body is documentation.
   - The implementer must read **only** the label. Never re-parse the comment to "double-check".
   - If you find yourself parsing the comment as a tiebreaker, you have re-introduced the bug — go fix the writer instead.

3. **Make every write a single atomic transition**:
   - `gh issue edit --add-label X --remove-label Y --remove-label Z` is one HTTP call.
   - This is the closest to "atomic" you get with the GitHub API; two-step (remove then add) leaves a window where the issue has zero state labels.
   - Always remove **both** opposing labels even if you believe one is absent — `gh issue edit --remove-label` no-ops cleanly on absence.

4. **Ship a tiny idempotent provisioner so the first write doesn't race**:
   - `gh label create --force <name> --color <hex>` creates-or-updates with one call per label per repo.
   - Run it as a setup step in CI, or as a one-shot script over every org repo.
   - `--force` makes it idempotent: re-running is safe and converges on the desired color/name.

5. **Auto-tag new issues with `state:needs-plan` via an `on: issues: opened` workflow**:
   - Keep the workflow tiny: one job, `permissions: contents: read, issues: write`, calls `gh api -X POST /repos/.../issues/<num>/labels`.
   - **Harden against Actions injection (CWE-94)**: consume only server-controlled integers (`github.event.issue.number`), validate they are numeric before use, and use `gh api` against the labels endpoint instead of building shell commands from event data.
   - Never interpolate `github.event.issue.title` or `body` into a shell string — those are attacker-controlled.

6. **Provide a one-time self-healing backfill**:
   - The migration moment is fragile: existing issues have a comment-form verdict but no label.
   - On startup of each pipeline component, **once per issue**: if no state label is set and the latest plan-review comment parses to GO or NOGO, promote that to a label and return.
   - This is the ONLY place the legacy comment-scan path remains. All steady-state reads use the label.
   - Self-heal converges the org without manual cleanup; you can delete the backfill code in a release or two.

7. **Make the planner and implementer read the same signal**:
   - The infinite-loop class of bug comes from two components disagreeing.
   - Both `has_existing_plan` (planner skip-gate) and `is_plan_review_go` (implementer go-gate) must consult the same label set.
   - If a plan exists but the verdict is `state:plan-no-go`, the planner must **re-plan** (not skip), and the implementer must **defer** (not implement). They agree on the signal, not the action.

8. **Treat `state:plan-go` as terminal and never reversible**:
   - Once GO is applied, the implementer trusts it absolutely. No re-review, no re-parse.
   - If a plan turns out wrong post-GO, the recovery path is a new issue, not a `state:plan-no-go` flip back.
   - This invariant is what unlocks the cheap short-circuit: one label read replaces 100+ comment fetches per loop iteration.

9. **Execute every documented transition edge — the re-plan edge is the one that gets forgotten** *(design-stage, pending implementation in ProjectHephaestus issue #1857)*:
   - A labels-first plan gate that returns False under `state:plan-no-go` (independent of any plan comment) has a hidden precondition: **something must eventually clear that rejection label**, or the gate is stuck-closed forever.
   - The lifecycle diagram documents `state:plan-no-go ──re-plan──▶ state:needs-plan`, but a diagram edge is not code. Audit: *which component actually performs each documented transition edge?* The deadlock is almost always an edge that is drawn but never executed.
   - The component that **re-plans** (the planning stage's `on_enter`) must be the one to execute this edge: on re-entry it must **atomically clear `state:plan-no-go` and restore `state:needs-plan`**. Otherwise the shared gate (`has_existing_plan` / `is_plan_review_go`) stays False, VERIFY never ADVANCEs, and the retry budget (`plan_cycles`) drains to a FINISH_FAIL — the intended second plan cycle is unreachable.
   - **The re-plan write is a SWAP, not a bare ADD** *(v1.2.0 refinement — a plan reviewer will NOGO the naive version)*: the failing verdict helper (`apply_plan_verdict` on NOGO) returns `(add=state:plan-no-go, remove=[state:plan-go, state:needs-plan])`, so on fail-back the issue carries `state:plan-no-go` and **neither sibling**. A naive fix that only ADDs `state:needs-plan` back (`if X not in labels: add([X])`) leaves `state:plan-no-go` in place — this **transiently violates the mutually-exclusive-label invariant** (both labels present) AND still leaves `has_existing_plan` stuck-False. The correct helper must **remove the sibling rejection/terminal labels**: `replan_transition() -> (add=[needs-plan], remove=[plan-no-go, plan-go])`.
   - **The swap must be ONE atomic write, not paired add+remove calls** *(v1.2.0 refinement)*: Detailed Step #3 already mandates a single `gh issue edit --add-label X --remove-label Y --remove-label Z`. But a pipeline whose GitHub accessor exposes only SEPARATE `add_labels` / `remove_labels` methods (each its own `gh issue edit`) **cannot honor that rule** — a two-call sequence leaves a crash window where the issue has zero or two state labels. Lesson: **when the state-label accessor lacks a combined-edit primitive, ADD one** (`edit_labels(issue, add=[...], remove=[...])` mapped onto a single `gh issue edit`) and route ALL `state:*` transitions through it. A plan reviewer WILL (and did) NOGO a swap implemented as two separate mutator calls, flagging the residual atomicity gap.
   - Keep the transition in the **single state-vocabulary module** as a pure helper (`replan_transition() -> (STATE_NEEDS_PLAN, [STATE_PLAN_NO_GO, STATE_PLAN_GO])`) living beside the GO/NOGO `apply_plan_verdict` helper. Do **not** inline label-name literals at the `on_enter` call site.
   - **Ordering matters:** clear the no-go label *before* any "plan already exists → fast-forward" check in the same `on_enter`, so the label state is coherent for the whole entry body. A stale plan comment plus a last-verdict-of-NOGO still reads as *not approved*, so this ordering also prevents a premature fast-forward.
   - **Idempotency:** guard the transition write on *`state:plan-no-go` present* (mirror the existing `state:needs-plan` presence guard). Steady-state re-entry then produces **zero mutations**.
   - **Do NOT "fix" this by making VERIFY scan the plan-comment marker directly** — that reintroduces two-signals-for-one-gate divergence (Failed Attempt #2). The fix is to execute the missing transition, not to add a second reader.

10. **Canonicalize mutations and fail closed on every state read** *(v1.3.0, proposed and unverified)*:
    - Put one pure normalization authority beside the label vocabulary. Convert additions and removals to sorted, de-duplicated lists and reject their intersection **before** logging, label provisioning, dry-run handling, or GitHub I/O. This makes permutations observationally identical and prevents a label from being both added and removed in one command.
    - Route generic add, remove, and combined-edit helpers plus repo-scoped transport builders through that authority. A state swap still emits exactly one `gh issue edit`; normalization changes only determinism and validation.
    - Parse GitHub label payloads into sets. Readers for a mutually-exclusive family must compare the active family labels to exact singleton sets. GO+NO-GO, multiple plan states, malformed payloads, transport errors, and JSON errors all fail closed rather than selecting the first label or treating membership as approval.
    - Keep ownership explicit: generic label helpers canonicalize and mutate but do not infer a state family. The state-transition owner performs the atomic swap and then a **fresh exclusive readback**. A repo-scoped adapter confirms through its repo-scoped reader; an ambient adapter delegates the entire operation to the ambient transition owner and does not confirm twice.
    - Provisioning is an idempotent prerequisite, not part of a rollback protocol. If provisioning succeeds but mutation or readback fails, propagate the exception and issue no compensating add/remove writes. Retry the identical canonical atomic swap and readback; this reconciles absent, successful-but-unconfirmed, and contradictory outcomes.
    - Test at three seams: pure normalization/exclusivity, command construction and dry-run diagnostics, and transition-owner mutation/readback/retry. Include duplicate and reversed inputs, pre-I/O overlap rejection, one-edit assertions, contradictory label sets, malformed reads, mutation exceptions, and failed-readback retry.

11. **Preserve unavailable versus successfully empty label state** *(v1.4.0, proposed and unverified)*:
    - Define one strict payload parser beside the label vocabulary. A valid payload is an object whose `labels` value is a list containing only objects with a non-empty string `name`. Collapse duplicate names into a set, but reject mixed strings/dictionaries, missing collections, malformed nodes, and empty names as a whole; never discard only the bad siblings.
    - At every `check=False` CLI boundary, require `returncode == 0` before decoding JSON. Transport failure, invalid JSON, and invalid payload shape are unavailable state, not an empty successful read and never authorization.
    - Model batched reads with three meanings: a label list is successful state (including `[]` for a confirmed empty collection), `None` is unavailable or malformed state, and absence of an issue key is also unavailable. Initialize every requested issue to `None`; populate only aliases whose repository, issue, label connection, nodes, and nodes' names all validate.
    - When a planner receives `None` from the batch, perform one independent strict per-issue REST read. Only a successful exclusive `state:plan-go` result may skip planning. If the fallback fails or remains malformed, retain `None`, keep the issue eligible for work, and do not convert uncertainty into GO or a durable empty cache entry.
    - Make plan and implementation predicates symmetric. GO and NO-GO each require that their own label be the exact singleton active label in the family. A contradictory pair returns neither flag, regardless of payload order.
    - Re-parse raw payloads at authorization and transition-confirmation boundaries even when a production adapter normally validates them. This protects against compatibility callers and test doubles bypassing the adapter and keeps every writer's one-edit/one-readback contract locally enforceable.
    - Exercise all mutation owners, not only the shared helper. Standalone plan review, planning-stage re-entry, plan-review verdicts, ambient implementation markers, and repo-scoped implementation markers must each prove exactly one combined edit followed by exactly one fresh exclusive read. Malformed or contradictory confirmation must raise or retry without advancing.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| 1 | Comment-text-only gate: `is_plan_review_go` regex-scanned the latest plan-review comment for `Verdict: GO/NOGO` | Comments written before the contract existed (or by an agent that drifted off-format) were unparseable and defaulted to NOGO → permanently blocked. 320 "no parseable Verdict" WARNINGs observed on a single org-wide run. | Text formats drift; structured GitHub primitives don't. Use server-validated labels for state. |
| 2 | Plan-existence-only skip: `has_existing_plan` checked only whether a plan comment existed, not its quality | Issues with a plan + unparseable review were both "already planned" (planner skips) and "not yet approved" (implementer defers) → infinite loop, no party will move it forward. | When two pipeline components share a gate, they must read identical signals. Make the source of truth one thing, not two. |
| 3 | Adding `state:review-in-progress` as an intermediate state to "explain" the limbo | Unnecessary churn: the transient state has no consumer, and any failure mid-review leaves issues stuck in the intermediate. Three terminal/transitional states are sufficient. | YAGNI applies to state machines too. Don't add a state unless a real consumer reads it. |
| 4 | Comment-only verdict with a "second-chance" re-parse on the most recent N comments | Doubled the parse-failure surface area (N comments, any of which might be unparseable). Added log noise without raising the success rate, because the failure was in the writer, not the reader. | Don't paper over a contract violation by widening the parser; fix the writer (or move to structured state). |
| 5 | Storing state in a JSON file inside the repo via PR comments to a state branch | Added a PR per state transition; the rate of state changes was higher than the merge bandwidth → state branch fell behind reality; defeated the cheapness goal. | GitHub already has structured per-issue state — labels. Don't reinvent it as a file. |
| 6 | Building the state-tagging workflow to consume `github.event.issue.title` to derive the label | Opened a GitHub Actions injection vector — attacker-controlled title could break out of the shell command. Even with quoting it's fragile. | Only consume server-controlled integers (`issue.number`); validate numeric before use; call `gh api` against typed endpoints rather than shelling commands built from event data. |
| 7 | Manual provisioning of labels per repo via the web UI | Race: the first reviewer write hits "label does not exist" → 404 → reviewer comment-only fallback → the very bug the labels were meant to fix. | Ship the labels via an idempotent `gh label create --force` CLI; provision before the first write. |
| 8 | Skipping the backfill — "we'll just relabel old issues by hand" | Hand-relabeling 100+ org-wide issues is the kind of toil that never finishes; meanwhile the pipeline burns compute re-planning already-approved work. | A one-time, self-healing backfill is essential for migration. It deletes itself a release or two later. |
| 9 *(design-stage, pending implementation in ProjectHephaestus issue #1857)* | Labels-first plan gate correct, but the **re-plan edge was documented in the diagram and never executed in code**: `plan_review` exhausts its per-cycle budget, applies `state:plan-no-go`, and FAIL_BACKs to `planning`; `planning` re-plans and upserts a fresh plan comment, but VERIFY calls `has_existing_plan()` → labels-first `is_plan_review_go`, which returns False while `state:plan-no-go` is present (independent of any plan comment). | VERIFY never ADVANCEs; it RETRYs until the `plan` budget (2) drains → FINISH_FAIL. The intended second plan cycle (`plan_cycles=2`) is unreachable. This is a **new facet of Failed Attempt #2**: here the two components *agree* on the label signal, but the re-planning writer never performs the documented `no-go → needs-plan` transition, so the shared gate is **stuck-closed**, not divergent. | When a labels-first gate deliberately returns False under a rejection label, **every edge leaving that rejection state must be executed by some component — not just drawn in a diagram**. Audit "which component performs each documented transition edge?"; the deadlock is the unexecuted edge. Fix: the re-planning `on_enter` atomically clears `state:plan-no-go` and restores `state:needs-plan` (pure helper in the state-vocabulary module, guarded on the label being present for idempotency). Do NOT make VERIFY read the plan-comment marker directly — that recreates Attempt #2's divergence. |
| 10 *(design-stage, pending implementation in ProjectHephaestus issue #1857 — UNVERIFIED; a plan-review NOGO forced this refinement)* | Two naive versions of the Attempt-#9 re-plan fix: **(a)** a bare ADD — `if STATE_NEEDS_PLAN not in labels: add_labels([STATE_NEEDS_PLAN])` — restoring `state:needs-plan` without removing the sibling; **(b)** implementing the swap as **two separate mutator calls** (`add_labels(...)` then `remove_labels(...)`) because the GitHub accessor only exposed separate `add_labels` / `remove_labels` methods, each its own `gh issue edit`. | **(a)** leaves `state:plan-no-go` still present → **both** state labels set at once, transiently violating the mutually-exclusive-label invariant, and `has_existing_plan` stays stuck-False (the no-go label still gates it) — the deadlock is NOT cleared. **(b)** leaves a crash/observation window between the two writes where the issue has zero or two state labels; a concurrent reader (or a crash) sees an incoherent state. A plan reviewer NOGO'd version (b) for exactly this residual atomicity gap. | The re-plan write is a **SWAP, not a bare ADD**: the helper must ADD the fresh label AND REMOVE both siblings — `replan_transition() -> (add=[needs-plan], remove=[plan-no-go, plan-go])` (mirrors `apply_plan_verdict`'s add-one/remove-two shape). And the swap must be **ONE atomic write**: when the state-label accessor lacks a combined-edit primitive, **ADD one** (`edit_labels(issue, add=[...], remove=[...])` → single `gh issue edit --add-label … --remove-label … --remove-label …`) and route every `state:*` transition through it; never emit a transition as paired add+remove calls. |
| 11 *(design-stage, unverified)* | Passing raw caller lists directly into command construction, provisioning, dry-run logging, and audit logs. | Duplicate and permuted inputs produced different argv and diagnostics for the same logical mutation, complicating retries and evidence comparison. Overlapping add/remove inputs could reach I/O with ambiguous intent. | Normalize once at the boundary: `sorted(set(...))` in both directions, reject overlap before every side effect, and reuse the canonical lists everywhere downstream. |
| 12 *(design-stage, unverified)* | Testing approval with membership (`GO in labels`) or extracting the first matching `state:*` label from an ordered payload. | GO+NO-GO could be interpreted as GO, and shuffled API payloads could change the selected state. The durable journal became order-dependent and contradictory state could authorize progress. | Convert payloads to sets and require exact singleton equality for each exclusive family. Contradiction, absence, malformed payload, and read failure must all fail closed. |
| 13 *(design-stage, unverified)* | Letting a state-marking helper return after mutation without a fresh readback, or letting both ambient and repo-scoped layers confirm independently. | An unknown mutation outcome could be reported as success; duplicate confirmation blurred ownership and introduced extra reads with potentially different repository scope. | The transition owner performs one atomic edit plus one fresh exclusive readback. Repo-scoped and ambient paths each have one owner; ambient adapters delegate completely. |
| 14 *(design-stage, unverified)* | Issuing compensating label writes after a provisioned edit or readback failure. | The original write may actually have succeeded, so compensation creates more uncertain states and breaks the one-command swap guarantee. | Propagate failure without rollback. Retrying the same canonical atomic swap is idempotent and reconciles the state, then confirms it with a fresh exclusive read. |
| 15 *(design-stage, unverified)* | Parsing labels with a permissive comprehension that keeps valid dictionaries while silently dropping malformed siblings. | A payload containing GO plus one malformed node looked identical to a clean GO payload and could authorize progress from incomplete evidence. | Validate the entire collection first. One malformed node invalidates the read; duplicate valid names may still collapse into a set. |
| 16 *(design-stage, unverified)* | Initializing every batched GraphQL issue result to `[]` and leaving that default on missing aliases, GraphQL errors, malformed repositories, or invalid label nodes. | The cache could not distinguish "successfully read no labels" from "labels unavailable," so callers could suppress fallback or treat missing evidence as durable state. | Use `None` for unavailable and reserve `[]` exclusively for a successfully read empty label collection; retry `None` through a strict per-issue boundary before authorizing. |
| 17 *(design-stage, unverified)* | Decoding output from a `check=False` GitHub command without first checking the exit status. | Stale, partial, or empty stdout from a failed command could be interpreted as a real empty label set. | Check status before JSON parsing. Nonzero status is unavailable state and cannot authorize any transition. |
| 18 *(design-stage, unverified)* | Assuming the GitHub adapter made every downstream confirmation strict, including test doubles and compatibility paths that returned raw payloads. | A writer could accept a permissively shaped readback in tests or alternate integrations and advance without proving the exclusive durable state. | Parse again at every authoritative gate and post-mutation confirmation boundary; adapter validation and gate validation defend different seams. |

## Results & Parameters

### The State Vocabulary (Authoritative Specification)

| Label | Color | Set By | Removed By | Meaning | Implementer Action |
|-------|-------|--------|------------|---------|--------------------|
| `state:needs-plan` | yellow `fbca04` | `on:issues:opened` workflow; reviewer (when re-planning required) | reviewer (on first GO/NOGO) | Planner must produce a plan for this issue | Defer; await plan |
| `state:plan-no-go` | red `d73a4a` | reviewer (per NOGO iteration) | reviewer (on subsequent GO or when re-planning required) | Latest plan was rejected; planner must revise | Defer; await re-plan |
| `state:plan-go` | green `0e8a16` | reviewer (on first GO — TERMINAL) | nobody (terminal) | Plan accepted; safe to implement | **Proceed to implementation** |

**Invariants:**

- At most one `state:*` label may be set on an issue at any time.
- Absence of any `state:*` label is treated identically to `state:needs-plan` (eases migration).
- `state:plan-go` is terminal. The reviewer never flips it back. Post-GO recovery is via a new issue.
- Mutation additions and removals are deterministic, de-duplicated, and disjoint before any side effect.
- Readers never choose a state by payload order. A contradictory exclusive family authorizes nothing.
- A transition is complete only after its owner observes the expected exclusive state in a fresh read.

### Lifecycle Diagram

```
                     issues:opened
                          │
                          ▼
                  ┌────────────────┐
                  │ state:needs-   │◄────────────────┐
                  │     plan       │                 │
                  └───────┬────────┘                 │ (reviewer
                          │ (planner produces plan,  │  requests
                          │  reviewer evaluates)     │  re-plan)
                          ▼                          │
              ┌───────────┴───────────┐              │
              │                       │              │
              ▼                       ▼              │
       ┌──────────────┐        ┌──────────────┐      │
       │ state:plan-  │◄──────►│ state:plan-  │──────┘
       │     go       │  (no   │   no-go      │
       │ (terminal)   │  back) │              │
       └──────┬───────┘        └──────────────┘
              │
              ▼
        implementer
        proceeds
```

> **⚠ The re-plan edge (`state:plan-no-go ──re-plan──▶ state:needs-plan`) must be
> EXECUTED by a component, not just drawn here.** In ProjectHephaestus issue #1857
> the planning stage's `on_enter` was the intended executor of this edge but never
> performed the transition — so a labels-first gate that returns False under
> `state:plan-no-go` stayed stuck-closed and the re-plan cycle deadlocked at budget
> exhaustion. See Failed Attempt #9. Audit rule: *for every documented transition
> edge, name the component that executes it.*
>
> **⚠ And execute the edge as an ATOMIC SWAP** (v1.2.0, Failed Attempt #10): add
> `state:needs-plan` AND remove **both** siblings in ONE `gh issue edit`. A bare
> add leaves `state:plan-no-go` present (two labels at once, gate still closed);
> a two-call add-then-remove leaves a zero-or-two-label crash window. If the
> state-label accessor only offers separate `add_labels`/`remove_labels`, add a
> combined `edit_labels(add, remove)` primitive and route every transition through it.

### Backfill Decision Logic (One-Time Self-Heal)

```python
def derive_state_label(issue) -> str | None:
    """Compute the desired state label for an issue.

    Steady-state path: labels are authoritative; return None to indicate
    'no change needed'.

    Migration path: when no state label is set, attempt to promote a
    parseable verdict from the latest plan-review comment.
    """
    existing = [lbl for lbl in issue.labels if lbl.startswith("state:")]
    if existing:
        # Labels are authoritative; never override.
        return None

    # No label set — try backfill from existing comments (one-time fallback).
    verdict = parse_latest_plan_review_comment(issue)  # returns "GO" | "NOGO" | None
    if verdict == "GO":
        return "state:plan-go"
    if verdict == "NOGO":
        return "state:plan-no-go"
    # No parseable comment either → treat as needs-plan.
    return "state:needs-plan"
```

### Reviewer Transition Command (Copy-Pasteable)

```bash
# NOGO this iteration:
gh issue edit "$ISSUE_NUM" \
    --repo "$OWNER/$REPO" \
    --add-label state:plan-no-go \
    --remove-label state:needs-plan \
    --remove-label state:plan-go

# GO (terminal):
gh issue edit "$ISSUE_NUM" \
    --repo "$OWNER/$REPO" \
    --add-label state:plan-go \
    --remove-label state:needs-plan \
    --remove-label state:plan-no-go
```

### Org-Wide Provisioning CLI (Idempotent)

```bash
provision_state_labels() {
    local repo="$1"
    gh label create --force --repo "$repo" \
        state:needs-plan --color fbca04 \
        --description "Planner must produce a plan for this issue"
    gh label create --force --repo "$repo" \
        state:plan-no-go --color d73a4a \
        --description "Latest plan was rejected; planner must revise"
    gh label create --force --repo "$repo" \
        state:plan-go --color 0e8a16 \
        --description "Plan accepted (terminal); safe to implement"
}

# Run across every repo in an org:
gh repo list "$ORG" --limit 200 --json nameWithOwner --jq '.[].nameWithOwner' |
    while read -r repo; do
        provision_state_labels "$repo"
    done
```

### Hardened `on: issues: opened` Workflow (Actions-Injection-Safe)

```yaml
name: state-needs-plan-on-open
on:
  issues:
    types: [opened]

permissions:
  contents: read
  issues: write   # least privilege — labels endpoint only

jobs:
  tag:
    runs-on: ubuntu-latest
    steps:
      - name: Tag new issue with state:needs-plan
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          # Only consume the server-controlled integer; never the title or body.
          ISSUE_NUM: ${{ github.event.issue.number }}
          REPO: ${{ github.repository }}
        run: |
          # Validate numeric — defend against any future schema drift.
          case "$ISSUE_NUM" in
              ''|*[!0-9]*) echo "ISSUE_NUM not numeric: $ISSUE_NUM" >&2; exit 1 ;;
          esac
          # Call the typed labels endpoint, not a shell-built command.
          gh api -X POST \
              "/repos/$REPO/issues/$ISSUE_NUM/labels" \
              -f "labels[]=state:needs-plan"
```

### Proposed Canonical Mutation and Exclusive Read Pattern

*Design-stage in v1.3.0 — not yet implemented or locally/CI verified.*

```python
from collections.abc import Iterable


def normalize_label_mutation(
    *,
    add: Iterable[str] = (),
    remove: Iterable[str] = (),
) -> tuple[list[str], list[str]]:
    """Return deterministic, de-duplicated, disjoint label mutations."""
    normalized_add = sorted(set(add))
    normalized_remove = sorted(set(remove))
    overlap = set(normalized_add).intersection(normalized_remove)
    if overlap:
        raise ValueError(
            f"labels cannot be both added and removed: {sorted(overlap)}"
        )
    return normalized_add, normalized_remove


def exclusive_state_flags(
    labels: Iterable[str],
    *,
    go: str,
    no_go: str,
) -> tuple[bool, bool]:
    """Return exclusive flags; contradictions and absence fail closed."""
    active = set(labels).intersection({go, no_go})
    return active == {go}, active == {no_go}
```

Apply normalization before `_skip(...)`, provisioning, command construction, or
logging. A combined edit uses the normalized collections in one command:

```python
add, remove = normalize_label_mutation(add=add, remove=remove)
if not add and not remove:
    return

cmd = ["issue", "edit", str(issue_number)]
for label in add:
    cmd.extend(["--add-label", label])
for label in remove:
    cmd.extend(["--remove-label", label])
gh_call(cmd)  # exactly one mutation
```

The state-transition owner, rather than the generic mutation helper, confirms
the expected family after the write:

```python
def mark_state(
    issue_number: int,
    *,
    expected: str,
    sibling: str,
    expected_flags: tuple[bool, bool],
) -> None:
    edit_labels(issue_number, add=[expected], remove=[sibling])
    if exclusive_state_flags(
        fresh_label_names(issue_number),
        go=STATE_IMPLEMENTATION_GO,
        no_go=STATE_IMPLEMENTATION_NO_GO,
    ) != expected_flags:
        raise RuntimeError(f"#{issue_number} {expected} read-back failed")
```

On mutation or readback failure, do not issue a compensating write. Retry
`mark_state(...)`; it replays the same canonical, idempotent swap and readback.

### Proposed Strict Payload and Batched-Fallback Pattern

*Design-stage in v1.4.0 — not yet implemented or locally/CI verified.*

```python
def label_names_from_payload(payload: object) -> set[str] | None:
    """Return unique label names, or None when any payload node is malformed."""
    if not isinstance(payload, dict):
        return None
    raw_labels = payload.get("labels")
    if not isinstance(raw_labels, list):
        return None

    names: set[str] = set()
    for raw_label in raw_labels:
        if not isinstance(raw_label, dict):
            return None
        name = raw_label.get("name")
        if not isinstance(name, str) or not name:
            return None
        names.add(name)
    return names
```

For batched GraphQL reads, preserve a per-issue unavailable sentinel instead of
defaulting uncertainty to an empty successful read:

```python
def fetch_label_batch(issue_numbers: list[int]) -> dict[int, list[str] | None]:
    results: dict[int, list[str] | None] = {
        number: None for number in issue_numbers
    }
    payload = fetch_graphql_payload()  # transport and JSON errors leave None
    repository = require_repository_object_without_graphql_errors(payload)

    for index, number in enumerate(issue_numbers):
        issue = repository.get(f"issue{index}")
        if not isinstance(issue, dict):
            continue
        labels = issue.get("labels")
        if not isinstance(labels, dict) or "nodes" not in labels:
            continue
        names = label_names_from_payload({"labels": labels["nodes"]})
        if names is not None:
            results[number] = sorted(names)  # [] means confirmed empty
    return results
```

The authorization consumer retries only unavailable entries and skips work only
after a successful exclusive read:

```python
labels = batch_cache.get(issue_number)
if labels is None:
    labels = strict_rest_fallback(issue_number)  # list[str] | None
    batch_cache[issue_number] = labels

if labels is not None and is_exclusive_plan_go(labels):
    skip_issue()
else:
    keep_issue_eligible()
```

Authorization matrix:

| Observation | Stored value | May authorize GO? | Next action |
|-------------|--------------|-------------------|-------------|
| Successful empty collection | `[]` | No | Continue normal non-GO flow |
| Successful sole GO label | `[GO]` | Yes | Apply the exclusive predicate |
| GO plus NO-GO | Both names | No | Fail closed as contradictory |
| Mixed valid/malformed nodes | `None` | No | Strict per-item fallback or error |
| Missing alias/collection | `None` | No | Strict per-item fallback or error |
| Nonzero CLI/GraphQL/JSON failure | `None` | No | Propagate, retry, or keep work eligible |

### Shared-Gate Read (Planner + Implementer Agree and Fail Closed)

```python
def get_plan_state(issue) -> str:
    """Read one canonical state; contradictions fail closed."""
    known = set(issue.labels).intersection(
        {"state:needs-plan", "state:plan-no-go", "state:plan-go"}
    )
    if len(known) > 1:
        raise ValueError(f"contradictory state labels: {sorted(known)}")
    if not known:
        return "needs-plan"  # migration default, not approval
    return {
        "state:needs-plan": "needs-plan",
        "state:plan-no-go": "no-go",
        "state:plan-go": "go",
    }[next(iter(known))]


# Planner uses this:
def should_plan(issue) -> bool:
    return get_plan_state(issue) in {"needs-plan", "no-go"}

# Implementer uses this — same source, opposite question:
def should_implement(issue) -> bool:
    return get_plan_state(issue) == "go"
```

### Re-Plan Transition (Executing the No-Go → Needs-Plan Edge — as an Atomic Swap)

*Design-stage, pending implementation in ProjectHephaestus issue #1857 — not yet CI-verified.*

Keep the transition as a **pure helper in the single state-vocabulary module**,
right next to the GO/NOGO `apply_plan_verdict` helper. Never inline the label-name
literals at the `on_enter` call site.

Two v1.2.0 requirements, both forced by a plan-review NOGO on the naive fix:

1. **SWAP, not bare ADD** — the helper adds the fresh label AND removes *both*
   siblings (mirrors `apply_plan_verdict`'s add-one/remove-two shape). A bare
   `add_labels([needs-plan])` leaves `state:plan-no-go` in place → two state
   labels at once (mutually-exclusive-invariant violation) and the gate is still
   stuck-False.
2. **ONE atomic write** — if the GitHub accessor exposes only separate
   `add_labels` / `remove_labels`, ADD a combined `edit_labels(add, remove)`
   primitive mapped onto a single `gh issue edit`, and route ALL `state:*`
   transitions through it. Never emit a swap as paired add+remove calls (that
   leaves a zero-or-two-label crash window).

```python
# ── state_vocabulary.py (the single home for label literals) ──
STATE_NEEDS_PLAN = "state:needs-plan"
STATE_PLAN_NO_GO = "state:plan-no-go"
STATE_PLAN_GO = "state:plan-go"


def replan_transition() -> tuple[list[str], list[str]]:
    """The documented `no-go → needs-plan` re-plan edge, as an atomic SWAP.

    Returns (labels_to_add, labels_to_remove). Removing BOTH siblings keeps
    the mutually-exclusive-label invariant intact — a bare add of
    STATE_NEEDS_PLAN would leave STATE_PLAN_NO_GO present (two labels at once)
    and keep the labels-first gate stuck-closed.

    Callers perform ONE atomic `gh issue edit --add-label … --remove-label …`.
    """
    return ([STATE_NEEDS_PLAN], [STATE_PLAN_NO_GO, STATE_PLAN_GO])


# ── The combined-edit primitive to ADD when the accessor lacks one ──
def edit_labels(issue, *, add: list[str], remove: list[str]) -> None:
    """Apply an atomic add+remove in a SINGLE `gh issue edit`.

    Route every state:* transition through this. Do NOT implement a swap as
    a separate add_labels(...) followed by remove_labels(...) — that two-call
    sequence leaves a window where the issue has zero or two state labels.
    """
    args = ["gh", "issue", "edit", str(issue.number), "--repo", issue.repo]
    for name in add:
        args += ["--add-label", name]
    for name in remove:
        args += ["--remove-label", name]
    run(args)  # one HTTP call
```

```python
# ── planning stage on_enter (the component that RE-PLANS executes the edge) ──
def on_enter(issue) -> None:
    labels = set(get_labels(issue))

    # 1. Execute the re-plan edge FIRST, guarded on the no-go label being present.
    #    Idempotent: steady-state re-entry (no no-go label) writes nothing.
    #    ONE atomic swap — add needs-plan, remove BOTH siblings.
    if STATE_PLAN_NO_GO in labels:
        add, remove = replan_transition()
        edit_labels(issue, add=add, remove=remove)  # single gh issue edit
        labels = (labels - set(remove)) | set(add)

    # 2. Only AFTER the label state is coherent, consider fast-forward.
    #    A stale plan comment + last-verdict-NOGO still reads as not-approved,
    #    so ordering the transition first prevents a premature fast-forward.
    if has_existing_plan(issue):   # labels-first: False while no-go was set
        fast_forward_to_verify(issue)
        return

    produce_plan(issue)
```

> **Plan-review discipline (meta-lesson, briefly):** the NOGO that forced this
> refinement was itself caused by submitting reviewer-self-critique bullets
> *instead of* a concrete plan (no named files/lines, no fenced code, two fix
> options left unresolved). Resolve to a SINGLE approach with cited evidence
> and concrete `file:line` + code + named tests before submitting. (This is a
> general planning-discipline point already covered by the `*-before-planning`
> skills — noted here only because it shaped this specific fix.)

**Deadlock check (copy-paste audit):** for every edge in your state diagram, confirm a
component executes it — not just that the diagram draws it.

```bash
# List the transition edges you believe exist, then grep for the writer of each.
# Any edge with no add/remove-label writer is a stuck-closed candidate.
grep -rn "add.label state:needs-plan\|--add-label state:needs-plan\|STATE_NEEDS_PLAN" \
    hephaestus/ | grep -i "on_enter\|planning\|replan"
```

### Why Labels Beat Comment-Text (Comparison Table)

| Property | Free-Text Comment Gate | `state:*` Label Gate |
|----------|------------------------|----------------------|
| Parse failure mode | Silent default to NOGO → permanent block | Structured: either present or absent |
| Query cost across N issues | N comment fetches + N regex runs per loop | One `--label` filter on the list endpoint |
| Contract drift survival | Format change invalidates every prior approval | Label name change is a one-time rename |
| Atomicity of transition | Two writes (delete prior comment + post new) | One `gh issue edit` with add+remove |
| Determinism | Depends on caller/payload ordering | Sorted, de-duplicated mutation sets |
| Contradictory state | Parser or first match may authorize progress | Exact singleton read; contradiction fails closed |
| Unknown write outcome | Often guessed or compensated | Propagate; retry identical swap and fresh readback |
| Race during first write | First reviewer hits 404 if label missing | Provisioner runs first, idempotent |
| Observability | grep through 100k log lines for the verdict | `gh issue list --label state:plan-go` |
| Self-heal of existing issues | Manual relabeling of every legacy issue | One-time backfill on startup |
| GitHub Actions injection surface | Tempting to consume `event.title` | Labels are server-side; no shell interpolation |

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| ProjectHephaestus | PR #707 — `architecture-github-labels-as-state-vocabulary` end-to-end pattern | 911 automation tests pass locally; ruff + mypy clean; auto-merge SQUASH armed. CI in flight at time of writing — flip `verification` to `verified-ci` once green. [PR link](https://github.com/HomericIntelligence/ProjectHephaestus/pull/707) |
| ProjectHephaestus | Live observation that motivated the pattern | 320 "no parseable Verdict" WARNINGs across an org-wide automation run; multiple re-plans of already-approved issues because the latest comment had drifted from the regex contract |
| ProjectHephaestus | Issue #1857 — re-plan cycle deadlock (Failed Attempt #9) — **design-stage, UNVERIFIED for this specific learning** | Planning→plan_review re-plan cycle could never converge: `plan_review` applies `state:plan-no-go` and FAIL_BACKs to `planning`; `planning` re-plans but the labels-first VERIFY gate (`has_existing_plan` → `is_plan_review_go`) stays False while `state:plan-no-go` is set, so VERIFY RETRYs until the `plan` budget (2) drains → FINISH_FAIL; the intended `plan_cycles=2` second cycle is unreachable. Root cause: the documented `no-go → needs-plan` re-plan edge is never executed by any component. Fix designed (pure `replan_transition()` helper + atomic add/remove in planning `on_enter`, guarded for idempotency) and unit-test-specified, but **NOT yet implemented or CI-verified in this session.** |
| ProjectHephaestus | Issue #1857 — atomic-swap refinement (Failed Attempt #10) — **design-stage, UNVERIFIED; a plan-review NOGO forced this** | A plan reviewer NOGO'd two naive versions of the Attempt-#9 fix: **(a)** a bare `add_labels([needs-plan])` that left `state:plan-no-go` present (two labels at once → mutually-exclusive-invariant violation, gate still stuck-False); **(b)** the swap emitted as two separate mutator calls because the GitHub accessor exposed only `add_labels` / `remove_labels`, leaving a zero-or-two-label crash window. Refined fix: `replan_transition() -> (add=[needs-plan], remove=[plan-no-go, plan-go])` (SWAP, remove BOTH siblings) applied via a NEW combined `edit_labels(add, remove)` primitive that maps onto a SINGLE `gh issue edit`, with all `state:*` transitions routed through it. Designed + unit-test-specified, **NOT implemented or CI-verified.** |
| ProjectHephaestus | Deterministic label mutation and exclusive implementation-state plan — **design-stage, UNVERIFIED** | Proposed one normalization authority for sorted, de-duplicated, disjoint add/remove sets; set-based exact-singleton plan and implementation readers; one-command GO/NO-GO swaps with explicitly owned fresh readback; and retry-without-compensation recovery. Acceptance tests were specified for canonical argv/logs, pre-I/O overlap rejection, contradictory reads, one-edit transitions, and failure reconciliation, but no implementation or tests were executed in this learning session. |
| ProjectHephaestus | Strict label-read and batched-fallback revision plan — **design-stage, UNVERIFIED** | Proposed whole-payload validation for ambient, repo-scoped, PR, and compatibility readers; `None` versus `[]` GraphQL results; strict per-issue REST fallback; symmetric exclusive plan/implementation predicates; and one-edit/one-readback regressions for every transition owner. The implementation and acceptance commands were fully specified, but no code or tests were executed in this learning session. |
