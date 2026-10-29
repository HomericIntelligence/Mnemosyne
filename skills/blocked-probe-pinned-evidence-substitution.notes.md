# Notes: Blocked Probe — Pinned Evidence Substitution

Supporting detail for `blocked-probe-pinned-evidence-substitution.md`. All
identifiers generalized; the source case involved no public identifiers that
are safe to republish.

## Source-case fact pattern (generalized)

An approved single-issue plan gated its recipe fix on a five-row decision
table keyed on tokenizer/config probe facts F1–F4. The probe command required
a container-capable scheduler partition plus a model-weights mount. One day
before this session, a lane recorded the park row verbatim ("probe cannot
run": scheduler rejects `--container-image`; mount is owner-only, probe uid
gets EACCES) and merged only the peripheral failure-attribution half of the
plan. The decision itself stayed open.

Substitution, one session:

1. **Image.** The pinned runtime image (`*.sqsh`, mode 0444, world-readable)
   was listed in the recipe. `unsquashfs -d <scratch> <image>.sqsh -e
   <runtime/source/subtree>` extracted 4949 files of engine source with no
   daemon, root, scheduler, or network. Reading the error-site source,
   the warmup-payload builder, and the chat-encoding dispatch settled facts
   that the plan had marked as open questions.
2. **Artifact.** The configuration declared an upstream source of record
   (public hub repository) pinned to an exact revision. Fetching only the
   small build inputs (config, tokenizer, tokenizer config, encoder module)
   at that revision reproduced the production artifact's relevant surface
   byte-identical without touching the owner-only mount.
3. **Toolchain.** The image's `*.dist-info` metadata gave the packaged
   framework version; a scratch virtual environment pinned to that version
   ran the load/template/encode behavior probes (F1/F2/F3) plus extra
   encoder-level probes against the extracted image module directly.
4. **History.** `git log --follow -p` on the recipe file showed the actual
   defect (a parser pin whose value took precedence over architecture in the
   serving dispatch) and the already-merged fix that replaced the pin with
   `auto`. The same history explained a later "fix already landed" linkage
   comment whose quoted PR title did not match the real PR — auditing the
   merged diff prevented a wrong close.

Outcome: every decision-table row re-evaluated against evidence. The row the
plan would have applied on a naive reading (pin the older explicit values)
proved to be the exact defect that caused the incident; the evidence showed
the root cause was already fixed and the correct disposition was an
evidence-backed close plus one follow-up issue (a validator gap), with no new
code change.

## Decision details that generalized

- Chat-encoding selection in the serving layer concatenated several dispatch
  stages (literal parser value, then architecture, then template presence,
  then tokenizer capabilities). Any recipe value that overrode auto-detection
  silently re-keyed the whole chain. The F-fact probes were necessary but not
  sufficient; the dispatch source settled which facts mattered.
- The warmup failure text had exactly one raise site in the extracted source,
  and enumerating its two trigger branches (empty rendered text, uninitialized
  tokenizer) and each reachable caller settled which branch could fire —
  something the production log line alone could not distinguish.
- The substitution set cost under one gigabyte of scratch and under an hour;
  the equivalent "correct" path (operator-run probe with elevated access on a
  container-capable allocation) carried a multi-day queue and no decision
  advantage, because the probed surfaces were identical by construction.

## Constraints and boundaries

- Owner-only mounts were not bypassed; the substitute was the artifact's own
  declared public source of record at the same pinned revision.
- Image extraction used the image's world-readable mode; nothing below the
  image's filesystem that required privilege was touched.
- Scratch data lived outside tracked checkouts and was removed at completion.
- A follow-up validator issue was filed instead of fixing out of scope.
