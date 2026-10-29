# Notes: forked-engine-model-support-evidence

Session evidence for the skill, October 2026, LLM360 org.

## Support analysis pattern applied to K2-Horizon

- Question: does the internal K2-Horizon family support continuous batching
  and PagedAttention under vLLM, with which attention-architecture limits.
- The family is internal (`IFM/K2-Horizon-*`, architecture
  `K2HorizonForCausalLM`, `model_type: k2_horizon`; catalog:
  `comet` repository, `docs/k2-horizon/models.md` and
  `deployment/k2-horizon/source-profiles.yaml`).
- vLLM: the organization fork checkout (remote `LLM360/vllm`) registers
  `XllmForCausalLM -> xllm.py` in `vllm/model_executor/models/registry.py`,
  added by fork commits such as `c5abce00f` ("Add native XllmForCausalLM
  model support"). It implements `SupportsPP`, `SupportsLoRA`,
  `SupportsEagle3`, and `MixtureOfExperts`, so the v1 continuous-batching
  and paged-KV path applies without a special cache layout. The attention is
  plain grouped-query attention, not MLA.
- SGLang: the checkout was the upstream `sgl-project` remote. It had no
  `xllm`/K2 model and no `layers/mova.py`. Support exists only in the
  `LLM360/sglang` fork at the pinned revision recorded in the catalog docs
  (`9040ecfd...`): `python/sglang/srt/models/xllm.py`,
  `xllm_mova_fp8.py`, and `layers/mova.py`, fetched directly for review.
- MoVA (mixture-of-value-attention) support: SGLang fork only. The vLLM
  `xllm.py` contained no MoVA code. For the 36B MoVA rows this made SGLang
  the only candidate engine even before qualification status was checked.

## Validator paths as the support matrix

The SGLang fork's `xllm.py` rejects loader/runtime combinations instead of
silently serving them differently. These reject paths supplied the
constraints section of the support answer:

- Runtime dtype must be `bfloat16`: released checkpoints persist float32
  metadata while the weights and validated runtime contract are BF16.
- Dense rows: no query/key normalization, no sliding-window attention, no
  gated attention; explicit `rope_parameters` required (default or YaRN).
- MoVA rows: bias-free Q/K/V/O projections; the xLLM attention gate is
  required (`silu` or `softplus`); full-head interleaved RoPE (`rope_head_dim
  == head_dim`); default RoPE only; `TP <= KV heads` with KV heads divisible
  by TP (TP in {1, 2, 4, 8} for 8 KV heads); the dense-layer prefix must
  match the MoE layout exactly.
- MoVA value routing needs explicit source router GEMM provenance
  (partitions 1 or 2, passed as a model override); the runtime does not
  infer it from tensor parallelism. This was the catalog's
  "Blocked: router provenance" gate.
- Excluded runtime modes: two-batch overlap; EPLB, non-trivial expert
  placement, and redundant experts (no logical-to-physical remap);
  elastic expert joining for MoVA FP8; quantization limited to
  compressed-tensors (plus fp8 for MoVA with provenance).

## Numbers used in the answer

- KV footprint for full-K/V GQA, BF16: 375B = 61 layers x 8 KV heads x
  128 head_dim x 2 x 2 B = about 244 KiB per token, about 122 GiB for one
  full 524,288-token context. 0.9B = about 56 KiB per token. These estimates
  showed that batching at 524k context is KV-capacity-limited, not
  engine-limited.
- Registry diff at the inspected revisions: vLLM fork 247 registered
  classes, upstream SGLang 142 `EntryClass` classes, 66 shared. 181
  vLLM-only (included `XllmForCausalLM`, KimiLinear, KimiVL) and 76
  SGLang-only (included DeepseekV4 with MTP variants, KimiK25 with Eagle3,
  MiMoV2, MiniMaxM3Sparse, Qwen3_5 multimodal, GlmMoeDsa, NemotronH MTP,
  Grok1, HYV3). K2-Horizon existed only through the forks.

## Qualification kept separate from code support

- Catalog (`comet/src/comet/k2_vllm_compatibility.py`,
  `k2_sglang_compatibility.py`) marked every K2-Horizon row as blocked or
  qualification-pending: SGLang gates LLM360/sglang#49, #50, comet#811,
  #874, #848; vLLM gates comet#926, #542, #1144, #872, #901, #877, #845,
  plus #847 (FP8), #868 (typed `moe_backend: triton`), #874/#848 (Uno).
- Uno rows need conditional LoRA plus diffusion sampling, which neither
  engine implements; the publisher reference engine was a different one.
  This is a code-support absence, independent of the gates.

## Regex fix that corrected the diff

The first registry scan used `EntryClass\s*=\s*\[?([A-Za-z_,\s]+)\]?`. It
truncated every class with a digit: `KimiK25ForConditionalGeneration`
became `KimiK`, which removed rows from the intersection set and distorted
the support comparison. The corrected pattern used `([^]]+)` and kept
digits. Diff results were recomputed and quoted above.
