---
name: architecture-claude-md-agents-md-single-source-ecosystem-migration
description: "How to consolidate a repo's CLAUDE.md into AGENTS.md so AGENTS.md becomes the single source of truth for agent/system-prompt guidance, across a whole multi-repo ecosystem — one PR per repo. Use when: (1) migrating agent guidance so AGENTS.md is authoritative and CLAUDE.md is reduced to a short pointer stub; (2) sweeping an org where MOST repos may already be converted — API-probe main before swarming; (3) handling the inverted-pointer case where AGENTS.md already points BACK at CLAUDE.md and cross-references must be flipped and rewritten; (4) running a docs-only, markdownlint-gated multi-repo PR sweep with squash/merge-queue auto-merge."
category: architecture
date: 2026-07-19
version: "1.0.0"
user-invocable: false
verification: verified-local
tags:
  - claude-md
  - agents-md
  - single-source-of-truth
  - agent-contract
  - multi-repo-sweep
  - ecosystem-migration
  - pointer-stub
  - inverted-pointer
  - cross-reference-rewrite
  - api-probe-before-swarm
  - docs-only
  - markdownlint
  - squash-merge-queue
---

# Consolidating CLAUDE.md into AGENTS.md as the Single Source of Truth Across an Ecosystem

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-07-19 |
| **Objective** | Across every non-fork HomericIntelligence repo, merge `CLAUDE.md` into `AGENTS.md` and reduce `CLAUDE.md` to a short pointer stub, so `AGENTS.md` is the single source of truth for agent/system-prompt guidance. One PR per repo. |
| **Outcome** | Success (docs-only). Of 17 org repos: 1 fork skipped, 12 already converted on main, only 4 needed a PR. 4 PRs opened, all OPEN + MERGEABLE + auto-merge armed (squash), no failing checks — CI QUEUED not yet green at capture. |
| **Verification** | verified-local — the 4 conversion PRs were opened and are MERGEABLE with no failing checks, but their CI was still QUEUED (not observed green) at capture time. Not verified-ci. |
| **Category** | architecture |

The durable win is not "edit a markdown file." It is the discovery method that
avoids wasted work (**probe main via the GitHub API before swarming — most of the
ecosystem was already done**) plus the technical trap that makes the edit non-trivial
(**the inverted-pointer case**, where `AGENTS.md` already points back at `CLAUDE.md`).

## When to Use

- Migrating a repo (or a whole org) so `AGENTS.md` is the authoritative agent/system-prompt
  contract and `CLAUDE.md` is reduced to a short pointer stub that defers to it.
- Sweeping a multi-repo ecosystem where MANY repos may ALREADY be migrated — you want to
  find the 4 that need work without fanning out 16 agents (see the "check upstream main before
  swarming" ecosystem lesson).
- Handling the **inverted-pointer** starting state, where `AGENTS.md` already exists and points
  BACK at `CLAUDE.md` as the source of truth — the opposite of the target direction.
- Running a docs-only, markdownlint-gated PR sweep with squash-only / merge-queue-governed
  auto-merge.
- Complements `[[architecture-agents-md-contract-from-codebase]]` (authoring a NEW `AGENTS.md`
  from codebase source): that skill is "write it from scratch"; this one is "consolidate/migrate
  an existing pair of files."

## Verified Workflow

### Quick Reference

```bash
# 1) Enumerate org repos + fork status (skip forks; they are out of ecosystem scope)
gh repo list HomericIntelligence --limit 100 \
  --json name,isFork,isArchived,defaultBranchRef

# 2) For EACH non-fork repo, probe both files' sizes WITHOUT cloning.
#    A ~122-byte CLAUDE.md is the tell-tale sign the repo is ALREADY converted
#    (it is the pointer stub). AGENTS.md 404 => file absent.
gh api "repos/HomericIntelligence/<repo>/contents/CLAUDE.md" --jq '.size'
gh api "repos/HomericIntelligence/<repo>/contents/AGENTS.md" --jq '.size'

# 3) Confirm a suspected stub by base64-decoding its content
gh api "repos/HomericIntelligence/<repo>/contents/CLAUDE.md" --jq '.content' \
  | base64 -d

# 4) For each repo that NEEDS work: fresh clone (NEVER the shared submodule checkout),
#    do the merge, then gate on markdownlint only (docs-only change).
git clone "https://github.com/HomericIntelligence/<repo>" "/tmp/convert-<repo>"

# 5) Docs-only gate = markdownlint on just the two touched files
npx --yes markdownlint-cli2 --config .markdownlint.yaml CLAUDE.md AGENTS.md

# 6) After merge: grep AGENTS.md for residual CLAUDE.md references — must be ZERO
grep -n "CLAUDE.md" AGENTS.md   # expect no output

# 7) Commit signed + sign-off, arm squash auto-merge (repos are squash/merge-queue)
git commit -S -s -m "docs: make AGENTS.md the single source of truth"
gh pr merge <n> --auto --squash   # prints merge-queue note, but auto-merge DOES register
```

### The canonical pointer stub (copy EXACTLY — this is what the 12 done repos have)

The stub that reduces `CLAUDE.md` to a pointer is, verbatim:

```markdown
# Claude Code guidance

Follow [`AGENTS.md`](AGENTS.md). It is the sole authoritative agent contract for this repository.
```

### Detailed Steps

1. **Probe before swarming.** Enumerate the org, drop forks and archived repos, then API-probe
   both `CLAUDE.md` and `AGENTS.md` sizes for every remaining repo. A ~122-byte `CLAUDE.md`
   means the repo is already the pointer stub — skip it. Blindly fanning out one agent per repo
   wastes an agent on every already-done repo.
2. **Classify each repo that needs work into one of four starting states** (below) — the merge
   is NOT uniform "merge + stub"; the inverted cases require flipping a pointer and rewriting
   cross-references.
3. **Merge policy: UNION of both files.** On a genuine CONFLICT, `CLAUDE.md` wording WINS
   (explicit user choice). Deduplicate genuinely overlapping sections. The final `AGENTS.md`
   must read as ONE coherent standalone doc — not two files stapled together.
4. **Flip and rewrite cross-references.** If `AGENTS.md` pointed at `CLAUDE.md`, invert the
   pointer, then rewrite EVERY reference that resolved to `CLAUDE.md` (anchors like
   `CLAUDE.md#skill-catalog`, prose like "see CLAUDE.md for commit policy") to resolve to the
   now-in-document headings. `grep -n "CLAUDE.md" AGENTS.md` must return ZERO.
5. **Reduce `CLAUDE.md` to the canonical stub** (verbatim block above).
6. **Gate = markdownlint only.** Docs-only change: no build / pixi / pytest. Run
   `markdownlint-cli2` against the repo's own `.markdownlint.yaml` on just the two files.
7. **One sub-agent per repo, each in a FRESH `/tmp/convert-<repo>` clone.** NEVER edit the
   shared submodule checkout — its branch state / worktrees are shared and get clobbered.
8. **Commit GPG-signed + sign-off (`git commit -S -s`); arm squash auto-merge.** HI repos are
   squash-only / merge-queue-governed, so `gh` prints "merge strategy is set by the merge
   queue" but auto-merge DOES register (`autoMergeRequest.mergeMethod: SQUASH`).

### The four starting states (classify before editing)

1. **AGENTS.md defers to CLAUDE.md (inverted)** — e.g. AchaeanFleet (~8KB CLAUDE, 814B AGENTS).
   Flip the pointer; move the body into `AGENTS.md`; rewrite every back-reference.
2. **Both files full and cross-referencing** — e.g. Hephaestus (~21KB CLAUDE, ~12KB AGENTS).
   The union must PRESERVE BOTH bodies (rules + agent-topology map) and fix cross-refs.
3. **Both files full and independent** — e.g. Proteus (~8.9KB CLAUDE, ~2.7KB AGENTS).
   Union + dedup the one genuinely overlapping section (a cross-repo dispatch flow in both).
4. **No AGENTS.md at all** — e.g. Mnemosyne (~10KB CLAUDE, AGENTS 404). Just create
   `AGENTS.md` = `CLAUDE.md` content, adapting only the top heading.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| ------- | ------- | ------- | ------- |
| Assume all 16 repos need work | Plan to fan out one agent per non-fork repo | 12 of 16 were ALREADY the pointer stub on main; 12 agents would be wasted | API-probe main first; a ~122-byte CLAUDE.md is the "already converted" tell. Matches the standing "check upstream main before swarming" ecosystem lesson |
| Assume CLAUDE.md is always the source and AGENTS.md is empty/absent | Treat conversion as a uniform "merge + stub" | AchaeanFleet and Hephaestus had AGENTS.md pointing BACK at CLAUDE.md (inverted) | Read BOTH files; flip the pointer; rewrite every cross-ref that resolved to CLAUDE.md; then `grep CLAUDE.md AGENTS.md` must be empty |
| Treat it as a build/swarm task with heavy agents | Throttle like a pixi/cmake fan-out | It is docs-only; only markdownlint gates. Over-throttling wastes time; running pixi/cmake is pointless | Docs-only: skip build/pixi/pytest; gate is markdownlint on the two touched files |
| Edit the shared submodule / clone checkout | Reuse an existing shared checkout to make the edit | Shared branch state / worktrees get clobbered across agents | Fresh `/tmp/convert-<repo>` clone per repo; never the shared checkout |
| Claim "done" when auto-merge is armed | Report success after `gh pr merge --auto --squash` registered | PRs were still QUEUED, not merged/green — arming auto-merge is not merging | Report honest BLOCKED/queued state; verified-local, not verified-ci, until the gate is observed green |
| Rely on full pre-commit to bootstrap the gate (Hephaestus) | Run the repo's whole pre-commit suite | Hephaestus host had Python 3.9; yamllint needs 3.10+, so pre-commit could not bootstrap | Run `markdownlint-cli2` directly against the repo's `.markdownlint.yaml` on just the two files as the real gate |

## Results & Parameters

**Scope finding (the big lesson).** Of 17 org repos: 1 fork (`modular-community`, skipped).
Of the 16 non-fork repos, **12 already had the CLAUDE.md pointer stub on main** — Agamemnon,
Argus, Athena, Charybdis, Hermes, Keystone, Myrmidons, Nestor, Odysseus, Odyssey, Scylla,
Telemachy. Only **4 needed a PR**: AchaeanFleet, Hephaestus, Proteus, Mnemosyne.

**Merge policy.** UNION of both files; on genuine conflict, `CLAUDE.md` wording WINS
(user's explicit choice). Final `AGENTS.md` reads as one coherent standalone doc, deduplicated.

**PRs opened (honest, as of capture — all OPEN + MERGEABLE + auto-merge armed (squash), NO
failing checks, all CI still QUEUED, i.e. NOT green):**

| Repo | PR | Notes |
| ------- | ------- | ------- |
| AchaeanFleet | #729 | Inverted-pointer starting state |
| Hephaestus | #2334 | Watch the pr-policy `Closes #<issue>` caveat (below) |
| Proteus | #225 | Union + dedup of one overlapping section |
| Mnemosyne | #3192 | No prior AGENTS.md — created it |

**Repo-specific CI trap — Hephaestus `pr-policy` gate.** It requires a literal
`Closes #<issue>` line in the PR body. A docs PR with no associated issue may FAIL that gate
even though the content is fine — flag it; a maintainer must attach an issue number or grant an
exception before auto-merge can complete. (Also: the Hephaestus host had Python 3.9, so full
pre-commit could not bootstrap yamllint (needs 3.10+) — run `markdownlint-cli2` directly against
that repo's `.markdownlint.yaml` on just the two files as the real gate.)

**Auto-merge behavior on HI repos.** They are squash-only / merge-queue-governed. `gh pr merge
--auto --squash` prints "merge strategy is set by the merge queue", but auto-merge DOES register
— verify with:

```bash
gh pr view <n> --repo HomericIntelligence/<repo> \
  --json autoMergeRequest --jq '.autoMergeRequest.mergeMethod'   # => SQUASH
```

**Cross-references (related skills):**

- `[[architecture-agents-md-contract-from-codebase]]` — the complementary "write a NEW
  AGENTS.md from codebase source" skill (vs. this "consolidate/migrate an existing pair" skill).
- `[[automation-multi-repo-pr-sweep-rebase-resolve]]` — the one-agent-per-repo / fresh-clone +
  squash / merge-queue auto-merge sweep pattern reused here.
- The standing "check upstream main before swarming — HI mains are often already migrated"
  ecosystem lesson, which this session confirmed again (12 of 16 already done).
