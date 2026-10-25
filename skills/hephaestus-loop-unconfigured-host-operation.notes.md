# Notes: Hephaestus Loop on an Unconfigured Host

Supporting evidence for `hephaestus-loop-unconfigured-host-operation.md`. All endpoints,
paths, and identifiers below use placeholders; substitute the site values. No tokens or
internal hostnames appear in this file.

## Gateway protocol facts (probed 2026-10-07 with curl, then through the CLI)

Endpoint: `<gateway-url>` (a self-hosted model gateway exposing an Anthropic Messages bridge).

| Probe | Result |
| ----- | ------ |
| `GET /v1/models` with `Authorization: Bearer <key>` | 200; catalog lists the served models |
| `POST /v1/messages` (anthropic-version header, Bearer) | 200; full Anthropic Messages reply |
| `Authorization` replaced by `x-api-key` on the same request | `{"error":"invalid or missing API key"}` |
| `POST /anthropic/v1/messages` | `{"detail":"Not Found"}` |
| `POST /v1/responses` | absent → codex CLI cannot use this gateway |
| Thinking model, first real call after idle | ~10 s to first content; cold/stopped deployment: no response in >60 s |

Consequence matrix for CLI configuration:

- `ANTHROPIC_AUTH_TOKEN` → claude sends Bearer → accepted.
- `ANTHROPIC_API_KEY` → claude sends `x-api-key` → rejected.
- codex 0.160.x → requires `/v1/responses` for the served models (`wire_api = "chat"`
  is rejected by the model layer; the CLI instructs `wire_api = "responses"`) → unusable
  here.

## Claude CLI auth surface (2.1.179 observed)

| Configuration | `auth status` exit | `auth status` body | `claude -p` result |
| ------------- | ------------------ | ------------------ | ------------------ |
| `env` block in `settings.json` only | 0 | `loggedIn:false` | `Not logged in · Please run /login` |
| No settings file; shim exports `ANTHROPIC_*` in process env | 0 | `loggedIn:true, authMethod:oauth_token` | prints the model reply |

Automation note: the pipeline builds agent child environments from an allowlist
(PATH/HOME/USER/LANG/…), so `export` on the launcher does not reach the agent. A wrapper
binary early on PATH (the shim) is the injection point that survives. The shim prepends
nothing to argv; automation adapters pass their own flags straight through.

## Run-by-run evidence (r1–r21)

| Run | Reached | Failure signature | Layer fixed next |
| --- | ------- | ----------------- | ---------------- |
| r1–r3 | intake validation | `gh` rejected: symlink escapes the extra path root | real gh directory (row 8) |
| r4–r7 | intake validation | run journal self-poisoning from a reused launch cwd | scratch launch cwd (row 6) |
| r8 | intake | `git worktree list --porcelain -z` unsupported by system git 2.34 | user-space git 2.56 early on PATH (row 7) |
| r9 | intake | dirty worktree after crashes | lane worktree removal + `build/` cleanup (row 11) |
| r9 | intake | legacy `.automation-state`/`.issue_implementer` outside the intake layout | moved, not deleted (row 10) |
| r10 | intake | repo-local git config referenced a missing excludes file | pruned stale local config (row 9) |
| r10–r11 | agent preflight | opencode v1 flags vs v2 CLI; codex Responses-API requirement; claude unauthenticated | backend settled on claude via shim (rows 1, 3, 4) |
| r11 | planner | `job failed: timeout` at the 1200 s default; retry resumed mid-run got killed | timeouts raised (row 12) |
| r12 | publish | planner resumed the timed-out session → `No response requested.` → "proposed plan is empty" → `state:plan-blocked` | transcript reset (row 14) |
| r13 | planner | resume again (reset flag did not cover the planner session) | stopped early; transcript archived instead |
| r14 | review | plan published, `plan verified; advancing`; reviewer spiraled into denied `Bash`, died with `reviewer error` | prompt overlay (row 13) |
| r15 | amend | reviewer NOGO in 5 min with verified code citations; amend resumed planner → turns degraded empty → blocked again | transcripts archived before relaunch; overlay kept |
| r16 | review | 28-min exhaustive review died verdict-less; resume continued but also ended without a verdict (~14 min) | overlay extended with bounded-inspection + mandatory-verdict text |
| r17 | review | bounded overlay worked for tool choice (86 calls, grep-dominant) but the session still died verdict-less at ~25 min; forensics showed bridge-truncated turns after thinking blocks plus client auto-continue ("Continue from where you left off.") | filed the gateway bridge bug; switched backend to opencode |
| r18 | preflight | `Agent 'opencode' is installed but not authenticated` — the v1 `providers list` auth probe does not exist in v2 | shim rewrite `providers list` → `auth list` (row 4) |
| r19–r20 | admission | `review-session-lost: reviewer tool or model changed` guard on the claude→opencode switch; guard published `state:plan-blocked`, next run seeded 0 items | `--reset-plan-review-session` + restore `state:needs-plan` (row 14) |
| r21 | **completed** | — | opencode + `comet/kimi-k3`: fast-forward verify, NOGO (round 1, revision 1), amend → revision 2, NOGO (round 2), amend → revision 3, **GO (round 3)**; sessions resumed across rounds without the degradation seen on the Anthropic-bridge client; 5 agent jobs, 0 reviewer errors, ~73 min wall |

Final review evidence on the completed loop: the GO iteration verified all prior findings as
fixed in the artifact (not merely acknowledged), ran security/dependency/docs sweeps, scored
every rubric dimension A, and recorded exactly one minor finding (a one-line transition note
for live deployments pointing at pre-change client manifests). The final plan carries per-AC
committed test names and an implementation order with red-first steps.

## Run-by-run evidence (r22–r24, 2026-10-21, opencode backend, issue wave of 26)

Same multi-issue repository as r1–r21; a full issue wave (`--issues` with 26 explicit
numbers) driven by `hephaestus-automation-loop`. Each run is one edit, one launch, one new
signature, and matches the layered model: the first three failures all stopped inside the
repo/checkout-preparation stage before any agent call.

| Run | Reached | Failure signature | Layer fixed next |
| --- | ------- | ----------------- | ---------------- |
| r22 | agent preflight | `RuntimeError: Agent 'opencode' is installed but not authenticated. Run \`opencode providers login\` (environment keys also work) before running automation.` — the translating shim directory was not on PATH, so the adapter's v1 `providers list` probe hit the raw v2 CLI | shim directory first on PATH (row 4); through the shim, the mapped `auth list` exits 0 and the probe passes |
| r22 | repository checkout preparation (attempt 1/2 ×2, then `FAIL:clone exhausted after 2 attempts`) | `required GitHub executable is unavailable; pass --gh-extra-path-root ROOT when ROOT/bin/gh is the intended installation` — gh is a real binary user-installed at `<home>/.local/bin/gh`, absent from system locations | `--gh-extra-path-root <home>/.local` (row 8) |
| r23 | checkout preparation (attempt 1/2 ×2, then FAIL) | `repository-intake Git common directory permissions are unsafe: <repo>/.git (mode 0775); run: chmod 755 <repo>/.git, or re-clone with umask 022, then rerun. A mode of 0755 is enough for the intake check.` | `chmod 755 <repo>/.git` (row 16); `stat -c '%a'` confirmed 0755, intake preparation then completed |
| r24 | intake completed (`isolated intake preparation completed`); per-issue planning began | advise disabled per `--no-advise`; still, planning and implementation jobs died under `SourceWorkspaceError: source workspace registration changed`; log shows `Failed to list worktrees: Command '['git', 'worktree', 'list', '--porcelain', '-z']' returned non-zero exit status 129` | Standalone check: system git 2.34.1 answers `git worktree list --porcelain -z` with `error: unknown switch 'z'` (row 7). The host had no newer git; the run stopped there |

Two operating notes from the wave shape:

- Prep stages for the wave ran serially with no host churn; all 26 intake lanes shared one
  prepared intake (`Queue stages: repo,planning,plan_review,implementation,pr_review,merge_wait`).
- The summary's `planning finished` + `FAIL:...`/`BLOCKED:...` dispositions are routing words;
  the diagnosis lives at the stage-boundary log lines quoted above. With explicit `--issues`,
  a drained selection skips discovery re-seed, so nothing downstream runs after an exhausted
  checkout-preparation failure.

Key positive evidence:

- r15 review artifacts (intake state `plan-review/artifacts/<cycle>/0000.txt`): the reviewer
  verified plan claims against specific file lines, confirmed accurate ones, and returned
  a NOGO with two major and two moderate findings, all code-cited. This proves the full
  chain works when the layers hold.
- Planning fast-forward: once a plan comment exists, later runs log
  `plan comment already exists; fast-forward to VERIFY` and reuse it.

## Degradation forensics (signatures 13 and 14)

Transcript JSONL located in the CLI's per-cwd project store
(`~/.claude/projects/<cwd-slug>/<session-id>.jsonl`).

- Denied-tool spiral: `tool_result` events with `is_error:true`,
  "Permission to use Bash has been denied because Claude Code is running in don't ask
  mode." The stage's error classification is "reviewer error", which the pipeline reports
  only when the final output has no GO/NOGO/BLOCKED verdict.
- Exhaustive review death: 151 inspection calls (Read 60, Grep 79, Glob 12) in 28.5 min,
  then the session ended mid-narration ("Continuing verification with parallel checks.")
  with no verdict. Bounded-inspection guidance in the overlay targets this branch.
- Resume degradation: assistant events with empty text and `stop_reason: stop_sequence`;
  in one resumed session the model's own thinking recorded
  "My turns keep coming back empty without executing tool calls." In another, the resumed
  turn was the synthetic line "No response requested." (model field `<synthetic>`).
  Freshly created sessions in the same windows completed 5–19 min of real work.
- The adapter creates vs resumes by transcript presence (`create = not transcript.is_file()`);
  the session id itself is deterministic per (repo, issue, agent, model). Archiving → next
  call logs `mode=create`; resume of a missing id is handled as a lost session
  ("review-session-lost") and a new cycle starts.

## Intake crash-recovery script (shape)

```bash
#!/bin/sh
# compact clean-intake: preserve evidence, then reset the intake worktree
cd <intake-worktree>
git status --porcelain | tee /tmp/intake-dirt.log
git worktree list --porcelain | awk '/^worktree .*(auto-|issue-)/{print $2}' \
  | while read -r wt; do git worktree remove --force "$wt"; done
[ -d build ] && rm -rf build
git worktree prune
echo "intake clean at $(git rev-parse HEAD)"
```

Confirm afterwards that the intake receipt revision did not move; a clean repair keeps it.

## opencode v1→v2 shim translation (the working `opencode` shim)

```text
drop  --dir <path> / --dir=<path>   v2 anchors the project at the process cwd
drop  --variant <v> / --variant=<v> v2 uses provider/model#variant inline
drop  --pure                        v2's --agent plan keeps edit denial
map   providers list -> auth list   v1 auth probe; v2 semantic twin (exit 0)
keep  everything else verbatim      run, --format json, --model, --session, --agent
```

Verified before loop use: stdin prompt accepted, `--format json` JSONL stream matches the
v1-era adapter parser (`type:"text"`, `part.text`, `sessionID`), default build agent
permits workspace writes headless (file write executed without extra flags), `--agent plan`
runs clean, and `--session <ses_id>` continues or creates.

## Overlay template insertion (review prompt)

Shadow `planning/plan_loop_review.j2` in `--prompt-dir` with the stock template plus:

```text
# Tool contract

Your available tools are Read, Glob, and Grep only. Bash and all write
capabilities are disabled for this review. ... If a tool call is denied, do not
stop, ... continue the review with the allowed tools. ...

# Bounded inspection

Inspect only what the rubric scores. Prefer targeted Grep over full-file Reads ...
If you have made about forty inspection tool calls, stop immediately and write
the verdict ... Your final message must contain the complete verdict ... a turn
that ends with narration instead of the verdict is a failed review.
```

All other templates fall through to the packaged defaults; the planner is unaffected.

## Review outcome on the worked issue (substance)

Round 1 NOGO (revision 1) verified against source: one plan decision claimed a
documentation-level change was sufficient, but the source hard-codes the removed binary
in four places (manifest `_REQUIRED` set, launcher module map, entry-point mode set,
launcher-hash loop) — every publish would fail. Grade card: Requirements C+,
Completeness B, Concreteness C, Risk C, Verification B+, Handoff C+. Spot-checks of the
cited lines confirmed the reviewer was accurate on every sampled claim.

## Run evidence (r25, 2026-10-25, masked row-7 variant with single-variable repair)

Same multi-issue wave repository as r22–r24, some days later, queue-pipeline runs with the
opencode backend. The row-7 cause (system git 2.34.1) was present again, but the current
pipeline-era code hid it completely.

Masked signature anatomy:

- Pipeline summary: `FAIL:source_workspace_recovery_receipt_invalid: Preserve all state.
  Obtain valid ownership evidence before retry through the source manager.
  creation_failure=writer_transition`
- Stage warning: `worktree job failed: source_workspace_terminal`
- Durable record per attempt: `<checkout>/.git/hephaestus-source-workspaces/<issue>-impl-terminal.json`
  with `outcome: manual_recovery_required`. The record's cause/action text is a generic
  capture; the true inner exception is not in the record or the run log (`exc.__cause__`
  is dropped two layers up).
- Forensics hint: each failed attempt also reserved a new remote branch
  `<issue>-auto-impl-direct-<digest>` at the then-current base. Several digests on one
  issue therefore mean repeated masked-failure attempts, not distinct causes.

Diagnosis method: temporarily add `logger.exception` (exception traceback) to the worktree
worker's terminal catch and rerun once. The instrumentation printed
`subprocess.CalledProcessError: Command '['git', 'worktree', 'list', '--porcelain', '-z']'
returned non-zero exit status 129`, which names the row-7 cause. Revert the instrumentation
immediately after the run.

Repair verification (single variable): the identical launch with the host wrapper's
`<wrapper-bin>` prepended to PATH created the implement worktree and launched the implement
job; three consecutive runs without the prepend had failed before any agent call. Empirical
floor on this host: git 2.34.1 answers `error: unknown switch 'z'` (exit 129), git 2.56
completes the same subcommand. The exact upstream version that introduced `-z` was not
re-verified; the row-7 working floor (>= 2.36) stands.

Wrapper trap: a private newer-git wrapper existed in an allowlisted discovery root (through
the intended local patch) and its binary worked, but every launch without `<wrapper-bin>`
on PATH still bound the system git. The worktree enumeration resolves `git` through the
inherited PATH, so discovery registration alone is not enough.
