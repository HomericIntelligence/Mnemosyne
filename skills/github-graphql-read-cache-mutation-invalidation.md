---
name: github-graphql-read-cache-mutation-invalidation
description: "Design a TTL read-through cache for GitHub GraphQL reads that stops duplicate budget burn without serving stale data. Use when repeated automation reads exhaust the GraphQL budget, or when you must choose the cache boundary, key, bypass list, and invalidation scope."
category: architecture
date: 2026-11-01
version: "1.0.0"
user-invocable: false
verification: verified-local
tags:
  - github-api
  - graphql
  - caching
  - rate-limit
  - invalidation
  - read-through-cache
  - ttl
  - token-scope
  - automation
---

# GitHub GraphQL Read Cache: Boundary, Key, and Mutation Invalidation

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-01 |
| **Objective** | Stop duplicate GraphQL reads from spending a shared hourly budget, without a second transport and without stale reads. |
| **Outcome** | Success. One read-through cache at the single query entry point, disabled by default, with mutation and label-write invalidation. |

## When to Use

Use this skill when:

- Repeated GraphQL reads in a poll loop spend the shared GraphQL budget. See
  [github-shared-token-lockout-rate-limit-diagnosis](github-shared-token-lockout-rate-limit-diagnosis.md)
  first to prove that duplicate reads, not concurrency, are the cause.
- You must choose where to put a cache in a client that has one query entry
  point and several write paths.
- Several processes for one repository must share cache entries.
- You must decide which reads may never come from a cache.

Do not use it for the internal thread-safety mechanics of a cache object. See
[architecture-threadsafe-cache-per-key-locks](architecture-threadsafe-cache-per-key-locks.md)
for the per-key lock and TTL container.

## Verified Workflow

### Put the cache at the one query entry point

Cache at the shared `run_graphql` boundary. Do not add a second transport, a
second client, or per-call-site caches.

```python
# Inside the single query path, before the HTTP call.
cached = _query_cache_lookup(operation, variables, repo)
if cached is not None:
    return cached
response = _raw_transport(operation, variables)
_read_cache.store(key, response)
return response
```

A cache at the boundary covers every caller at once, keeps one transport, and
keeps the JSON and response-contract tests meaningful. Extract the transport
into a small helper when the cache lookup pushes the query function over the
cyclomatic-complexity limit. Do this before you add `noqa` suppressions.

### Bind the key to identity, not to call order

Use `token hash + repository + operation + variables digest`.

- Hash the token and truncate the digest. Do not store the token.
- Normalize variables before the digest, with sorted keys and a stable
  separator.
- Do not cache an operation whose variables are not scalars, or whose
  repository owner and name are not resolvable. Fail open.

### Fail closed on the operation allow-list

Keep one explicit allow-list of cacheable query operations. Every other
operation, including schema or contract reads, goes upstream. Add a separate
bypass list for state that a worker acts on: review state, comment bodies,
comment IDs, and batch comment reads. A stale read of these values changes an
agent decision.

### Invalidate by scope on every write

- A mutation invalidates the repository that the ambient context resolves. If
  that lookup fails, log a warning and invalidate the token scope. Do not stop
  the mutation.
- Invalidate in a `finally` block around the mutation, so a mutation with an
  unknown outcome still clears the entry.
- Label writes use a separate helper. Call the same invalidation from each
  label-write function.

### Choose the default and the store

- Default the time to live (TTL) to `0`, disabled. A positive TTL of `3600`
  seconds is a good first value for repository metadata.
- Put the store on local disk with owner-only permissions: directory `0700`,
  entries `0600`. Keep it outside the source tree and shared by every process
  for one repository.
- Emit counters to the existing event or metrics path: hits, misses, bypasses,
  evictions, entries, and the TTL. One emission each poll cycle is sufficient.

### Respect the layering rule

If a lower layer must not import the upper layer, put the configuration
function that reads parsed arguments in the cached module. Keep the argument
definitions in the shared argument module. The entry point then calls one
function with the parsed namespace. See
[library-product-import-boundary-enforcement-test](library-product-import-boundary-enforcement-test.md).

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| ------- | ---------------- | --------------- | ---------------- |
| Cache in each caller | A cache near each repeat caller was the first instinct. | Several callers meant several caches, separate TTLs, and separate invalidation. | One cache at the single query entry point covers every caller. |
| Add a suppression for complexity | A `noqa` was considered when the cache lookup raised complexity. | The function mixed policy, cache, and transport. | Extract the transport first. Do not suppress a complexity gate. |
| Invalidate only on mutation success | Invalidation ran after a confirmed result. | A mutation with an unknown outcome left a stale entry. | Invalidate in a `finally` block whenever a mutation was prepared. |
| Cache every read operation | The allow-list started as the complete operation set. | Review state and comment reads must be current for the worker decision. | Keep an explicit allow-list and a bypass list. |

## Results & Parameters

### Configuration

```bash
--gh-cache-ttl 3600          # 0 disables the cache (default)
--gh-cache-max-entries 2048
--gh-cache-dir build/.issue_implementer/gh-read-cache/
```

```text
key = sha256(token)[:32] + repo + operation + sha256(sorted variables)
store modes: directory 0700, entry files 0600
bypass: review state, comment bodies, comment IDs, batch comment reads
invalidate: mutation (finally) and label write -> ambient repository, else token scope
```

### Expected Output

- One `gh_read_cache_stats` event per poll cycle with the counter fields.
- Fewer GraphQL points spent after the first cycle. Check with
  `gh api rate_limit --jq '.resources.graphql'` before and after a run.
- A stale-read test that fails before the invalidation call and passes after it.

## Verified On

| Project | Context | Details |
| ------- | ------- | ------- |
| Private automation repository | Pull-request implementation of the read cache in a queue-based automation loop | See [notes](github-graphql-read-cache-mutation-invalidation.notes.md). |

## References

- [github-shared-token-lockout-rate-limit-diagnosis](github-shared-token-lockout-rate-limit-diagnosis.md)
- [architecture-threadsafe-cache-per-key-locks](architecture-threadsafe-cache-per-key-locks.md)
- [github-graphql-fail-closed-mutation-proof](github-graphql-fail-closed-mutation-proof.md)
- [library-product-import-boundary-enforcement-test](library-product-import-boundary-enforcement-test.md)