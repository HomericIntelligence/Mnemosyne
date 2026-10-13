---
name: hf-repo-size-estimation-paginated-tree
description: "Estimate a Hugging Face model's storage footprint from the paginated tree API before you stage or download it. Use when: (1) a capacity, budget, or quota check needs a model's byte size before weights are staged, (2) a tree listing looks small for the model class or shard names carry -of-000NN totals above the fetched count, (3) a gated repository returns 401 to anonymous reads and a same-size public proxy is needed, (4) an operator names a product that publishes several precision variants and the estimate must bind to one."
category: tooling
date: 2026-10-09
version: "1.0.0"
user-invocable: false
verification: verified-local
tags:
  - huggingface
  - hf-api
  - tree-api
  - pagination
  - link-header
  - model-weights
  - storage-estimation
  - capacity-planning
  - gated-repository
  - staged-copy-validation
---

# Hugging Face Repository Size Estimation Through the Paginated Tree API

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-09 |
| **Objective** | Estimate the storage that an unstaged Hugging Face model artifact needs, from remote listing data only. |
| **Outcome** | Operational. A first-page-only tree read truncated a 48-shard weight listing to 5 shards and underestimated one public MoE checkpoint by about 21x (22 GiB reported versus 476 GiB real). The paginated reader summed every page; the totals matched three locally staged models within about 5%. See [notes](./hf-repo-size-estimation-paginated-tree.notes.md) for the measurement record. |
| **Verification** | verified-local — 29 public repositories measured; totals cross-checked against three staged copies. |

The Hugging Face tree endpoint
`GET /api/models/{repo}/tree/{revision}?recursive=true&expand=true` paginates
through the HTTP `Link` response header (`rel="next"`). The JSON body has no
cursor field. A client that reads one page gets a complete, valid-looking
list with no error and no truncation marker. The failure is a plausible
partial sum, not an empty result.

## When to Use

- A capacity, budget, or quota check needs a model's byte size before the
  weights are staged or downloaded.
- You need per-file sizes without pulling LFS content, with or without a
  token.
- A tree listing looks small for the model class, or shard names carry
  `-of-000NN` totals above the count you fetched.
- You estimate an aggregate (a sum of bytes), not only presence or absence.
  Presence-only use is a different, easer problem.
- A gated repository returns 401 to anonymous reads and planning must
  continue with a same-size public proxy.
- An operator names a product whose publisher ships several precision
  variants (BF16, FP8, NVFP4, GGUF). The estimate must bind to one exact
  repository.

Do not use this estimate as an authoritative admission manifest. Manifest
generation is a governed staging operation. Do not use a bounded read to
prove absence; that authority boundary belongs to
[automation-graphql-batch-comment-fetch](automation-graphql-batch-comment-fetch.md).

## Verified Workflow

### Quick Reference

```bash
# Follow Link: rel="next" until it is absent; sum every page.
python3 - <<'EOF'
import json, re, urllib.request

def repo_bytes(repo, weight_ext=(".safetensors", ".bin", ".pt", ".pth", ".ckpt")):
    url = f"https://huggingface.co/api/models/{repo}/tree/main?recursive=true&expand=true"
    total = weights = 0
    while url:
        with urllib.request.urlopen(urllib.request.Request(url), timeout=90) as r:
            page = json.load(r)
            m = re.search(r'<([^>]+)>;\s*rel="next"', r.headers.get("Link", ""))
            url = m.group(1) if m else None
        for f in page:
            if f.get("type") != "file":
                continue
            size = f.get("size") or (f.get("lfs") or {}).get("size") or 0
            total += size
            if f["path"].endswith(weight_ext):
                weights += size
    return total, weights
EOF
```

### Detailed Steps

1. Request `recursive=true&expand=true`. `expand=true` puts a byte `size` on
   each entry, and on each entry's `lfs` object for LFS files.
2. Follow the `Link` header `rel="next"` until it is absent. Do this per
   repository: truncation is per repository and can cut at any entry, not
   only after large repos.
3. Sum `size` with a fallback to `lfs.size` for entries of type `file`. For
   capacity figures, sum all files (the full-repo value); weight-only and
   full-repo totals differed by less than 2% in the measured set, so the
   full-repo sum is the safer budget number.
4. Check for truncation with shard-name totals when shard files exist:
   `model-00005-of-00048.safetensors` tells you the true shard count. If the
   highest fetched index is below the `-of-000NN` total, pages are missing.
   A 200 status and parseable JSON do not prove completeness.
5. Validate the method against any locally staged copy before you trust a
   fleet-wide sum (`du -sb` against the staged directory). In the measured
   set, the API totals matched staged bytes within about 5% for all three
   available models. If a staged copy is much larger than the API total,
   check for local conversions or duplicate copies before you blame the
   estimate.
6. Use bounded read concurrency (about 8 workers) across repositories. All
   calls are read-only.
7. Gated repository branch: anonymous reads return 401 (not 404). If terms
   acceptance is pending, use a same-family public derivative (for example
   the RL or Instruct sibling) as a size proxy and record the substitution
   in the estimate. The weight set of a derivative is usually the same size
   class.
8. Variant-binding branch: record the exact repository that the estimate
   binds to, including the precision. One product name covered artifacts
   from 0.32 TiB (NVFP4) to 1.02 TiB (BF16) in the measured set.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Single recursive GET, one page parsed | One `tree/main?recursive=true` call per repository, sum of the returned array | The endpoint paginates through the `Link` header; the first page of one public MoE repo held only 5 of 48 weight shards. The sum (about 22 GiB) looked plausible and no error was raised | The dangerous failure is a plausible partial sum. Follow `rel="next"` to exhaustion and cross-check `-of-000NN` shard totals |
| Fleet totals from first pages | The same one-page read across 29 repositories | Every repository whose file count spans pages was under-counted; the fleet grand total was wrong | There is no fleet-level signal that any one repo was truncated; pagination completeness is per repository |
| Parameter-count arithmetic instead of a listing | Estimating bytes as parameters times an assumed bytes-per-parameter | Precision was unknown up front; a 2.4T-class artifact measured 4.45 TiB, its sibling FP8 artifact 2.27 TiB, and a different product's variants differed by 3x | Measure the bound repository. Names and parameter counts do not fix precision, and precision moves size by 2-4x |

## Results & Parameters

### Configuration

```yaml
endpoint: "https://huggingface.co/api/models/{repo}/tree/main"
query:
  recursive: "true"   # all descendants in each page
  expand: "true"      # per-file size fields, including lfs.size
weight_extensions: [".safetensors", ".bin", ".pt", ".pth", ".ckpt"]
concurrency: 8        # parallel repositories; read-only GETs
truncation_check: "highest shard index must reach the -of-000NN total"
validation: "du -sb on each available staged copy; expect < ~5% delta"
```

### Expected Output

- One TiB/TB total per repository: all-files and weights-only.
- A truncation check per repository with shard-style names.
- A validation delta against each available staged copy.
- Recorded substitutions for gated sources (401) and the exact bound
  repository for each named product variant.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Serving-fleet capacity audit | Storage-budget estimate for 15 new model variants plus three families already in service | [notes.md](./hf-repo-size-estimation-paginated-tree.notes.md) |

## References

- [Hugging Face Hub API: get a tree](https://huggingface.co/docs/hub/api)
- [automation-graphql-batch-comment-fetch](automation-graphql-batch-comment-fetch.md) — a bounded read is never authoritative absence; use complete pagination for aggregates
