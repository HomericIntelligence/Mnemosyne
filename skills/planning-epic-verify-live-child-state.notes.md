# Live Child State: Notes

This companion is not part of normal retrieval. Keep the rules in the main entry.

## 2026-11: A dispatch that closes the epic while a child is open (v1.6.0 source case)

Source evidence: an implementation dispatch for a 10-child tracking epic. The epic carried an
approved plan and the implement-ready label. The plan was orchestration-only: "This epic plan
implements no code and does not re-plan children". It put the closing keyword on step S11, the
close-out: "`Closes #<epic>` belongs to the close-out step after all exit criteria pass". The
dispatch instead ordered one pull request with the closing keyword.

Live sweep at the branch base (generalized):

| Check | Observed |
|-------|----------|
| Child state sweep | 8 of 10 children CLOSED COMPLETED |
| Merged-pull-request confirmation | Every shipped child had a merged pull request that named it |
| Open child 1 | Open, plan-approved label, one open unmerged pull request |
| Open child 2 | OPEN, needs-plan label, no plan comment, no pull request |
| Repository word search | New alias rows, retired-cluster cards, shared navigation builder and mode variable all present |
| Open pull requests on the epic | None |

Both readings were defensible from the dispatch alone. The plan text decided the fork: it named the
close-out step as the link owner and gave each remaining child its own plan and review. A closing
pull request would have closed the epic ahead of its exit criteria. To avoid that, it would also
have had to implement the child without a plan, which the plan forbids.

Repair shape that the case supports:

1. Run the dispatch-close-out gate before the first branch or commit.
2. Post one decision request with: the per-child state table, the merged pull request for each
   shipped child, the repository check of the shipped claims, both readings quoted from the plan
   and the dispatch, and the options (plan and ship the child, authorize it under the epic plan, or
   descope it).
3. Stop. Zero branches, zero commits, zero pull requests, zero labels, and no implementation of the
   unplanned child.
4. State the verification limits. In this case the postgres-profile migration command could not run
   because the container socket denied access. The other epic commands passed. Report that limit and
   rely on the hosted profile per child pull request.

Why the gate is not the same as "check the labels":
`automation-loop-exclude-epic-roadmap-issues` stops a worker at the container before a plan exists.
This case has a container with an approved plan, a mostly shipped child set, and a dispatch that
asks for the closing step early. The container rule says "stop"; the decision here is which of three
close-out paths the owner selects, and the evidence is the per-child shipped record.