---
name: tooling-opencode-v2-service-health-api
description: "Diagnose a running OpenCode V2 service read-only through its HTTP API before you blame the database or restart anything. Use when: (1) history, sessions, or a project look missing and you must decide between a client fault, a stale server process, and lost data; (2) you need proof of what the running service can serve without a restart; (3) you script health checks against a live instance."
category: tooling
date: 2026-10-30
version: "1.0.0"
user-invocable: false
tags: [opencode, http-api, diagnostics, service-health, read-only, sqlite]
---

# OpenCode V2 service health through the HTTP API

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-30 |
| **Objective** | Decide, without a restart or any write, whether missing history comes from the client, a stale server process, or the database. |
| **Outcome** | Successful. Read-only API probes proved that the service served a project and its history while the server log repeated SQLite malformed errors. This cancelled a destructive recovery of an intact database. Verified against OpenCode v2.1.x. |

## When to Use

- The product shows no history, a missing project, or database errors, and you must choose between "restart the client", "restart the service", and "recover the database".
- A server log repeats SQLite errors and you must show what the running process can still serve before you repair or replace data.
- You must script a health check against a live instance and need the exact endpoints and authentication.

Do not use this workflow to change state. Use GET requests only. It is safe while sessions run.

## Verified Workflow

### Quick Reference

```bash
SVC=~/.local/state/opencode/service.json          # url, pid, password, version
URL=$(python3 -c "import json;print(json.load(open('$SVC'))['url'])")
PW=$(python3 -c "import json;print(json.load(open('$SVC'))['password'])")
curl -s -u "opencode:$PW" "$URL/api/project"                                  # known projects
curl -s -u "opencode:$PW" "$URL/api/session?directory=<abs project path>&limit=5"
curl -s -u "opencode:$PW" "$URL/api/session/<session-id>/message?limit=3"     # transcript proof
```

Basic auth is required: `-u "opencode:<password from service.json>"`.

### Suggested Approach

1. **Read the service file, then confirm the process.** The state file gives the base URL, the serving PID, the password, and the version. Check that the PID is alive. A file whose PID is gone describes a dead instance; treat the file as stale, not as evidence.
2. **Authenticate with basic auth, not a bearer token.** A bearer header or a custom password header returns `401` with `Authentication required`. The same password works as an HTTP basic password with any username. This one detail decides whether a probe works at all.
3. **Judge the body, not the status code.** Paths outside `/api/*` return the single-page application with HTTP `200`. A green status can hide a wrong path. Success is a JSON body with the expected shape; unknown `/api/*` paths return a JSON `404`.
4. **Split the fault with a three-way comparison.** Compare what the API serves, what the database file holds (`SELECT count(*)` per key table), and what the client displays. Service and database agree but the client shows nothing: a client or transport fault. The database holds rows but the API errors: a server-side fault, often a stale process reading a changed schema. Both are empty: data loss.
5. **Pair the API proof with a file-integrity proof.** `PRAGMA integrity_check` shows the file is sound; the API shows the product can serve it. Together they justify or cancel a destructive recovery. See [tooling-opencode-v2-corrupt-db-recovery](tooling-opencode-v2-corrupt-db-recovery.md) for the recovery path and for the stale-reader decision branch.
6. **Report what you proved, not what you assume.** An API probe that returns the expected sessions is evidence that history is servable. Keep the probes read-only so the evidence stays valid while you decide.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Bearer token from the service file | Sent the service password as `Authorization: Bearer <password>`. | `401` with `{"_tag":"UnauthorizedError","message":"Authentication required"}`; a custom password header failed the same way. | The service expects HTTP basic auth. Use `-u "opencode:<password>"`. |
| Trusted HTTP status alone | Probed a project path without the `/api` prefix and got `200`. | The body was the web application HTML, not data. The path was wrong and the check proved nothing. | Only `/api/*` paths return data. Verify the JSON shape of the body. |

## Results & Parameters

### Configuration

| Endpoint | Returns | Use |
| --------- | --------- | --------- |
| `/api/project` | JSON array of projects (`id`, `canonical`, `vcs`, `time`) | Confirms the service sees the project |
| `/api/session?directory=<abs path>` | `{"data":[<session>]}`; `projectID` also works | Lists sessions for one project |
| `/api/session/<id>/message` | `{"data":[<message>]}` with content blocks | Proves a transcript is servable |

### Expected Output

- A healthy instance returns JSON for every `/api/*` probe, and the session list contains the sessions that the database holds.
- A stale-reader fault returns `500` with a SQLite error for indexed reads while point reads and the file integrity check stay clean. Restart every process of the product once; do not recover data.
- A dead service file (PID gone) means the next client start creates a new instance; re-read the service file after any restart.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| OpenCode v2.1.x (public release) | Stale-reader incident: log repeated malformed-database errors, API served the full history, file integrity clean | [notes.md](../skills/tooling-opencode-v2-service-health-api.notes.md) |

## References

- [OpenCode V2 documentation](https://opencode.ai/v2/docs/)
- Related: [tooling-opencode-v2-corrupt-db-recovery](tooling-opencode-v2-corrupt-db-recovery.md)
- Related: [tooling-opencode-v2-batch-session-messages](tooling-opencode-v2-batch-session-messages.md)
