---
name: architecture-rest-pagination-client-loop
description: "Client-side pagination loop for limit/offset REST list endpoints with a server-capped limit. Use when: (1) a server adds default-limit pagination and existing clients silently see only the first page, (2) choosing between passing a large limit vs. a pagination loop, (3) a paginated client must stay backward-compatible with pre-pagination (bare list) responses."
category: architecture
date: 2026-07-10
version: "1.0.0"
user-invocable: false
verification: unverified
tags: [rest, pagination, httpx, python, api-client, backward-compatibility]
---

# Client-Side Pagination Loop for Limit/Offset REST Endpoints

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-07-10 |
| **Objective** | Update a Python API client after the server (ProjectAgamemnon PR #336) added limit/offset pagination (default 100, hard cap 1000) to its list endpoints |
| **Outcome** | Design complete and plan-reviewed; implementation not yet executed |
| **Verification** | unverified — pattern authored in a planning session, never run end-to-end |

## When to Use

- A REST server adds `limit`/`offset` pagination with a default page size, and existing param-less client fetches now silently truncate to the first page
- Deciding between "pass one big limit" and "loop over pages": check whether the server clamps `limit` server-side before choosing
- The client must keep working against both paginated (envelope) and pre-pagination (bare JSON list) servers during a rolling deploy
- The pagination envelope is `{<collection-key>: [...], "total": N, "limit": L, "offset": O}`

## Verified Workflow

> **Warning:** This workflow has not been validated end-to-end. Treat as a hypothesis until CI confirms.

### Quick Reference

```python
_PAGE_LIMIT = 1000  # match the server's hard cap (e.g. kMaxLimit in routes.cpp)

async def _list_paginated(self, path: str, key: str) -> list[Any]:
    first = await self._request("GET", path, params={"limit": _PAGE_LIMIT, "offset": 0})
    if isinstance(first, list):          # pre-pagination server: bare list
        return first
    items: list[Any] = list(first.get(key, []))
    total = int(first.get("total", len(items)))   # missing total => complete
    while len(items) < total:
        page = await self._request("GET", path,
                                   params={"limit": _PAGE_LIMIT, "offset": len(items)})
        batch = page if isinstance(page, list) else page.get(key, [])
        if not batch:                    # guard: stale total must not hang the loop
            break
        items.extend(batch)
    return items
```

### Detailed Steps

1. **Read the server's cap before choosing a strategy.** If the server clamps `limit` (here `kMaxLimit = 1000`, silently applied via `std::min`), a "just pass limit=1000000" client truncates silently at cap+1 items — the loop is mandatory, not optional.
2. **Request the cap-sized page (`limit=<server max>`)** to minimize round trips; do not rely on the server default.
3. **Advance `offset` by items collected so far** and loop while `len(items) < total` — equivalent to the `offset + len(page) >= total` termination condition.
4. **Keep backward compatibility**: return a bare JSON list unchanged, and treat an envelope with no `total` field as already complete (0 extra requests). This keeps all pre-pagination tests passing unmodified.
5. **Guard against a stale `total`**: if a follow-up page is empty while `total` still claims more (items deleted between pages), break instead of looping forever.
6. **One shared helper, not N copies** — each `list_*` method passes its path and collection envelope key (these may differ per endpoint, e.g. `"agents"`, `"teams"`, `"tasks"`, `"faults"` — read them from the server's serialization code, don't guess).
7. **Test with mocked page sequences** (e.g. respx `side_effect=[resp1, resp2]`): assert item count, request count, and the second request's `offset` param; add a single-page test (no extra requests) and an empty-page-guard test (terminates).

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Large fixed limit (issue "option a") | Pass one explicit big `limit` and skip the loop | Server clamps limit to a hard cap (1000) via `std::min` with no error — silently truncates beyond cap | Grep the server for the cap constant before choosing; a clamped limit makes option (a) a silent-data-loss bug |
| Loop terminating only on `len(items) >= total` | Trust the envelope's `total` unconditionally | If items are deleted between page fetches, `total` overcounts and an empty page loops forever | Always break on an empty batch regardless of `total` |
| Assuming one envelope key for all endpoints | Reuse `"items"`-style key everywhere | Each collection uses its own key (`agents`/`teams`/`tasks`/`faults`), verified in the server's store serialization | Read envelope keys from server source; pass the key per endpoint |

## Results & Parameters

Design parameters from the source session (ProjectAgamemnon issue #337 / PR #336):

- Server defaults: `kDefaultLimit = 100`, `kMaxLimit = 1000` (`src/routes.cpp:176-177`); invalid params → 400
- Envelope: `{<key>: [...], "total": N, "limit": L, "offset": O}` (`src/store.cpp:455,561,686,700,732`)
- Client page size: `_PAGE_LIMIT = 1000` (= server cap)
- Test matrix: multi-page (1000+500 of total 1500 → 2 calls, second offset=1000), single-page (1 call), empty-page guard (terminates at 2 calls), bare-list and no-`total` envelope backward-compat tests unchanged

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| ProjectAgamemnon | Issue #337 plan for `AgamemnonClient` (clients/python) after server PR #336 added pagination | Design only — implementation pending |
