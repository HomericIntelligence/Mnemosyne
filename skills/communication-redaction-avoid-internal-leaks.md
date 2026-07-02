---
name: communication-redaction-avoid-internal-leaks
description: "Prevent internal infrastructure identifiers from leaking into user-facing summaries, durable notes, PR bodies, reports, reproducibility packages, golden files, and reusable examples. Use when: (1) reporting operational validation or launch details, (2) writing durable artifacts from logs, endpoints, checkpoints, prompts, or commands, (3) committing repro artifacts copied from cluster runs."
category: documentation
date: 2026-07-01
version: "1.1.0"
user-invocable: false
verification: verified-local
history: communication-redaction-avoid-internal-leaks.history
tags: [communication, redaction, documentation, reporting, reproducibility, artifacts, security]
---

# Communication Redaction: Avoid Internal Leaks

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-07-01 |
| **Objective** | Keep operational reporting and reproducibility artifacts useful while preventing internal infrastructure identifiers from appearing in user-facing or durable artifacts unless explicitly requested. |
| **Outcome** | Use neutral placeholders for commands, endpoints, logs, checkpoints, prompts, golden files, cluster debug paths, and launch details by default. |
| **Verification** | verified-local - Inference360 repro artifacts were redaction-scanned locally and passed their PR CI; this skill amendment has local validation only until its own PR CI passes. |
| **History** | [changelog](./communication-redaction-avoid-internal-leaks.history) |

## When to Use

- Reporting validation results, operational commands, launch details, endpoints, logs, checkpoints, or run summaries.
- Writing PR bodies, issue comments, notes, runbooks, postmortems, learnings, or other durable artifacts from an operational session.
- Turning raw terminal output or logs into a user-facing summary.
- Creating examples that could otherwise reveal infrastructure identifiers.
- Packaging repro directories, golden files, raw responses, logits, tokens, benchmark outputs, or debug artifacts for a PR or issue.
- Updating GitHub issues or PR descriptions from cluster-local evidence.

## Verified Workflow

### Quick Reference

```text
Before publishing a user-facing or durable artifact:
1. Identify operational identifiers.
2. Replace them with neutral placeholders.
3. Preserve the workflow shape and outcome.
4. Scan every changed repro/doc/golden file, not just the latest file you edited.
5. Run pre-commit over the full PR diff or package directory before pushing.
6. Include exact internal details only when the user explicitly asks for that exact detail.
```

```bash
# Example scan. Add repo- or org-specific path/user/service patterns locally.
rg -n "(/(home|mnt|scratch|data|users)/[^[:space:]]+|https?://[0-9]|[0-9]{1,3}(\\.[0-9]{1,3}){3}|checkpoint[_-]?[0-9]+|Authorization:|Bearer |cookie|token)" \
  docs repro tests
```

### Detailed Steps

1. **Classify the target surface.** Treat final answers, PR bodies, issue comments, notes, skills, runbooks, report files, examples, repro packages, and golden artifacts as user-facing or durable unless the user says otherwise.
2. **Inventory raw sources.** List every copied input: logs, endpoint responses, token files, logits, benchmark outputs, run scripts, `repro.sh` files, debug traces, screenshots, issue comments, and Slack/chat excerpts.
3. **Scan for internal identifiers.** Look for endpoint addresses, hostnames, IPs, absolute infrastructure paths, checkpoint paths, tokenizer paths, user-specific locations, usernames, account names, partition names, private prompts, tokens, cookies, job IDs, allocation IDs, ports, internal service names, and raw cluster/debug artifact paths.
4. **Replace identifiers with placeholders.** Prefer explicit neutral terms such as `<REDACTED_ENDPOINT>`, `<REDACTED_CHECKPOINT_PATH>`, `<REDACTED_INFRA_PATH>`, `<REDACTED_PATH>`, `<TOKENIZER_OR_HF_CHECKPOINT_PATH>`, `<HF_CHECKPOINT_PATH>`, `<XLLM_REPO>`, `<job-id>`, and `<account>`.
5. **Preserve operational meaning.** Keep the command category, request shape, model family or public alias, token counts, failure mode, validation result, sequence of steps, and decision logic. Remove only the identifying values.
6. **Check golden files directly.** Do not assume generated artifacts are safe because the docs are sanitized. Open or scan raw `output.txt`, `tokens.jsonl`, `logits.jsonl`, `request.json`, `response.json`, `server.log`, and `repro.sh` files before committing.
7. **Run a package-wide scan.** Scan the whole repro/doc/test package or the full PR diff, not just the file changed in the latest commit. Older committed files can still fail hooks or leak stale details.
8. **Run full relevant hooks.** For repro packages, run pre-commit over the package or the full PR diff so normalization and leak checks cover older golden/doc files too.
9. **Respect explicit requests.** If the user asks for an exact command, exact endpoint, exact log path, or exact identifier, provide only the requested detail and avoid adding unrelated identifiers.
10. **Do a final redaction pass.** Re-read the artifact before publishing and check code blocks, tables, commit messages, branch names, PR bodies, issue comments, and references.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Raw operational copy-paste | Copied commands, log excerpts, and validation details directly into a durable artifact | Operational output often contains paths, endpoints, job identifiers, ports, service names, and checkpoint values that are not needed for the learning | Summarize the workflow and outcome first, then add placeholders only where structure matters |
| Over-redacting everything | Removed all command and validation structure | The artifact became hard to reuse because readers could not tell what was validated or in what order | Redact identifiers, not the process |
| Treating non-secret identifiers as harmless | Left infrastructure identifiers visible because they were not credentials | Internal topology and operational metadata can still be sensitive or unnecessary in durable artifacts | Apply least-disclosure to all internal identifiers, not only secrets |
| Scanning only the newest edits | Ran checks on the latest changed files while older committed golden or doc files still existed in the PR | Repro packages accumulate raw files across commits; an earlier file can still leak or fail normalization hooks | Scan the full PR diff or the complete repro directory before every push |
| Sanitizing docs but not raw artifacts | Updated README/runbook prose but left raw response, token, logit, or `repro.sh` artifacts unchecked | Reproducibility packages often expose the exact same internals through machine-readable files | Treat raw artifacts as durable documentation and redact them with the same policy |

## Results & Parameters

### Placeholder Policy

| Internal detail type | Placeholder |
|----------------------|-------------|
| Absolute path or generated file location | `<internal-path>` |
| Repository, project, or product-specific name | `<project>` |
| Cluster, host, or node identity | `<node-id>` |
| API URL, IP address, hostname, or port-bearing target | `<endpoint>` |
| Runtime service or process name | `<service-name>` |
| Job, run, task, or allocation identifier | `<job-id>` |
| Checkpoint, artifact, or model checkpoint path | `<checkpoint>` |
| User, account, tenant, or partition name | `<account>` |
| Exact endpoint address from a private cluster | `<REDACTED_ENDPOINT>` |
| Exact infrastructure or debug artifact path | `<REDACTED_INFRA_PATH>` |
| Exact checkpoint or tokenizer path | `<REDACTED_CHECKPOINT_PATH>` or `<TOKENIZER_OR_HF_CHECKPOINT_PATH>` |
| Source repository path needed only for local loading | `<XLLM_REPO>` or `<REDACTED_PATH>` |

### Safe Reporting Template

```text
Validation: <passed|failed|blocked>
Command category: <what was checked, without exact internal command text>
Target: <project> / <service-name> / <endpoint>
Evidence: <short sanitized result>
Next step: <sanitized action>
```

### Review Checklist

- No absolute paths, concrete filenames, repository or project names, node names, job identifiers, IPs, ports, checkpoint paths, usernames, account names, partition names, or internal service names appear unless explicitly requested.
- Examples use placeholders such as `<internal-path>`, `<service-name>`, `<node-id>`, `<endpoint>`, `<checkpoint>`, and `<project>`.
- The artifact still explains what was validated, what happened, and what action follows.
- Verification status states only what actually ran.
- Raw repro artifacts such as logs, JSONL files, request/response bodies, token/logit dumps, and rerun scripts were scanned directly.
- Pre-commit was run over the full relevant package or PR diff, not only the newest files.

### Verified On

| Project | Context | Details |
|---------|---------|---------|
| LLM360/Inference360 | Issue 257 repro package and PR 326 | Sanitized `repro/257` documentation, scripts, golden outputs, and investigation notes before committing; local redaction scans and PR CI passed. |
