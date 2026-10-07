---
name: hephaestus-loop-unconfigured-host-operation
description: "Bring up and keep alive the Hephaestus plan/review issue loop on a host that has no prepared automation configuration. Use when: (1) hephaestus-plan-issues or hephaestus-implement-issue exits fast with intake, preflight, or agent errors on an unfamiliar machine, (2) the Claude CLI reports \"Not logged in\" against a self-hosted model gateway even after configuration, (3) planner or reviewer jobs die with timeout, a missing verdict, or empty output, or (4) an interrupted run left the intake worktree dirty and the loop refuses to start."
category: tooling
date: 2026-10-07
version: "1.0.0"
user-invocable: false
verification: verified
tags:
  - hephaestus-automation
  - plan-review-loop
  - host-bring-up
  - claude-cli
  - codex-cli
  - opencode
  - gateway
  - anthropic-messages-api
  - path-shim
  - bearer-auth
  - intake-recovery
  - session-reset
  - prompt-overlay
  - thinking-model
  - timeout
---

# Hephaestus Loop on an Unconfigured Host: Layered Host-Commons Repair

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-10-07 |
| **Objective** | Run `hephaestus-plan-issues` end to end (plan published, reviewer verdict reached, amend cycle entered) on a cluster host with no prepared automation backend, while fixing only the host, never the automation codebase. |
| **Outcome** | Operational. After repairing seven host layers in dependency order, the loop published a plan, a reviewer produced a verified NOGO with code citations, and the amend cycle started. Sixteen run failures were diagnosed one signature at a time. |
| **Verification** | verified-live: real loop runs r1–r17 against one GitHub issue; the plan comment and review artifacts persist on the issue and in the intake state directory. No automation source was patched. See [notes](hephaestus-loop-unconfigured-host-operation.notes.md). |

## When to Use

- Running `hephaestus-plan-issues` or `hephaestus-implement-issue` on a machine without the standard operator configuration; runs exit within seconds or minutes with intake-valid, preflight, or agent-launch errors.
- The Claude CLI answers `Not logged in · Please run /login` against a self-hosted gateway even though credentials were configured, or `claude auth status` exits 0 while `loggedIn` stays `false`.
- Choosing an agent backend (claude, codex, opencode, pi) when the host CLI stack or the gateway protocol does not match what the automation adapter emits.
- Planner or reviewer jobs fail with `job failed: timeout`, end without a verdict (`reviewer error`), or return empty output after resume.
- A killed or crashed run left the intake worktree dirty, and the next run refuses to start with intake validation errors.

## Verified Workflow

### Quick Reference

Repair host-commons in this dependency order. Each layer blocks the next; diagnose by signature, fix the host, rerun, and take the next signature from the run log:

```text
L1 agent backend   CLI can authenticate and print-answer through the gateway
L2 launch cwd      scratch directory; run journals are cwd-relative
L3 tool versions   git >= 2.36, real gh binary, no stale repo git config
L4 intake state    reconcile legacy state; clean lane worktrees after crashes
L5 run budgets     planner/reviewer timeouts sized for thinking-model latency
L6 prompt contract overlay sets tool scope, bounded inspection, mandatory verdict
L7 session reset   archive the transcript to force create-mode on degradation
```

### Layer table: signature, cause, fix

| # | Signature in the log or CLI | Cause | Host fix |
| - | --------------------------- | ----- | -------- |
| 1 | claude `-p` prints `Not logged in · Please run /login`; `auth status` exits 0 but `loggedIn:false` | The CLI (2.1.x observed) gates print mode on `ANTHROPIC_*` in the **process environment**; the `env` block of `settings.json` satisfies `auth status` only | Run the CLI through a PATH **shim** that exports `ANTHROPIC_BASE_URL` and `ANTHROPIC_AUTH_TOKEN` before `exec` on the binary. Read the token from a 0600 key file **at run time**; never write it into the shim. Automation builders strip `ANTHROPIC_*` from child environments, so an exported variable on the launcher survives only inside a wrapper binary |
| 2 | Gateway answers `invalid or missing API key` | Token was sent as `x-api-key`; the gateway accepts Bearer only | Use `ANTHROPIC_AUTH_TOKEN` (sent as `Authorization: Bearer`), never `ANTHROPIC_API_KEY` (sent as `x-api-key`). Probe with `curl` before involving the CLI |
| 3 | codex exits after provider setup: chat-only endpoint, or asks for the Responses API | codex (0.160.x) requires `/v1/responses` for the served models; the gateway exposes `/v1/messages` only | Do not select codex for a Messages-only gateway. Probe `POST /v1/responses`; a 404 settles the backend choice without adapter debugging |
| 4 | opencode preflight fails; emitted flags absent from `opencode --help` | Adapter built for an older CLI major version (v1 flags against a v2 binary) | Compare every emitted flag with the installed `--help`. A flag mismatch is a hard version gate, not a configuration problem; switch the backend or provide a matching CLI build |
| 5 | First agent call hangs >60 s with no error; catalog lists the model | Deployment is served but cold or stopped | Probe each candidate model with a short prompt, small `max_tokens`, and a timeout (45–60 s) **before** choosing it. A listing in `GET /v1/models` does not imply the deployment answers |
| 6 | Intake validation fails and the run journal shows self-referential paths | Run journals are relative to the launch cwd; launching from a reused directory lets one run poison the next run's validation | Always launch from an empty scratch directory dedicated to the loop |
| 7 | Intake or worktree step errors on `worktree list` output | System git too old for `git worktree list --porcelain -z` (needs >= 2.36) | Put a newer git early on PATH (a package-manager env is enough); confirm with the exact subcommand |
| 8 | `gh` rejected despite `--gh-extra-path-root` | Only real binaries are accepted; a symlink that escapes the extra root is refused | Resolve symlinks and point the extra path root at the directory that holds the real binary |
| 9 | Intake validation fails before any network call; repo-local git config references missing files | Stale repository config (`core.excludesFile`, hooks paths) survives checkouts | Inspect `git config --local --list` on the target checkout; remove entries that point at nonexistent paths |
| 10 | Next run refuses to start: `legacy/conflicting state requires manual reconciliation` | Intake state names (`.automation-state`, `.issue_implementer`) exist outside the intake layout | **Move** the durable state into the intake destination worktree; never delete it |
| 11 | After a kill or crash, intake validation reports a dirty worktree | Lane worktrees and `build/` artifacts remain inside the intake worktree | Recover with: record `git status` for evidence, `git worktree remove --force` for nested lane worktrees, delete the intake worktree's `build/`; confirm the receipt revision is unchanged |
| 12 | Planner fails `job failed: timeout` at the default budget | Default planner timeout (~1200 s) is too small for a thinking model with ~10 s per request and multi-minute thinking turns | Raise `--planner-timeout` (5400 s observed) and `--reviewer-timeout` (3600 s) for thinking models |
| 13 | Reviewer ends with `reviewer error`; transcript shows many denied `Bash` calls, or exhaustive full-file Reads, and no verdict | The review sandbox allows only `Read,Glob,Grep`; a model that ignores denial feedback spirals, and a model that inspects exhaustively can die without emitting the required verdict line | Add a prompt overlay through `--prompt-dir`: (a) a tool contract (name the allowed tools, require continuing after a denial), (b) bounded inspection (grep before full reads, stop at ~40 calls), (c) a mandatory final verdict line. The overlay shadows one template; all other prompts fall through |
| 14 | After resume, the session answers with empty turns or the synthetic line `No response requested.`; `stop_reason:stop_sequence` | Long, resumed conversations can degrade through an Anthropic-Messages bridge gateway; create-mode sessions in the same window stay healthy | Archive the session transcript JSONL (in the CLI's per-cwd project store). The adapter resumes by transcript presence and creates a fresh session when the file is missing; the deterministic session id can stay. Amend prompts are self-contained, so a fresh amend needs no prior transcript |
| 15 | Pipeline summary shows `blocked` with "The proposed plan is empty" right after an amend | The amend produced unchanged or empty text; publication requires a change | Find the cause upstream (usually signature 13 or 14); then move the issue label back to `state:needs-plan` as the blocked comment instructs, and rerun |

### Suggested approach

1. Prove the path from the CLI to the model **before** starting the loop: catalog probe, one `max_tokens=10` liveness probe per candidate model, shim `auth status`, and a print-mode round trip. A failure here makes every later pipeline error ambiguous.
2. Launch from the scratch cwd with the shim directory and the newer toolchain early on PATH. Keep the exact command in a rerun script; each layer fix is one edit, one launch, one new signature.
3. Read failures in the run log at the stage boundary that printed them; the pipeline summary's disposition word (`blocked`, `fail`, `resumable`) is routing, not diagnosis.
4. When an agent session misbehaves, inspect its transcript JSONL directly (thinking blocks and `stop_reason` expose what the summary hides). Empty turns, denial spirals, and synthetic replies each have a different layer fix in the table.
5. Keep the loop's invariants while repairing: never edit the automation source, never delete intake state, never weaken a review sandbox to make a model pass, and never put a token in a file that another user or a commit can read.

### If a step is unavailable

- No newer git: install a user-space package env; do not patch call sites.
- No writable shim location on PATH: pick any directory and prefix PATH in the launch script; the shim works from any absolute path.
- Gateway down or cold on every model: stop; a loop run cannot fix serving. Record the probe evidence.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| opencode backend | Existing adapter against the installed v2 CLI | Adapter emits v1-only flags; preflight rejects them | Compare emitted flags with `--help` first (row 4) |
| codex backend | `wire_api = "chat"` in codex config | codex 0.160.x hard-requires the Responses API for the served models | Probe `/v1/responses` before configuring codex (row 3) |
| `settings.json` auth for claude | Endpoint and token in the user settings `env` block | `auth status` exits 0 with `loggedIn:false`; print mode stays gated | Only the process environment authorizes print mode (row 1) |
| Cold model as planner | Listed model selected without a liveness probe | First real call hung >60 s | Catalog membership is not liveness (row 5) |
| Default timeouts | Planner at the 1200 s default with a thinking model | `job failed: timeout` mid-plan | Size agent budgets to the model's latency (row 12) |
| Resume without reset | Loop retried a timed-out planner session in place | Resumed turn answered the synthetic `No response requested.`; the parsed plan was empty and the loop self-blocked | Archive the transcript to force create-mode (row 14) |
| Review without a prompt contract | Stock review prompt, read-only tool scope | Reviewer spiraled into denied `Bash` calls and died with `reviewer error` | Add the tool contract and bounded inspection through the overlay (row 13) |

## Results & Parameters

### Configuration

```bash
# Launch contract that survived all seventeen iterations
cd <empty-scratch-dir>
PATH=<shim-dir>:<newer-git-dir>:$PATH hephaestus-plan-issues \
  --repos <repo> --issues <n> \
  --agent claude --model <probed-model> \
  --planner-timeout 5400 --reviewer-timeout 3600 \
  --prompt-dir <overlay-dir> \
  --gh-extra-path-root <real-gh-dir> \
  --log-file <run>.log -v
```

```sh
# Shim shape (mode 0700); the token never enters shim text
#!/bin/sh
export ANTHROPIC_BASE_URL="<gateway-url>"
export ANTHROPIC_AUTH_TOKEN="$(cat \"$HOME/<key-dir>/api-key\")"
exec /absolute/path/to/claude "$@"
```

### Expected Output

- First successful gate sequence in the log: preflight passes, `claude invoke: agent=planner ... mode=create`, then `publishing plan revision` and `plan verified; advancing`.
- A completed review prints a verdict (`NOGO verdict (round 1/3)` or a GO), and a NOGO starts the amend cycle (`requesting amend job`).
- The issue shows exactly one plan comment and one review comment; repeated runs fast-forward (`plan comment already exists; fast-forward to VERIFY`) instead of replanning.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Hephaestus plan/review loop + comet | One issue driven through publish, NOGO with verified code citations, and amend start on a fresh host (2026-10-07) | [notes.md](hephaestus-loop-unconfigured-host-operation.notes.md) |

## References

- [automation-agent-tool-scopes-least-privilege](automation-agent-tool-scopes-least-privilege.md) — provider-side tool availability mechanics (`--allowedTools` vs `--tools`, `--bare`); this skill adds the model-compliance failure mode and the prompt-overlay mitigation.
- [tooling-claude-cli-keep-prompts-off-argv](tooling-claude-cli-keep-prompts-off-argv.md) — claude CLI stdin prompt transport and session create/resume mechanics that the transcript reset in row 14 relies on.
- [automation-loop-log-driven-layered-debug](automation-loop-log-driven-layered-debug.md) — the debugging methodology for layered loop failures; use it together with the per-signature table here.
- [automation-plan-review-journal-bounded-liveness](automation-plan-review-journal-bounded-liveness.md) — why repeated runs fast-forward instead of replanning, and why an unchanged amend publication self-blocks.
