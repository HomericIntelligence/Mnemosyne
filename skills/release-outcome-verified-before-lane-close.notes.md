# Notes: release-outcome-verified-before-lane-close

Supporting evidence for the main skill. Generalized from one closure audit.
Repository names, release numbers, milestone numbers, pull-request identifiers,
commit identifiers, and dates of record are omitted under the privacy rules.

## Evidence chronology

1. A review lane had driven unreviewed pull requests toward a release. The lane
   paused at a safety limit after a large number of review deliveries.
2. Several days later, a directive stated that the release outcome had shipped
   through other lanes, and asked for a live audit instead of more work.
3. The audit read the forge in this order: the milestone list with open counts and
   creation times, then the release list, then the tag commits and their ancestry.
4. The live result was zero delta for this lane:
   - the release object existed, and its title named a tag with a hotfix suffix;
   - the target milestone had closed with zero open issues;
   - a later milestone had also closed, and the live release had moved on;
   - older releases had milestone records that were created after those releases,
     so a title match alone would have selected history;
   - the release tag pointed to a promotion merge on the deployed branch, and the
     development branch did not contain that commit;
   - every pull request the lane had reviewed was merged;
   - no open pull request carried a review from the lane;
   - the lane's own branch had merged, and its remote ref and worktree were
     already gone.
5. The deployed branch reported the same non-zero ahead count against the
   development branch in both directions. Reading the deployed-branch-only commits
   showed that all of them were merges of the development branch. The deployed
   branch was therefore a merge-down target, not a branch that lagged.
6. The lane posted one terminal record, corrected one wrong identifier in its own
   record after a readback, and closed its objective with the audit evidence.

## Why the rule generalizes

- Release state lives in release objects, tags, and branch ancestry. Milestone
  counts live in the issue tracker. The two stores disagree whenever a release,
  a tag, or a retroactive record changes without a matching tracker update.
- A symmetric ahead/behind pair is consistent with two different models: two
  independent lineages, or one merge-down branch. Only the branch-only commit
  subjects separate them, and the two models demand different actions.
- The delta of a review lane is a property of its artifacts. Counting merged
  pull requests settles it without any new source review.

## Limits

- The evidence comes from one host whose releases are published with tags that
  can include a hotfix suffix. A host that publishes releases without tags needs
  an alternative binding, such as the release target commit from the API.
- The branch model was established from commit subjects. A host that platforms
  commits or merges with custom messages needs a different signal, such as a
  protected-branch rule or a documented promotion process.
- This rule decides closure and delta. It does not replace the required checks of
  the release itself.