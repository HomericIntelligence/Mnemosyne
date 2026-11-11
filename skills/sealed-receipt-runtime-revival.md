---
name: sealed-receipt-runtime-revival
description: "Revive a sealed, receipt-bound runtime when some sealed modules or artifacts are missing. Use when follow-on work depends on hash-pinned receipt chains you cannot fully retrieve. Rebuild byte-for-byte from surviving evidence, bind substitutes by their own identity, declare one-field substitutions, and verify every wall offline before a scarce allocation."
category: tooling
date: 2026-11-11
version: "1.0.0"
user-invocable: false
tags: [sealed-receipts, runtime-revival, provenance, evidence-chain, offline-validation]
---

# Sealed Receipt Runtime Revival

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-11 |
| **Objective** | Let a sealed, receipt-bound campaign run again when its sealed runner modules and artifacts are only partially preserved on storage |
| **Outcome** | Operational — the full sealed loader chain and every producer-identity check pass in CPU-side dry runs, and the GPU wall reduces to documented residue |

## When to Use

- A sealed, hash-pinned receipt chain (layouts, identities, manifests, runners) governs what code may run, and part of that chain no longer exists on storage.
- Follow-on work must consume previous sealed evidence to compute or evaluate a report.
- Submission capacity is scarce (for example, a single shared allocation), and early failures are expensive.
- The pinned runtime environment no longer matches the pinned code (compat drift between backend libraries).
- The team forbids private absolute paths or exported run configuration in published scripts.

## Verified Workflow

### Quick Reference

Inventory and verify everything; rebuild byte-for-byte; bind substitutes by their own names; declare one-field substitutions; reproduce each wall offline before the next submission.

### Suggested Approach

1. **Inventory and verify before substitution.** List every sealed hash- or name-pinned artifact the validator requires. Locate each survivor and hash-verify it against its sealed constant before staging it. Do not assume the store version matches; spot-check by hash, not name.
2. **Rebuild byte-for-byte at the declared absolute paths.** When a receipt chain must reappear, rebuild its required layout *at the exact paths the receipts pin*, from hash-confirmed survivors. Hashed completion records embed absolute paths: staging under any other path fails validation, even when bytes match. Never edit hashed content, never fabricate a sealed file, and never put substitute content under a sealed name. A non-recoverable sealed file is a wall, not an invitation to write one.
3. **Bind substitutes by their own identity.** For modules whose sealed form is gone, write a dev substitute that consumes exactly the interface its callers need, declares itself a substitute, and lets run receipts hash *its own* files. Receipts of the new runs must read the substitute's identities, not the sealed ones.
4. **Declare one-field substitutions explicitly.** Where a sealed validator compares an identity document to a fresh computation and one field (typically a runner file hash) is the only legitimate difference, the *caller* may accept drift only through a named substitution rule with two guards: the single named field passes while every other identity field still must match byte-exact, and the accepted substitution is logged into the run's own receipts.
5. **Reproduce every wall offline before the GPU.** Sealed validator flows are CPU-safe up to the compute probe. Drive `prepare → loader → static qualification → producer identity → runtime-build` against the staged artifact root on a CPU host first. Every submission that passes that gate either runs or surfaces exactly one new wall; a wall seen offline is never re-learned on the allocation.
6. **Resolve policy gates before packaging.** The publication guard bans absolute private paths in the published tree — keep them under required long CLI flags, with a `CONFIG_*` block logged next to the job artifacts. Apply both publication-style rules and any new environment-variable policy to scripts and sbatches before the next bundle ships.
7. **Run the sanctioned compat guard in fresh environments.** A pinned code line can import a compatibility surface the pinned backend lacks; the campaign may supply its own hash-verified compat guard that rewrites exactly one backend source file atomically and refuses a mismatch. Run it once per fresh environment *before* any model import, with the ancestry guaranteed owner-controlled.
8. **Sequence checkpoints and exits cleanly.** When redundant eval/aggregation/integration steps exist, stage work so upstream receipts exist before downstream validators read them, and print effective configuration after each stage so a future session can account for what ran.

Example decision branches:

| Case | Decision | Reason |
| --- | --- | --- |
| An absolute-path binding in a hashed receipt points at a path that no longer exists | Rebuild the layout at that exact absolute path with hash-verified bytes | Hashed receipts pin paths; alternatives refuse at validation |
| The sealed runner module is absent but only one hash field leaves a gap | Accept the single-field drift through the caller's declared substitution, and record it | Fabricating the sealed file would falsify the chain; a declared substitution keeps it honest |
| A model-import-only fix is found live on the cluster | Apply the sanctioned compat module to the path it owns, with hash verification after replace | Prevents drift in the full layout while only one file is rewritten atomically and verifiably |

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Substitute module under the sealed name | Replaced a missing sealed runner with a same-named dev file | The receipts hashed the file and refused the substitute as drift | Substitutes must keep their own names/identities; interface wiring, not names, restores the call chain |
| Stage receipts at a new local path | Copied hash-correct checkpoint receipts under a fresh artifact root | The hashed contents embedded the original absolute paths; validators rejected the drift | Rebuild layouts at the exact paths the receipts pin, because hashing covers embedded locations too |
| Resubmit to surface the next wall | Ran short GPU submissions to enumerate walls one by one | Ten-plus wasted allocations across a day; each wall was discoverable offline | Reproduce and fix each validator gate offline first; the first GPU pass should fail at most on verifiable compute, not provenance |
| Hardlink staged files from source | Linked frozen runner copies back to dev files | A later chmod of the staged copy changed the dev source file's mode | Stage frozen files by copy only; shared inodes make receipt-mode changes propagate into the source |

## Results & Parameters

The validator chain that this revives is CPU-verifiable through every stage except the backend compute probe:

```text
prepare (stage layout, hash-verify every staged byte)
→ loader resolves sealed protocol + prepared manifests
→ static qualification (sealed file bindings)
→ producer identity (checkpoint training-identity field equality)
→ runtime build (sealed graft or parallel construct)
→ GPU/TPU probe (the only stage that must wait for the allocation)
```

A submission that reaches the compute probe has passed the evidence chain; evidence-chain failures at that point are pre-existing residue, not new wall work.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Internal research-campaign runtime | Revival of a sealed research campaign whose sealed runner modules and artifacts were partially archived; GPU wave first passed all offline evidence gates before the allocation | Authored with [notes](sealed-receipt-runtime-revival.notes.md) |

## References

- [architecture-cross-repo-migration-verify-issue-inventory](architecture-cross-repo-migration-verify-issue-inventory.md) — inventory before substitution, applied to archived evidence
- [checkout-other-ref-silent-file-clobber](checkout-other-ref-silent-file-clobber.md) — shared-inode hazards across staged paths
