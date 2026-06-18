# Inference360 IFM Agentic Tool Parser Flags Notes

Raw learning captured on 2026-06-18.

## Error

OpenCode command failure against model `h200-32b/k2v3-bbq-32b-mid2`:

```text
Error: "auto" tool choice requires --enable-auto-tool-choice and --tool-call-parser to be set
```

## Durable Rule

For IFM/K2V3 model surfaces using vLLM, launch args must include:

```text
--enable-auto-tool-choice
--reasoning-parser ifm
--tool-call-parser ifm
```

For SGLang model surfaces with parser flag support, launch args must include:

```text
--reasoning-parser ifm
--tool-call-parser ifm
```

## Inference360 Session Evidence

- `scripts/generate_ifm_m1_manifests.py` emits IFM parser and tool flags.
- The multi-model launcher defaults `REASONING_PARSER="${REASONING_PARSER:-ifm}"`.
- The multi-model launcher defaults `TOOL_CALL_PARSER="${TOOL_CALL_PARSER:-ifm}"`.
- The vLLM command path includes `--enable-auto-tool-choice`.

Regression tests added or verified:

```text
test_ifm_vllm_manifests_enable_ifm_tool_and_reasoning_parsers
test_ifm_manifest_parser_flags_use_ifm
test_ifm_m1_manifest_generator_emits_ifm_tool_and_reasoning_parsers
test_multi_model_ifm_launcher_defaults_to_ifm_agentic_parsers
```

Verification evidence reported from the source repository:

```text
focused tests passed
full local validation passed
CI passed on Inference360 PR #161
verification: verified-ci
```
