---
name: gpu-oom-long-context-prefill-transient-peaks
license: BSD-3-Clause
description: "Find and bound the transient GPU-memory peaks that crash a serving engine during long-context prefill. Use when a replica dies with a CUDA out-of-memory error on a small allocation (1-4 GiB) while it serves short requests normally, or when you are about to lower the static memory fraction."
category: debugging
date: 2026-11-21
version: "1.0.0"
user-invocable: false
tags: [gpu, cuda, oom, prefill, long-context, allocator, expandable-segments, in-place, preallocation, torch-cat, overlay, serving, validation-order]
---

# GPU OOM in Long-Context Prefill: Bound the Transient Peaks

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-21 |
| **Objective** | Make the longest allowed prompt finish without an out-of-memory error, with no loss of throughput. |
| **Outcome** | Successful on one test replica: each fix removed one failure, and the full context window passed after all three fixes. |

## When to Use

- A serving replica exits after hours with `CUDA out of memory. Tried to allocate 1-4 GiB`, the process holds almost all device memory, and short requests are fine.
- The failing frame is in an attention indexer, a scoring step, or a mask or logits builder that grows with context length.
- Someone proposes to lower the static memory fraction as the fix.

## Verified Workflow

### Quick Reference

1. Open the source of the artifact that really runs (read the running job's record), then open the failing frame. The configured name can differ from the running image.
2. Read the OOM text. If "reserved but unallocated" is at least the requested size, the cause is fragmentation: set `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True` and test engine start. Otherwise the peak is too high.
3. Count the live copies at the peak of the failing function (see the patterns below). Remove one copy per fix.
4. After each fix, rerun the longest prompt. The next allocation fails next.
5. Use a lower memory fraction only as an extra margin.

### Suggested Approach

**Count live copies, not tensor sizes.** Two patterns hid most of the peak:

- A list of per-chunk tiles followed by one `torch.cat` holds the tiles and the result together: two copies. Write each tile into one preallocated output instead.
- A chain of out-of-place element-wise ops on a large tensor (for example `x.relu() * w`, then a reduction) keeps every intermediate alive until the reduction ends: three copies. Use in-place ops on the dead intermediates.

**Keep the numerics the same.** Guard the in-place path with a dtype check and keep the old expression as the fallback. Use in-place ops only on fresh tensors under inference mode, because autograd rejects them.

**Fix fragmentation separately.** A request can fail with several GiB reserved but unallocated. Expandable segments remove that gap at no speed cost. It can interact with engine features that share device memory, so check that start-up, graph capture and any cache init still pass.

**Validate at the full advertised window.** Run one request each at about 10 percent, 85 percent and 100 percent of the window on a fresh server. Then run a mixed load of at least one hour with a few very long requests. Then measure throughput at a representative shape against a baseline with the same flags except the change. Put the longest request last in a job: a crash there discards every later arm.

**Read headroom honestly.** `nvidia-smi` counts the allocator cache as used, so its minimum free memory is a lower bound. A 5-second sample misses spikes. Use the framework's free memory plus reserved-but-unallocated for the real margin.

**Ship a code fix without a rebuild.** Mount one patched file read-only over the image's file. The overlay matches one image digest only. Keep a diff against the image's file in the repository and put the file hashes in the directory name.

**Harness gotchas that changed recovery.**

- Non-contiguous GPU ids from the scheduler break NUMA binding (`device N is not visible`). Request an exclusive node.
- A step that ends `CANCELLED` with exit 0:9 and no traceback needs the cgroup `memory.events` (`oom_kill`) and `memory.max` before you blame the kernel or the scheduler.
- A per-user quota can return "No space left on device" while the filesystem shows free space. Write run output to a project work directory and keep a copy of the result tables there.
- A launch built by hand can miss environment and flags that the real launcher adds. Render the launch from the same code as production.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Lower the memory fraction only | Gave about 2 GiB more headroom (0.85 to 0.835). | The longest prompt still failed. Only a further cut passed, with about 100 MiB free. | The fraction moves the cliff by its own size. Treat it as margin. |
| Fix the first peak only | Replaced the `torch.cat`. | The next allocation, in the scoring step, failed. | Rerun the longest prompt after every fix. |
| Analyze the configured image | Read the source of the image the recipe named. | The running image was another build with another code path. | Take the artifact from the running job's record. |
| Fix the peak without the allocator setting | Both code fixes at the 100 percent prompt. | The request failed with several GiB reserved but unallocated. | Fragmentation is a second cause. |
| Read `nvidia-smi` minimum free as the margin | Reported 21 MiB free at the full window. | The figure includes the allocator cache; the run did not fail. | State the limit of this measure. |
| Long prompt first in a job | Ran the full-window prompt before the soak and throughput arms. | The crash discarded those arms. | Order arms by risk, longest last. |

## Results & Parameters

```python
# One output tensor instead of a tile list plus torch.cat.
out = None
for start in range(0, n, step):
    tile = f(start, step)
    if out is None:
        out = tile.new_empty((n, *tile.shape[1:]))
    out[start:start + tile.shape[0]] = tile
    del tile
```

```python
# In place, with the old expression as the fallback.
if w.dtype == s.dtype:
    s = s.relu_().mul_(w.unsqueeze(-1)).sum(dim=1)
else:
    s = (s.relu() * w.unsqueeze(-1)).sum(dim=1)
```

```bash
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
```

Observed on one test replica: with both code fixes and expandable segments, prompts at about 10 percent, 85 percent and 100 percent of the window finished, and a 90-minute mixed load ran with no failure and no restart. Throughput changed by less than 2 percent. Limits: one replica, the lowest free device memory at the full window was 21 MiB by `nvidia-smi`, and output hashes after a long load differed from a fresh run on filler text.
