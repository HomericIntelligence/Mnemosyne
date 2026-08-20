# Bash Script and jq Failure Modes — Notes

Supporting case evidence for
[`bash-script-and-jq-failure-modes`](bash-script-and-jq-failure-modes.md). The exact 30,074-byte
v1.2.0 main is archived once in
[`bash-script-and-jq-failure-modes.history`](bash-script-and-jq-failure-modes.history), with
SHA-256 `27c5a2d2f8b7a3068a9c623794064736164ab4e275fc5b29fbea52f5e2e2a1bc`.

## Case Index

| Case | Source | Verification status | Reusable result |
| --- | --- | --- | --- |
| grep no-match under `pipefail` | [Myrmidons PR #564](https://github.com/HomericIntelligence/Myrmidons/pull/564) | verified-ci | Guard grep and use process substitution |
| Nounset arrays and jq false serialization | [Myrmidons PR #623](https://github.com/HomericIntelligence/Myrmidons/pull/623) | verified-ci | Initialize arrays with `=()` and test null explicitly |
| Exit-127 function recovery | [Immutable v1.2.0 source](https://github.com/HomericIntelligence/Mnemosyne/blob/10e28497993009cc221cb991e1ee183e6117eda8/skills/bash-script-and-jq-failure-modes.md) | verified-local; later consolidated status remains `verified-ci` | Use `bash -x` to distinguish missing functions from binaries |
| Older-jq conditional array syntax | [ai-maestro issue #272](https://github.com/23blocks-OS/ai-maestro/issues/272) | verified in reported environment | Build compatible JSON and pass through `--argjson` |
| Multi-worktree cwd divergence | [Immutable v1.2.0 source](https://github.com/HomericIntelligence/Mnemosyne/blob/10e28497993009cc221cb991e1ee183e6117eda8/skills/bash-script-and-jq-failure-modes.md) | verified-local | Anchor every shell command to the intended worktree |
| Job-control/subshell continuation loss | [Immutable v1.2.0 source](https://github.com/HomericIntelligence/Mnemosyne/blob/10e28497993009cc221cb991e1ee183e6117eda8/skills/bash-script-and-jq-failure-modes.md) | verified-local replacement | Trace ERR/EXIT, restructure, or replace a brittle orchestrator |
| `gh api` stderr corrupting jq input | [ProjectHephaestus issue #1122](https://github.com/HomericIntelligence/ProjectHephaestus/issues/1122) and [PR #1273](https://github.com/HomericIntelligence/ProjectHephaestus/pull/1273) | verified-ci | Keep diagnostic stderr out of captured JSON |
| Exported-function `gh` test stub and D401 | [ProjectHephaestus PR #1273](https://github.com/HomericIntelligence/ProjectHephaestus/pull/1273) | verified-ci | Test both streams without a fake binary; use imperative docstrings |

## Detailed Case Notes

### Myrmidons strict-mode failures

The grep hook stopped before its intended else branch because no-match status 1 propagated through
`pipefail`. A pipeline-wide `|| true` appeared attractive but would also mask failures in the loop.
In a separate case, a declared-but-uninitialized failure array crashed at its first length read,
and jq's alternative operator replaced a valid false. These cases validate three distinct language
semantics rather than one generic “strict mode” fix.

### ProjectHephaestus JSON boundary

The merge-method probe captured `gh api ... 2>&1`; advisory stderr prefixed otherwise valid JSON,
so jq produced an empty result and the caller reported that a valid repository allowed no merge
method. PR #1273 preserved stdout as the data channel and tested realistic stderr noise through an
exported Bash `gh` function. Its private Python test helper also established that D401 applies to
underscore-prefixed functions.

### Shell complexity escape hatch

The job-control case combined `set -euo pipefail`, `set -m`, RETURN/ERR/EXIT traps, manual errexit
defanging, and a trailing external command inside a subshell. Once control-flow correctness depends
on several interacting shell options, a structured subprocess loop can be a smaller and more
testable fix than another local shell patch. This is a decision threshold, not a rule that every
shell script should be rewritten.

## Verification Checklist

- Reproduce with the failing Bash/jq versions and the same option set.
- Save `bash -x` around the first missing continuation, not only user-facing stdout.
- Test grep match, no-match, and actual error separately.
- Test JSON `true`, `false`, `null`, missing field, empty selection, and stderr noise.
- Verify the absolute worktree root before and after every cross-worktree command.
- For shell-to-Python rewrites, retain exit codes, signals, stream routing, and phase ordering.
