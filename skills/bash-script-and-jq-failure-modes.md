---
name: bash-script-and-jq-failure-modes
description: "Diagnose and fix silent failures in bash scripting and jq under strict error-checking modes. Use when: (1) a bash script with set -euo pipefail exits unexpectedly mid-loop or mid-function, (2) grep finds no matches and kills the script via pipefail, (3) bash arrays crash with 'unbound variable' despite being declared, (4) exit 127 appears and all binaries are installed, (5) jq // operator silently drops boolean false values, (6) jq fails with syntax errors on array concatenation with conditionals, (7) Claude Code Bash cwd drifts from Read/Edit absolute paths in multi-worktree sessions."
category: debugging
date: 2026-05-19
version: "1.0.0"
user-invocable: false
history: bash-script-and-jq-failure-modes.history
tags:
  - bash
  - pipefail
  - set-euo
  - grep
  - array
  - exit-127
  - shell-function
  - jq
  - boolean
  - falsy
  - cwd
  - worktree
  - tool-divergence
  - json
---

# Bash Script and jq Failure Modes Under Strict Error-Checking

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-05-19 |
| **Objective** | Consolidate known failure modes in bash scripting and jq processing under set -euo pipefail and related strict modes |
| **Outcome** | Synthesised from 6 verified skills; all patterns confirmed in CI or local runs |
| **Theme** | Shell/jq behavior under error-checking modes silently produces wrong behavior, requiring the same class of defensive fixes |

## When to Use

- A bash script with `set -euo pipefail` exits silently mid-loop — especially around `grep \| while read` pipelines
- Bash exits with code 127 and all binaries (`yq`, `jq`, `curl`) are installed — function-not-found, not binary-not-found
- A sourced shell library was recently refactored and old function names were removed or renamed in a merge
- An array is declared (`local -a ARRAY`) but crashes with "unbound variable" when first accessed
- A jq expression using `//` returns empty when the JSON field holds `false`
- jq fails with `syntax error, unexpected '+', expecting '}'` on array concatenation with conditionals
- `Read` shows content that `grep` in Bash cannot find — or a commit lands on the wrong branch — in a multi-worktree session

Do NOT use when:

- The 127 originates from a bats test (different diagnostic path — bats wraps function calls differently)
- The jq error is unrelated to array concatenation (e.g., malformed JSON input)
- Only one git worktree is checked out (cwd divergence cannot occur)

## Verified Workflow

### Quick Reference

```bash
# --- EXIT 127: trace the missing function ---
bash -x tests/foo.sh 2>&1 | head -80
git log --all --oneline --grep='<function-name-stem>'
git show <sha>:scripts/lib/api.sh | grep -A 50 '^old_function_name()'

# --- GREP KILLING SCRIPT: guard before piping ---
# WRONG:
grep "pattern" "$file" | while read -r line; do process "$line"; done
# CORRECT (preferred):
if grep -q "pattern" "$file"; then
  while read -r line; do process "$line"; done < <(grep "pattern" "$file")
fi

# --- UNBOUND ARRAY: always initialize ---
# WRONG:
local -a FAILED=
# CORRECT:
local -a FAILED=()

# --- ARITHMETIC COUNTER: guard set -e ---
(( count++ )) || true
# or:
count=$(( count + 1 ))

# --- JQ BOOLEAN: never use // on booleans ---
# WRONG:
value=$(echo "$json" | jq -r '.converged // empty')
# CORRECT:
value=$(echo "$json" | jq -r '.converged | if . == null then "" else tostring end')

# --- JQ ARRAY CONCAT COMPATIBILITY: build array in bash ---
files_json="[\"${DIR}/file1.sh\"]"
if [[ "$condition" == "true" ]]; then files_json+=", \"${DIR}/extra.sh\""; fi
files_json+="]"
jq -n --argjson files "$files_json" '{ files: $files }'

# --- CWD DIVERGENCE: anchor at session start ---
cd /abs/path/to/main/worktree && pwd
git rev-parse --show-toplevel
git worktree list
```

### Failure Mode 1: Exit 127 — Orphaned Shell Function

Exit 127 in a bash test has two distinct causes: missing binary vs. missing function. The `-x` trace distinguishes them — a missing binary shows `command not found`; a missing function just stops.

1. Trace where the 127 fires: `bash -x tests/foo.sh 2>&1 | head -100`
2. Ignore misleading stdout (e.g., tool help text emitted in an unexpected context).
3. Search git history for the function:
   ```bash
   git log --all --oneline --grep='<function-name-stem>'
   git show <sha>:scripts/lib/api.sh | grep -A 50 '^old_function()'
   ```
4. Restore the function body and add a delegate shim so both old and new callers work.
5. Fix any co-located `jq select` fallback bugs (see Failure Mode 4).

### Failure Mode 2: grep No-Match Killing Script Under set -euo pipefail

`grep` exits 1 when it finds no matches. Under `set -e` + `pipefail`, this exit code is indistinguishable from a real error and aborts the script — the loop body is never entered, but the script also does not continue.

**Preferred fix — process substitution with guard:**

```bash
if grep -q "pattern" "$file"; then
  while read -r line; do
    process "$line"
  done < <(grep "pattern" "$file")
fi
```

**Alternative — temporarily disable pipefail:**

```bash
set +o pipefail
grep "pattern" "$file" | while read -r line; do process "$line"; done
set -o pipefail
```

Avoid `|| true` at the end of the whole pipeline — it silently swallows all errors inside the loop body, not just grep's exit 1.

### Failure Mode 3: Unbound Array Under set -u

`local -a ARRAY` and `declare -a ARRAY` *declare* the variable as an array type but leave it in an unset state. Under `set -u` (nounset), reading `${#ARRAY[@]}` or `${ARRAY[0]}` on an unset array triggers "unbound variable" and `set -e` exits immediately.

**Fix — one character:**

```bash
# WRONG:
local -a FAILED_AGENT_NAMES
# CORRECT:
local -a FAILED_AGENT_NAMES=()
```

**Pattern for tracking failures:**

```bash
my_function() {
  local -a FAILED=()
  local -i failure_count=0
  for item in "${ITEMS[@]}"; do
    if ! run_item "$item"; then
      FAILED+=("$item")
      (( failure_count++ )) || true  # arithmetic exit code guard
    fi
  done
  echo "Failures: ${#FAILED[@]}"
}
```

### Failure Mode 4: jq // Operator Dropping Boolean false

jq's `//` operator returns the right side when the left is `false` OR `null`. This traces to Perl's `||` semantics — unlike most JSON tools, jq treats `false` and `null` as equivalent "alternatives."

**jq manual (1.6+):** "The operator `//` produces its left-hand side if it is not `false` or `null`, and otherwise produces its right-hand side."

**Correct patterns by use case:**

```jq
# Serialize boolean to string (null-safe):
.converged | if . == null then "" else tostring end

# Default only for null/missing (not false):
(.converged // false) | tostring

# In object construction:
{convergence: (.converged | if . == null then null else tostring end)}
```

Also applies to `select` + fallback:

```bash
# WRONG — select filters out the row; // never fires on empty:
result=$(jq -r '.[] | select(.name == $name) | .status // "unknown"' ...)
# CORRECT — first() so fallback applies when no match:
result=$(jq -r 'first(.[] | select(.name == $name) | .status) // "unknown"' ...)
result="${result:-unknown}"   # shell-level fallback
```

### Failure Mode 5: jq Array Concatenation Syntax Error (Older jq)

`] + (if $var then [...] else [] end)` works on jq 1.6+ but fails on older versions with `syntax error, unexpected '+', expecting '}'`.

**Fix — build the array in bash:**

```bash
local files_json
files_json="[\"${INSTALL_DIR}/file1.sh\", \"${HELPERS_DIR}/file2.sh\""
if [[ "$condition" == "true" ]]; then
  files_json+=", \"${DIR}/optional.sh\""
fi
files_json+="]"

jq -n \
  --argjson files "$files_json" \
  '{ files: $files }'
```

### Failure Mode 6: Bash CWD Drifting from Edit/Read Absolute Paths

Claude Code's Bash tool persists cwd across invocations. Read/Edit/Write/Grep/Glob always use absolute paths verbatim. When a `cd <other-worktree>` appears in any Bash call, Bash commands silently operate on the sibling worktree while Edit/Read operate on the main worktree.

**Tool cwd behavior:**

| Tool | CWD-dependent? | Notes |
| ---- | -------------- | ----- |
| Bash | YES — persists across calls | Every `cd` leaks into the next Bash turn |
| Read | NO | Requires absolute path |
| Edit | NO | Requires absolute path |
| Write | NO | Requires absolute path |
| Grep | NO | Uses absolute or workspace-relative path arg |
| Glob | NO | Uses absolute or workspace-relative path arg |

**Prevention — anchor cwd at session start:**

```bash
cd /abs/path/to/main/worktree && pwd
git worktree list
git rev-parse --show-toplevel
```

**Prefer cwd-free patterns:**

```bash
git -C /abs/path/to/other/worktree status       # no cd needed
(cd /abs/path/to/other/worktree && cmd)          # subshell — does not leak
```

**Detection when results disagree:**

```bash
pwd
git rev-parse --show-toplevel
realpath <file>
git log -1 --oneline -- <file>
```

**Recovery from stray commit in wrong worktree:**

```bash
cd /wrong/worktree && git log --oneline -5
cd /correct/worktree && git cherry-pick <stray-sha>
cd /wrong/worktree && git reset --hard HEAD~1
```

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Reading stderr/stdout from test runner | Examined "Available tasks:" output in stdout to diagnose 127 | Output was pixi help text from `yq` called in unexpected context — a red herring | Trust `bash -x` trace over raw stdout when diagnosing exit 127 |
| Assuming 127 = missing binary | Checked whether `yq`\|`jq`\|`curl` were installed | All binaries present; 127 came from a missing bash function in a sourced library | Exit 127 has two distinct causes: missing binary vs. missing function; `-x` trace distinguishes them |
| `grep "pattern" file \| while read line; do` | Direct pipe from grep into while-read | When grep exits 1 (no matches), pipefail propagates non-zero exit and set -e aborts script | Never pipe grep into while-read under set -euo pipefail without a guard |
| `\|\| true` on the whole while-read pipeline | Appended `\|\| true` after `done` | Works but silently swallows ALL errors inside loop body, masking real failures | Use process substitution (Option A); reserve `\|\| true` only for truly ignorable errors |
| Logic inversion: else sets rc=1 for non-matching files | Expected that `else rc=1` would fire on non-matching files | The abort-on-grep-miss masked the real logic flow; else branch was never reached | Pipefail trap can invert apparent logic: what looks like a missing-string check exits instead |
| `local -a FAILED_AGENT_NAMES` (no `=()`) | Declared array without initializing | Under `set -u`, bash treats unassigned array as unbound on first access | Always use `=()` when declaring arrays; declaration alone is not initialization |
| Guarding with `[[ -v ARRAY ]]` check | Used `[[ -v FAILED_AGENT_NAMES ]]` before each access | Verbose and easy to miss in new code paths; doesn't fix root cause | Initialize at declaration instead of guarding every access site |
| `.converged // empty` | Used jq alternative operator to skip null | `false` is falsy in jq — `//` triggers on `false` too, returning empty | Never use `//` with boolean fields; use `if . == null` instead |
| `.converged // "false"` | Tried to default to string "false" | `//` replaces `false` with the alternative regardless — output is always `"false"` even when `.converged` is `true` | The alternative operator is wrong for booleans; use `tostring` with a null guard |
| `.converged \| tostring` | Direct tostring without null check | Works for booleans but crashes if field is missing (null input to tostring) | Add `// null` guard before `tostring` or use `if . == null then "" else tostring end` |
| jq inline array concatenation `] + (if $cond then [...] else [] end)` | Used jq's `+` operator for conditional array building | Fails on jq 1.5 and some distro-patched builds with `syntax error, unexpected '+'` | Build conditional arrays in bash; pass via `--argjson` for version compatibility |
| Trust Edit succeeded (multi-worktree) | Assumed Edit on an absolute path edited the file Bash subsequently grep'd | Edit operated on main worktree path; Bash grep ran in sibling worktree via stale cwd | Edit and Bash can target different copies of the same logical file when multiple worktrees exist |
| Re-Read to verify after Edit | Re-read file via Read (absolute path) to confirm the edit landed | Read showed correct content (main worktree) — but Bash kept grepping wrong copy via relative path | A successful Read does not prove subsequent Bash commands see the same file |
| Python heredoc rewrite | Switched to `python3 <<EOF` rewrite when Edit refused | Python interpreter inherits Bash cwd; opened relative path resolving into wrong worktree | Heredoc/subprocess tools inherit Bash cwd — same root cause, different surface |
| Grep with relative path | Used `grep PATTERN .github/workflows/file.yml` to confirm change | Relative path resolved against stale cwd; returned no match | Always use absolute paths in Bash when cross-checking Edit results |
| Blame the Edit tool | Suspected Edit was silently no-oping or operating on a cached buffer | Edit had worked correctly — divergence was in the verifier, not the editor | When two tools disagree, suspect cwd before suspecting tool bugs |

## Results & Parameters

### grep exit code semantics

```
grep exit codes: 0 = matches found, 1 = no matches, 2 = error
Under set -e + pipefail, exit code 1 (no matches) is indistinguishable from a real error.
```

### Arithmetic counter guard pattern

```bash
(( count++ )) || true       # safe: || true prevents set -e seeing 0 result
count=$(( count + 1 ))      # also safe: arithmetic expansion never triggers set -e
```

### Restored function with delegate shim pattern

```bash
# Restored original with retry logic:
_agamemnon_curl_retry() {
  local max_attempts="${AGAMEMNON_MAX_RETRIES:-3}"
  local attempt=1
  local response
  while [ "$attempt" -le "$max_attempts" ]; do
    response=$(curl -sf "$@") && { printf '%s' "$response"; return 0; }
    attempt=$((attempt + 1))
    sleep 1
  done
  return 1
}

# Renamed public function delegates so both old and new callers work:
_agamemnon_curl() {
  _agamemnon_curl_retry "$@"
}
```

### jq select + fallback pattern

```bash
result=$(echo "$json" | jq -r --arg name "$name" \
  'first(.[] | select(.name == $name) | .status) // "unknown"')
result="${result:-unknown}"   # shell fallback in case jq returns empty
```

### Pre-commit hook template (grep no-match safe)

```bash
#!/usr/bin/env bash
set -euo pipefail

rc=0
for workflow_file in .github/workflows/*.yml; do
  if grep -q "gitleaks detect" "$workflow_file"; then
    while read -r line; do
      echo "Found in $workflow_file: $line"
    done < <(grep "gitleaks detect" "$workflow_file")
  else
    echo "WARN: $workflow_file does not call gitleaks detect" >&2
    rc=1
  fi
done
exit "$rc"
```

### Session-start checklist for multi-worktree sessions

```bash
cd /abs/path/to/main/worktree
pwd
git worktree list
git rev-parse --show-toplevel
```

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| HomericIntelligence/Myrmidons | PR #564 — check-gitleaks-coe.sh pre-commit hook exited on grep no-match before reaching else rc=1 | grep \| while-read abort under pipefail |
| HomericIntelligence/Myrmidons | PR #623 — apply.sh failed-agent tracking crashed at `${#FAILED_AGENT_NAMES[@]}` | Unbound array under set -u |
| HomericIntelligence/Myrmidons | PR #623 — convergence serialization bats test 318 failing on false value | jq // operator falsy boolean trap |
| HomericIntelligence/Myrmidons | CI debug session — test-api-retry.sh exit 127 after `_agamemnon_curl_retry` renamed | Exit-127 function recovery |
| ai-maestro (23blocks-OS) | Issue #272 — install-agent-cli.sh jq syntax error on older jq | jq array concatenation compatibility |
| HomericIntelligence/ProjectOdyssey | Multi-worktree session — stray commit cf710fb4 on ci-pipe-handler-cores-gate branch | Bash cwd drift from Edit/Read absolute paths |
