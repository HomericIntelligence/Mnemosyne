# Notes: Live Hotfix Content-Addressed Identity Rotation

Supporting evidence for `live-hotfix-content-addressed-identity-rotation`.
All product, model, host, job, release, and digest identifiers are
intentionally omitted. The evidence below preserves only decision-relevant
shapes: counts, orders of events, and message classes.

## Incident shape

- A production serving lane with 15 model pools. A release document pins one
  runtime-contract digest per pool and derives component, state, release, and
  context identifiers from content. A scheduler (Slurm) runs the traffic
  entrypoint (blue/green lifecycle) and the per-pool replica jobs. An
  operator-host authorization service fronts administrative verbs over a local
  socket on shared storage.
- Trigger: one model family required a serving-engine trust flag that only a
  recipe change could carry. The flag changed that recipe's qualification
  digest, which changed the contract digests downstream.

## Evidence behind each rule

1. **Four-layer cascade from one flag.** After the recipe edit, the release
   document no longer validated against the lane: pool pins, then component,
   state, release, and context identifiers all described the pre-edit
   content. Hand-editing one derived layer produced base/schema validation
   failures until the whole chain was recomputed with the system's own
   functions and the document model revalidated offline in one pass.

2. **Stale-pin audit shape.** 10 of 15 pool pins were stale, in two groups:
   4 from one model family and 6 from another, all authored before the
   current recipe generation. The pools that first reported errors were only
   a subset: repinning those alone left the derived chain invalid. One
   cascade repin for all stale pools produced the final lineage that the
   lane accepted. A sibling set of pools repinned but not yet floored keeps
   the fix latent: contract drift would have resurfaced at first floor
   assignment, and did not, because the repin preceded demand.

3. **RAM re-serialization reverts disk edits.** An operator-host service
   resolved identity at boot and held it in RAM. After the on-disk identity
   document was corrected, the next lifecycle verb on that service rewrote
   the document from its in-RAM copy, restoring the old identity. Three such
   orphaned processes were found across the rotation: the drain/teardown
   verbs had not reaped any of them, and each held a socket path on shared
   storage (visible cluster-wide, served only by the binding host; see the
   socket-locality skill). Terminating the processes before the disk write
   made the write durable. The canonical start script that replaced them
   sanitizes every exported identity variable and reports a pid-matched
   heartbeat.

4. **Boot refusal from sourced environment.** Starting the service with the
   previous release's exported environment file (which pins an identity
   trio and related identifiers) failed closed with a message telling the
   operator to restart from the active deployment release. Boot succeeded
   only with all identity variables unset, credentials supplied from the
   rotation-managed store, and identity derived from the disk document.

5. **Requeue resurrection.** The entrypoint job and some replica jobs carry
   a batch requeue directive. Cancelling the old-generation entrypoint job
   directly brought a replacement job with a new ID within seconds, still
   rendering the old identity. Setting requeue off through the scheduler
   control verb before cancelling stopped the resurrection. Verified on two
   job classes.

6. **Membership binding rebind.** The launch gate for one pool failed with a
   binding mismatch: expected = the qualification digest of the current
   recipe, got = the manifest's digest set. The manifest had been rewritten
   hours earlier by an untracked actor and no longer contained the current
   recipe's digest. The designed rebind verb appended the current digest;
   the manifest set after rebind was the union of the old and current
   digests, and the pool launched with all checkpoint files reused. No byte
   edit of the read-only manifest was needed or attempted.

7. **Declaration-driven floors.** Two pools had replica floors declared at
   rollout time. With zero demand, autoscale never reduced them; the pools
   retried scale-out on a loop. Scaling to zero used a positional CLI form
   (the flag form one would expect was not accepted). After scale-to-zero,
   the supervisor did not cancel its own pending scheduler submissions; two
   requeue-marked leftovers were reaped by hand (requeue disabled first).

8. **Cosmetic receipt timeout.** The traffic-up command reported a
   receipt-verification timeout; the job log showed activation about 90
   seconds after submission, and the published record then carried the new
   identity. Class result: treat CLI receipt timeouts as unknown outcome and
   verify through the log and the record before any resubmission.

9. **Catch-all CLI message.** Administrative failures surfaced as one
   generic "operation did not complete" line. Re-running the same operation
   in process, through the same parse-and-execute path used by the CLI,
   exposed the real tracebacks (including the stale-pin class and the
   binding-mismatch class) and selected each repair.

10. **End state.** All 15 pools cleared contract errors. The hotfixed model
    family served real traffic (prefill batches plus metrics polls) past its
    previously observed crash window (~8 minutes; the healthy replica
    exceeded 45 minutes at capture). One still-misbehaving engine was left
    under watch with its failure recorded, without blocking the release —
    the behavioral-independence rule.

## Limits

- Single-lane, single-incident evidence. The carrier taxonomy (rendered
  scripts, exported environment, long-lived RAM services, published records)
  is the reusable core; the exact scheduler verbs and CLI forms are
  deployment-specific.
- Timings (the ~90-second activation, the ~8-minute failure window) are
  one-lane observations, not guarantees.
- The untracked manifest rewrite was never attributed; treat manifest
  oddities as integrity events and check the digest set, not just the file
  freshness.
