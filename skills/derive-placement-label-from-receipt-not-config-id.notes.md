# Notes: Derive Placement Labels From Receipts, Not Config IDs

## Provenance

Source evidence: one interactive session on 2026-11-01, during the publication of
an inference-throughput dataset measured on a shared GPU cluster. The session
found that a config id encoded only a total device count, and that the archive
tool built the topology label from that count alone. The main skill records the
generalized rule. These notes record the evidence shapes that did not fit the
main entry.

All cluster-specific and project-specific identifiers stay out of both files:

- cluster, partition, and host names;
- model, checkpoint, and dataset names;
- account and user identifiers;
- internal paths and repository names; and
- exact node, GPU, and memory totals.

Replace every `<placeholder>` with the value for the target environment.

## Environment Facts That Bound the Rule

The per-node ceiling was taken from the scheduler, not from the request:

| Fact source | What it showed | Why it matters |
| ------------- | ---------------- | ---------------- |
| Per-partition resource report | Every GPU partition advertised the same per-node generic-resource count | The ceiling is uniform, so a single constant is correct for this cluster |
| The same report across all partitions | No partition offered a larger single node | A single-node variant of the high count was physically impossible, not merely unsupported |

The practical consequence is the core rule: when no node exceeds
`<per_node_ceiling>` devices, any request above that ceiling resolves to exactly
one node count, and a single-node label for that request is a false claim about
the hardware rather than a formatting preference.

## The Two Refusal Branches

The ceiling check alone was not sufficient. A launcher that reserves one whole
node per rank
(`--gpus-per-node=<per_node_ceiling>` with `--ntasks-per-node=1`) never produces
a placement that leaves a node partly used. Both branches matter:

| Requested devices | Nodes | Label under ceiling-only check | Correct disposition |
| ------------------- | ------- | -------------------------------- | --------------------- |
| above ceiling | 1 | refusal | refusal: exceeds per-node ceiling |
| whole number of nodes x ceiling | node count | accepted | accepted |
| below ceiling x nodes | 2 | accepted (wrong) | refusal: not reachable by this launcher |
| ceiling, twice | 2 | accepted (wrong) | refusal: not reachable by this launcher |
| uneven split | any | refusal | refusal: does not split evenly |

Read the launcher's resource request before you decide the policy. If the
launcher ever gains a packing mode that fills nodes partially, the second branch
becomes valid and the rule must change with it.

## The Deferred-Label Design

The first implementation passed the node count into the parser with a default of
one. That looked sufficient but was not, because callers enter the pipeline at two
different points:

1. the stage collector, which parses every config before it reads any run; and
2. the per-run record builder, which is the first point where a receipt exists.

A parser default of one makes point 1 emit the same wrong label as before, so the
fix has to change the contract rather than add an argument. The working design:

- the parser reports the total device count and leaves the label empty, with the
  node count zero;
- the per-run builder fills both from the receipt;
- a missing or unreadable receipt yields one node, which matches all prior
  single-node evidence; and
- a placement that cannot be constructed yields a reported work item for that
  one run, not an abort of the whole pass.

## Collector Layout Widening

Correct labelling produced nothing until the collector also descended the
multi-node directory shape. Two layouts had to coexist:

```text
<config>/<sweep|anchor>/<probe>/result.json
<config>/<mode>-<plan>/c<k>/attempt-<job>/<probe>/result.json
```

A single `attempt-<job>` level had to be traversed inside both the new shape and
any capacity-probe shape. Probes nested deeper than one attempt level need an
explicit decision, because an unbounded descent risks double-counting.

## What Was Verified and What Was Not

Verified offline:

- the ceiling-labelled placement for a run above the ceiling was refused with a
  minimum node count in the message;
- the partial-node placements in the table above were refused;
- the canonical single-node counts kept their existing labels;
- the real multi-node receipt resolved to two nodes; and
- the module compiled.

Not verified before the session ended:

- the end-to-end collector walk in its final form;
- the per-run record builder against a real multi-node result set; and
- the publication path for the new label.

The end-to-end test did not complete, and the harness called the changed parser
with its old signature. That is a harness defect. Do not read it as a product
defect, and do not read the incomplete walk as a pass. The work was left
uncommitted in the source repository, and no dataset was published.

## Related Session Finding, Not Part of the Rule

A prior multi-node attempt for the same dataset reached full weight load and KV
allocation across both nodes before it failed on a shared compiled-kernel cache
race between ranks. The launcher had since received a per-node cache isolation
change that was never retested. That is a separate capacity-and-cache lesson, not
a placement-labelling lesson, and it is not recorded in the main entry.