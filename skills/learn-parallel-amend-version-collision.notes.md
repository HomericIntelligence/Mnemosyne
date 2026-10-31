# learn-parallel-amend-version-collision — Development Notes

Supporting evidence for `learn-parallel-amend-version-collision.md`.

## Case: 2026-10-26…29 parallel learn wave

### Reconstruction from merged history

One review-exchange skill entry received three amends in fast sequence from
independent learn lanes:

1. v1.1.0 (`59561129`, 10-26) — delivery-side rebind branches. Base for both
   racing lanes.
2. v1.2.0 (`30ab0216`, merged 10-27) — metadata-only fix rebinds head. Lane A.
3. Lane B's amend, also stamped v1.2.0 at branch time, merged 10-29
   (`dea9ee1e`). Its branch carried a merge-commit ("Merge origin/main into
   …") that re-stamped the frontmatter to v1.3.0 at merge time. The merge
   commit's subject and the pull-request title still claim v1.2.0.

Observed end state: frontmatter on the default branch reads 1.3.0; both
competing changes present in full (keyword counts for the lane-B rule set
verified post-merge); history text and frontmatter disagree on the later
commit exactly as the lesson describes.

### What the repair looked like

- Detection point: merge time, not author time. Lane B's author had gated
  freshness at discovery (upstream refresh verified) but the entry drifted
  during the three days the pull request waited.
- Repair mechanism: merge upstream main into the feature branch, keep both
  changes, move the frontmatter stamp to the free next number.
- Residue: subject/stamp divergence on the merged commit; PR title unchanged.
  Per the lesson, this residue is the correct end state — history is not
  rewritten for a cosmetic version-text fix.

### Why a stack did not apply

The two lanes ran as independent agents with no shared plan, so the
dependency-ordered-stack branch of the rule (planned waves) was unavailable;
serialization had to happen at merge time.

### Privacy note

Commit prefixes are public in-repo provenance. Pull-request numbers exist in
the same public history and are omitted here by habit; the repository's own
`git log` recovers them.
