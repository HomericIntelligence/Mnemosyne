# Notes: Comet User Credential Lifecycle Diagnosis

Supporting evidence for `comet-user-credential-lifecycle-diagnosis.md`. The
main skill carries the decision rules; these notes carry the verified session
evidence and the debug-script pattern. Account names, host names, and key
identifiers are generalized on purpose.

## Verified session evidence (2026-10-22, m2 production, release `69db2296`)

### Account A — ordinary test account, cluster GPU node

Environment: public client shim on `PATH` through `$COMET_ROOT`; no
operator-venv access needed.

Baseline and store:

- `comet status`, `comet endpoint`: exit 0, gateway up. Public reads healthy.
- `~/.config/comet/credentials`: mode 0600, mtime 16:59Z that day — a delivery
  had completed earlier.
- `comet whoami` at 18:39Z: HTTP 401 ("the server rejected authentication …
  allow time for key propagation"). ~100 minutes after the save, far beyond
  the ~60 s propagation window. Same minute, a staff account's older credential
  authenticated with 200. Classification: link 3 (admission) dead, consistent
  with LLM360/comet#2784 (key-cache database partition empty).

Request-key behavior:

- `comet request-key --wait 15` under `timeout 120`: exit 0 after 67 s,
  terminal line `Credential request state: pending.` (submit + reconcile +
  recovery waits stack beyond the nominal wait value).
- `--wait 1` under `timeout 90`: exit 0 after 11 s, same `pending`.
- A third run sampled at 25 s: `/proc/<pid>/wchan` = `hrtimer_nanosleep`;
  open fds only `/dev/null`, the captured output file, `/dev/urandom`. No
  network or filesystem descriptors. The wait is a local sleep-poll for a
  service result that never arrives.
- `strace -p` as the same uid: refused, `yama/ptrace_scope` blocks non-child
  attach. `py-spy`: not installed. `/proc` sampling was sufficient.

Rendezvous state (metadata only; contents are service-owned):

- `$COMET_ROOT/prod/credentials`: mode 0711 (`drwx--x--x`).
- `requests/`: mode 3733 (`drwx-ws-wt`), parent mtime same day — clients can
  publish and do.
- `deliveries/` parent mtime ~3 weeks old; `results/` parent mtime ~3 weeks
  old — the consume/deliver loop had not moved for weeks.
- Listing `requests/` as a non-owner: EACCES, expected on `--x` parents.
  The per-user request subdirectory did not exist from the account's view
  (ENOENT), consistent with requests being consumed-or-never-visible.

Classification: link 2 (fulfillment) dead — matching LLM360/comet#2874
(gateway launch omits `COMET_DB_DSN`; filed the same day) and
LLM360/comet#2157 (runtime template withholds the DSN by design). Combined
with the link-3 admission failure, self-service issuance was a dead end at two
links for this lane.

### Account B — staff account, login node

Environment: no `comet` on `PATH`; the absolute client shim path ran fine
(world-traversable client tree — this resolved the reachability concern in
LLM360/comet#2102 for the published client).

- `comet whoami`: 200 in 8 s — the saved credential worked (team-scoped,
  reported `is_service: true`; attribute worth an operator sanity check but
  not a blocker).
- `comet request-key --wait 15`: exit 1 after 9 s with an unhandled traceback:

```text
comet/cli/main.py:244 in request_key
comet/sdk/discovery.py:385 in prepare_key_request
comet/sdk/credential_publication.py:582 in prepare_key_request
PermissionError: credential lifecycle intent does not match saved credential
```

- The failing branch compares `key_id_of(saved_key)` with the durable
  lifecycle record's `key_id`; a valid-but-different saved credential (an
  older rotation artifact) dead-ends the prepare step. No rotate or repair
  command exists (LLM360/comet#2161). Commented on LLM360/comet#2868 with the
  distinction from that issue's 401-driven case: here the saved key is
  healthy, yet `request-key` still raises instead of reporting a no-op or a
  typed rotation path.

## Debug-script pattern (user-runnable, read-only)

Give the affected account a script with these sections. It writes one report
file to a writable temp dir. No secret value leaves the machine.

1. Identity and environment: `date`, `hostname`, `id`, `getent`-based primary
   gid vs `id -g` (request-key requires them to match), `umask`, relevant
   `COMET_*` variables with values masked.
2. Client build identity: resolved shim path, version output, dist location.
3. Public runtime reachability: `status.json`/`gateway.json` metadata,
   `comet endpoint`, `comet status` — each under `timeout`, with
   `[exit=N elapsed=Ts]` trailers.
4. Credential-store state, masked: `stat` of `~/.config/comet/credentials`;
   single-level jq mask for structure; `comet whoami` under timeout.
5. Rendezvous state: `stat`/`getfacl` of the credentials parents; listing
   attempts with the expected errno annotated; latest parent mtimes under
   `results`/`deliveries`.
6. The hang itself: `request-key --wait 15` and `--wait 1`, each under
   `timeout`, exit + elapsed recorded.
7. Where it blocks: start `request-key` in the background, after ~25 s print
   `/proc/<pid>/wchan`, `/proc/<pid>/status` state line, and `ls -l`
   `/proc/<pid>/fd`; try `py-spy dump`/`strace` only if available and
   permitted.
8. Filesystem latency probe: timed `stat` of the rendezvous dirs and the
   client shim; ~0 s excludes a mount stall as the hang cause.

Masking rules:

- Print `COMET_API_KEY=<set-masked>` only; never the value.
- Mask credential values with a single-level filter, for example
  `jq 'with_entries(.value |= (if type=="object" then with_entries(if (.key|test("key|token|secret";"i")) then .value="<masked>" else . end) else . end))'`.
  A recursive `def mask` variant ended with `error: cannot allocate memory`
  in the verified session; the single-level form is sufficient for the store
  schema.
- Never include key identifiers in reports or issues; describe vintages
  ("older key", "freshly delivered key") instead.

## Failure-mode to owner map (m2 lane, 2026-10-22)

| Link | Verified failure | Owning issues |
|------|------------------|---------------|
| Prepare + publish | `PermissionError: credential lifecycle intent does not match saved credential` at `credential_publication.py:582`; exit 1, no repair path | LLM360/comet#2868, LLM360/comet#2161 |
| Fulfillment | `pending` exit 0; `results`/`deliveries` parents untouched for weeks; local nanosleep polling | LLM360/comet#2874, LLM360/comet#2157 |
| Admission | saved key 401 at ~100 min; older keys authenticate | LLM360/comet#2784 |
| Admin fallback | no supported admin-side ordinary-user issuance | LLM360/comet#2162 |

## Privacy screening applied

- Account names generalized to "an ordinary test account" / "a staff account".
- Host names removed ("cluster GPU node", "login node").
- No API key values, key identifiers, or per-user directory listings.
- Deployment paths reduced to `$COMET_ROOT`-relative form.
- Issue references use the public tracker, consistent with corpus precedent.
