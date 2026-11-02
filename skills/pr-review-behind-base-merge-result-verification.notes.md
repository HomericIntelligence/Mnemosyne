# Notes: pr-review-behind-base-merge-result-verification

Supporting evidence for the main skill. Generalized from one review session.
Repository names, pull-request identifiers, field names, and file paths are
omitted under the privacy rules.

## Evidence chronology (2026-11-01)

1. Round 1 reviewed a pull request whose branch was behind its target. The
   review verified the branch delta against the branch base: code, tests, and
   documentation agreed. The verdict was a pass.
2. A correction review re-examined the same head against the current target.
   The target had advanced past the branch base and removed a configuration
   field. The branch still passed that field, and the strict loader of the
   target raised during construction of the merged configuration. A second
   defect surfaced in the same merged tree: the branch added a test module that
   no merged inventory row covered.
3. The pass verdict was withdrawn and replaced with a fail verdict that cited
   the merged-tree evidence.
4. Round 2, later the same day, reviewed a different behind-base pull request
   with the merge-result procedure: a detached worktree at the bound target
   commit, a real merge of the bound head, and focused checks against the
   merged tree (configuration loading and inventory enumeration). The merge was
   clean, the checks passed, and the terminal pass verdict cited both lenses.

## Why the rule generalizes

- A branch validates itself against the base that it was cut from. Only the
  merge result composes the branch with the target advance, so only the merge
  result can exhibit base-drift failures.
- The failing contracts are computed behavior: a strict loader fails during
  execution, and an inventory check counts merged files. File reads at the
  endpoints cannot produce either result.
- The materialization is cheap and disposable: one worktree, one merge, and a
  bounded check set. The verdict quality gain is large relative to the cost.

## Limits

- The evidence comes from one Python codebase with strict configuration models
  and registry-based test inventories. The method applies wherever merged
  behavior is computed; the concrete check set is project-specific.
- A clean merge result is not a substitute for the target repository's own
  required checks. It is reviewer-side evidence about the composed tree.
  Merge gates stay governed by repository policy.
- Forge mergeability is a signal, not behavior evidence. Use it to decide
  whether to materialize a merge; do not read it as a verdict.
