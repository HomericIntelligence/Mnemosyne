# Notes: destructive-reset-requires-explicit-rejection

Privacy-safe supporting evidence. All hostnames, paths, account names, product
names, and internal issue identifiers are intentionally generalized.

## Incident mechanics (production, one afternoon)

Context: a model-serving deployment rollout with self-serve credential
onboarding. The onboarding script verified a saved credential by calling the
deployment's identity endpoint, and on failure it reset local credential state
(credentials file + lifecycle journal + lock, with backup) and minted a fresh
key via the platform's self-serve request flow. Server-side, the credential
store enforced one active ordinary key per user per cluster: an unrevoked row
counts as active even when its key material no longer exists on any client.

1. **HTTP 502 incident** — user A's run hit `HTTP 502` from the identity
   endpoint (the serving layer was under capacity churn; the endpoint itself
   was intermittently unhealthy). The script classified it as "stale key" and
   reset. The user's pre-registration state was discarded; luckily the
   fresh registration succeeded, so the blast radius was limited to an
   unnecessary key mint.
2. **ReadTimeout incident** — the platform team's test account, holding a key
   confirmed minutes earlier (identity 200), hit `ReadTimeout` on the same
   endpoint on the next run. The script reset the working key. The server kept
   the entitlement active; every subsequent self-serve registration returned
   `conflict`. The account was wedged until an operator (a) snapshotted the
   affected config tables, (b) revoked the orphaned row with the audited
   administrative revoke verb, (c) cleared the fulfillment worker's stale
   `conflict` results for the queued request so the same request could be
   re-evaluated, and (d) re-ran fulfillment → `registered`. Total operator
   time: ~30 minutes; user-visible outage: ~1 hour.
3. **Post-gate behaviour** — after the gate shipped, an intermittent
   ReadTimeout hit user A again during the same endpoint flakiness; the
   script failed soft ("identity check failed but NOT with an auth rejection
   — saved key kept, nothing reset; retry shortly"), and the next run
   succeeded. Identity endpoint confirmed healthy for the same user both
   before and after.

## The gate as shipped (bash)

```bash
if cenv comet whoami >"$TMP" 2>&1; then
  VALID=1                      # key verified; reuse this result, do not re-check later
else
  grep -Eq "HTTP 401|rejected authentication" "$TMP" || \
    fail_soft "identity check failed but NOT with an auth rejection — saved key kept, nothing reset; retry shortly"
  # only here: backup, delete credentials + lifecycle journal + lock, fresh REGISTER
fi
```

Two extra decisions the incidents motivated:

- **Skip redundant re-verification**: the script originally ran the identity
  check a second time after the validation step; seconds after a 200, the
  second call hit a ReadTimeout and failed the run for an already-valid user.
  Reusing the first positive result removed the exposure entirely.
- **Fail-soft message discipline**: the failure banner explicitly tells the
  user not to hand-delete local state — manual deletion is how the orphan was
  created in the first place.

## Second-order mechanism: published-result short-circuit

The platform's fulfillment worker consumes queued requests idempotently: once
a result is published for a request, later passes do not re-evaluate it. After
the blocking condition (orphaned active row) is removed, the queued request
still carries its stale published `conflict`. Re-fulfillment only registers
after the stale result is quarantined (moving the worker's own published
artifact aside) or a fresh request is submitted. Diagnosis hint: check
result-file mtimes against the fix time — a result older than the fix can
never reflect the fixed state.

## Related operational rules from the same rollout

- Backup before any state change you cannot reverse: applied to local client
  state (tar backup of the credential directory) and to database mutations
  (per-table snapshots of the small config tables; a full dump was impractical
  because the bulk of the database was telemetry history far outside the
  mutation path).
- Scrub the environment of tool invocations (`env -i` with explicit pins):
  ambient variables from a developer's shell repeatedly hijacked child
  tooling (lane selection, credential discovery). Same root insight as the
  reset gate: automation around credentials must control its inputs exactly.

## Verification evidence

- Pre-gate: two resets on non-rejection failures (one 502, one ReadTimeout),
  one orphaned entitlement, one permanent-`conflict` wedge, one operator
  rescue.
- Post-gate: zero resets on transient failures; three users completed
  self-serve onboarding, including one full register+acknowledge cycle with
  no operator involvement, while the identity endpoint continued to flake
  intermittently.
