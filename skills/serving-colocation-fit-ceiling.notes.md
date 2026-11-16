# Notes: serving-colocation-fit-ceiling

Supporting evidence for the main skill. Internal identifiers, model names, paths, and issue
numbers are intentionally omitted; the arithmetic below uses public-equivalent values that
preserve each decision branch.

## Evidence chain that led to the ceiling change

1. A serving pool of large-model replicas began failing with `FAILED 9:0` (SIGKILL) after a
   host-side cache tier was changed from a fixed size to a ratio of the device pool. Scheduler
   accounting showed the engine step's peak RSS saturating at the per-job memory request
   (~99.8% of it) before the kill. A pre-change baseline job of the same shape had run for days
   at ~74% of the same request. This is a host memory-cgroup OOM signature, distinct from a
   device (GPU) OOM: device OOMs appear in engine logs as allocation failures, while host memcg
   OOMs appear as signal-9 step deaths with peak RSS at the request.
2. The remediation raised the per-replica host-memory request. Review of that remediation found
   the derived co-location side effect described in the main skill: the new request crossed
   half the per-node capacity ceiling, and the derived replicas-per-node count dropped from two
   to one.
3. The first ceiling raise used a round number above the exact multiple. It restored the count
   but left phantom headroom between the declared ceiling and the real packed claim, which
   triggered a reviewer question about whether an unrelated control-plane job still fit on a
   fully packed node.
4. The follow-up set the ceiling to the exact multiple `N * request`. Fit questions were then
   answered with real-request arithmetic (sum of real per-job requests plus the control-plane
   job's own request, against node RAM), not with ceiling subtraction.

## Validation evidence

- Before/after derivation sweep with the platform's own `derived_replicas_per_node`-style
  function over all 36 profiles, old ceiling vs new exact-multiple ceiling: 36/36 derived
  counts identical. This is the check that makes a ceiling retune behavior-preserving for
  placement.
- Focused configuration and render suites, including the platform's canonical derived-count
  pin sweep: 1225 passed, 0 failed.
- `git diff --check` on the one-line config change: clean.

## Fit table shape used in the change description

| Replica request | Count at old ceiling | Count at new exact-multiple ceiling |
| --- | --- | --- |
| packed pair member (edited) | 2 (restored by the first raise) | 2 |
| largest single-node profile | 1 | 1 |
| half-node profile | 2 | 2 |
| small profiles | unchanged | unchanged |

The table's purpose is to show that only the intended derivation moved. Include every distinct
request size, not every profile name, when profiles share request sizes.

## Decision branches worth keeping

- If placement of other services uses live free memory and real requests, a ceiling retune does
  not change any real claim; do not block it on reservation-style arithmetic.
- If a platform instead places against the declared ceiling, the same retune changes real
  placement feasibility and needs the stricter review. Check the mechanism before answering.
- An exact-multiple ceiling is self-documenting only when the config comment states the
  derivation (`ceiling = N x request`) and the remaining reserve below node RAM.
