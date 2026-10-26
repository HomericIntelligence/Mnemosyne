# Notes — background-agent-silent-lane-wait-or-replace

Supporting measurements from the issue-backlog orchestration drive that produced the
skill. Kept out of the main entry per the retrieval-bounded rule. No repository names,
issue identifiers, paths, or hostnames appear here.

## Measurement window

Two consecutive days in October 2026, one agent host, fleet-wide concurrency of many
parallel agent sessions. Host signal during the windows: agent daemon at ≈46%
sustained CPU; system load average ≈7 on a comparable core count.

### Lane set 1 (one issue, three dispatch attempts)

- Lane A: dispatched; worktree created; zero visible output for ≥45 minutes. The
  orchestrator diagnosed a wedge and held at a first threshold. Lane A completed in
  ≈5.5 hours and delivered a merge-grade pull request (later merged).
- Lane B (replacement for the presumed wedge): dispatched on a second branch. Lane B
  also completed in ≈5.5 hours and delivered a duplicate pull request against the same
  plan. The duplicate was closed as superseded after Lane A's pull request merged. The
  review effort ran twice for one issue.
- Lesson: both lanes were load-slowed. The zero-output phase was identical in both
  (≈45–60 minutes), and both recovered without any intervention.

### Lane set 2 (next issue, applied policy)

- Dispatched with the measured budget in place: no replacement before a 2-hour silence.
- First visible artifacts at ≈1 hour 59 minutes after worktree creation. Edits landed
  strictly inside the assigned file ownership; focused test cycles followed at
  ≈10-minute spacing; the lane then produced its first signed commit and staged the
  remaining plan steps.
- Mid-run, the lane parked its session on its own background shell (a full test-file-
  set run) and emitted an interim structured report. The session auto-resumed on the
  shell's native completion notification and continued the pipeline (commits, pull
  request, review) without orchestrator contact.
- Lesson: interim "partial" completion with a pending background shell is a hold-over
  point in the lane lifecycle, not a failure and not a final report.

## Probe commands used (passive sampling)

```bash
# file-system signal in the lane, excluding .git and __pycache__ noise
find <lane-worktree> -type f -newermt "<UTC time>" ! -path "*/.git/*" ! -path "*__pycache__*" -printf '%T+ %p\n' | sort -r | head -6
# uncommitted lane state
git -C <lane-worktree> status --porcelain
# lane commits vs the fresh base
git log --oneline origin/main..<lane-branch> --no-decorate
# remote head (did the lane push?)
git ls-remote --heads origin <lane-branch>
# spawned work (tests, runners) with elapsed seconds
ps -eo etimes,args | grep -E "(pytest|to-probe-pattern)" | grep -v grep
# host load signal
uptime; ps -eo pcpu,args --sort=-pcpu | head -5
```

## Threshold derivation

- Silence budget = 2 × (longest measured zero-output phase of a completed sibling lane
  under the same load). Measured siblings: ≈45–60 minutes and ≈120 minutes; a
  conservative orchestration budget rounded to "escalate beyond ≈2 hours of zero
  output with no host-side generation signal".
- Below the budget: sample every 10–15 minutes, no prompts, no churn.
- Beyond the budget: escalate with the sampled evidence; replace only as the last
  action, on a new branch, with a duplicate-PR guard instruction.

## Anti-collision instruction given to a replacement or a fresh lane

- Before any PR creation, search open pull requests for the issue. If a PR exists and
  is not a release-train, stop and report "BLOCKED: duplicate PR appeared" instead of
  pushing.
- If the lane receives commits or edits that its own session did not create, stop and
  report "BLOCKED: foreign writes"; never push over a foreign head.

## Related decisions already covered elsewhere

- Classifying a failing test as introduced vs pre-existing: re-run the same selector
  against a pristine base checkout; do not claim either without that evidence. Use the
  existing CI-failure-triage guidance in the corpus for the full procedure.
- Trust-but-verify gates for lane pull requests (file set, review trail, labels, merge
  state): use the orchestration recipe that owns the lane set.
