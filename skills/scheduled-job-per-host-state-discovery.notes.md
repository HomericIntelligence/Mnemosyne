# Notes: scheduled-job-per-host-state-discovery

Supporting evidence for `scheduled-job-per-host-state-discovery.md`. Subject-matter
specifics are generalized here per the privacy rules; provenance lives in Git.

## Incident shape

An hourly self-resubmitting batch job exported session state from a per-user
application database to shared storage. Its state path was fixed to the
application default under home (`$HOME/.local/share/<app>`). One long-running
interactive allocation on a compute node launched the application with an
environment override pointing the state directory to node-local scratch
(`/var/tmp/<user>/<app>`), a reasonable choice because a shared home must not
back a live WAL database.

Effects, measured from the run log:

- Every scheduled run on that node failed with `database not found` — 29
  consecutive failures spanning roughly three days — yet each run exited 0,
  so nothing surfaced the gap.
- The failure list also contained `database disk image is malformed` and
  `file is not a database` from races against the live WAL files, plus one
  `TypeError: ... 'NoneType' and 'int'` caused by a NULL timestamp column:
  one bad row aborted the entire dump.
- The wrapper chained `flock -n` to the producer, so rc 1 meant both "lock
  busy" and "producer failed"; overlapping runs were logged as failures.

## What changed

1. The producer gained a precedence-list resolver: explicit argument wins,
   then `$XDG_DATA_HOME/<app>`, then the home default, then
   `/var/tmp/$USER/<app>`. No match → exit 2 with every searched path printed
   and a hint on how to override. The static default constant was removed so
   an import-time evaluation cannot freeze a wrong path.
2. NULL timestamp handled as "cannot prove currency" → rewrite; regression
   test reproduces the crash. Schema check confirmed the column has no
   NOT NULL constraint in the real database, so the case is reachable.
3. Wrapper now takes the lock on its own descriptor; busy lock exits 0
   silently; real failures log timestamp, exit code, and hostname. A
   heartbeat file records each successful run; staleness is directly visible.

## Behavior-first tests added (all failed before the change, passed after)

- NULL timestamp in `is_current`-style freshness check → False, not TypeError.
- Full dump survives a session row with NULL timestamp (rewritten, not abort).
- Candidate precedence: XDG first, home second, scratch last; deduplication.
- XDG precedence honored over the home default; home fallback when unset.
- No database anywhere → exit 2 with every searched path in stderr.

## Verification evidence

- Full module test suite: 24 passed (18 pre-existing + 6 new).
- Live host: no-argument discovery selected the correct database and dumped
  23 sessions. Empty-`HOME` simulation: exit 2 with the full searched list.
- Two concurrent wrapper invocations: one worker, one silent exit 0.
- Recovery side: stranded-node state (≈1.7 GB) archived through a scheduler
  job onto shared storage; recovered database passed `PRAGMA quick_check`
  with 2,499 sessions / 102,257 messages; 291 sessions missing from shared
  storage were backfilled and spot-verified by exact message counts; a later
  full-file merge of sidecar state (28,707 files across `shell/`,
  `snapshot/`, `tool-output/`) was verified byte-identical with `cmp` —
  filename presence alone was treated as insufficient.
- The upstream fix landed through normal review with all required checks
  green.

## Deferred-to-existing-skill material

Two sessions had divergent histories (neither a superset, each holding a few
message IDs the other lacked). The overwrite policy that kept both is exactly
`durable-export-overwrite-guard`; the resolution decision (inspect content:
all divergent messages were failed turns — an auth-401 dead turn and an
empty-content turn; preserve rejected versions with hashes; then adopt the
strictly newer, larger history via the guard's explicit bypass) was recorded
in local recovery notes, not this skill, because it is an application of the
existing guard, not a new decision rule.

## Why a new skill instead of amending a sibling

- `durable-export-overwrite-guard` protects destination artifacts from bad
  overwrites. This lesson is about *finding the source at all* and *making
  absence loud* — different retrieval intent.
- `slurm-memcg-oom-kills-cross-filesystem-copy` and
  `hephaestus-interrupted-implementation-lane-recovery` are failure-arrest
  recoveries with unrelated triggers and outcomes.
- The corpus's many "fail loud" entries cover flags, resolvers, guards, and
  gates — none covers per-host state-path discovery for re-launched jobs.

TSO: tool-environment notes are generic on purpose; public standards (XDG
spec, FHS `/var/tmp`, Slurm concepts, SQLite semantics) carry the concrete
content.
