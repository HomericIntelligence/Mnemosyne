# Notes: replace-forked-dependency-with-upstream

Supporting evidence for [replace-forked-dependency-with-upstream.md](./replace-forked-dependency-with-upstream.md).
This file is not in normal retrieval. It holds measurements and command detail only. All
organization, repository, issue, and host identifiers are generalized.

## Session shape

The work was a multi-round planning session. Each round began with the directive "replan this
task". The durable value is in the survey method and in what each round changed.

| Round | Directive change | Effect on the plan |
| ----- | ---------------- | ------------------ |
| 1 | Plan the migration at all | Three dependencies surveyed; no tracking artifact existed |
| 2 | "Do not retire the fork; other teams use it" | Outcome boundary moved from the fork to the consumer; non-goals added |
| 3 | One dependency per release, starting at the next minor line | Release sequence added; ordering reason recorded |
| 4 | "Replan with the most recent version of main" | Untracked upstream changes found: a new stable release, a partially executed rebuild, and a new drift issue |

## Measurements that changed a decision

### Branch that production consumes can differ from main

The gateway fork compared as four commits ahead of upstream on its default branch. All four
commits were CI or deploy automation. The branch that production consumed carried the product
code as a small patch on top of upstream.

```bash
gh api "repos/UPSTREAM/PROJ/compare/main...ORG:main" --jq '{ahead_by, behind_by}'
gh api "repos/UPSTREAM/PROJ/compare/main...ORG:deploy" --jq '{ahead_by, behind_by}'
```

Decision changed: a fork refresh was rejected in favor of a pinned upstream revision plus the
small patch stack from the consumed branch.

### Upstream parent can be a different project

One fork's parent project name did not follow the naming pattern of the other two. A search
against the guessed parent returned "could not resolve". Reading `parent` from the forge
returned the correct project. Decision changed: discovery was repeated against the real parent.

### Lag must be measured at the consumer pin

One deployed artifact was a single release behind its fork. A second was thousands of commits
behind its fork because the pin had not moved. Both looked similar in a repository-level
comparison. Decision changed: the second dependency was promoted in priority and its surface
survey was scoped to a much larger version gap.

### A found internal endpoint with no upstream match

The consumer called an internal endpoint on the gateway. A code search of upstream and of the
fork's product branch found no match. Decision changed: this became a named blocker in the plan
before any cutover step.

## Survey checklist used

1. Read `parent` and `defaultBranchRef` from the forge.
2. Compare each production-reachable branch with upstream. Read both `ahead_by` and `behind_by`.
3. For each commit ahead, read the touched paths and classify it.
4. Read the consumer pin file and the deployed artifact version separately.
5. Enumerate the consumer surface: API calls, launch flags, environment variables, metric names,
   runtime overlays, internal endpoints.
6. Search upstream at the target revision for each surface point.
7. Classify the open issues filed against the dependency.
8. Read the upstream release list again immediately before finalizing.

## Replanning cost note

Four full planning rounds ran before the plan was accepted. Each round re-read forge state, and
each round found a fact that changed the plan. The replans were cheap because the survey
commands are read-only. Do not cache a survey result across rounds when the round exists
because the state may have moved.