# Notes: Hybrid-SSM Prefix-Cache Retention

Privacy-safe supporting evidence for
[hybrid-ssm-prefix-cache-retention](hybrid-ssm-prefix-cache-retention.md).
Project, model, host, job, dataset, and issue identifiers and private
measurements are withheld.

## Controlled observations

The server used one accelerator and one running request. The prompts were
distinct, and the same checkpoint and decoding limits were held constant.
The cache unified full-attention KV and recurrent-state retention.

| Arm | Cache configuration | Observed result | Decision |
| --- | --- | --- | --- |
| Initial | Prefix retention enabled; initial static-memory fraction | Device memory grew across successful serial requests until a scheduler out-of-memory error ended the workload | Reject the partial result and investigate cross-request retention |
| Reduced allocation | Prefix retention enabled; lower static-memory fraction | More requests completed, but the same growth ended in an out-of-memory error | Classify the change as a delay, not a repair; reject the partial result |
| Prefix retention disabled | The same lower static-memory fraction with radix caching disabled | The performance run and both full evaluation datasets completed without a server resource error | Retain as a validated configuration workaround and rerun matched performance measurements |

The failed arms produced valid responses before failure. Those responses were
not combined with later runs and were not used for reported accuracy.

## Control semantics and evidence boundary

The observed recovery used the engine's global radix-cache disable switch.
For the tested cache implementation, this skips completed-prefix insertion
and lets finished-request recurrent state leave the retention path. The A/B
result therefore supports prefix retention as the operative trigger.

The separate recurrent-cache `no_buffer` strategy was not measured as a
recovery arm. Public engine semantics keep prefix caching enabled under this
strategy while changing recurrent-state buffering and checkpoint behavior.
It must not be reported as equivalent to global cache disablement. Engine
versions can change these controls, so the effective arguments and installed
version's documentation remain part of a reproduction record.

The evidence does not identify the exact faulty ownership, insertion, or
eviction line. It also does not show that every hybrid model or prefix-cache
implementation has the same defect. A root-cause report needs cache-component
occupancy and ownership evidence, plus a minimal reproducer.

## Reproduction record

Keep these fields with each arm:

- engine and cache implementation versions;
- effective prefix-cache and recurrent-buffer arguments;
- model architecture class and accelerator memory capacity;
- serial concurrency and distinct-prompt statement;
- warm-up, request-order, and output-limit controls;
- memory and cache-occupancy samples after warm-up;
- active and completed request counts at failure;
- full-run completion and error audit; and
- matched performance from the accepted configuration.

Do not publish private identifiers or measurements to make the pattern
reusable. The decision rule depends on the controls and observed lifecycle,
not on the private run identity.
