# Notes: Planning — Verify Premises Before Implementing

Supporting cases for `planning-verify-issue-premise-before-implementing`. Rules that the
skill requires for operation live in the skill itself, not here.

## 2026-10: Self-produced reproduction on a stale checkout (v3.4.0 source case)

A production service logged a code-level
`ValueError` on a recurring scheduler state. The responder ran the same live inputs against
the source tree and reproduced the failure, then filed an issue with a root-cause analysis,
a proposed predicate fix, and started the plan-review round.

Days later, a fresh fetch for an unrelated change showed the default branch already
contained the predicate fix with regression tests. The earlier reproduction had run from a
local checkout that lagged the default branch by multiple merges. The deployed release
artifact also predated the branch, so the production errors were real at the deployed
version but already remediated upstream. The issue closed as already-fixed; the only
remaining action was a routine deployment. The verification that would have prevented the
cycle took thirty seconds: the same live inputs run against a throwaway worktree at the
fetched default-branch head all passed, and a `-S` history search on the fixed predicate
named the upstream change.

Cost classification: the issue, plan draft, and one review round were recoverable but
wasted. Two cheap checks would have prevented them:

1. Re-run the reproduction at the fetched default-branch head (throwaway worktree), not
   the checkout as-found. A stale checkout proves a defect existed, not that it exists.
2. For a deployed service, compare the deployed artifact's version with the default
   branch. Fixed upstream plus a lagging deployment means operational remediation, and a
   second implementation of the same code is a redundant fix.

Outcome classification applied: `already_fixed_on_branch` with deployment currency as the
remaining action.
