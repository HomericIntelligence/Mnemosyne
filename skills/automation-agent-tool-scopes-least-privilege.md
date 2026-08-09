---
name: automation-agent-tool-scopes-least-privilege
description: "Enforce and test least-privilege tool policy at both host job construction and provider invocation boundaries. Use when: (1) an automation role must be non-mutating, (2) ambient CLI configuration can add tools, plugins, hooks, skills, or MCP servers, (3) caller grants must not broaden read-only execution, (4) a stage-produced AgentJob must carry an exact builder/parser/tool contract, or (5) older CLIs must fail closed instead of retrying under weaker defaults."
category: architecture
date: 2026-08-05
version: "2.1.0"
user-invocable: false
verification: unverified
history: automation-agent-tool-scopes-least-privilege.history
tags:
  - automation
  - least-privilege
  - allowed-tools
  - tool-availability
  - read-only
  - permission-mode
  - strict-mcp
  - bare-mode
  - security
  - fail-closed
  - claude-cli
  - provider-adapter
  - policy-lock-tests
  - agent-job
  - host-owned-policy
---

# Automation Agent Tool Scopes: Enforce Availability, Not Just Permission

**History:** [changelog](./automation-agent-tool-scopes-least-privilege.history)

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-08-05 |
| **Objective** | Make headless agent permissions host-owned, visible in stage-produced jobs, and enforced as provider tool availability rather than prompt prose. |
| **Outcome** | V2.0 provider enforcement succeeded locally. V2.1 proposes an additional stage-boundary contract over the job's builder, parser, structured inputs, and exact tool scope. |
| **Verification** | `unverified` for the v2.1 stage-job extension; the v2.0 provider-adapter behavior remains `verified-local`, with live Claude execution and CI still pending. |

### Core distinction

For Claude Code, these flags answer different questions:

- `--allowedTools` controls which matching tool calls execute without a permission
  prompt. It does **not** restrict which tools are available to the model.
- `--tools` restricts built-in tool availability. It does not restrict MCP tools.
- `--bare` skips automatic discovery of project/user hooks, skills, plugins, MCP
  servers, memory, and instruction files for the scripted call.
- `--strict-mcp-config` limits MCP loading to the supplied `--mcp-config`.
- None of these flags creates an operating-system sandbox. They constrain the
  model-visible tool/configuration surface inside Claude Code.

The authoritative behavior is documented in the
[Claude CLI reference](https://code.claude.com/docs/en/cli-usage) and
[custom tools reference](https://code.claude.com/docs/en/agent-sdk/custom-tools).

## When to Use

- A provider-neutral option such as `sandbox="read-only"` must be translated into
  an enforceable Claude policy.
- A headless reviewer, classifier, planner, or audit runner must inspect files
  without write, edit, or shell tools.
- A call currently omits Claude permission flags in read-only mode and therefore
  inherits ambient CLI behavior.
- A call passes only `--allowedTools Read,Glob,Grep` and reviewers assume that
  makes other built-ins unavailable.
- Project/user plugins, hooks, skills, or MCP servers could widen the execution
  surface of a scripted invocation.
- An older CLI may not support required enforcement flags and the caller must fail
  the stage instead of silently retrying with weaker defaults.
- Caller-supplied `allowed_tools` must remain configurable for workspace-write
  runs but must never broaden read-only runs.
- A stage creates an `AgentJob` for remediation or review and tests currently infer
  permissions or parser behavior from prompt wording instead of inspecting the job.

## Verified Workflow

Verified locally only — CI and a live Claude CLI invocation are pending.

### Quick Reference

For a Claude read-only one-shot invocation, append this exact policy:

```text
--bare
--permission-mode dontAsk
--tools Read,Glob,Grep
--allowedTools Read,Glob,Grep
--strict-mcp-config
--mcp-config {"mcpServers":{}}
```

The provider-neutral API may keep `sandbox="read-only"`, but the Claude adapter
must translate that value into the explicit policy above. Workspace-write behavior
can continue using the caller-supplied `allowed_tools`.

### Detailed Steps

1. **Keep the public option provider-neutral.** Preserve existing
   `sandbox="read-only"` and `sandbox="workspace-write"` values. Translate them
   inside the provider adapter instead of leaking Claude-specific flags into every
   caller.

2. **Reuse one canonical read-only scope.** Source the tool list from the
   repository's established reviewer/classifier policy rather than inventing a new
   string at the direct runner:

   ```python
   CLAUDE_READ_ONLY_TOOLS = "Read,Glob,Grep"
   CLAUDE_EMPTY_MCP_CONFIG = '{"mcpServers":{}}'
   ```

3. **Enforce built-in availability as well as permission pre-approval.** In the
   Claude read-only branch, pass the same fixed scope to both `--tools` and
   `--allowedTools`. The first constrains the model-visible built-ins; the second
   lets those non-mutating tools execute under `dontAsk`.

4. **Close ambient extension paths.** Add `--bare` to skip automatic discovery
   of project/user hooks, skills, plugins, MCP servers, memory, and instruction
   files. Pair it with `--strict-mcp-config` and an explicit empty MCP object
   because `--tools` does not constrain MCP tools.

5. **Clamp read-only input at the adapter boundary.** Ignore a caller-supplied
   `allowed_tools` value when `sandbox == "read-only"`. Hard-code the fixed
   read-only scope in that branch so `Write`, `Edit`, or `Bash` cannot be
   reintroduced through an argument.

6. **Preserve workspace-write behavior.** In every other sandbox mode, keep the
   existing `dontAsk` plus caller-supplied `--allowedTools` construction. A
   security fix for read-only execution should not silently change writer roles.

7. **Fail closed on incompatible CLIs.** Retain the non-raising
   `subprocess.run(..., check=False)` contract. If an older Claude CLI rejects
   `--bare`, `--tools`, or strict MCP flags, return its nonzero status and let
   the stage propagate it. Never retry after deleting enforcement flags.

8. **Test behavior at the command boundary.** Add tests that assert:
   - the full read-only argv exactly;
   - caller grants cannot widen the `--tools` or `--allowedTools` sets;
   - a nonzero policy rejection is returned by the stage without fallback;
   - workspace-write argv remains unchanged;
   - documentation calls the feature a tool policy rather than an OS sandbox.

9. **Keep role maps and provider enforcement separate.** A central per-role policy
   map remains useful for choosing the intended scope at one chokepoint. The
   provider adapter must still translate that intent into an actual availability
   boundary. A map that only feeds `--allowedTools` is permission policy, not
   read-only enforcement.

## Proposed Stage-Job Contract Extension

> **Warning:** This extension has not been validated end-to-end. Treat it as a hypothesis until the stage tests and CI pass.

Provider-adapter tests prove the final CLI boundary, but they do not prove that a stage
selected the intended prompt builder, result parser, structured input, or workspace-write
scope. Assert those fields on the host-produced job before the agent runs:

```python
result = stage.handle(work_item)

assert result.job.prompt_builder is expected_prompt_builder
assert result.job.parse is expected_result_parser
assert result.job.allowed_tools == EXPECTED_STAGE_TOOL_SCOPE
assert json.loads(result.job.prompt_kwargs["threads_json"]) == expected_threads
```

Use the exact scope owned by the production stage. For example, an address-remediation job
may intentionally include read/write/edit/shell/task/skill tools, while a reviewer job must
remain read-only. The stable contract is the job field and provider-enforced availability,
not a sentence inside the prompt claiming which tools are allowed.

Keep both layers:

1. **Stage boundary:** the correct route constructs a job with the intended builder, parser,
   structured kwargs, and scope.
2. **Provider boundary:** sandbox mode clamps or translates that scope into enforceable CLI
   availability and fails closed on incompatibility.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Ambient CLI defaults | Omit permission/tool flags for a headless read-only call | The invocation inherits ambient built-ins and configuration; absence of explicit write grants is not proof that write paths are unavailable | Construct the complete restrictive policy explicitly |
| `--allowedTools Read,Glob,Grep` as the only boundary | Treat pre-approved tools as the total available set | Claude's CLI reference states that `--allowedTools` skips permission prompts and directs callers to `--tools` to restrict availability | Use both flags with the same fixed scope |
| `--bare` alone | Assume minimal mode means read-only | Bare mode disables discovery but still provides built-in Bash, read, and edit tools unless `--tools` restricts them | Combine discovery isolation with an explicit built-in allowlist |
| `--tools` alone | Restrict built-ins but leave ambient MCP sources enabled | The CLI reference explicitly says `--tools` does not affect MCP tools | Add a strict empty MCP configuration |
| Caller-configurable read-only scope | Reuse `allowed_tools` in both read-only and workspace-write branches | A caller can accidentally or deliberately add `Write`, `Edit`, or `Bash` to a supposedly read-only call | Override caller grants with a fixed constant in read-only mode |
| Compatibility fallback | Retry an older CLI after removing unsupported policy flags | The retry succeeds under a weaker surface and turns a visible compatibility failure into a silent security downgrade | Preserve the nonzero result and do not retry |
| Call it a sandbox | Describe Claude CLI tool/configuration flags as filesystem isolation | These controls operate inside Claude Code and do not provide seccomp, namespaces, chroot, or OS-level write prevention | Document this as model-tool restriction |
| Run selected tests under the repository-wide coverage gate | Execute only five node IDs while `fail-under=83` remained enabled | All assertions passed, but pytest exited nonzero because selected tests cover only a small fraction of the package | Use `--no-cov` for focused behavior checks and run the full coverage suite separately |
| Test permissions through prompt wording | Assert that the rendered prompt says which tools an agent may use | Prompt prose does not construct or enforce the host job; a differently scoped `AgentJob` can still run | Assert the stage-produced job's exact scope, then separately test provider enforcement |
| Test only the provider adapter | Locked final CLI argv but did not prove the stage selected the intended builder, parser, or structured input | Correct adapter behavior cannot repair a wrongly constructed job or route | Add a stage-level job-construction assertion beside the adapter tests |

## Results & Parameters

### Reference adapter shape

```python
def run_claude_text(
    prompt: str,
    *,
    cwd: Path,
    timeout: int,
    model: str = "",
    sandbox: str = "workspace-write",
    allowed_tools: str = "Read,Write,Edit,Glob,Grep,Bash",
) -> subprocess.CompletedProcess[str]:
    """Run Claude Code with an explicit tool policy for read-only calls."""
    cmd = ["claude", "--print", "--output-format", "text"]
    if model:
        cmd.extend(["--model", model])

    if sandbox == "read-only":
        cmd.extend(
            [
                "--bare",
                "--permission-mode",
                "dontAsk",
                "--tools",
                CLAUDE_READ_ONLY_TOOLS,
                "--allowedTools",
                CLAUDE_READ_ONLY_TOOLS,
                "--strict-mcp-config",
                "--mcp-config",
                CLAUDE_EMPTY_MCP_CONFIG,
            ]
        )
    else:
        cmd.extend(
            [
                "--permission-mode",
                "dontAsk",
                "--allowedTools",
                allowed_tools,
            ]
        )

    return subprocess.run(cmd, ..., check=False)
```

### Expected read-only command

```python
[
    "claude",
    "--print",
    "--output-format",
    "text",
    "--bare",
    "--permission-mode",
    "dontAsk",
    "--tools",
    "Read,Glob,Grep",
    "--allowedTools",
    "Read,Glob,Grep",
    "--strict-mcp-config",
    "--mcp-config",
    '{"mcpServers":{}}',
]
```

### Verification checklist

- Assert the exact read-only command sequence, not merely the absence of write
  flags.
- Pass a deliberately broad caller scope and compare both effective tool sets
  to the fixed read-only set.
- Return a fake incompatible-CLI result and assert the stage preserves its
  nonzero exit code.
- Lock the existing workspace-write command as a regression test.
- Assert stage-produced job builder/parser identity, decoded structured kwargs,
  and the exact host-owned scope for each security-sensitive route.
- Run focused tests independently from any repository-wide coverage threshold,
  then run the project's full coverage gate separately.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| ProjectHephaestus | Issue #2369 plan applied in a disposable worktree | [Local verification evidence](./automation-agent-tool-scopes-least-privilege.notes.md) |
| ProjectHephaestus | Issue #1950 behavior-first test refactor plan | Proposed remediation-job assertions for builder, parser, decoded thread JSON, and host-owned tool scope; implementation and CI pending. |
