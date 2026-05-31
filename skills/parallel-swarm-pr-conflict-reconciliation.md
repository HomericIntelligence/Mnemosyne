---
name: parallel-swarm-pr-conflict-reconciliation
description: "Detect and reconcile overlapping PRs from a parallel issue-implementation swarm, AND turn a coupled repo into a pure-X library via the verified decouple→port→delete extraction playbook (not a deletion-only PR). Use when: (1) you launched one-PR-per-issue across a backlog and multiple PRs auto-merge-race on the same paths so only one squash-merges cleanly, (2) a CONFLICTING PR must be rebased onto an already-merged sibling rather than merging main into it, (3) you are extracting a coupled subsystem out of a repo (e.g. ProjectKeystone → pure C++20 transport) and a deletion-only PR STALLS because the retained core still references the doomed module or the destination port is incomplete — decouple FIRST behind a tiny interface, port verify-or-port to the destination, then delete in build-refs→sources→dead-deps order, (4) two sibling PRs both edit a shared lockfile/script so the second goes CONFLICTING and must be rebased (git auto-drops already-upstream commits; re-sign on rebase), (5) several PRs implement the same end-state and you must pick a canonical superset to land and close the subsumed ones, (6) Edit-tool exact-match fails on conflict markers in files with em-dashes or alignment whitespace, or git restore/checkout to discard stale worktree mods is Safety-Net-BLOCKED."
category: architecture
date: 2026-05-31
version: "2.0.0"
user-invocable: false
verification: verified-local
history: parallel-swarm-pr-conflict-reconciliation.history
tags: [parallel-swarm, pr-conflict, rebase, file-overlap, extraction, decouple-before-delete, pure-library-refactor, superset-pr, force-with-lease, signed-commits, nats]
---

# Reconciling Overlapping PRs + Extraction (Decouple → Port → Delete)

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-05-31 |
| **Objective** | Two related cross-repo PR patterns: (1) reconcile CONFLICTING PRs from a parallel one-PR-per-issue swarm, and (2) turn a coupled repo into a pure-X library via a verified **decouple → port → delete** extraction playbook — NOT a deletion-only PR (which stalls because the retained core still references the doomed module) |
| **Outcome** | Successful — extraction executed end-to-end this session: **9 PRs merged across 2 repos**, all signed + squash-auto-merged, ADRs marked Implemented (ProjectKeystone became a pure C++20 transport library per ADR-015/016) |
| **Verification** | verified-local (executed end-to-end this session, may be read as verified-ci-observed: every PR's full CI matrix went green and squash-auto-merged). Keystone #577/#578/#579/#580/#581 and Agamemnon #419/#420/#421 all merged + signature-verified. The original Odysseus #43 reconciliation is also verified-local |

## When to Use

- You launched a swarm of one-PR-per-issue across an issue backlog and several PRs touch the same paths — only the first auto-merges, the rest stall `CONFLICTING`
- A CONFLICTING PR needs reconciling against a sibling that already landed on `main`
- **You are extracting a coupled subsystem to make a repo a "pure X library"** (e.g. ProjectKeystone → pure C++20 transport, removing the agent layer + Python orchestration per ADR-015/016) and a pure-**deletion** PR keeps failing or deferring — because the retained core still references the doomed module, or the destination port is incomplete. Use the decouple → port → delete playbook below.
- Two sibling PRs both edit a shared lockfile/script: the first squash-merges, the second goes CONFLICTING and must be rebased onto main (git auto-drops the already-upstream commit; you must re-sign)
- Multiple PRs implement the same end-state and you must consolidate to one canonical PR
- The Edit tool cannot exact-match conflict markers because the file has em-dashes or alignment whitespace, or `git restore`/`checkout` to discard stale worktree edits is Safety-Net-BLOCKED

## Verified Workflow

### Quick Reference

```bash
# ════════ A. EXTRACTION: decouple → port → delete (a repo → "pure X library") ════════

# A1. DECOUPLE FIRST (own PR — MUST merge before any deletion).
#     Find the MINIMAL coupling: the core often depends on the doomed type by ONE method.
#     Introduce a tiny interface the core owns; core stores/registers the INTERFACE,
#     the concrete (doomed) type inherits it. Then prove the core no longer names the module:
grep -rn "doomed_module/" core_paths/        # MUST be 0 after the decouple
#   e.g. core::IMessageSink{ virtual void receiveMessage(const Msg&)=0; };
#        core registers IMessageSink*, agents::AgentCore : public core::IMessageSink
#   Add a test using a NON-module stub of the interface to PROVE decoupling.

# A2. PORT to the destination repo (own PR; verify-or-port).
#     For EACH capability: does the destination repo ALREADY provide an equivalent? (often yes — don't dup.)
#     Port only what's genuinely missing; ported code must build STANDALONE — no new dep back on the source:
#       add a dependency-free in-process router + a dep-free logger rather than importing the source's transport lib.
#     Parity-audit ported code vs the originals BEFORE any deletion.

# A3. DELETE from source (only after A1 + A2 are MERGED). Ordering:
#     build-system refs (CMake targets / test registrations / install lists)  ← FIRST
#       → source files
#       → now-dead deps (proto / codegen / 3rd-party)                          ← LAST
grep -rn "RemovedSymbol\|removed_target" .   # MUST be 0
#     Mark ADRs Implemented in BOTH the header status line AND the Document Metadata block.

# A4. RE-AUDIT for leftovers — a first pass can MISS a sibling orchestration layer
#     (e.g. an src/network/ gRPC coordinator). Such leftovers are often DEAD/test-only + already broken
#     (ctor header/impl mismatch, absent from CMake) → safe to delete outright once the destination covers them.

# ════════ B. RECONCILE a CONFLICTING swarm PR (rebase, never merge main in) ════════
git fetch origin
REMOTE_SHA=$(git rev-parse origin/<branch>)          # verify nobody pushed since you started
git switch -c <branch>-rebase origin/<branch>
git rebase origin/main                               # resolve toward what already landed on main
# git auto-DROPS commits whose patch is already upstream (sibling lockfile/script edits) — expected.
# Re-SIGN every replayed commit (rebase strips signatures):
git rebase --exec "git commit --amend --no-edit -S --no-verify" <base>
#   %G? may show "U" locally; REST verification.verified is authoritative — trust the API, not %G?.

# If Edit can't exact-match conflict markers (em-dashes / alignment whitespace), regex hunk-replace:
python3 - <<'PY'
import re
p = "configs/nats/server.conf"
s = open(p).read()
s = re.sub(r'<<<<<<< HEAD\n(.*?)\n=======\n.*?\n>>>>>>> [^\n]+\n',
           lambda m: m.group(1) + "\n", s, flags=re.DOTALL)   # keep HEAD (what landed on main)
open(p,"w").write(s)
PY
grep -c '^<<<\|^>>>\|^===' configs/nats/server.conf  # MUST be 0
nats-server -t -c configs/nats/server.conf           # only "cert file not found" == valid syntax

export GPG_TTY=$(tty)
git push --force-with-lease origin HEAD:<branch>     # re-confirm REMOTE_SHA unchanged first
gh pr merge <N> --auto --squash                      # --squash if rebase-merge disabled
```

### Detailed Steps

#### Workflow A — Extraction: decouple → port → delete (make a repo a "pure X library")

The headline failure mode: a pure-**deletion** PR ("delete module X, it lives in repo B") STALLS, because the retained core still names X and the destination port is incomplete. The verified sequence that actually lands it — executed this session across ProjectKeystone (→ pure C++20 transport) and ProjectAgamemnon, all signed + squash-auto-merged, ADRs marked Implemented:

1. **Decouple FIRST — its own PR, MUST merge before any deletion.** Find the *minimal* coupling: the retained core usually depends on the doomed type by exactly ONE method. Introduce a tiny interface the core owns and make the core register/store the **interface**, not the concrete type; make the doomed concrete type inherit it.
   - e.g. `core::IMessageSink { virtual void receiveMessage(const Msg&) = 0; };` — `MessageBus`/core registers an `IMessageSink*`; `agents::AgentCore : public core::IMessageSink`.
   - Prove it: `grep -rn "doomed_module/" <core paths>` must hit **0**.
   - Add a test that drives the core through a **non-module stub** of the interface — this proves the core builds and works with the module gone. **This is the step every prior deletion-only PR skipped** → why those branches couldn't build (see the `git-rebase-over-deletion` symptom).

2. **Port to the destination repo — its own PR; verify-or-port.** For each capability the source provided, FIRST check whether the destination repo *already* has an equivalent — it frequently does; do not duplicate it. Port only what is genuinely missing, and the ported code must build **standalone** with no new dependency back on the source repo. Concretely: add a dependency-free in-process router and a dep-free logger rather than importing the source's transport library. **Parity-audit** the ported code against the originals *before* deleting anything.

3. **Delete from source — only after steps 1 and 2 have MERGED.** Deletion ordering matters: remove **build-system refs first** (CMake targets, test registrations, install lists), **then source files**, **then the now-dead deps last** (proto/codegen/3rd-party that only the deleted code used). `grep`-zero the removed symbols. Mark the governing ADRs **Implemented** in BOTH places: the header status line *and* the Document Metadata block (see the `adr-status-deferred-update` pattern — it's easy to update one and forget the other).

4. **Re-audit for leftovers.** A first deletion pass can MISS a *sibling* layer that is also orchestration — e.g. an `src/network/` gRPC coordinator left behind next to the agent layer you removed. These leftovers are commonly DEAD / test-only and already broken (constructor header/impl mismatch, not registered in CMake), so once you confirm the destination repo covers their function they are safe to delete outright.

#### Workflow B — Reconcile overlapping swarm PRs

5. **Detect overlap BEFORE and AFTER launching.** Group planned issues by the files their plans name; flag clusters touching the same paths. At scale expect clusters (multiple issues removing the same module, or one issue adding what another deletes). Serialize or consolidate a cluster instead of letting all its PRs auto-merge-race.

6. **Reconcile a CONFLICTING PR by rebasing its branch onto current `origin/main`** — never merge `main` into the branch (keep history linear). Resolve in favor of what already landed on `main`. Before force-pushing, re-verify nobody pushed since you started by comparing the remote branch SHA to the head you began from.
   - Concrete example (Odysseus PR#43 vs already-merged PR#32 on `configs/nats/server.conf` + `leaf.conf`): #32 had REAL active TLS; #43 had a REDUNDANT commented-out TLS scaffold. Resolution = keep main's real TLS (HEAD), drop #43's scaffold, but PRESERVE #43's unique non-conflicting additions. The PR went DIRTY/CONFLICTING → MERGEABLE.

7. **Two sibling PRs editing a shared lockfile/script.** When PR-1 squash-merges, PR-2 goes CONFLICTING on the shared file. Rebase the loser onto `main`; `git rebase` **auto-drops** any commit whose patch is already upstream (PR-1's identical lockfile edit) — that's expected, not data loss. Because rebase strips signatures, **re-sign** the replayed commits: `git rebase --exec "git commit --amend --no-edit -S --no-verify" <base>`. Locally `git log --format=%G?` may show `U` (unverified) even after re-signing; the GitHub REST `commit.verification.verified` field is **authoritative** — trust the API over `%G?`.

8. **When the Edit tool can't exact-match a conflict marker** (em-dashes / alignment whitespace defeat literal matching), resolve with a Python regex replace on the `<<<<<<< HEAD ... ======= ... >>>>>>>` hunks instead. Then `grep -c` the markers to confirm 0.

9. **Validate the result parses** before committing. For NATS configs: `nats-server -t -c <file>` — only a "cert file not found" error means the syntax is valid (it parsed far enough to look for the cert).

10. **Sign, force-push-with-lease, re-arm auto-merge.** `export GPG_TTY=$(tty)`, commit/amend `-S`, `git push --force-with-lease` (after re-confirming the remote SHA), then re-arm `gh pr merge <N> --auto` with the repo's allowed method (`--squash` if rebase-merge is disabled).

11. **Discarding stale worktree edits is Safety-Net-BLOCKED.** `git restore` / `git checkout -- <path>` (and `git worktree remove --force`) are blocked by the safety net while work is uncommitted. Do NOT `--force`. Instead print the exact discard command for the user to run, or commit/stash first. To clean a reconciliation worktree: commit+push everything, then plain (non-force) `git worktree remove <path>`, then `git worktree prune`.

### Consolidating PRs that implement the same end-state

Pick the canonical SUPERSET PR to land. Close the subsumed ones with explanatory comments. Salvage any UNIQUE bits into a follow-up PR. CLOSE PRs that CONTRADICT the agreed end-state (e.g. ones re-adding what should be removed) — only file follow-ups if real value would otherwise be lost.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Pure-deletion without decoupling | Opened an extraction PR that just deleted module X from the source repo | Retained core still held `shared_ptr<agents::AgentCore>` / named the doomed module via `i_agent_registry.hpp`; branch didn't build, "Phase 4" perpetually deferred | DECOUPLE FIRST behind a tiny core-owned interface (own PR, merge before any deletion), then verify-or-port to the destination, THEN delete. Extraction ≠ deletion |
| Slim the transport struct before deleting its consumers | Tried to remove a transport struct's orchestration fields while the agent/network layer still consumed them | Consumers were woven through 49 refs in ONE file — the struct couldn't be slimmed while they referenced it | STOP and reorder: slim the transport struct AFTER the consumer-layer deletion, not before |
| Re-port what the destination already had | Started porting every source capability into the destination repo | Destination repo already provided an equivalent for several — duplicated functionality | For each capability, verify-or-port: check if the destination ALREADY has it before porting; port only what's genuinely missing, build it standalone (dep-free router/logger, no dep back on source) |
| Two sibling PRs both edit the shared lockfile/script | Let both keep `--auto`; first squash-merged, second went CONFLICTING | Both touched the same shared lockfile/script path | Rebase the loser onto main; `git rebase` auto-drops the commit whose patch is already upstream; re-sign with `git rebase --exec "git commit --amend --no-edit -S --no-verify" <base>`. `%G?` shows `U` locally but REST `verification.verified` is authoritative |
| `git restore`/`checkout`/`worktree remove --force` to discard stale worktree mods | Tried to discard stale worktree edits (and force-remove the worktree) mid-work | Blocked by the safety net while work was uncommitted | NEVER `--force`; print the discard command for the user, or commit/stash first, then plain (non-force) `git worktree remove` + `prune` |
| Race all overlapping auto-merge PRs | Let every swarm PR keep `--auto` and merge whenever CI passed | Only the first PR in a file-overlap cluster merged; the rest went CONFLICTING and stalled | Detect file-overlap clusters before/after launch and serialize or consolidate them — don't let a cluster race |
| Exact-string Edit on conflict markers | Used the Edit tool to replace `<<<<<<< HEAD ... >>>>>>>` hunks in `configs/nats/*.conf` | Files contained em-dashes and alignment whitespace, so literal matching never matched | Use a Python regex hunk-replace on the conflict markers instead of exact-string Edit |
| Merge main into the conflicting branch | Considered `git merge origin/main` to clear the conflict | Pollutes history with a merge commit; squash-merge then bundles unrelated diff | Rebase the branch onto `origin/main` (linear history), resolve toward what landed, force-push-with-lease |

## Results & Parameters

### Session outcome (2026-05-31) — Keystone pure-transport extraction

| Repo / PR | What it did | Step in playbook |
|-----------|-------------|------------------|
| Keystone #577 | Decouple core/transport from agents via `core::IMessageSink`; core registers the interface, `agents::AgentCore` inherits it; non-module stub test proves decoupling | A1 — decouple FIRST |
| Keystone #578 | Verify-or-port missing capabilities into destination; standalone dep-free in-process router + dep-free logger (no dep back on source transport) | A2 — port |
| Keystone #579 | Delete agent layer: CMake targets/test-regs/install lists first → sources → dead deps last; grep-zero removed symbols | A3 — delete |
| Keystone #580 | Re-audit leftovers: removed the dead/test-only `src/network/` gRPC coordinator (ctor header/impl mismatch, absent from CMake) | A4 — re-audit |
| Keystone #581 | Mark ADR-015/016 Implemented in header status + Document Metadata; final pure-C++20-transport cleanup | A3 — ADR status |
| Agamemnon #419/#420/#421 | Destination-side: accept ported orchestration capability; parity-audit; squash-auto-merged | A2 — destination repo |
| Odysseus #43 (v1.0.0, vs merged #32) | NATS config conflict: keep main's real TLS, drop redundant scaffold, preserve unique adds | B — reconcile |

All 9 PRs signed (`-S`) and squash-auto-merged; full CI matrices green.

### Key parameters

```yaml
# Extraction (Workflow A)
extraction_order_of_PRs: decouple (own PR, merge FIRST) -> port (own PR) -> delete (own PR) -> re-audit
decouple_proof: grep -rn "doomed_module/" <core paths>  == 0 ; non-module stub test of the new interface
minimal_coupling: core usually depends on the doomed type by ONE method -> tiny core-owned interface
port_rule: verify-or-port (don't dup what destination already has); ported code builds STANDALONE, no dep back on source
deletion_order_within_delete_PR: build-system refs (CMake/test-regs/install) -> source files -> dead deps (proto/codegen/3rd-party)
adr_status: mark Implemented in BOTH header status line AND Document Metadata block
re_audit: a first pass can miss a sibling orchestration layer (e.g. src/network/ gRPC) — often dead/test-only + broken -> delete outright

# Reconciliation (Workflow B)
reconcile_strategy: rebase onto origin/main   # never merge main into the branch
resolution_bias: keep what already landed on main (HEAD side); preserve PR's unique non-conflicting adds
rebase_drops_upstream_commit: expected for sibling lockfile/script edits (already-upstream patch) — not data loss
re_sign_on_rebase: git rebase --exec "git commit --amend --no-edit -S --no-verify" <base>
signature_truth: REST commit.verification.verified is authoritative; local %G? may show U
push_flag: --force-with-lease                  # re-verify remote SHA == PR head you started from
conflict_marker_resolution: python regex hunk-replace when Edit can't exact-match (em-dashes/whitespace)
nats_validate: nats-server -t -c <file>        # only "cert file not found" == valid syntax
discard_stale_worktree_edits: BLOCKED by safety net — never --force; print command for user or commit/stash first
sign: git commit -S  (export GPG_TTY=$(tty))
auto_merge_method: --squash if rebase-merge disabled in repo settings
worktree_cleanup: commit+push first, then plain (non-force) git worktree remove, then prune
```

### Overlap-detection heuristic

```
For each planned/open swarm PR:
  record the set of file paths its plan/PR touches.
Group PRs that share ≥1 path into a cluster.
For each cluster of size > 1:
  - one PR will squash-merge cleanly; the rest will go CONFLICTING.
  - decide: serialize (rebase each onto the prior winner) OR
            consolidate into a canonical superset PR and close the others.
Watch specifically for:
  - multiple issues removing the SAME module
  - one issue ADDING what another DELETES (contradictory end-states → close the contradicting one)
  - two siblings editing the SAME shared lockfile/script → second goes CONFLICTING, rebase + re-sign
```

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| ProjectKeystone | pure-transport refactor (session 2026-05-31) | Decouple→port→delete extraction to pure C++20 transport per ADR-015/016. PRs #577 (decouple), #578 (port), #579 (delete), #580 (re-audit leftover gRPC coordinator), #581 (ADR Implemented) — all signed + squash-auto-merged, CI green |
| ProjectAgamemnon | extraction destination (session 2026-05-31) | Accepted ported orchestration capability; PRs #419/#420/#421 signed + squash-auto-merged |
| Odysseus | Issue swarm reconciliation (2026-05-29) | PR#43 rebased onto already-merged PR#32; NATS config conflict resolved keeping real TLS, signed, force-pushed, auto-merge re-armed |
