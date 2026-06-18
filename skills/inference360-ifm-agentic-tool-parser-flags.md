---
name: inference360-ifm-agentic-tool-parser-flags
description: "Configure IFM/K2V3 Inference360 model surfaces for agentic tool use. Use when: (1) vLLM or SGLang serves IFM/K2V3 models, (2) OpenCode or another OpenAI-compatible client uses auto tool choice, (3) errors mention --enable-auto-tool-choice or --tool-call-parser."
category: tooling
date: 2026-06-18
version: "1.0.0"
user-invocable: false
verification: verified-ci
tags: [inference360, ifm, k2v3, h200, slurm, vllm, sglang, tool-calling, opencode]
---

# Inference360 IFM Agentic Tool Parser Flags

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-06-18 |
| **Objective** | Make IFM/K2V3 model surfaces in the H200 Slurm Inference360 stack work with OpenCode and other OpenAI-compatible clients that request automatic tool choice. |
| **Outcome** | Successful. IFM parser and tool-call flags are emitted for generated manifests and launcher defaults, with vLLM also enabling automatic tool choice. |
| **Verification** | verified-ci |

## When to Use

- An Inference360 IFM/K2V3 model served through vLLM or SGLang fails OpenCode or another agentic client.
- The client error says `"auto" tool choice requires --enable-auto-tool-choice and --tool-call-parser to be set`.
- Adding or reviewing IFM M1 manifests, multi-model launcher defaults, or H200 Slurm service command args for K2V3 surfaces.
- Auditing production versus experimental surfaces for parser flags before exposing tool use.

## Verified Workflow

### Quick Reference

```bash
# vLLM IFM/K2V3 agentic surface
python -m vllm.entrypoints.openai.api_server \
  --model "$MODEL_PATH" \
  --served-model-name "$MODEL_ID" \
  --enable-auto-tool-choice \
  --reasoning-parser ifm \
  --tool-call-parser ifm

# SGLang IFM/K2V3 surface when parser flags are available
python -m sglang.launch_server \
  --model-path "$MODEL_PATH" \
  --served-model-name "$MODEL_ID" \
  --reasoning-parser ifm \
  --tool-call-parser ifm

# Inference360 multi-model launcher defaults
REASONING_PARSER="${REASONING_PARSER:-ifm}"
TOOL_CALL_PARSER="${TOOL_CALL_PARSER:-ifm}"
```

### Detailed Steps

1. Treat IFM/K2V3 agentic serving as an explicit parser configuration problem, not as a generic OpenAI route issue.
2. For vLLM surfaces, include all three flags: `--enable-auto-tool-choice`, `--reasoning-parser ifm`, and `--tool-call-parser ifm`.
3. For SGLang surfaces that support parser flags, include `--reasoning-parser ifm` and `--tool-call-parser ifm`.
4. In Inference360 generators, emit parser flags from the manifest source of truth rather than hand-patching service commands.
5. In launchers, default `REASONING_PARSER` and `TOOL_CALL_PARSER` to `ifm` for IFM model surfaces so ad hoc launches match generated manifests.
6. Add focused regression tests around generated manifests and launcher text before relying on full validation or CI.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| OpenCode against `h200-32b/k2v3-bbq-32b-mid2` without IFM parser flags | Ran an agentic client using `"auto"` tool choice against the model surface | vLLM returned `Error: "auto" tool choice requires --enable-auto-tool-choice and --tool-call-parser to be set` | IFM/K2V3 tool use must be enabled at engine launch, not only at the client or route layer |
| Set only a reasoning parser | Added IFM reasoning support but no IFM tool-call parser | Auto tool choice still lacks the parser vLLM needs to interpret tool calls | Reasoning and tool-call parsing are separate serving concerns and both must be configured |
| Set parser flags without vLLM auto tool choice | Included parser selection but omitted `--enable-auto-tool-choice` | vLLM still rejects requests that ask for automatic tool choice | vLLM requires the explicit auto-tool-choice gate in addition to parser selection |
| Hand-patch one service command | Fixed a single launch path manually | Generated manifests and multi-model launches can drift back to missing flags | Put the rule in the manifest generator and launcher defaults, then cover both with tests |

## Results & Parameters

Durable rule:

```text
IFM/K2V3 model surfaces using vLLM:
  --enable-auto-tool-choice
  --reasoning-parser ifm
  --tool-call-parser ifm

IFM/K2V3 model surfaces using SGLang with parser flag support:
  --reasoning-parser ifm
  --tool-call-parser ifm
```

Inference360 implementation points verified in the session:

```text
scripts/generate_ifm_m1_manifests.py
  Emits vLLM IFM flags, including --enable-auto-tool-choice,
  --reasoning-parser ifm, and --tool-call-parser ifm.

multi-model IFM launcher
  Defaults REASONING_PARSER="${REASONING_PARSER:-ifm}"
  Defaults TOOL_CALL_PARSER="${TOOL_CALL_PARSER:-ifm}"
  Includes --enable-auto-tool-choice in the vLLM command path.
```

Regression tests added or verified:

```text
test_ifm_vllm_manifests_enable_ifm_tool_and_reasoning_parsers
test_ifm_manifest_parser_flags_use_ifm
test_ifm_m1_manifest_generator_emits_ifm_tool_and_reasoning_parsers
test_multi_model_ifm_launcher_defaults_to_ifm_agentic_parsers
```

Verification evidence:

```text
Focused tests passed.
Full local validation passed.
CI passed on Inference360 PR #161.
Verification level: verified-ci.
```

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| LLM360/Inference360 | PR #161 IFM/K2V3 agentic parser flags for H200 Slurm model surfaces | OpenCode failure fixed by vLLM/SGLang IFM parser flags, focused tests passed, full local validation passed, CI passed |
