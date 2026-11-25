---
name: automation-clean-checkout-intermediate-artifacts
license: BSD-3-Clause
description: "Diagnose reusable automation checkout cleanliness when generated artifacts, ignored files, or ambient configuration affect synchronization and agent admission. Use also when a sandboxed agent test or review phase aborts instantly with a checkout-not-clean result at near-zero duration while the operator believes the tree was clean before handoff: the cause can be the agent's own uncommitted edits."
category: tooling
date: 2026-08-06
version: "1.1.0"
user-invocable: false
verification: verified-local
tags: [automation, git, checkout, gitignore, untracked-files, trust-boundary, intermediate-artifacts, tdd, preflight, agent-dirty-tree]
history-source: "https://github.com/HomericIntelligence/Mnemosyne/blob/1956c91d76867bc2e484eaf573a57051855186f8/skills/automation-clean-checkout-intermediate-artifacts.history"
history-cleanup-date: "2026-09-20"
---

# Keep Reusable Automation Checkouts Clean Without Blocking Ignored Artifacts

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-08-06 |
| **Objective** | Let automation generate logs and build products without weakening the clean-checkout boundary used before synchronization or agent execution. |
| **Outcome** | Require `git status --porcelain --untracked-files=all` to be empty. Put every expected intermediate under a reviewed ignore rule or outside the checkout; reject every remaining tracked or untracked entry. |
| **Verification** | Verified locally with behavior-first RED/GREEN tests, affected suites, formatting, type, lint, documentation, and pre-push validation. |

## When to Use

- A reusable checkout refuses to synchronize because a prior automation phase created logs,
  reports, caches, or build output.
- A proposed workaround changes `git status` to `--untracked-files=no` or otherwise suppresses all
  untracked paths.
- A later agent or tool reads project-local configuration, discovers helpers, or executes commands
  from the checkout after the cleanliness gate.
- The repository needs one clear rule for files created before a clean-tree preflight: ignored,
  outside the checkout, or rejected.
- Tests cover a clean checkout but do not separately prove rejection of a non-ignored file and
  acceptance of an ignored artifact containing real data.
- A sandboxed agent test or review phase aborts instantly with a checkout-not-clean result at
  near-zero duration, and the operator believes the tree was clean before the agent ran. The agent
  can have made its own uncommitted edits.

## Verified Workflow

### Quick Reference

```bash
# The reusable-checkout admission check. Success requires no output.
git -c core.fsmonitor=false status --porcelain --untracked-files=all

# Confirm each expected intermediate is ignored by the intended rule.
git check-ignore -v -- <generated-path>

# Confirm the scratch tree has not become tracked despite the ignore rule.
git ls-files -- <scratch-directory>/
```

### Detailed Steps

1. **Define clean at the trust boundary.** A reusable checkout is clean only when porcelain status
   reports no staged changes, unstaged changes, or non-ignored untracked files. Do not redefine
   clean to mean only “no tracked changes” when later automation can consume ambient files.

2. **Keep Git's ignore rules authoritative.** Every log, cache, build product, generated report,
   temporary worktree, and other intermediate created before the check must either:

   - match a reviewed `.gitignore` rule;
   - be emitted into a repository-defined ignored scratch directory; or
   - be written outside the reusable checkout.

   Do not maintain a second filename allowlist inside the cleanliness checker. Two authorities drift,
   and the checker eventually permits or blocks paths differently from normal Git behavior.

3. **Inspect all non-ignored untracked paths.** Use:

   ```bash
   git -c core.fsmonitor=false status --porcelain --untracked-files=all
   ```

   `all` expands files inside untracked directories, which produces actionable diagnostics and
   prevents an untracked directory from hiding project-local configuration or executable helpers.
   Ignored files remain absent from normal porcelain output, so expected artifacts do not block the
   operation once the ignore contract is correct.

4. **Fail before synchronization or agent admission.** If porcelain output is non-empty, stop and
   include the exact entries in the error. Do not fetch-and-merge first and do not dispatch an agent
   into a checkout that failed admission. Recheck after any network or synchronization boundary
   that could race with another writer.

5. **Document the producer contract.** The operator-facing architecture should say that the command
   requires a clean checkout and that all intermediates created before detection must be ignored or
   stored elsewhere. Name the sanctioned scratch location when the repository defines one.

6. **Test both sides of the policy with real Git behavior.** Use temporary repositories rather than
   mocking the status output for the core regression:

   - Create a non-ignored file with content and assert admission fails with its `??` porcelain entry.
   - Commit an ignore rule, create a file with content under the ignored location, and assert
     admission succeeds.
   - Retain staged and unstaged tracked-change cases.
   - Put a file inside an ignored directory; an empty directory is not Git state and cannot prove
     the behavior.

7. **Keep the scratch directory untracked.** `.gitignore` does not prevent a forced add. When the
   scratch location has packaging or distribution significance, retain a separate index guard that
   asserts `git ls-files -- <scratch-directory>/` is empty.

### Pre-Flight Rejection Can Masquerade as a Sandbox Failure

An operator-side cleanliness gate and an agent-side sandbox produce different failure shapes for
the same dirty-tree cause.

1. **Identify the signature.** When a sandboxed phase is refused before it executes, the returned
   result reports `ok=False` with an error in the form `review_checkout_not_clean` and a duration
   at or near zero. Near-zero duration is the tell: no test or review code ran.

2. **Ask the discriminating question.** Run:

   ```bash
   git status --porcelain --untracked-files=all
   ```

   If the output lists the agent's own uncommitted edits, the failure is pre-flight rejection, not
   a product regression. An empty report with the same signature points back at the operator side
   of this entry.

3. **Commit, then re-run.** Commit the pending edits first and re-run the focused suites. Do not
   debug, bisect, or regression-triage the suites before the checkout is clean.

4. **Make the tell a triage rule.** When a phase fails instantly, check the result duration and the
   delta commit state before any other hypothesis.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Hide all untracked files | Changed the admission command to `--untracked-files=no` so generated logs stopped blocking synchronization. | It also hid arbitrary ambient configuration and helpers that later automation could discover or execute, so the checkout was treated as verified without inspecting all relevant state. | Keep `--untracked-files=all`; make expected intermediates ignored or external instead of weakening admission. |
| Delete or stash generated artifacts before every run | Treated each dirty-tree failure as cleanup work. | Long-running producers recreated the files, and cleanup raced with active tools. | Give runtime outputs a durable ignored location rather than repeatedly fighting their lifecycle. |
| Add a checker-specific artifact allowlist | Planned to permit a few known log and build names in the synchronization function. | The allowlist duplicated `.gitignore`, created a second policy surface, and would drift as producers changed. | Use Git's ignore engine as the single artifact-admission authority. |
| Test an empty ignored directory | Created the directory but no file within it, then asserted the checkout remained clean. | Git does not report empty directories, so the test passed regardless of the ignore rule and could not detect a regression. | Write a real file under the ignored directory and verify the ignore rule with `git check-ignore -v`. |
| Treat an instant sandbox failure as a change regression | Ran a full test tree with uncommitted edits and triaged two instant checkout-not-clean results as regressions of the change. | A pre-flight cleanliness gate rejected the sandbox before any test executed; both suites passed after the edits were committed and the focused runs re-executed clean. | Check the result for near-zero duration and the checkout for the agent's own edits before debugging any suite. |

## Results & Parameters

### Configuration

```gitignore
# Repository-defined automation scratch output; never source.
/<scratch-directory>/

# Root-level run logs, when the producer cannot use the scratch directory.
/*.log
```

Use root-anchored patterns when only the repository-root location is sanctioned. Use broader
patterns only when the same intermediate is intentionally valid at every matching depth.

### Expected Output

Clean or ignored-only checkout:

```text
$ git status --porcelain --untracked-files=all
<no output>
```

Unsafe non-ignored intermediate:

```text
$ git status --porcelain --untracked-files=all
?? intermediate.txt
```

The automation should reject the second state and report the porcelain entry. It should not delete,
stash, or silently suppress the file.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Python automation repository | Reusable-checkout synchronization before agent dispatch | A behavior-first regression failed while arbitrary untracked files were hidden, then passed after restoring full untracked inspection; ignored build/log artifacts, affected suites, and repository gates also passed. |
| Python automation repository | Sandboxed agent test and review phases before gate runs | Two instant checkout-not-clean results reproduced only on the agent's dirty tree and passed after commit; focused suites re-ran clean. Triage the checkout state first whenever a phase fails at near-zero duration. |

## References

- [Git status `--untracked-files` documentation](https://git-scm.com/docs/git-status#Documentation/git-status.txt--ultmodegt)
- [Gitignore pattern documentation](https://git-scm.com/docs/gitignore)
- [Runtime lockfile gitignore guidance](claude-code-scheduled-tasks-lockfile-gitignore.md)
- [Ignored scratch-directory tracked-state guard](gitignored-scratch-dir-regression-guard.md)
