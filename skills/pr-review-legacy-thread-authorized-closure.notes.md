# Notes: PR Review Legacy Thread Authorized Closure

Companion evidence for
[pr-review-legacy-thread-authorized-closure](pr-review-legacy-thread-authorized-closure.md).
Generalized diagnostics and the single-case incident material. Every rule the
skill needs for operation lives in the main file.

## Incident reconstruction (v1.0.0 source material)

One verified session drove a wave of pull requests whose review exchanges had
been started by out-of-band automation. The automation published its round as
a findings-ledger comment and an empty-body review at an old head. The threads
carried only legacy severity markers. No version-1 finding markers existed.

### Diagnostic sequence

1. Forge enumeration per artifact: one legacy ledger comment with an old-head
   carrier marker, one empty-body `COMMENTED` review, and threads whose bodies
   ended in severity trailers only.
2. Read-only preflight on each artifact with the delivery helper's manifest
   preparation. Every prepared entry had a legacy `native:` identity,
   `required` disposition, and no author answer. The manifest state field was
   null and the terminal visible content was empty.
3. The flow's closure reference requires zero open threads for a terminal GO.
   Its thread rules forbid resolving a foreign thread or a thread without a
   terminal-ledger disposition, and require a separately authorized actor for
   legacy recovery.
4. Under explicit authority, one artifact's three legacy threads closed in
   the verified order: one author-response review on the exact current head
   with one cited resolving change per finding; visibility verified; then
   three resolutions. The fast-lane test that closed the major finding was
   executed locally and passed under the required gate's own selection.
5. The re-run preflight then showed an empty entry list. The manifest state
   field stayed null. No version-1 terminal reviewer state existed, because
   the round had never been published as a version-1 carrier.
6. The same manifest signature reproduced on three more artifacts in the
   wave. The cause was systemic, not per-item.
7. The repository merge queue later merged all four artifacts. The queue
   path made the remaining publish-a-real-round decision unnecessary. Forge
   state was re-read before every write throughout.

### Observations that shaped the rules

- The preflight is read-only. Running it first costs nothing and classifies
  the blocker before any reviewer round is spent. On the unblocked artifact
  of the same wave, the preflight had shown no adoptable entries at all.
- Hand-authoring the missing terminal state was evaluated and rejected. The
  terminal ledger is a digest over the verified exchange chain. A hand-written
  state envelope is fabrication, and the flow's integrity guards reject it.
- A same-wave actor error corroborated the void-repair reference: an in-place
  review-body edit failed the immutability check, and an unvoided repost of
  the identical body duplicated the inline finding threads. The sanctioned
  repair for an established record is tombstone plus single byte-identical
  repost, never edit and never repost without voiding.

### Verification limits

- Single-wave evidence. The classification cues and closure order are
  observed behavior; the fabrication prohibition follows from the flow's
  fail-closed design.
- The authorized-actor closure ran once, on three threads of one artifact.
  The state-null branch readback ran on four artifacts.
- The merge-queue completion superseded the remaining terminal rounds. It is
  recorded as the wave outcome, not as a verification of the round path.
