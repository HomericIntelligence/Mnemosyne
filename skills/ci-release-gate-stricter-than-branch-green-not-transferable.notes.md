# Notes — ci-release-gate-stricter-than-branch-green-not-transferable

Supporting evidence for the skill. The skill holds the rules; this file holds the observations
behind v1.0.0.

## The setup

A plugin repository published an npm package from a tag-triggered release workflow. Its required
checks were defined in one reusable workflow, called by two callers:

- the **branch path** (pull requests and pushes to the default branch) called it with the default
  input value, which selected a fast test tier — a marker-filtered subset of the suite, with no
  coverage step;
- the **release path** (tag push) called the same workflow with the input set, which selected the
  full suite plus a per-file branch-coverage floor.

Both paths showed a job with the same name. The commands behind that name were different.

## How the divergence was found

The first two release attempts failed at the coverage floor. The branch was green throughout.

The failure signature was:

```text
<one helper module>: Branch coverage is 79.64 percent. The minimum is 80.00 percent.
```

The next check was the decisive one: read the reusable workflow's `workflow_call` block and the
condition guarding each test step, then compare the two callers' input values.

```yaml
# reusable workflow
on:
  workflow_call:
    inputs:
      full-tests:
        type: boolean
        default: false
jobs:
  validate:
    steps:
      - name: Run the fast contract tests
        if: ${{ !inputs['full-tests'] }}
        run: <fast tier, marker-filtered>
      - name: Run all contract tests with the coverage threshold
        if: ${{ inputs['full-tests'] }}
        run: <full suite + coverage threshold>
```

```yaml
# branch path: default input
uses: ./.github/workflows/<required>.yml
# release path: input set
uses: ./.github/workflows/<required>.yml
with:
  full-tests: true
```

The branch path therefore **never executed** the coverage-threshold step. It could not report a
threshold failure. Its green status carried no information about the gate that the release path
enforced.

## The defect the stricter gate exposed

The failing check was a per-file branch-coverage floor on a single helper module in a review
plugin: 223 of 280 branch arcs covered, against a floor of 80 percent (224 arcs).

The uncovered arcs were live defensive logic — bounded pipe draining, path-manifest validation, and
child-process cleanup — each called from normal code paths, none referenced by any test. The
defect was the missing test, not the code.

Repair: behavior tests that assert observable state (the recorded error, the overflow flag, the
limit message, the collected paths) rather than call sequences. Result: 231 of 280 arcs, 82.50
percent. The threshold was not touched.

This was a real defect on the default branch, not a release-only artifact. It had been present for
an unknown period because no ordinary signal could report it.

## What the release run's job conclusions showed

The failure shape was worth recording because it reads as something it is not:

```text
completed/failure   required-checks / validate
completed/failure   required-checks / required-checks-gate
completed/skipped   release
completed/skipped   publish-npm
```

A run-level summary of "failed" is ambiguous about whether anything was published. The publish job
being **skipped** is the unambiguous signal that the artifact was never released.

## Things that did not work

- **Re-running the failed run.** It re-executed the same stricter invocation against the same
  tagged commit and failed with the same numbers. A re-run cannot clear a defect that lives in the
  commit the tag points at.
- **Mirroring the branch path's gate onto the release path.** The natural-looking move, given the
  general convention that a release path must enforce the same gate as the pull-request path. In
  this direction it is actively harmful: it would delete the coverage floor from every future
  release. The convention is directional and only valid when the release path is the weaker one.
- **Waiting for the branch to go red.** The branch path does not run that gate, so it stays green
  indefinitely and provides no confirmation either way.
- **Lowering the floor so the release went green.** A validation bypass that hides the next gap.

## Re-cut outcome

The repair landed on the default branch through a normal pull request, and only then was the tag
replaced on the fixed commit. The re-triggered run cleared `verify-release-trust`, the validation
job, and the aggregate required gate. The publish job moved from **skipped** to running.

One gate remained open at capture time and is independent of the coverage repair: the release
environment required a reviewer, so the publish jobs waited for a human approval. The CI gates were
green; the environment gate was still pending.

## Verification performed

- The stricter invocation was reproduced locally in the same container image the release job uses,
  before and after the repair, with the per-module coverage number read from the report both times.
- The re-triggered run's job conclusions were read individually to confirm the publish job ran
  rather than skipped.
- The tag's signature verification state was read from the forge, and the tag's target commit was
  confirmed to be the merge commit that carried the repair.
