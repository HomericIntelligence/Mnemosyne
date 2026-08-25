# Troubleshooting Guide Template

Use this template to map errors to solutions.
Write active technical prose according to the
[Mnemosyne ASD-STE100 writing policy](../../../../docs/asd-ste100.md).
Preserve exact errors, commands, configurations, outputs, and quotations.

## Common Issues

### Category: [Training Errors]

#### Issue 1: [Error Name]

**Symptom**: [Observable behavior]
**Cause**: [Why it happens]
**Solution**: [How to fix]
**Prevention**: [How to avoid]

#### Issue 2: [Error Name]

Use the same structure.

### Category: [Infrastructure Errors]

[Add more issues.]

## Debugging Checklist

Before you file an issue, complete these checks:

- [ ] Verify that the environment uses the documented versions.
- [ ] Verify that the dataset has the correct format.
- [ ] Make sure that the hardware has sufficient resources.
- [ ] Validate the configuration file.
- [ ] Install all required dependencies.

## Quick Reference

| Error Pattern | Likely Cause | Quick Fix |
| -------------- | -------------- | ----------- |
| OOM errors | Batch too large | Reduce batch_size by 50% |
| NaN loss | Learning rate too high | Reduce LR by 10x |
| Slow convergence | LR too low | Increase by 2-5x |
