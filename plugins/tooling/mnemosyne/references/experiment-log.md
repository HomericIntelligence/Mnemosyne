# Experiment Log Template

Use this template to record an experiment in detail.
Write active technical prose according to the
[Mnemosyne ASD-STE100 writing policy](../../../../docs/asd-ste100.md).
Preserve exact values, commands, configurations, outputs, and quotations.

## Experiment: [Name]

**Date**: YYYY-MM-DD
**Objective**: [State what you want to learn]
**Hypothesis**: [State the expected result]

### Environment

| Item | Details |
| ------ | --------- |
| Hardware | [GPU model, RAM, CPU] |
| Software | [Framework versions, OS] |
| Dataset | [Name, size, splits] |
| Baseline | [Reference performance] |

### Parameters

```yaml
# Copy-paste ready configuration
param1: value1
param2: value2
```

### Results

| Run | Config | Metric | Notes |
| ----- | -------- | -------- | ------- |
| 1 | baseline | 85.3% | [Observations] |
| 2 | +changes | 87.1% | [Observations] |

### Failed Runs

| Run | Config | Error | Root Cause | Fix |
| ----- | -------- | ------- | ------------ | ----- |
| 3 | x=10 | OOM | Batch too large | Reduce to x=5 |

### Conclusions

**What Worked**:

- [List the successful approaches]

**What Failed**:

- [List each failed approach and its cause]

**Next Steps**:

- [List the next actions]
