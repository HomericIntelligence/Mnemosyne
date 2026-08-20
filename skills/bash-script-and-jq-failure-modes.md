---
name: bash-script-and-jq-failure-modes
description: "Diagnose and fix silent failures in bash scripting and jq under strict error-checking modes. Use when: (1) a bash script with set -euo pipefail exits unexpectedly mid-loop or mid-function, (2) grep finds no matches and kills the script via pipefail, (3) bash arrays crash with 'unbound variable' despite being declared, (4) exit 127 appears and all binaries are installed, (5) jq // operator silently drops boolean false values, (6) jq fails with syntax errors on array concatenation with conditionals, (7) Bash cwd drifts from absolute-path editing in multi-worktree sessions, (8) set -m plus a single-command subshell silently loses continuation, (9) gh API stderr corrupts JSON captured for jq."
category: debugging
date: 2026-06-13
version: "2.0.0"
license: BSD-3-Clause
verification: verified-ci
user-invocable: false
history: bash-script-and-jq-failure-modes.history
tags: [bash, pipefail, set-euo, grep, array, exit-127, shell-function, jq, boolean, cwd, worktree, set-m, job-control, subshell, stderr, command-substitution, gh-cli, integration-test, ruff, D401]
---

# Bash Script and jq Failure Modes Under Strict Error Checking

## Overview

Use trace evidence and shell/jq semantics to diagnose scripts that exit, skip work, or produce
empty data under `set -euo pipefail`. The canonical rules are `verified-ci`; project-specific
reproductions and their verification are indexed in
[the notes](bash-script-and-jq-failure-modes.notes.md).

## When to Use

- A strict Bash script stops after `grep`, an arithmetic increment, array access, function call,
  command substitution, or a single-command subshell.
- Exit 127 occurs although expected binaries are installed or a sourced function was renamed.
- jq drops a JSON `false`, fallback after `select` never fires, or conditional array concatenation
  fails on the repository's jq version.
- An API command captured with `2>&1` feeds warnings or debug traces into jq.
- File reads and Bash verification disagree across multiple worktrees.
- A subprocess test needs a controllable `gh` stub, or ruff D401 rejects a private helper.

First reproduce with the same shell, options, jq version, environment, and working directory as
the failing consumer. Do not use these patterns for malformed JSON or a genuinely missing binary
without confirming the distinct cause.

## Verified Workflow

### Quick Reference

```bash
# Trace the first missing continuation or failing command.
bash -x <script> <args> 2>trace.log

# Make grep no-match nonfatal without hiding loop failures.
if grep -q '<pattern>' "$file"; then
  while IFS= read -r line; do process "$line"; done < <(grep '<pattern>' "$file")
fi

# Initialize nounset-safe arrays and counters.
local -a failures=()
count=$((count + 1))

# Preserve boolean false; default only null/missing.
jq -r '.converged | if . == null then "" else tostring end'

# Capture machine-readable stdout separately from diagnostics.
if ! raw=$(gh api "repos/${owner}/${repo}"); then
  echo 'gh api failed' >&2
  return 1
fi
printf '%s' "$raw" | jq .
```

### 1. Diagnose exit 127 by trace, not surrounding noise

Exit 127 can mean a missing external command or an orphaned shell function. Run `bash -x` and find
the last traced command. An explicit `command not found` identifies the missing executable; an
abrupt stop at a bare function call after a library refactor suggests a removed function.

```bash
git log --all --oneline --grep='<function-name-stem>'
git show <commit>:<library> | rg -n -A 40 '^<old_function>\(\)'
```

Restore the required implementation when callers still depend on it. If a new public function
supersedes the old name, keep the old implementation and make the new name delegate until all
callers migrate. Do not diagnose from unrelated help text on stdout.

### 2. Distinguish benign non-match from pipeline failure

`grep` returns 0 for matches, 1 for no matches, and 2 for an error. With `errexit` and `pipefail`,
1 aborts a pipeline before the script can apply its intended “not found” logic. Guard with
`grep -q`, then use process substitution as shown above. Avoid `... | while ...; done || true`:
that swallows failures from the loop body as well as the benign grep result.

Arithmetic commands also expose status: `((count++))` returns 1 when the expression evaluates to
zero. Prefer `count=$((count + 1))`, or narrowly use `((count++)) || true` when the status is
deliberately irrelevant.

### 3. Initialize arrays under nounset

`local -a items` declares a type but can remain unset. `${#items[@]}` and `${items[0]}` then fail
under `set -u`. Initialize at declaration:

```bash
local -a failed_items=()
local -i failure_count=0
```

Fix the invariant once instead of scattering `[[ -v ARRAY ]]` guards across consumers.

### 4. Preserve jq booleans and empty-stream fallbacks

jq's `//` selects its right side when the left is either `null` or `false`. Therefore
`.converged // empty` drops a valid false. Use an explicit null test when false is data:

```jq
.converged | if . == null then "" else tostring end
```

For a selection, `select` can emit no value at all, so a downstream `//` never executes. Collapse
the stream before applying the fallback:

```jq
first(.[] | select(.name == $name) | .status) // "unknown"
```

Keep a shell fallback such as `result="${result:-unknown}"` only when an empty string is also
invalid by contract.

### 5. Support the repository's jq version

Some older or patched jq builds reject inline array concatenation around conditional expressions.
When compatibility is required, construct JSON in Bash and pass it through `--argjson`:

```bash
files_json='["path/to/required.sh"'
if [[ "$condition" == true ]]; then files_json+=', "path/to/optional.sh"'; fi
files_json+=']'
jq -n --argjson files "$files_json" '{files: $files}'
```

Validate the generated JSON before using it; do not interpolate untrusted strings into this
pattern. For arbitrary values, build JSON with jq arguments rather than manual quoting.

### 6. Anchor multi-worktree commands

When file inspection and Bash disagree, print the active roots before editing or verifying:

```bash
pwd
git rev-parse --show-toplevel
git worktree list
realpath <file>
git log -1 --oneline -- <file>
```

Prefer `git -C /absolute/worktree ...` or `(cd /absolute/worktree && command)` so a directory change
cannot leak. Absolute-path reads do not prove a later relative Bash command sees the same copy.
Move a stray commit with a reviewed `git cherry-pick`; do not discard the original branch during
diagnosis.

### 7. Detect lost continuation after a subshell

With job control (`set -m`) and a single-command `(...)` subshell ending in an external command,
Bash may exec-replace the subshell. If the trace shows the phase start and child completion but no
command after the subshell, additional `set +e` cannot help because continuation never runs.

```bash
set -E
trap 'echo "ERR line=$LINENO rc=$? cmd=$BASH_COMMAND" >&2' ERR
trap 'echo "EXIT line=$LINENO rc=$?" >&2' EXIT
```

Restructure into a real function and ensure the child command is not the lone trailing command. If
three or more interacting mechanisms (`errexit`, job control, RETURN/ERR traps, nested subshells,
manual defanging) are required, replace the orchestrator with a structured subprocess loop in a
language with explicit control flow.

### 8. Keep stderr out of JSON

Never use `2>&1` inside a command substitution whose value is parsed as JSON. `gh` may emit update,
deprecation, rate-limit, or `GH_DEBUG` lines to stderr on a successful request. Capture stdout only;
on failure, let the command's stderr remain visible and emit a contextual error that does not quote
the empty capture.

To prove contamination, separate the streams:

```bash
raw=$(GH_DEBUG=1 gh api "repos/${owner}/${repo}" 2>/tmp/gh.stderr)
jq . <<<"$raw"
sed -n '1,20p' /tmp/gh.stderr
```

### 9. Test shell integrations at the process boundary

For a Python integration test that sources a Bash snippet, define and export a Bash function named
`gh` in the same shell. Make it write JSON to stdout and optional advisory noise to stderr, then
source the script and call the target. `export -f gh` avoids a fake binary and verifies stdout/
stderr separation. The Python helper docstring must begin with an imperative verb even when its
name begins with an underscore.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --- | --- | --- | --- |
| Pipeline-wide `|| true` | Suppressed a grep/while pipeline | It also hid real loop-body failures | Guard grep and use process substitution |
| Declared-only array | Used `local -a ARRAY` under nounset | The array remained unset | Initialize with `=()` |
| Boolean `//` fallback | Used `.field // empty` for a boolean | jq treats false like null for this operator | Test null explicitly |
| Inline conditional array | Used jq `] + (if ...` syntax | The deployed jq rejected it | Use a compatible `--argjson` construction |
| More `set +e` | Defanged errexit after a lone subshell | No continuation ran after exec replacement | Restructure control flow |
| Captured `2>&1` | Mixed `gh` diagnostics with API JSON | jq received a non-JSON prefix | Capture stdout only |
| Relative verification path | Grepped from a stale worktree cwd | It inspected a different file than the editor | Anchor the worktree and path |
| “Helper to” docstring | Described a private Python test helper | ruff D401 still applied | Use an imperative opener |

## Results & Parameters

| Failure signature | Required rule |
| --- | --- |
| Exit 127 | Trace to distinguish missing binary from missing function |
| grep no-match | Treat status 1 as benign only at the grep boundary |
| Nounset array | Initialize with `=()` before every read |
| Counter under errexit | Assignment form or narrowly guarded arithmetic command |
| JSON boolean | Explicit null test; preserve false |
| Empty selection | `first(stream) // fallback` |
| Machine output | stdout only; diagnostics on stderr |
| Worktree commands | Explicit absolute root or `git -C` |
| Silent subshell return | Trace ERR/EXIT, then restructure rather than defang |
| Private docstring | Imperative first line for D401 |

## Companions

- [Case index and detailed verification](bash-script-and-jq-failure-modes.notes.md)
- [Version history and superseded content](bash-script-and-jq-failure-modes.history)
