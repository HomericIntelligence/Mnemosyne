---
name: tooling-claude-cli-keep-prompts-off-argv
description: "Keep sensitive or large Claude CLI prompts out of process arguments by routing them through stdin without breaking session create/resume, model fallback, or best-effort compaction. Use when: (1) an automation pipeline passes generated prompts to Claude, (2) multiple dispatch types invoke Claude through different subprocess seams, (3) tests must prove prompt content is absent from argv for ordinary and very large inputs."
category: tooling
date: 2026-08-05
version: "1.0.0"
user-invocable: false
verification: unverified
tags:
  - claude-cli
  - stdin
  - prompt-transport
  - process-arguments
  - subprocess
  - session-resume
  - model-fallback
  - compact
  - security
  - testing
---

# Keep Claude CLI Prompts Off Argv

## Overview

| Field | Value |
| ----- | ----- |
| **Date** | 2026-08-05 |
| **Objective** | Route every live pipeline Claude prompt or command through stdin so sensitive or large content never enters process arguments. |
| **Outcome** | Source-reviewed implementation handoff covering both helper-based agent dispatch and the separate direct `/compact` subprocess path. Implementation and tests were not executed in the learning session. |
| **Verification** | unverified |

## When to Use

- A Python automation service passes issue bodies, diffs, plans, reviews, credentials, or other sensitive generated content to the Claude CLI.
- Prompt size can reach shell or operating-system argument limits, even though the subprocess API accepts the command as an argv list rather than a shell string.
- A pipeline has more than one Claude execution route, such as ordinary agent jobs through a shared helper and maintenance commands through direct `subprocess.run(...)` calls.
- Stdin transport must preserve deterministic session creation and resume, model-cap fallback, output parsing, retry behavior, and tool scopes.
- A shared helper already has an opt-in stdin seam, but only selected live callers should enable it while compatibility callers retain positional-prompt behavior.
- Regression tests need to prove both ordinary and 200,000-character prompts stay intact at the invocation boundary and never appear in argv.

## Verified Workflow

> **Warning:** This workflow has not been validated end-to-end. Treat it as a hypothesis until the focused tests and CI confirm it.

No workflow is verified yet; the proposed steps below are source-aligned implementation guidance.

### Quick Reference

```bash
# Inventory helper-based and direct Claude dispatches separately.
rg -n 'invoke_claude_with_session|subprocess\.run|CompactJob|AgentJob|/compact' \
  hephaestus/automation tests/unit/automation

# After implementing the transport changes, verify both live routes and the
# session/fallback invariants.
uv run pytest \
  tests/unit/automation/pipeline/test_worker_pool.py \
  tests/unit/automation/test_claude_invoke_session.py \
  tests/unit/automation/test_compact.py -v
```

### Detailed Steps

1. **Trace dispatch by job type before editing.** Start at the worker's type switch and follow every live Claude route. Do not assume all Claude work passes through the same helper. In the ProjectHephaestus example, `AgentJob` reaches `_run_agent()` and `invoke_claude_with_session(...)`, while `CompactJob` reaches `_run_compact()`, `compact_agent_session()`, and a direct `subprocess.run(...)` in `compact_session()`.

2. **Reuse the helper's transport seam for ordinary agent jobs.** Keep prompt construction, session-agent identity, model, cwd, timeout, output format, tool scope, permissions, retries, and parsing unchanged. Opt the live pipeline caller in explicitly:

   ```python
   stdout, _ = invoke_claude_with_session(
       repo=job.repo,
       issue=job.issue,
       agent=session_agent,
       prompt=prompt,
       model=job.model,
       cwd=job.cwd,
       timeout=job.timeout_s,
       output_format=job.output_format,
       allowed_tools=scope.allowed_tools,
       permission_mode=scope.permission_mode,
       input_via_stdin=True,
   )
   ```

3. **Preserve the helper's compatibility default.** Leave `input_via_stdin=False` on the shared helper. In stdin mode, build create/resume/model flags exactly as before, append `--print`, omit the prompt from `cmd`, and invoke the tracked subprocess with:

   ```python
   stdin_text=prompt
   use_devnull_stdin=False
   ```

   Positional-mode callers should continue appending the prompt to argv and using the existing stdin behavior. This keeps the change local to the pipeline paths that require it.

4. **Move direct slash commands independently.** A direct compaction helper does not inherit the shared helper's stdin setting. Retain its deterministic `--resume <session-id>` command and move only `/compact` from argv to the subprocess input:

   ```python
   result = subprocess.run(
       [
           "claude",
           "--resume",
           sid,
           "--output-format",
           "text",
           "--print",
       ],
       input="/compact",
       cwd=str(cwd),
       timeout=timeout_s,
       check=False,
       capture_output=True,
       text=True,
   )
   ```

5. **Keep identity and fallback logic outside the transport change.** Session UUID derivation, create-versus-resume probing, and fallback-model selection should not depend on whether input is positional or stdin. A model-cap retry must receive the same prompt on stdin for every attempt, while retaining the established model-specific deterministic session identity.

6. **Keep compaction best-effort.** Do not turn `/compact` into a pipeline gate. Preserve timeout and `OSError` handling, non-zero-to-`False` behavior, zero-exit-to-`True` behavior, and the worker's successful completion wrapper even when compaction returns `False`.

7. **Test at each behavior boundary.** Add or retain these regressions:

   - Worker boundary: parameterize an ordinary prompt and `"sensitive-large-prompt:" + ("x" * 200_000)`; assert the prompt reaches the helper intact and `input_via_stdin is True`.
   - Helper boundary: for both prompt sizes, assert argv ends at `--print`, no argv element contains the prompt, `stdin_text` equals the prompt, and `use_devnull_stdin is False`.
   - Create/resume: make the first mocked call create the deterministic transcript; assert the next call resumes the same UUID, each stdin payload is distinct, and neither appears in argv.
   - Model fallback: force the first attempt to hit a model cap; assert every attempt receives the same stdin prompt and no attempt exposes it in argv.
   - Compaction: assert `/compact` is absent from every argv element, equals `subprocess.run(input=...)`, and uses text mode.
   - Best effort: retain timeout, missing-binary, non-zero, zero-exit, and failed-compaction pipeline-result tests.

8. **Run overlapping acceptance slices.** Run the worker plus compact tests to prove both live routes, the invocation plus compact tests to prove argv absence, and finally all three files together to detect shared-fixture or stateful-fallback interactions.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| ------- | -------------- | ------------- | -------------- |
| Treat Claude invocation as one shared boundary | Planned only the ordinary `AgentJob` call to `invoke_claude_with_session(...)` | `CompactJob` follows a separate direct subprocess route, leaving `/compact` in argv | Trace the worker's full type dispatch and inventory helper-based and raw-subprocess paths independently |
| Change only the helper internals | Relied on the existing stdin option without opting the live pipeline caller into it | The helper default intentionally remains positional for compatibility, so the production caller would still expose prompts | Keep the default stable and set `input_via_stdin=True` at the live caller |
| Assert only that the prompt is not a standalone argv item | Used membership-style checks that can miss prompt content embedded inside another argument | Sensitive content is exposed even when concatenated with a flag or prefix | Assert the prompt is absent as a substring from every argv element |
| Test only a short prompt | Verified transport with a small constant | It does not guard the large-input reason for using stdin or catch accidental truncation at the boundary | Parameterize ordinary and 200,000-character inputs and assert exact stdin equality |
| Route `/compact` through a new abstraction | Considered unifying direct compaction with ordinary agent invocation | It changes more than transport and risks session, tool, parsing, and best-effort semantics | Make the smallest direct subprocess edit: remove the command from argv and add `input="/compact"` |
| Treat failed compaction as a failed job | Propagated `False` as pipeline failure | Compaction is an optimization; making it a gate can stall otherwise valid work | Preserve non-fatal return values and the worker's successful completion contract |

## Results & Parameters

| Parameter or invariant | Required value |
| ---------------------- | -------------- |
| Pipeline helper opt-in | `input_via_stdin=True` |
| Shared-helper default | `input_via_stdin=False` |
| Ordinary test prompt | `ordinary prompt` |
| Large test payload | 200,000 `x` characters after a recognizable prefix |
| Claude argv terminator in stdin mode | `--print` |
| Tracked subprocess stdin | Exact prompt text |
| Tracked subprocess devnull flag | `use_devnull_stdin=False` |
| Direct compaction stdin | `/compact` |
| Direct compaction text mode | `text=True` |
| Session behavior | Existing deterministic create/resume identity unchanged |
| Model-cap behavior | Same stdin prompt on original and fallback attempts |
| Compaction behavior | Timeout, `OSError`, or non-zero exit returns `False`; zero exit returns `True`; pipeline job remains non-fatal |
| Verification command | `uv run pytest tests/unit/automation/pipeline/test_worker_pool.py tests/unit/automation/test_claude_invoke_session.py tests/unit/automation/test_compact.py -v` |

## Verified On

| Project | Context | Details |
| ------- | ------- | ------- |
| ProjectHephaestus | Queue-pipeline stdin-transport implementation handoff | Source paths and test seams were reviewed; implementation, local tests, and CI remained pending, so verification stays `unverified` |
