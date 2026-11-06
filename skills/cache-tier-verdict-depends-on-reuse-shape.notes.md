# Notes: Cache Tier Verdict Depends On Reuse Shape

Privacy-safe supporting evidence for
[cache-tier-verdict-depends-on-reuse-shape](cache-tier-verdict-depends-on-reuse-shape.md).
Project, model, host, queue, job, and issue identifiers are withheld.

## Measured shapes

Two shapes were used with the same request count and the same
per-request token total, so the stream caps stayed comparable.

| Shape | Construction | Reuse |
| --- | --- | --- |
| No reuse | Random token stream per request | None. Cache cleared before each level. |
| Maximum reuse | One long shared system prompt, then a shorter distinct question per request | Every request after the first shares the long prefix. |

A real workload with a mix of prefixes lands between the two.

## Measured results

Per-unit throughput at each configuration's own saturation
point, in output tokens per second per accelerator.

| Configuration | No reuse | Shared prefix | Ratio |
| --- | ---: | ---: | ---: |
| Plain, two-slice topology | 64.8 | 201.0 | 3.1x |
| Plain, one-slice topology | 48.2 | 170.6 | 3.5x |

The ratio is the workload shape effect. It is larger than every
other change measured in the same campaign, including the
parallelism choice, the attention-backend choice, and every
speculative-decoding option.

## Tier effect within each shape

Each figure is the tiered row against the plain row of the same
shape, in output throughput. The tiers are a host-memory cache
tier on its own, and that tier plus a network storage tier.

| Tier | No reuse, two-slice | Shared prefix, two-slice | No reuse, one-slice | Shared prefix, one-slice |
| --- | ---: | ---: | ---: | ---: |
| Host-memory tier | -7.8% | -0.5% | -1.1% | +4.0% |
| Host + storage tiers | -5.3% | +6.0% | -8.0% | -9.7% |

Every no-reuse cell is a loss. The shared-prefix column is the
only place a tier gains, and the two topologies disagree about
which tier does it. Under shared-prefix load the host-memory
tier gains on the one-slice topology and loses on the
two-slice topology, while the combined tier does the opposite.

Each cell is one run. The spread between topologies is larger
than the tier effect, so no cross-topology tier ranking is
claimed, and neither topology should be tuned from these cells
alone. A repeat run would settle it.

## Why the plain shared-prefix row captures most of the gain

The serving engine runs a prefix cache by default. A request
whose long prefix is already resident skips the prefill for
that prefix without any host or storage tier. The evidence is
the first-token time distribution:

- Plain no-reuse: minimum 3.60 s, median 10.67 s.
- Plain shared-prefix: minimum 0.90 s, median 4.94 s.

The low minimum is a request served from the device cache. The
warm median is the wave after the first request populated the
prefix.

## Capacity claim that did not hold

The first tier run, under a job memory limit that was too small,
allocated a fraction of the intended host pool and the engine
reduced its request cap by about a third. That produced a real
capacity loss and a real throughput loss, but it was an artifact
of the memory limit, not a property of the tier.

After the job memory limit was raised so the intended pool size
fitted, the engine kept the same request cap and the same device
token count as the plain row. The lesson: read the engine's
request cap under each tier. A host tier adds tokens that the
engine may not schedule, and a pool that does not fit its own
job limit silently shrinks.

## Client reporting trap

The benchmark client reported a per-request error list with one
entry per request. Read literally it looked like every request
failed. The entries were empty strings, which means no error was
recorded. The completed-request count and the success line
agreed with a clean run. Confirm a failure from the completed
count and the exit record before discarding a run.