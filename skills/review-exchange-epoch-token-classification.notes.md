# Notes: review-exchange-epoch-token-classification

Privacy-safe supporting evidence. Source: a same-day multi-lane review campaign of chain-verified plan/review exchanges on a shared forge (details generalized).

## Evidence synthesis

- Two independent reviewer lanes received dispatches binding "source epoch" as a 64-hex string. On a SHA-1 repository, `git fetch <token>` fails and no history search finds it. One lane proceeded with a reconstructed proxy checkout (risk: approximate base). The second lane proved the token equals `sha256(`the issue/requirements source bytes`)` by direct byte comparison, then read the carrier's explicit `revision` field, fetched that revision, and re-derived roughly thirty measured pins — every pin exact. The identity chain requirements-source → carrier → plan revision verified end-to-end.
- A third lane, briefed with the same classification step, resolved its epoch to the publication-preceding main tip via `git rev-list -1 --before="<plan publication time - 1 minute>" main` (tip landed seconds before the plan comment) and audited every pin — exact at the epoch, drifted at the current base. Classification: one hundred percent base drift, zero defects; proven with `git log --follow` evidence retained.
- Drift classes observed and re-derived: source line shifts from accumulated feature commits; wholesale file removal by a shim refactor (plan sections referencing the removed file fail at current base while being true at authoring); flag renames (`--parallel` → `--max-workers`) breaking plan verification commands; test-file size growth shifting every downstream pin. Each was classified with the same two-checkpoint rule.
- A reviewer counted six commits for a path interval and the author counted seven; `git rev-list --count <epoch>..<base> -- <path>` returned seven. Cause of the human miss: one commit touched two files that the summary table listed separately.
- Byte-versus-character counts diverged by single digits across several artifacts containing non-ASCII punctuation; digests matched exactly in every case. Dispatch advice "trust the digest, never the byte count" held in all lanes.

## Boundary observations (not part of the rule; recorded for travelers)

- A `visible_content_sha256` binding inside a review carrier binds the review's own visible content (review prose plus the generated reviewed-plan source token), not the plan body. An author who tests plan-body byte variants against that digest tests the wrong artifact. Reproduce it from the review body instead.
- Publication-time verification of an artifact comment requires the snapshot built after the write (post-publication), not the pre-write snapshot; a pre-write snapshot yields an identity-conflict diagnostic from the verifier even though the write itself is correct.
- The immediate-state gate (issue still open, artifact bodies unchanged) must run immediately before every forge write, not just at lane start; a lane in this campaign was blocked mid-run because the issue had been closed hours before its write step, caught only because the gate ran pre-write.

## Generalization limits

- The digest-identity proof requires the exact source bytes (marker and framing included or excluded as the carrier family defines). If hashing the source does not match and no explicit revision field exists, stop and report rather than guessing; the proxy-checkout route is a last resort and must be labeled approximate.
- The classification does not decide severity. A drifted pin and a defective pin can both be required findings under the exchange contract; the class changes the remedy (re-pin or epoch marker versus plan rewrite), not the requirement to act.
