# Notes: ci-slow-test-phase-probe-ab-dispatch

Supporting evidence for the probe-and-measure workflow. All identifiers are
generalized; no repository, organization, issue, path, or product names.

## Source context

One CI nightly product profile spent roughly two thirds of its runner minutes
in one test module. A single shared helper built the same staged environment
for every case and ran the full application pipeline two to three times per
case. The investigation used the workflow in the main skill.

## Probe run measurements (generalized)

Per-case probe timeline from one focused dispatch (six slow cases, all
passing after the sink fix):

- Installer fixture build: about 1.3 s (cleared).
- Staging subprocess copy: about 4 s per round, three rounds per case
  (cleared as the primary cost).
- Directory permission walks over the staged tree: below measurable resolution
  (cleared).
- Owned preparation pipeline, round 1: about 81 s.
- Owned preparation pipeline, round 2 (the retry/resume round): about 150-170 s
  (the dominant share).
- Owned preparation pipeline, round 3: about 34-41 s.
- Final assertions: roughly 20 s.

Case totals ranged from about 150 s to about 320 s. The two or three
preparation rounds carried about 90 percent of every expensive case.

## A/B rejection record

Hypothesis: per-connection `synchronous_commit=off` on the disposable test
database service should remove the per-commit write-ahead-log flush wait and
speed up durable appends.

| Case class | Before (s) | After (s) | Delta (s) |
| ---------- | ---------: | --------: | --------: |
| Two-round guard cases | 168.9, 167.8 | 178.1, 178.4 | +9 to +11 |
| Three-round cases | 281.6 to 321.4 | 289.9 to 338.1 | +8 to +17 |

Total across the paired set: +69.2 s. Every case measured slower. Verdict:
the flush wait was not a meaningful share of the cost; the change was
reverted. The pipeline cost is CPU and subprocess work, not commit latency.

## Operational details that changed the outcome

- The pytest JUnit capture includes test-process stdout only when
  `junit_logging = "system-out"` (or `all`) is set; captured application output
  is separate and is asserted on by the tests.
- One direct `print` at a probe site was enough to keep polluting a single
  case after the sink existed; every probe call must go through the sink
  helper.
- A dispatch checkout failed with a remote "not our ref" error after a
  hand-assembled commit identifier; the full SHA must be copied from the
  pushed head, never reconstructed.
- Baseline per-case numbers came from the JUnit `time` attribute of the
  previous run's artifact, so the A/B comparison needed no new instrumentation.
