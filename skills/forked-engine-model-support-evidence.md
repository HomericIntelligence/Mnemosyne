---
name: forked-engine-model-support-evidence
description: "Verify which models a serving engine supports, and under which constraints, when organization forks differ from upstream. Use when: (1) a task asks which models an inference engine supports or whether one model runs under vLLM or SGLang, (2) the answer must cover continuous batching, paged attention, prefix caching, or KV-cache behavior, (3) support can exist only in a fork or under an internal class name, (4) a catalog page, model card, or recipe is offered as support evidence."
category: evaluation
date: 2026-10-28
version: "1.0.0"
user-invocable: false
tags: [vllm, sglang, model-support, fork, model-registry, attention, pagedattention, continuous-batching, kv-cache, xllm]
---

# Forked-Engine Model-Support Evidence

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-28 |
| **Objective** | Give an evidence-bound answer to engine model-support questions when organization engine forks differ from upstream. |
| **Outcome** | Successful. Code-bound evidence replaced docs-based claims: an internal model family was found in the vLLM fork registry, a MoVA variant existed only in the pinned SGLang fork, and the absence in the upstream checkout was shown to be non-evidence. |

## When to Use

- A question asks which models an inference engine supports, or whether one
  model runs under vLLM, SGLang, or a comparable engine.
- The organization pins engine forks, and the upstream checkout and the fork
  can differ.
- A deployment catalog, model page, or upstream recipe is offered as evidence
  of model support.
- The answer spans continuous batching, PagedAttention or radix paging,
  prefix caching, speculative decoding, or KV-cache capacity.
- A support claim depends on runtime dtype, attention variant, tensor- or
  expert-parallel topology, or quantization scope.

## Verified Workflow

### Quick Reference

```bash
# vLLM: registered architectures live in the model registry map.
grep -oE '"[A-Za-z0-9_]+":' vllm/model_executor/models/registry.py

# SGLang: each model file exports its classes in EntryClass. Keep digits in
# the pattern, or names such as "K25" are truncated.
grep -hoE 'EntryClass\s*=\s*\[([^]]+)\]' python/sglang/srt/models/*.py

# The pinned fork revision is not local? Fetch it. Do not trust upstream:
curl -fsSL "https://raw.githubusercontent.com/<org>/<repo>/<pinned-rev>/<path>"
```

### Suggested Approach

1. Bind the question to exact artifacts and revisions. Select the engine
   checkout that the deployment pins, not the newest upstream checkout. A
   negative find in upstream is not evidence of no support. A positive find
   upstream is not evidence of the pinned deployment.
2. Enumerate support through each engine's own registration mechanism. vLLM
   keeps the architecture map in `model_executor/models/registry.py`. SGLang
   keeps per-file `EntryClass = [...]` lists. Match model directory names and
   configuration `model_type` strings too: an internal model family can
   register under a class name that differs from the public artifact name.
3. Read the model loader's validator paths. `raise ValueError` branches are
   the machine-readable support matrix: dtype contracts, attention-variant
   restrictions, tensor-parallel and expert-parallel topology limits,
   quantization scope, and excluded runtime modes. These constraints belong in
   the answer.
4. Classify the attention architecture before batching and paging claims:
   grouped-query attention, multi-head latent attention, linear, or hybrid.
   Continuous batching and paged KV cache are engine-level properties that
   apply to each registered model. The attention class decides the page
   layout and the KV bytes per token. For a full-K/V GQA model, estimate
   bytes per token as
   `layers x KV heads x head_dim x 2 (K and V) x dtype_bytes` and compare the
   result with the context profile before concurrency claims.
5. Keep code support separate from operational qualification. A row can be
   code-supported and blocked by catalog gates. Record both states
   independently.
6. If a checkout lacks the fork content, fetch the pinned revision directly,
   for example through the raw content host, and review the loader at that
   revision. Record each retrieval limit.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Judge support from the upstream checkout | Searched the upstream SGLang checkout for the internal model name | The model lived only in the organization SGLang fork at a pinned revision; upstream had neither the model file nor its MoVA layer | Fork pins are the ground truth for internal models. Upstream absence is not evidence of no support. |
| Extract class names without digits | Parsed `EntryClass` lists with the pattern `[A-Za-z_,\s]+` | Classes with digits in the name were truncated, which corrupted the support diff | Include digits in identifier patterns for model classes. |
| Treat the catalog as code evidence | Read deployment catalog rows as the support matrix | The catalog recorded gates and policies; the loader code defined what loads | Catalogs record qualification status. Code support lives in the loader and its validator paths. |

## Results & Parameters

### Configuration

Record these fields with a model-support claim:

```text
engine_checkout: <fork remote and checked-out revision>
model_inventory: registry map (vllm) | EntryClass scan (sglang)
support_constraints: validator reject paths in the model loader
attention_class: gqa | mla | linear | hybrid
kv_bytes_per_token: layers x kv_heads x head_dim x 2 x dtype_bytes
qualification_status: catalog gates, recorded separately from code support
```

### Expected Output

- A per-engine, per-artifact support statement that names the implementing
  class, the revision, and the loader constraints.
- An explicit separation of code support from qualification gates.
- A KV-bytes-per-token estimate when paged-cache capacity matters for the
  context profile.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| LLM360/comet, LLM360/vllm fork, LLM360/sglang fork | K2-Horizon engine-support analysis: internal family registered as `XllmForCausalLM` in the vLLM fork; MoVA and configuration normalization only in the pinned SGLang fork; the upstream sglang checkout had neither | [notes.md](./forked-engine-model-support-evidence.notes.md) |

## References

- [deployed-version-runbook-goal-feasibility](deployed-version-runbook-goal-feasibility.md) — read code at the deployed or pinned ref; main and docs are not evidence of that ref.
- [debugging-prefix-cache-nsight-kernel-evidence](debugging-prefix-cache-nsight-kernel-evidence.md) — prefix-cache nondeterminism evidence that a paged-cache investigation can need next.
