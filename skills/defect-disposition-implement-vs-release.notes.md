# Notes: defect-disposition-implement-vs-release

Supporting evidence for `defect-disposition-implement-vs-release.md`. Source:
one live-debugging session on 2026-10-26 in LLM360/comet. Rules for the main
skill were generalized from this case; the case itself is not required for
operation of the skill.

## Session sequence

1. **Symptom.** An operator reported: the fleet autoscaler grows pools while
   no user work justifies the growth.
2. **Live diagnosis.** Supervisor decision log showed scale-out intent on
   every evaluation tick for every enabled pool, blocked only by ceilings and
   pending-replica caps. One concrete scale-out was justified as
   `queue demand occurred during the prior collection interval: 0.0025s
   cumulative wait, maximum 0 sampled waiting requests`. Engine scheduler logs
   for the scaled pool showed, over 22 minutes, 19 admissions of 1-token
   prompts at one per minute and 1 admission of 19 tokens. The "demand" was a
   periodic probe; each admission spent single-digit milliseconds in the
   scheduler queue, and the policy accepted any positive cumulative wait as
   demand, with no materiality floor.
3. **Fix design (pre-disposition-draft).** Add a materiality gate to the
   interval-evidence thresholds; consider excluding probe traffic from
   accounting.
4. **Disposition checks (the skill).**
   - Signature search found issue #2858 (closed): same phantom-wait
     mechanism, same pool, same up/hold/down whipsaw, same flap-written
     desired state residue, filed 4 days earlier from an earlier supervisor
     run.
   - `gh pr view 3006 --json state,mergeCommit,mergedAt`: MERGED to `main`
     ~9 hours before the new investigation, carrying commit `4ce9c681`.
   - `git merge-base --is-ancestor 4ce9c681` against the local checkout HEAD
     and against the deployed venv `source_sha`: false for both.
   - `git describe --tags <deployed-source-sha>`: v0.2.3, while the local
     checkout predated the merge; deployed release predated the fix.
   - `git show 4ce9c681 --stat` and its changed policy code: the merged
     change implements exactly the recommended materiality gate, plus
     warming-replica idle protection and scale-in ordering. Content covered
     the mechanism; the design of step 3 became redundant before it was
     written.
5. **Disposition selected:** `deliver-release`. Production needed the release
   carrying the fix. No new implementation, issue, or competing PR.

## Check costs

The dispositioning commands ran in under two minutes: one tracker search, one
merge-state query, three ancestry tests, one `git show`. The abandoned fix
design would have taken an issue, a plan review, a worktree, tests, and a
review cycle.

## Harness notes

- The deployed source identity came from a runtime state directory (a JSON
  manifest naming the deployed source digest), not from `latest` or a
  checkout. That single binding made the "release lag, not implementation
  drift" classification possible.
- The defect was a design-level noise-amplification policy defect; an
  additional lesson for the autoscaler itself thresholds the evidence, but
  that rule belongs to the product, not to this workflow skill.
- Symptom fingerprint that matched across investigations: the decision-log
  phrase `queue demand occurred during the prior collection interval` with
  single-digit-millisecond cumulative waits and zero sampled waiting
  requests.

## Limits

- One case; the dispositions table is derived from this case plus the general
  upstream/downstream release model. No contradictions were observed.
- CI validation of the corpus repository is the merge-level gate; this entry
  was validated locally only.
