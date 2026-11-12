# service-down-report-triage notes

Supporting evidence for the main entry. Generalized: hostnames, product and
cluster names, model names, job identifiers, and issue numbers are removed.

## Source session

- Dates: 2026-11-11 to 2026-11-12. Trigger: a user asked why the tracked
  inference service of one GPU cluster was "down".
- All probes were read-only: health route, raw status record, queue listing,
  and one unauthenticated request.

## Probe evidence, day 1

- Health route: HTTP 200, body `ok: true`, fair-share healthy, peers healthy,
  supervisor healthy with heartbeat age about 14 to 40 seconds.
- Sub-component: a key-cache synchronization field reported the degraded state
  `stale_serving`, `degraded: true`, and the fixed error category
  `http_error` on every attempt. The category is one of a bounded enum
  (`transport_error`, `http_error`, `invalid_json`, `invalid_payload`,
  `invalid_row`, `authority_unavailable`, `generation_race`,
  `snapshot_write_error`, `snapshot_read_error` in the observed
  implementation), so it names the boundary without exposing payload data.
- Summary status CLI: printed a healthy gateway verdict and pool rows only. It
  did not surface the sub-component degrade.
- Bounded consequence: the gateway kept admitting existing keys from its last
  good snapshot; new or revoked keys would not propagate while degraded.
- Pool rows showed four states worth keeping in mind: `serving`,
  `floor_breach` with a short count, `off`, and `starting` with a pending
  count.

## Probe evidence, day 2 (self-heal)

- Same health route: sync state `fresh`, `degraded: false`, last error null.
  No intervention was recorded between the two observations.

## Tool-failure branch

- The installed public status client exited with a schema-validation error:
  `Extra inputs are not permitted` for a `published_at` timestamp field that
  the service had begun publishing in its status record.
- A client build that matched the deployed release parsed the same record and
  printed the full status matrix. The service was up during the whole window.

## Capacity branch

- Two pools reported zero live replicas against nonzero floors; one large pool
  reported a desired count far above its live count.
- The queue showed every replica job for the starved pool pending behind a
  scheduler group-limit reason while the account's running nodes stood at the
  reported cap. The service requests replicas; the scheduler owns the limit.
- A later observation showed the starved pool serving on the preemptible tier,
  which bypassed the cap that had blocked the protected tier.

## Unauthenticated front-door probe

- `GET /v1/models` without a key returned 401 with an invalid-key error body.
  This is a correct admission rejection and proves the front door works; it is
  not a failure signal.

## Classification outcome

- Report: "why is it down". Verdict delivered: the request path was up; the
  service was degraded-but-serving on one sub-component that self-healed; the
  visible capacity shortfall was a scheduler cap; and one broken status client
  was a version mismatch. No incident was opened, and no component was
  restarted.
