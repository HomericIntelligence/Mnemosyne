# Merge Queue Readiness

The required-check workflow in Mnemosyne supports a staged GitHub merge queue
rollout on `main`. This repository does not activate or modify the live queue.

[Odysseus issue #386](https://github.com/HomericIntelligence/Odysseus/issues/386)
and the Odysseus repository tools are the only authorities for future
activation.

All active technical prose in this document must follow the
[ASD-STE100 writing policy](../asd-ste100.md).

## Readiness Contract

[`configs/github/merge-queue-policy.json`](../../configs/github/merge-queue-policy.json)
is the machine-readable source of truth. It contains the approved queue rule
and the required contexts observed before this readiness change.

The file groups each context by its live repository ruleset:

- `homeric-main-baseline` (`17852368`) supplies nine required contexts.
- `homeric-main-extras` (`18221133`) supplies `pixi-check` and `symlink-check`.

The complete list contains 11 unique required contexts. Use this command to
inspect the contract. Do not copy the contract to another policy source.

```bash
jq '.required_contexts_by_ruleset, .merge_queue_rule' \
  configs/github/merge-queue-policy.json
```

`.github/workflows/_required.yml` emits these contexts for the following
events:

- `push` events on `main`.
- `pull_request` events on `main`.
- `merge_group` `checks_requested` events.

The advisory `validate-plugins.yml` workflow also handles `merge_group`
`checks_requested` events. It also handles pull requests, pushes to `main`,
and manual dispatches.

The release publisher runs for tags only. It has write permission only to
publish releases.

## Staged Activation

Merge of this documentation change does not enable the queue. Before
activation, the Odysseus operator must complete these steps:

1. Read both live Mnemosyne rulesets again.
2. Verify that their 11 required contexts match the policy artifact.
3. Use the Odysseus merge-queue rollout tool to add the approved rule.
4. Do not change existing conditions, enforcement, required contexts,
   permissions, or unrelated protection rules.
5. Queue the designated smoke pull request.
6. Verify that its exact `merge_group` run emits each required context one time.
7. Verify that each required context succeeds.
8. Record the live ruleset response, workflow run, and queued merge result.

[Mnemosyne issue #3115](https://github.com/HomericIntelligence/Mnemosyne/issues/3115)
records the earlier rollout work. The issue is closed.

Do not change a ruleset or branch-protection setting in this documentation
change.
