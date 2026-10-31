# Notes: OpenCode V2 service health through the HTTP API

Companion evidence for
[tooling-opencode-v2-service-health-api](tooling-opencode-v2-service-health-api.md).
All values come from one verified session against a public OpenCode v2.1.x
release on a developer workstation. No host, path, or identifier from the
source environment is recorded here.

## Why this entry exists

A database-incident triage produced two opposite signals at once: the server
log repeated `SQLiteError: database disk image is malformed` for indexed
message reads, while the product seemed unable to show history. The decisive
question was "is the file damaged, or is a process confused?". File-level
checks answered the first half; the HTTP API answered the second half by
showing that the running service still served the complete history. That
proof cancelled a recovery that would have replaced a healthy database.

## Authentication evidence

- `GET /api/project` with `Authorization: Bearer <service password>` returned
  `401` with body `{"_tag":"UnauthorizedError","message":"Authentication required"}`.
- `GET /api/project` with header `x-opencode-password: <service password>`
  also returned `401` with the same body.
- `GET /api/project` with `-u "opencode:<service password>"` (HTTP basic
  auth) returned `200` with the project JSON array. The username value was
  not validated; the password alone decided access.
- The service file path is the standard state location
  (`~/.local/state/opencode/service.json`) and holds `id`, `version`, `url`
  (loopback HTTP), `pid`, and `password`. The PID matched a live serving
  process during the probes.

## Path and status-code behavior

| Request | Status | Body |
| --------- | --------- | --------- |
| `/project` (no `/api`) | `200` | Web application HTML, not data |
| `/session` (no `/api`) | `200` | Web application HTML, not data |
| `/api/project` | `200` | JSON array of projects |
| `/api/session?directory=<abs>` and `?projectID=<id>` | `200` | `{"data":[...]}` |
| `/api/session/<id>/message` | `200` | `{"data":[...]}` with text and tool blocks |
| unknown `/api/*` path | `404` | JSON error |
| known `/api/*` path, wrong auth | `401` | JSON error |

The `200` on non-API paths is the false-success trap: a probe that checks
only the status code concludes the service works. Body shape is the signal.

## Three-way comparison in the verified incident

1. API: every project listed; one project returned its full session list; a
   sampled session returned its transcript. History was servable.
2. Database file: `PRAGMA integrity_check` returned `ok`; per-table counts
   matched the API results for the sampled project.
3. Product surface: the log showed the failures, which came from a process
   generation older than the installed binary during a version overlap.

Split: client-visible breakage came from the stale process generation, not
from data loss. Correct action: stop every process of the product and start
once. Recovery tooling was not used.

## Scope limits

- All probes were GET requests. Write or mutation endpoints were not tested
  and are out of scope for this entry.
- The exact response fields can change between product versions; the entry
  records the shapes observed on v2.1.x as an example, not as a contract.
- The basic-auth mechanism and the non-API `200` behavior are the two details
  most likely to stay stable and most likely to block a first probe.
