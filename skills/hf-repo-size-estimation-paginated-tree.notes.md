# Notes: hf-repo-size-estimation-paginated-tree

Session evidence for the main entry. All repositories below are public on
Hugging Face. Staged-copy figures come from an internal serving stack; the
staging paths and hostnames are internal and are omitted by policy.

## Trigger

A storage-budget question preceded the registration of 15 new model variants:
if the new set plus three already-supported families were all staged, would
the total stay under a 30 TB threshold? The answer needed byte sizes for 29
public repositories before any staging occurred.

## The truncation failure

The first measurement used one `tree/main?recursive=true&expand=true` GET per
repository and summed the returned array. Result for `deepseek-ai/DeepSeek-V4.1-Flash`:

- Reported: 43 files, 5 weight shards, about 22 GiB total.
- The staged copy of the same pinned revision held about 476 GiB.
- Shard names proved the truncation: the listing stopped at
  `model-00005-of-00048.safetensors`; the `-of-00048` total showed 43 weight
  shards were missing from page one.
- The response was HTTP 200 with parseable JSON and no error field. Only the
  HTTP `Link: <...>; rel="next"` response header indicated further pages.

After a paginated re-read (follow `rel="next"` until absent), the same
repository measured 0.464 TiB (about 476 GiB), matching the staged copy.

## Fleet totals after correct pagination

Public weight-byte measurements (all pages, full-repo sums), 2026-10-08:

| Repository | TiB |
| --- | --- |
| XiaomiMiMo/MiMo-V2.6-Pro-RL | 0.522 |
| Qwen/Qwen3.8-Flash-Next | 0.327 |
| Qwen/Qwen3.8-Flash-Next-FP8 | 0.169 |
| Qwen/Qwen3.8-2.4T-A95B | 4.450 |
| Qwen/Qwen3.8-2.4T-A95B-FP8 | 2.270 |
| deepseek-ai/DeepSeek-V4.1-Flash | 0.464 |
| zai-org/GLM-5.3 | 0.687 |
| MiniMaxAI/MiniMax-M3 | 0.777 |
| thinkingmachines/Inkling | 1.732 |
| thinkingmachines/Inkling-Small | 0.484 |
| nvidia/NVIDIA-Nemotron-3-Ultra-550B-A55B-NVFP4 | 0.320 |
| nvidia/NVIDIA-Nemotron-3-Ultra-550B-A55B-BF16 | 1.020 |
| Motif-Technologies/Motif-3-Beta | 0.573 |
| nex-agi/Nex-N2.5-Max | 1.505 |
| nex-agi/Nex-N2.5-Pro | 0.370 |
| meta-models/Muse-Glimmer-30B | 0.054 |
| IFM/K2-Horizon-375B-A23B | 0.690 |
| IFM/K2-Horizon-MoVA-36B-A4B | 0.068 |
| IFM/K2-Horizon-32B | 0.063 |
| IFM/K2-Horizon-7B | 0.016 |
| IFM/K2-Horizon-3.7B | 0.009 |
| IFM/K2-Horizon-0.9B | 0.002 |
| IFM/K2-Horizon-7B-Uno | 0.001 |
| IFM/K2-Horizon-0.9B-Uno | 0.000 |
| IFM/K2-Horizon-375B-A23B-FP8 | 0.355 |
| IFM/K2-Horizon-MoVA-36B-A4B-FP8 | 0.044 |
| IFM/K2-Horizon-32B-FP8 | 0.034 |
| IFM/K2-Horizon-7B-FP8 | 0.010 |
| moonshotai/Kimi-K3 | 1.420 |

Decision-relevant observations:

- The 2.4T-parameter Qwen artifact measured 4.45 TiB, its FP8 sibling 2.27
  TiB. Parameter-count arithmetic would have needed the precision up front;
  the listing removed that guess.
- One NVIDIA product name covered 0.32 TiB (NVFP4) and 1.02 TiB (BF16)
  repositories. The operator selected BF16; the estimate binds to that exact
  repository. This is the variant-binding example in the main entry.
- XiaomiMiMo/MiMo-V2.6-Pro returned HTTP 401 to anonymous reads. The public
  RL derivative (0.522 TiB) served as the size proxy, recorded as a
  substitution in the estimate. This is the gated-source example.
- Grand total for the budget question: about 17.7 TiB (about 19.5 TB) with
  the NVFP4 choice, about 18.4 TiB (about 20.3 TB) with the BF16 choice —
  under the 30 TB threshold in both cases. Locally staged directories already
  consumed about 2.3 TiB of the total, consistent with the API figures.

## Staged-copy validation

Three models had staged copies on the serving filesystem at measurement time:

| Model | API total | Staged (`du -s`) | Delta |
| --- | --- | --- | --- |
| moonshotai/Kimi-K3 | 1.42 TiB | 1.5 TiB | ~5% |
| deepseek-ai/DeepSeek-V4.1-Flash | 0.464 TiB | 476 GiB (~0.465 TiB) | <1% |
| zai-org/GLM-5.3-Flash | 0.299 TiB | 306 GiB (~0.299 TiB) | <1% |

The API totals tracked staged bytes within about 5% for all three. Staging
kept approximately the upstream payload for these models; models that go
through local format conversion can exceed the API figure, so validation
per model remains necessary before trusting a fleet sum.

## Tooling notes

- 29 repositories measured with 8 parallel workers; every call read-only;
  runtime under 2 minutes.
- `expand=true` is load-bearing: without it, entries can lack `size` and the
  sum silently drops LFS payloads on some listing formats.
- The `lfs.size` fallback mattered for entries whose top-level `size` was
  absent.
- GitHub-style pagination headers (RFC 8288 `Link`) apply here even though
  the endpoint is the Hugging Face Hub, not the GitHub API.
