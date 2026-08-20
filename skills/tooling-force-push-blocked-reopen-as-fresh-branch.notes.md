# Force-Push Blocked — Case Notes

These notes retain incident-specific branch names, PR states, and outcomes. The complete superseded
main is stored only in history.

## Case Index

| Case | Source | Verification |
| --- | --- | --- |
| Option A0: merge main and reformat without force | [Immutable source at batch base](https://github.com/HomericIntelligence/Mnemosyne/blob/d377a8924aff84e5cc193b720130b4c57e38c5c3/skills/tooling-force-push-blocked-reopen-as-fresh-branch.md) | verified-ci |
| Option A: tree-preserving fast-forward merge | [Immutable source at batch base](https://github.com/HomericIntelligence/Mnemosyne/blob/d377a8924aff84e5cc193b720130b4c57e38c5c3/skills/tooling-force-push-blocked-reopen-as-fresh-branch.md) | verified-ci |
| Option B: replacement PR on fresh remote ref | [Immutable source at batch base](https://github.com/HomericIntelligence/Mnemosyne/blob/d377a8924aff84e5cc193b720130b4c57e38c5c3/skills/tooling-force-push-blocked-reopen-as-fresh-branch.md) | verified-ci |
| File restoration through `git show` data path | [Immutable source at batch base](https://github.com/HomericIntelligence/Mnemosyne/blob/d377a8924aff84e5cc193b720130b4c57e38c5c3/skills/tooling-force-push-blocked-reopen-as-fresh-branch.md) | verified-local |

## Option A0 Incident

ProjectHephaestus PRs #1945 and #1949 failed lint only on GitHub’s synthetic merge commit after a
different PR introduced formatter drift on main. The branches were not rebased. Each branch merged
`origin/main`, reformatted the affected file, created a signed reconciliation commit, proved the old
remote tip and current main were ancestors, and performed one plain push. The same PRs remained open;
zero force-pushes and no blocked reset/checkout/restore operations were used.

The session also reconstructed tracked file content with `git show <ref>:path > path` when git-state
restore commands were prohibited. That operation is only safe after confirming the target contains
no unrelated user edits.

## Option A Incident

ProjectHephaestus PR #1079 became dirty after stacked dependency PR #1073 merged and the child was
retargeted to main. A verified rebased checkpoint already existed. The recovery produced a merge
whose tree matched that checkpoint, included both the old remote tip and main in its ancestry, and
plain-pushed `c1c6324..4d38ea2`. The PR identity and auto-merge state were retained; checks were
green after the update.

This case depended on operations that current harnesses may prohibit. It is precedent for the graph
and proof, not authority to run destructive recovery commands.

## Option B Incident

ProjectHephaestus PR #843 conflicted after concurrent PR #842 merged. The rebased content was pushed
once to a new `-rebased` remote ref, replacement PR #845 was opened, and original issue #841 remained
linked. The old PR was closed with a forward explanation and auto-merge was armed on the replacement.
Delivery took roughly three minutes and used one fresh-ref push.

A second rewrite of the fresh ref would have recreated the force-push problem. The recorded fallback
was another fresh suffix or explicit authorization for the canonical safe-force path.

## State and Cleanup Notes

- A closed PR’s auto-merge request does not transfer to its replacement.
- The original remote ref can remain after closing the PR; deletion is cleanup, not delivery.
- A squash-merge repository can flatten the feature merge commit from A0/A. Rebase-only policy may
  reject the same topology.
- `merge-base --is-ancestor origin/<branch> HEAD` is the key plain-push proof; a clean working tree
  alone is insufficient.
- `git diff --cached <checkpoint> --stat` must be empty for tree-preserving reconciliation.

## Compaction Disposition

- Kept in main: option selection, safety boundaries, copy-ready workflows, ancestry/tree proofs,
  replacement-PR linkage, and named failed approaches.
- Moved here: PR numbers, branch-state transitions, timing, and incident narratives.
- Archived only: repeated command commentary, long anti-pattern discussion, and the complete prior
  main.
