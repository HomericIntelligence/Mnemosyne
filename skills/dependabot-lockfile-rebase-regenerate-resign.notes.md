# Notes: dependabot-lockfile-rebase-regenerate-resign

Supporting evidence for v1.2.0 (the `stale info` compare-and-discard branch).
Details are generalized; names, identifiers, and repository-specific values
from the source session are withheld.

## Source session (v1.2.0 evidence)

- Context: one batch rebase of five open pull requests onto a moved trunk in
  a repository with label-gated CI. One PR was a dependency-bot branch for a
  Python dependency group; another bot branch for a container image group
  needed no rebase at all.
- The bot branches were fetched at batch start. The Python-dependency branch
  rebased cleanly onto the new trunk tip and every rewritten commit verified
  with a local signature.
- The lease push of the rebased bot branch failed with `stale info`: the
  remote ref had moved since the fetch.
- Re-fetch showed the bot had force-updated its own branch during the batch.
  Its new head sat directly on the current trunk tip (parent equal to the
  trunk head), with a regenerated bump whose subject differed slightly from
  the local rebase ("across 1 directory" wording). The content differed from
  the local rebase only in the manifest and generated lock.
- Decision: the bot's regenerated head was newer evidence of the same intent
  and already based on the correct trunk, so the local rebase was discarded
  (`git reset --hard` to the remote head) and nothing was pushed. The PR
  stayed mergeable; the only remaining gate was the repository's
  implementation label, which workers must not touch.
- Signature state: the untouched bot head showed `%G?` `E` locally (the local
  trust ring cannot check the bot's signature). The forge accepted it. No
  re-sign was needed or performed for that branch.
- Related observation from the same batch: an automation-authored branch
  carried stale conflict markers from an earlier rewrite in two of its
  intermediate commits; the marker named a commit that no longer existed.
  The final commit of that branch removed the markers, so the pull-request
  diff against the trunk was clean. Scan a rewritten branch's own commits
  for markers before treating intermediate-commit content as intended.

## Verification

- The compare-and-discard decision ran against live remote state: the
  re-fetch reported a forced update of the bot branch, and the parent of the
  bot's new head equaled the trunk tip. Evidence observed directly in the
  session; no reproduction harness exists.
- Classification: verified-local. The merged entry's verified-ci instance
  (the constraint-edit and regenerate workflow) is unchanged by this
  amendment.
