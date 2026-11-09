# Evidence notes: privileged input root scope

This file holds supporting evidence for
[privileged-input-root-scope.md](privileged-input-root-scope.md). The rules live
in the main entry. These notes give the provenance and the limits of the
evidence.

## Provenance

The evidence comes from one plan-review session in a 2026-11 repository. The
session inspected the gateway that reads batch input paths, its intake
confinement helpers, the deployment-context record, the service path-policy
table, and the private batch store helper. The inspection was read-only and
produced a plan. No code changed, so the entry carries `verified-design`.

## Observed repository facts (generalized)

| Fact | Generalized form |
| --- | --- |
| The gateway formed the accepted roots from three service-owned artifact directories under the administrative root. | Roots taken from service state never contain a caller-owned file. |
| The deployment context already verifies that the administrative deployment path equals the administrative root joined with the context suffix. | The suffix is a proven value, so the derived root needs no new configuration key. |
| The intake code refuses an outside path by a lexical check before `resolve()`, `stat()`, or `open()`, so no path-existence oracle exists. | Reuse an existing lexical preflight rather than add a second check. |
| The owner check compares the file owner with the account resolved through the host identity store. | The leaf identity and the owner check must use the same identity source. |
| The private batch store uses a strict owner-only directory mode and rejects any other metadata. | A drop-area design must not relax the child contract. |
| The service already publishes sticky, set-group-ID, write-without-read request directories. | That mode is the established drop-area convention in the same repository. |
| A stale public document promised a shared mount path that the service did not accept. | A false root claim in user documentation is a defect of the same change. |

## Limits

- The design was not implemented and no test ran. Verify the rules in the
  target repository before you treat them as proven there.
- The entry does not name the repository, its paths, its account names, or its
  issue identifiers.
- The reserved-name defense is an availability control. A complete security
  control for a shared drop area needs a separate ownership review.