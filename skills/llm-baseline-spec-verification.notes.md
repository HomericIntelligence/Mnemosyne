---
name: llm-baseline-spec-verification
description: "Supporting derivation for the memory-footprint split in the main entry. Uses synthetic geometry for arithmetic demonstration."
category: architecture
date: 2026-10-15
version: "1.2.0"
user-invocable: false
verification: verified-local
tags: []
---

# LLM Baseline Spec Verification — Notes

## Source case

A serving question asked for the GPU memory of a grouped-query-attention mixture-of-experts decoder at
a 128K context, with 4-bit weights and a quantized KV cache. A follow-up question asked for the
activation memory of one concurrent user.

The source evidence was a repository architecture record and two published weight-file totals. The
values themselves are not reproduced here. The method below uses synthetic geometry so that the
arithmetic is checkable without the source configuration.

## Worked arithmetic

Synthetic geometry: 48 layers, 8 key/value heads, 32 query heads, `head_dim` 128, hidden size 2560,
100 routed experts with top-8 selection, 1 shared expert, expert intermediate size 768, and a BF16
weight-file total of 75 GB.

### Term 1: weights

| Step | Value |
| ------ | ------ |
| BF16 parameter count | 75 GB / 2 bytes = 37.5 G parameters |
| 4-bit raw | 37.5 G x 0.5 = 18.75 GB |
| 4-bit with a 16-element block and an 8-bit scale | 37.5 G x 0.5625 = 21.09 GB |

A real artifact did not apply the 4-bit width to the whole model. It kept attention, value experts,
routers, and embeddings at BF16 and applied FP8 only to the routed expert linears. The weighted
result was about 34 GB, not 18.75 GB. This is the excluded-layer branch.

### Term 2: KV cache

`2 x 48 x 8 x 128 = 98,304` elements per token. At 131,072 tokens that is 12.885 G elements.

| KV precision | Bytes per token | Total |
| ------ | ------ | ------ |
| BF16 | 196,608 | 24 GiB |
| FP8 | 98,304 | 12 GiB |
| 4-bit with a 16-element block and an 8-bit scale | 55,296 | 6.75 GiB |

The 4:1 grouped query ratio is what keeps this small. A decoder with 32 KV heads at the same context
would need 4x the cache.

### Term 3: activations

Per token and per layer in BF16:

| Buffer | Bytes |
| ------ | ------ |
| q output | 8,192 |
| k output and v output | 2,048 each |
| attention output and o_proj input | 8,192 each |
| router logits for 100 experts, FP32 | 400 |
| gathered expert input, 8 selected copies | 40,960 |
| gate and up intermediate | 24,576 |
| activation output | 12,288 |
| down output, 8 copies | 40,960 |
| shared expert intermediate | 12,288 |

The high-water value is about 156 KiB per token per layer. One layer is live at a time, so decode
activation is about 156 KiB plus the logits.

The gathered expert input and the down output together are 80 KiB of the 156 KiB. Top-8 routing, not
attention, sets the activation high-water value for this architecture.

Prefill scales with the chunk, not with the context:

| Chunk | Layer activations |
| ------ | ------ |
| 2,048 tokens | 313 MiB |
| 8,192 tokens | 1.2 GiB |

### Contrast with a materialized score matrix

At a 1,024-token chunk against a 128K context, a materialized score matrix needs
`32 x 1,024 x 131,072 x 2` = 8 GiB per layer call. For the full sequence it is 1 TiB. The flash
backend is therefore a requirement at this context length.

## What architecture cannot answer

The three derived terms above are arithmetic on verified fields. They are not a GPU requirement. The
repository had no recorded measurement for graph capture or kernel workspace memory for this
architecture, and the serving engine reported a device bytes-per-token value slightly below the
architectural formula. Both limits must stay visible in any published figure.

## Verification

- Each term was recomputed from the stated geometry with an independent script.
- The 4-bit KV term at 6.75 GiB and the raw 4-bit term at 6.0 GiB differ only by the scale overhead,
  which matches the block arithmetic in the main entry.
- The MoE activation high-water value of 128.4 KiB exceeds the attention value of 28.0 KiB by
  4.6 times, which confirms that the gathered expert copies dominate.