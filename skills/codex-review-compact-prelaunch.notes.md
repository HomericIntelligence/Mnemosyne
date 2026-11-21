# Notes: codex-review-compact-prelaunch

Privacy-safe session context for the main skill. No secrets, credentials, or
private file contents.

## Session

- Repository: LLM360/comet, 68-issue Codex fleet through the Hephaestus
  automation loop.
- Fleet root: a private per-run directory with its own Codex home, logs, and
  projects directory.
- Roles: planner and implementer on one model, reviewer on another, with a
  third as fallback.
- Four workers, one loop pass, learning disabled.

## Evidence

- Review jobs failed with `codex_tool_or_provider_failure` and later with
  `reviewer failures exhausted: reviewer error`.
- Job diagnostics showed input token counts of about 1.1M to 1.18M tokens
  against a 1,048,576-token context limit.
- A 700,000-token auto-compact limit was installed in the Codex home
  `config.toml` and mirrored in the model catalog while the fleet ran.
  Config backups with a `.pre-auto-compact` suffix were kept before the edit.
- Sessions bound before the change continued to overflow after the change.
  One issue exhausted reviewer retries after repeated overflows and received
  a no-go plan label.
- Distinct, retryable failures also appeared: `stream disconnected before
  completion: idle timeout waiting for SSE`. These are provider-level and
  separate from overflow.

## Decision

Disposition `create`. Corpus candidates inspected on checkout
`8bd5814e75797c6b62a848c5f3bbf72977d86f69` and ruled out:

- `automation-plan-review-journal-bounded-liveness` — issue journal comments,
  not session context.
- `opencode-compaction-trigger-window-budget` — OpenCode compaction config,
  different tool and mechanism.
- `automation-codex-jsonl-fail-closed-routing` — provider event routing.
- `hephaestus-loop-unconfigured-host-operation`,
  `hephaestus-random-model-draw-launch-safety`,
  `interrupted-automation-loop-relaunch-salvage`,
  `detached-launch-survives-harness-restart` — launch and recovery triggers,
  not session binding lifecycle.

Open PR #4044 adds `opencode-context-limit-receipt-recovery`: post-failure
recovery for OpenCode sessions. This skill is pre-launch prevention for Codex
fleet plan-review sessions. Intents are distinct.

## Limitations

- The compact-limit relaunch path was verified as reasoning from the failure
  evidence and Codex config semantics; the post-relaunch green state was not
  reached inside the source session because the fleet was still running.
- Config key names can differ between Codex versions; confirm against the
  installed version's schema before launch.
