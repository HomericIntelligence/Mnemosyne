# Notes: review-author-reviewer-role-separation

Supporting evidence for the main skill. Generalized from one live session. Identifiers are omitted under the privacy rules.

## Observed sequence

1. A fresh-context reviewer found issues in a PR. The author had already answered them in a PR comment.
2. The reviewer wrote the author response and then published the verdict. A permission classifier flagged the action as self-approval.
3. The workflow changed. The reviewer returned a blocked result "needs author response". A fixer agent fixed the findings and published the author response. A new fresh-context reviewer reviewed the new head and delivered the verdict.
4. A later rebase and a base-branch merge each moved a PR head. Each move invalidated the earlier GO and cancelled auto-merge pinned to the old head. A re-review of the new head restored the gate.
5. One clean source review was refused at delivery. Causes seen: a linked-issue digest that drifted after a later issue comment, and an older unfinished exchange that made the reviewer-state history a forked chain. The owner gave explicit authority. The terminal state was rendered with the exchange reducer, published directly, and the readback was verified.
6. A chained publish command reused a stale payload file from a shared temporary directory. It published a stale duplicate review twice. The reviews could not be deleted.
7. A plain rebase of a branch with merge commits dropped the changes made inside the merges. The net diff was rebuilt as clean commits. Decision-record numbers collided with the base branch and were renumbered with all references. In one case the base already held the change, so the branch was not pushed and the owner was told to close the PR as superseded.

## Guard pattern for chained publish commands

- Create a new empty directory for each run.
- Run from the repository directory.
- Use `set -e` or an explicit `&&` chain so that a failed head or repository check stops the chain.
- Read the live head again immediately before each write.
