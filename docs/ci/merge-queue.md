# Merge queue readiness

Mnemosyne's required-check workflow is prepared for a staged GitHub merge
queue rollout on `main`. This repository does not activate or modify the live
queue. [Odysseus issue #386](https://github.com/HomericIntelligence/Odysseus/issues/386)
and its repository-owned tooling are the sole authority for future activation.

## Readiness contract

[`configs/github/merge-queue-policy.json`](../../configs/github/merge-queue-policy.json)
is the machine-readable source of truth for the approved queue rule and the
required contexts observed before this readiness change. The context list is
also grouped by its live repository ruleset so the two-rule source is explicit:

- `homeric-main-baseline` (`17852368`) supplies nine required contexts.
- `homeric-main-extras` (`18221133`) supplies `pixi-check` and `symlink-check`.

The aggregate list contains 11 unique required contexts. Inspect the contract
without copying it into another policy source:

```bash
jq '.required_contexts_by_ruleset, .merge_queue_rule' \
  configs/github/merge-queue-policy.json
```

`.github/workflows/_required.yml` emits those contexts for `push` and
`pull_request` events on `main`, and for `merge_group` `checks_requested`
events. The advisory `validate-plugins.yml` workflow keeps its existing
triggers. The release publisher remains tag-only and retains write permission
only for publishing releases.

## Staged activation

Merging the readiness pull request does not enable the queue. After it lands,
the Odysseus operator must:

1. Re-read both live Mnemosyne rulesets and verify the 11 required contexts
   still equal the policy artifact.
2. Use the Odysseus merge-queue rollout tool to add the approved rule without
   changing existing conditions, enforcement, required contexts, permissions,
   or unrelated protection rules.
3. Queue a designated smoke pull request and verify that its exact
   `merge_group` run emits every required context once and successfully.
4. Record the live ruleset response, workflow run, and queued merge result in
   [Mnemosyne issue #3115](https://github.com/HomericIntelligence/Mnemosyne/issues/3115).

Issue #3115 stays open until activation and queued-smoke evidence are recorded.
No ruleset or branch-protection mutation belongs in this readiness change.
