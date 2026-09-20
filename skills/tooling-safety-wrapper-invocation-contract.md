---
name: tooling-safety-wrapper-invocation-contract
description: "Construct complete arguments for safety-sensitive wrappers and classify failures before a retry or recovery."
category: tooling
date: 2026-09-11
version: "1.1.0"
user-invocable: false
tags: [wrapper, cli, argparse, remainder, preflight, retry, cleanup, fail-closed]
history-source: "https://github.com/HomericIntelligence/Mnemosyne/blob/e98a4da5d67f0766bc6b4bfaed1ab399fca90e9f/skills/tooling-safety-wrapper-invocation-contract.history"
history-cleanup-date: "2026-09-19"
---

# Safety-Sensitive Wrapper Invocation Contract

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-09-11 |
| **Objective** | Construct the complete wrapper argument vector before the first call. |
| **Outcome** | The wrapper validates its dependency, forwards the intended arguments, and stops safely after an unclassified failure. |

## When to Use

- A wrapper has one or more arguments for its own validation step.
- The wrapper forwards the remaining arguments to a second command.
- The second command can change or delete state.
- The wrapper contract prohibits a retry after a nonzero result.
- An operator knows the downstream command but has not inspected the wrapper interface.

## Verified Workflow

### Quick Reference

```bash
python3 <wrapper-path> --help
python3 <wrapper-path> <dependency-checkout> <forwarded-argument> ...
```

After a nonzero result, preserve the diagnostic and inspect whether the downstream action began.
If the applicable wrapper contract explicitly forbids retries, withhold that retry and continue
independent work. Otherwise, a corrected retry can use existing authorization when evidence shows
that it is safe and within scope.

### Detailed Steps

1. Read the applicable operation contract before you run the wrapper.
2. Run the wrapper with `--help` if the operation contract permits this read-only call.
3. Identify each wrapper-owned positional argument and option.
4. Identify the boundary where the forwarded argument vector starts.
5. Inspect the wrapper source when `--help` does not show the forwarding boundary clearly.
6. Resolve and validate each wrapper-owned dependency before the operation.
7. Construct the complete argument vector as a list. Do not infer it from the downstream command syntax.
8. Keep standard input attached when the downstream command must ask the operator for a decision.
9. Run the complete invocation within the operation contract.
10. If the result is nonzero, preserve the status and diagnostic output.
11. Classify the failure and side effects. Use existing authorization for a safe, permitted retry;
    seek new authorization only when the operation contract or changed scope requires it.
12. Confirm the final state before you report that cleanup or another state change is complete.

For a Python wrapper that uses one dependency argument and
`argparse.REMAINDER`, use this shape:

```python
parser.add_argument("dependency_checkout")
parser.add_argument("arguments", nargs=argparse.REMAINDER)
```

The call must put the dependency checkout before all forwarded arguments:

```bash
python3 <wrapper-path> <dependency-checkout> <downstream-option> <value>
```

Do not call the wrapper as if it were the downstream command.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Downstream-only call | The operator called the wrapper without its dependency-checkout argument. | The wrapper parser stopped with a missing positional-argument error before it started the downstream command. | Inspect the wrapper interface and include wrapper-owned arguments before forwarded arguments. |
| Immediate corrected retry | The operator planned to add the missing argument and run the command again. | A no-retry contract makes the first nonzero result terminal for that operation. The initial failure does not prove that a second execution is safe. | For that explicit no-retry cleanup contract, preserve state and obtain a new authorized operation; continue independent work. |
| Infer syntax from the downstream command | The operator used only the downstream command documentation. | The downstream documentation does not describe dependency validation or the forwarding boundary in the wrapper. | Inspect both interfaces and construct one complete argument vector. |

## Results & Parameters

### Configuration

The recorded cleanup wrapper had an explicit no-retry contract. This example describes that
wrapper, not a default for all commands. For another wrapper, use its actual retry policy:

```yaml
wrapper:
  path: <wrapper-path>
  own_arguments:
    - <dependency-checkout>
  forwarded_arguments:
    - <downstream-option>
    - <value>
  stdin_attached: true
  retry_policy: no-retry-after-nonzero
```

Use `stdin_attached: true` only when the operation contract requires an
operator to answer prompts. Do not answer a destructive prompt automatically.

### Expected Output

A valid preflight gives these results:

- The help output identifies each wrapper-owned argument.
- The resolved dependency satisfies the wrapper's validation rule.
- The first state-changing call contains the complete argument vector.
- A nonzero result produces a clear diagnostic and a recovery choice based on side effects,
  retry safety, and the applicable operation contract.
- The completion report agrees with the observed final state.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Local automation session | A repository-cleanup wrapper stopped before downstream execution because its required positional arguments were absent. | The parser returned status 2. No cleanup action started. See the companion notes for privacy-safe evidence. |

## References

- [Exact argv admission at the subprocess boundary](tooling-command-admission-exact-argv-boundary-enforcement.md)
- [Automation agent tool scopes](automation-agent-tool-scopes-least-privilege.md)
