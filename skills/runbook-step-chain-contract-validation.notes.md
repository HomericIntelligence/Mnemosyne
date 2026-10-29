# Notes — runbook-step-chain-contract-validation

Privacy-safe supporting context for `skills/runbook-step-chain-contract-validation.md`.
Supporting evidence only; the main skill carries every rule it needs.

## Source session (generalized)

A production cutover runbook of numbered Bash step scripts was executed by a
fresh-context coding-agent executor with three rules: run the steps in order,
stop on the first failure, and ask the helper before any script edit. The
helper owned script fixes; the executor owned runs and reports.

Three runs exposed three cross-step contract bugs, one per run:

1. **Clean-tree preflight vs pipeline helper file.** A patch-application step
   (step 19b) refused to start because a checkout-populating step (step 19)
   had written an untracked environment file into the checkout. The gate was
   `git status --porcelain` with default untracked-file behavior. The
   executor stopped and reported the exact porcelain entry instead of
   deleting the file or relaxing the gate.

2. **Sourced env file used as an interpreter directory.** The proof command
   expanded `"$DEPLOY_P_VENV/bin/python"`, but the variable held the sourced
   environment file path, so the run died with exit 126 `Not a directory`.
   The interpreter actually lived under the checkout's `.venv/bin`. The proof
   had never executed successfully; an earlier executor run had surfaced a
   different failure before reaching it. Additionally, the idempotent
   already-done branch would have exited 0 without running the proof at all.

3. **Marker format drift.** The marker file's first line was `P <revision>`
   (provenance prefix), while the rerun check used a whole-line grep for the
   bare revision. The mismatch forced the re-apply branch, which then failed
   on the by-design-dirty checkout. Fix: one exact line contract
   (`P <revision>` on both sides).

After each report the helper fixed the script, and the chain resumed from the
interrupted step. The full operator-free segment (checkout, patch + import
proof, rollback snapshot) then ran green. Nothing in production changed during
the loop; the failing steps were read-only toward live state by design.

## Why the entry defers to the clean-checkout skill

The session's deploy scripts locally tolerated the untracked helper file by
restricting the preflight to tracked files. The canonical
`automation-clean-checkout-intermediate-artifacts` rule records that exact
suppression as a failed approach for trust-boundary gates, because it hides
ambient content from later consumers. The durable rule for every new gate is
the canonical one: put the helper outside the checkout or ignore it
(`git/info/exclude` works for a detached worktree without changing the shared
`.gitignore`). The main skill instructs accordingly and does not bless the
suppression variant.

## Verification

- The import proof executed successfully against the patched checkout after
  the interpreter-path fix (explicit OK output from the patched modules).
- The rerun path executed the shared proof before exit after the marker
  format fix.
- The rollback-snapshot step ran green afterward through the same executor
  contract, with the log and report preserved in the session evidence.
- No CI or product-test evidence exists; the rules were exercised during a
  live operational rehearsal (`verified-live`).
