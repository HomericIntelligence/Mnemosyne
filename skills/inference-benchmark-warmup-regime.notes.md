# Notes: Inference Benchmark Warmup Regime

Supporting detail for [inference-benchmark-warmup-regime.md](inference-benchmark-warmup-regime.md).

These notes hold measurements and method detail. The main entry holds the rule.
Project, model, organisation, host, path, job, and issue identifiers are
withheld under the private and proprietary information rules.

## What was measured

Two inference replicas of one large mixture-of-experts model, identical image,
weights, topology, and prompt shape. The only difference was the cache-precision
setting. The comparison isolated one axis deliberately, so that a difference in
result could not come from two changed variables at once.

| Measurement | Warmup sample | Warm steady state |
| --- | --- | --- |
| Time to first token | about 3x the steady-state value | steady reference |
| Per-token latency | direction reversed against steady state | sign of the result |

The warmup sample sat roughly three times above steady state on time to first
token. That gap is the diagnostic: a first-request number that far above a later
number indicates warmup, not a serving regression.

## Significance arithmetic

After discarding the warmup sample, 19 repeats remained per configuration.
Standard deviations were small relative to the difference, which made the
comparison decisive.

```text
pooled_se = sqrt(stdev_a**2 / n_a + stdev_b**2 / n_b)
```

The per-token mean difference was about 25 times the pooled standard error, so
the reversed direction was treated as real rather than as scatter. Had the
difference been within about 2 pooled standard errors, the correct output would
have been that the two configurations are indistinguishable, not a direction.

## Mistake that produced the retraction

An earlier comparison had been built on one request per configuration and
published with a statement that the candidate was faster on per-token latency.
That statement was wrong in direction.

Two independent errors combined:

1. The sample was taken immediately after the engine reported ready, so it
   measured kernel and graph warmup.
2. A percentage difference was reported without any variance test, so no check
   existed that could have caught the problem.

Either error alone would have been survivable. Together they produced a
published claim that reversed once measured properly.

The correction had to reach three places, because a correction in one place does
not correct a claim repeated elsewhere:

- the comparison report, where the superseded figure was marked withdrawn in
  place with the reason;
- the tracking issue, which carried the figure inside its body text; and
- the implementation brief, which repeated it as an evidence line.

## Prompt-shape detail

Repeats used a distinct prompt per sample, generated from a per-index seed. This
matters: reusing one prompt lets the prefix cache serve the tail of every later
sample, which biases per-token latency and deflates time to first token in
exactly the metric under test. A related sweep driver in the same engagement
seeded every worker from one shared base, so its concurrency figures were
discarded. See
[debugging-prefix-cache-nsight-kernel-evidence.md](debugging-prefix-cache-nsight-kernel-evidence.md)
for the cache-side evidence.

## Baseline that was never measured

A second withdrawn figure in the same engagement failed for a different reason.
The comparison divided the candidate result by a baseline value that no run had
produced. The value appeared nowhere in the retained results. The only place it
turned up was as incidental digit matches inside unrelated evaluation logs.

| Property | Observation |
| --- | --- |
| Baseline in retained results | absent |
| Only trace of the value | coincidental digit matches in unrelated logs |
| Consequence | the derived percentage described a configuration that was never run |
| Correction | figure marked withdrawn in place, with the reason stated |

The failure mode is not arithmetic. It is source resolution. A value that has
already been written into a document looks like a result, and reusing it feels
like consistency rather than error. The matching digits made the error feel
confirmed, which delayed the correction.

The retained results held the real baseline. Re-measuring against it changed the
reported direction on one metric, so the withdrawn figure did not merely have the
wrong magnitude.

Check that the baseline row is matched as well as present: same shape, same
topology, same image, one changed variable. A matched baseline removes the need
to attribute a difference to more than one cause.

## Harness detail worth reusing

The latency client accepted a loopback address only, so it worked inside the
serving job and not from a coordinating host. Adding a host override with the
loopback value as the default preserved the in-job behaviour while allowing
repeated measurement from outside. Prefer an environment-variable override over
a positional argument change when the existing invocation sites must keep
working.

## Coverage limit

The comparison covered one model, one topology, and one prompt shape. It shows
that the method matters for this case. It does not establish that a given
percentage difference holds for other models, quantisation choices, or prompt
distributions.