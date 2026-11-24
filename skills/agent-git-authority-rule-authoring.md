---
name: agent-git-authority-rule-authoring
description: "Write or review an agent git-mutation authority rule so that no destructive update reads as permitted. Use when a rule keys a prohibition on a lease, a flag, or a command prefix; when a rule lets an agent retry a host-denied operation; or when a branch push can also send tags."
category: tooling
date: 2026-11-24
version: "1.0.0"
user-invocable: false
verification: verified-local
tags:
  - git
  - force-push
  - force-with-lease
  - instruction-files
  - agents-md
  - authority
  - permission-denial
  - tags
  - refspec
---

# Closing a Git Authority Rule Against Destructive Spellings

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-24 |
| **Objective** | State a git-mutation rule that an agent can obey without reaching a destructive effect or a denied action. |
| **Outcome** | Successful. Two review rounds closed the gaps below in a merged instruction file. |

A prohibition that names one spelling leaves the other spellings open. This entry gives the
closing tests for a git authority rule.

## When to Use

- You write or review the git section of an instruction file that an agent reads.
- A prohibition is stated by a flag, a lease, a command prefix, or the words "without `--force`".
- A permission sentence lets the agent retry, or reword, an operation that the host refused.
- A branch push can also send tags because of a repository setting.

## Verified Workflow

### Quick Reference

Test each rule against these questions. A "yes" is a defect.

| Test | Defect |
| --- | --- |
| Can a destructive command satisfy the rule as written? | The prohibition is keyed on a spelling, not on the effect. |
| Does the rule let an agent repeat or reword a denied operation? | The rule grants authority that the host withheld. |
| Can an allowed push also send tags? | The rule has a side effect that the release procedure did not approve. |
| Is one command form stated in two files? | The copies drift, and a correction reaches only one copy. |

### Suggested Approach

1. **Key the prohibition on the effect.** Git does not read `--force-with-lease` as a guard when
   `--force` is also present. `--force` disables the lease check in either flag order. A rule that
   prohibits "a forced update that no lease protects" therefore permits:

   ```bash
   git push --force --force-with-lease=refs/heads/<branch>:<stale-oid> <remote> <branch>
   ```

   This command exits 0 with `(forced update)` and discards the other author's commits. Name every
   forced spelling instead: `--force`, `-f`, `+<refspec>`, `--mirror`, and the `--force` plus
   `--force-with-lease` combination. State the cause, so a reader does not "fix" the list back to
   the lease phrase.

2. **Give the permitted form with a lease that is bound at push time.** Read the current remote oid,
   then put that oid in the lease. The lease then protects against a concurrent writer.

   ```bash
   git ls-remote <remote> refs/heads/<branch>
   git push --force-with-lease=refs/heads/<branch>:<remote-oid> --no-follow-tags <remote> refs/heads/<branch>
   ```

   Define each placeholder. An undefined `<expected-oid>` lets a reader invent the value.

3. **Stop tag side effects.** A repository with `push.followTags=true` sends annotated tags on an
   ordinary branch push. `git push -u <remote> <branch>` then publishes a release tag without the
   release procedure. Put `--no-follow-tags` in every permitted push command, and prohibit `--tags`,
   `--follow-tags`, and a tag refspec on a branch push.

4. **Make a host denial terminal.** A permission rule is an authority. Text such as "if the host
   still blocks it, run it once" or "the block continues, then ask" lets the agent retry a denied
   action and delays the report. Write: do not retry, do not reach the same effect in another form,
   give the user the exact command and the denial message, and continue independent work. A redirection
   or an encoded argv does not change a denial at command admission.

5. **Keep one authoritative location for each command form.** Two files that both state a push
   command drift. When a correction reached only one copy, the other copy kept the unsafe form, and
   a later reader had two answers. State the command in one file and link from the others.

6. **Do not add a workaround rule for a documented setting.** If the repository sets
   `push.followTags`, correct the command. Do not tell the agent to unset the setting, and do not
   add a second approval step.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Lease phrase | Prohibited "`git push --force` without a lease" | A command with `--force` and a stale `--force-with-lease` value has a lease, so the text permitted it; it exited 0 and removed another author's commit | Enumerate every forced spelling and state that `--force` disables the lease check |
| One retry | Allowed the agent to run a denied operation once more, then report | The host is the authority; the text granted an action the host refused | A denial is terminal: report the command and the denial, do not retry |
| Two copies | Stated the force-push form in two instruction files | The correction reached one copy; the other kept a different form | One authoritative location; the other files link to it |
| Tag list only | Prohibited `--tags`, `--follow-tags`, and a tag refspec | A repository with `push.followTags=true` still sent a tag from a plain branch push | Add `--no-follow-tags` to the permitted command |

## Results & Parameters

### Configuration

```yaml
# Repository settings that change push behavior
push.followTags: true    # a branch push also sends annotated tags
```

### Expected Output

- A forbidden-spelling check finds no permitted command that can force an update without a valid lease.
- A branch push sends no tag ref.
- The permission text contains no retry, and no alternate form.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Private | Instruction-file revision and review | Two review rounds, then a corrective revision. |
| Local Git 2.56.0 | Throwaway repositories | Reproduced the lease clobber and the tag side effect. See [notes](agent-git-authority-rule-authoring.notes.md). |

## References

- [Force-push blocked: preserve the PR or reopen safely](tooling-force-push-blocked-reopen-as-fresh-branch.md)
- [Git rebase, signing, and CI repair](git-rebase-signing-ci.md)
- [Chat approval questions versus tool permission prompts](agent-chat-approval-question-vs-tool-permission.md)
- [Peer rewrote the PR head: do not reprint the push](peer-rewrote-pr-head-orphaned-push.md)