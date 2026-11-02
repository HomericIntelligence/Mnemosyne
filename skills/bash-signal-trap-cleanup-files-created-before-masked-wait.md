---
name: bash-signal-trap-cleanup-files-created-before-masked-wait
description: "Remove temporary files that a signal trap must own when a bash script creates them before a blocking network or child-process wait. Use when: (1) a signal handler (INT/TERM) exits but files created earlier in the same function remain on disk after a cancel, (2) a temp path is a local variable that the trap cannot see because the handler runs outside the function scope, (3) a reviewer reports leftover dotfiles or scratch files after Ctrl-C during a slow fetch, download, or upload, (4) you need proof of the residue before and after the fix instead of a code-reading claim."
category: debugging
date: 2026-11-01
version: "1.0.0"
user-invocable: false
verification: verified-local
tags:
  - bash
  - trap
  - sigint
  - temp-files
  - cleanup
  - ctrl-c
  - scope
  - network-wait
---

# Signal Trap Must Own Files Created Before a Blocking Wait

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-01 |
| **Objective** | Prevent a Ctrl-C during a slow network fetch from leaving temporary files behind, and prove the residue with a controlled interrupt test |
| **Outcome** | SUCCESS (verified-local). A controlled SIGINT during a stalled fetch left two temp files before the fix and none after the handler gained global ownership of the paths |

## When to Use

Use this skill when all of these conditions hold:

- A bash script creates one or more temporary files before a call that can block for seconds or longer: a network fetch, an upload, or a child process with a long timeout.
- A signal handler such as `trap '... exit 130' INT` exists for user cancel.
- The script cleans the temporary files in its normal success and error paths with `rm -f`.
- A cancel path bypasses those cleanups because the handler exits first.

Do **not** use this skill for these cases:

- The script backgrounds work with `&` and must kill descendant trees. Use a process-group trap pattern instead. This skill does not manage child processes.
- The temporary files are created only after the blocking call returns. In that order, the handler has nothing to clean.
- The files are intentionally kept for diagnosis after a failed run. State that intent in the code and in the finding response.

## Verified Workflow

### Quick Reference

```bash
# 1. Declare the paths at global scope, next to the handler.
CLEANUP_BODY_FILE=''
CLEANUP_ERR_FILE=''
trap 'printf "\nCancelled.\n"; rm -f "$CLEANUP_BODY_FILE" "$CLEANUP_ERR_FILE"; exit 130' INT

fetch_data() {
  # 2. Assign the globals before the network wait, not before local setup.
  CLEANUP_BODY_FILE="$CONFIG_DIR/.fetch-body.$$"
  CLEANUP_ERR_FILE="$CONFIG_DIR/.fetch-err.$$"
  : > "$CLEANUP_BODY_FILE" && : > "$CLEANUP_ERR_FILE" || return 0

  # 3. Normal paths keep removing them.
  fetch_tool -o "$CLEANUP_BODY_FILE" 2>"$CLEANUP_ERR_FILE" || :
  # ...validate, then:
  rm -f "$CLEANUP_BODY_FILE" "$CLEANUP_ERR_FILE"
}
```

`rm -f ''` is a silent no-op. An empty global is therefore safe in the handler before any fetch runs.

### Suggested Approach

1. **Trace the cancel path, not the success path.** List each file the function creates and each line that removes it. If a removal line is reachable only after the blocking call returns, the handler does not cover that file.
2. **Check variable scope before you add a trap line.** A handler is a separate command. It cannot read a `local` variable that belongs to the function that was interrupted. A `local body_file` is invisible to the handler, so `rm -f "$body_file"` in the handler removes nothing. Promote the paths to globals declared at top level, next to the handler.
3. **Keep the handler simple.** Put the paths in globals and reference them from one handler. A second cleanup mechanism, such as a nested `trap RETURN` inside the function, does not run when the signal handler exits.
4. **Keep each normal path intact.** Do not remove the existing `rm -f` calls. They cover success and error paths. The handler covers only the cancel path.
5. **Prove the defect before you change the code.** Start the script against a stub server. Let the stub answer the preflight requests quickly and stall the data response. Send SIGINT to the script process group after the temp files appear. List the matching files in the target directory. This shows the residue for the current code.
6. **Repeat the same test after the fix.** Use the same stub and the same interrupt point. Require an empty residue list and the conventional exit code.
7. **Test the bind failure branch.** When the file creation fails, remove both paths and report a clear error. Do not leave one file when the second creation fails.
8. **Watch for name re-use.** If the function runs more than once, reassign the globals at the start of each run. A stale path from a prior run can point at a file that a later run does not own.

### Keep the trigger narrow

The defect needs the create-before-wait order and a handler that exits. A script that only creates files after the wait does not have this defect. When you answer a review finding on such a script, cite the creation line and the wait line to show the order. Do not add cleanup for a residue that cannot occur.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Declare the paths as `local` in the fetching function | Reviewers expected the existing handler to see the paths | The handler runs outside the function scope. It cannot read a `local` from the interrupted call, so a handler edit alone removes nothing | Declare the paths at global scope before you reference them from a handler |
| Rely on short fetch timeouts | The timeout was 20 seconds, which seemed short enough to ignore the window | A slow server or a hung connection can keep the fetch inside that window. The interrupt lands in the window and the residue supplies the evidence | Shorten the exposure, do not ignore it. The handler must own the paths |
| Reason from the code only | The fix looked correct by reading it | A handler edit can be a silent no-op for a scope reason. The residue is the only reliable proof | Build a stub that stalls the wait, send SIGINT to the process group, and list the residue before and after |
| Remove the temp files in a function `RETURN` trap | Used function-scope cleanup in place of the handler | A signal handler that exits does not return from the function, so the `RETURN` trap does not run on the cancel path | Use the signal handler for cancel cleanup, and the normal removals for success and error paths |

## Results & Parameters

### Configuration

| Parameter | Value | Notes |
| --------- | ----- | ----- |
| Exit code on cancel | `130` | The conventional code for a process terminated by SIGINT |
| Temp file location | The script's own configuration directory | Keep the files near their consumers so a residue is visible to the user |
| Temp file names | Fixed prefix plus `$$` | The PID suffix prevents two concurrent runs from sharing one file |
| Handler globals | Empty strings at start | Makes the initial handler state well defined and `rm -f` safe |
| Interrupt point in the test | After both files appear, during the stalled response | Proves the handler, not the normal path, did the cleanup |

### Expected Output

Before the fix, the controlled interrupt reports these results:

- the exit code is `130`;
- the cancel message prints; and
- the residue list contains both temporary files.

After the fix, the same test reports:

- the exit code is `130`;
- the cancel message prints; and
- the residue list is empty.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| LLM360/comet | A setup script that fetches a model list before it writes any user configuration | Controlled SIGINT during a stalled fetch. Two temp files remained before the fix and none remained after. The full contract test file passed after the change, and the lint and format checks passed. |