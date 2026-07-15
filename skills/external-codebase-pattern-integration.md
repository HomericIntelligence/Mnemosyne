---
name: external-codebase-pattern-integration
description: "Integrate proven patterns from existing codebases into new design plans. Use when: (1) design docs reference code from another repo, (2) implementing a subsystem that an existing project already solves, (3) adapting battle-tested Slurm/job-management/infrastructure code to a new project."
category: architecture
date: 2026-06-11
version: "1.0.0"
user-invocable: false
verification: verified-local
tags: [integration, codebase-reuse, slurm, design-docs, evaluation_service]
---

# External Codebase Pattern Integration

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-06-11 |
| **Objective** | Integrate proven patterns from an existing codebase (EvaluationService) into new design plans for a related project (Inference Service) |
| **Outcome** | Successfully identified and adapted 7 key patterns from EvaluationService’s SlurmManager into the Inference Service #86 plan, including instance isolation, health checks, graceful shutdown, and reconciliation loops |
| **Verification** | verified-local |

## When to Use

- Design docs explicitly reference code from another repository
- A sibling project already solves a subsystem you’re designing
- You need to adapt infrastructure code (Slurm, job schedulers, container management) from an existing project
- A plan review flags missing integration with a referenced codebase
- The user points out that code from another repo should be used

## Verified Workflow

> **Warning:** This workflow has been validated locally. Treat as a hypothesis until CI confirms.

### Quick Reference

```bash
# Fetch file from another repo via GitHub API
gh api repos/{owner}/{repo}/contents/{path} --jq '.content' | base64 -d

# List directory contents
gh api repos/{owner}/{repo}/contents/{path} --jq '.[].name'

# Check repo structure
gh api repos/{owner}/{repo} --jq '.default_branch'
```

### Detailed Steps

#### Phase 1: Discover Source Code

1. Identify the source repository and paths from issue/plan references
2. Use `gh api` to fetch files (web fetch may 404 on private repos)
3. Fetch the main module AND its dependencies (job model, config, templates)
4. Read the consumer/caller code to understand how the module is used

#### Phase 2: Extract Patterns

1. Read the source code thoroughly — identify the key abstractions:
   - Data models (what fields, what states)
   - Lifecycle methods (create, poll, cancel, cleanup)
   - Error handling patterns (retries, timeouts, terminal states)
   - Isolation patterns (how multiple instances coexist)
   - Health checking (HTTP probes, status polling)
2. For each pattern, note:
   - What problem does it solve?
   - Is this problem relevant to the target project?
   - What adaptations are needed?

#### Phase 3: Adapt to Target Project

1. Map source concepts to target concepts:
   - EvaluationService `instance_id` → Inference Service `endpoint_id`
   - EvaluationService `get_model_state` → Inference Service endpoint status lifecycle
   - EvaluationService `check_live` → Inference Service health check polling
2. Note what to KEEP:
   - Proven patterns (instance isolation, health checks)
   - Defensive measures (graceful shutdown, cache isolation)
3. Note what to CHANGE:
   - EvaluationService is async; Inference Service is synchronous
   - EvaluationService uses asyncio; Inference Service uses threading
   - Job naming convention changes
4. Note what to ADD:
   - Integration points with existing target project modules
   - New tests for adapted code

#### Phase 4: Update Design Plan

1. Document the source repository URL explicitly in the plan
2. List each integrated pattern with:
   - Source code reference
   - Adaptation notes
   - New test cases
3. Add integration tests that verify the adapted patterns work

#### Phase 5: Validate

1. Ensure all adapted patterns have corresponding tests
2. Verify no circular imports introduced
3. Check that the adapted code follows target project conventions
4. Run existing tests to ensure no regressions

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Web fetch of private repo URLs | `read_url` on github.com/blob URLs | 404 Not Found on private repos | Always use `gh api` for private repos — web fetches only work for public repos |
| Including source code inline in plan | Pasted large source files into plan comments | Plans became too long and noisy | Reference patterns by name with adaptation notes, not full source dumps |
| Assuming source code conventions match target | Copied EvaluationService patterns directly | Target project uses different conventions (sync vs async, different naming) | Always map conventions explicitly: async→sync, different naming, different state machines |
| Missing dependency files | Fetched only the main module | Caller code and data models were needed for context | Always fetch the main module AND its direct dependencies and consumers |

## Results & Parameters

### Pattern Extraction Template

For each pattern from the source codebase:

| Pattern | Source Location | Problem Solved | Adaptation Needed | Target Location |
|---------|----------------|----------------|-------------------|----------------|
| Instance isolation | `SlurmManager.__init__` | Prevent multiple managers from interfering | Use `inference_service-{instance_id}-{model}` naming | `SlurmJobManager` |
| Health checks | `SlurmManager.check_live` | Verify server is responding | Convert async to sync urllib | `SlurmJobManager._check_live` |
| Graceful shutdown | `SlurmManager.cancel_all_owned_jobs` | Clean up on exit | Filter squeue by prefix | `SlurmJobManager.cancel_all` |

### gh api Fetch Commands

```bash
# Fetch a file
gh api repos/example-org/evaluation-service/contents/scheduler/slurm_manager.py --jq '.content' | base64 -d

# List a directory
gh api repos/example-org/evaluation-service/contents/scheduler/slurm --jq '.[].name'

# Read first N lines of a file
gh api repos/example-org/evaluation-service/contents/scheduler/slurm_manager.py --jq '.content' | base64 -d | head -100
```

### Key Adaptation: EvaluationService → Inference Service

| EvaluationService Pattern | Inference Service Adaptation |
|--------------------|-----------------------|
| Async `asyncio` loops | `threading.Timer` for auto-kill |
| `instance_id` in job names | `inference_service-{instance_id}-{model_id}-{engine}` |
| `get_model_state` (pending/deploying/live/dead) | Endpoint status (pending/running/released/expired/dead) |
| `check_live` HTTP health probe | `_check_live` with `urllib.request.urlopen` |
| `cancel_all_owned_jobs` | `cancel_all` filtering squeue by prefix |
| `_live_urls` dict for fast lookup | Same pattern in EndpointRegistry |
| Cache isolation in `$SLURM_TMPDIR` | Per-job cache paths to prevent corruption |

## Verified On

| Project | Context | Details |
|---------|---------|--------|
| example-org/inference-service | Issue #86 Slurm Lifecycle | Integrated 7 patterns from EvaluationService’s SlurmManager into the Inference Service SlurmJobManager plan |
