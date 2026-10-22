# Notes: Comet Live Read-Only Release Status Probe

Supporting evidence for `comet-live-readonly-release-status-probe.md`. The
main skill carries the decision rules; these notes carry the verified
session outcomes and the per-finding issue dispositions. Account names, host
names, and infrastructure paths are generalized on purpose.

## Verified session outcomes (2026-10-22, m2 production, release v0.2.3 / `69db2296`)

### Probe environment

- Public client: `<deployment-root>/prod/client/current/bin/comet`, a shim
  resolving into `client/versions/<release-sha>/`.
- Operator CLIs: from the operator venv at `<operator-root>/prod/venv/current`
  (a symlink to `releases/<release-sha>/`).
- Deployment context: inside the operator venv,
  `lib/python3.12/site-packages/comet/data/deployment/contexts/<deployment-id>.yaml`,
  canonicalized once with `readlink -f` and reused for the session.
- Ambient hazard: the operator shell inherited a stale
  `COMET_DEPLOYMENT_CONTEXT` pointing at a retired release tree under a
  different root. Public-client probes ran under
  `env -u COMET_DEPLOYMENT_CONTEXT`; operator probes used the explicit
  canonical flag.

### Component matrix results

| CLI | Result | Notes |
|-----|--------|-------|
| `comet` (public client) | GREEN | `status`, `endpoint`, `whoami`, `smoke`, `chat` all behaved to contract (smoke: HTTP 200 against a live pool; chat: 200 with empty assistant content — see LLM360/comet#2709 and the reasoning-shape corpus entry) |
| `comet-admin` | GREEN except two rows | `logs` RED — operation failed for an operator (LLM360/comet#2879, filed); `paths repair` ORANGE — one unreconciled historical operation remained listed |
| `comet-service` | GREEN except one row | group-level `--help` without a deployment context raised a traceback instead of help text (LLM360/comet#2878, filed) |
| Offline CLI suite | GREEN | the repository's offline CLI test module passed (197 passed, 1 skipped) in the source checkout |

### Release-stage results

| Stage | Result | Evidence |
|-------|--------|----------|
| Tag / publish | GREEN | release v0.2.3 tagged and published at `69db2296` |
| Cutover / serving | ORANGE | release serving, but `health: NOT HEALTHY` in the published status; viewer/database observations missing |
| Open follow-ups | ORANGE | mergeable release PR pending; model qualification and new-pool bring-up steps open (tracked in the release thread issues) |

### Designed-behavior findings recorded as non-defects

- Exit codes 69/75 on deliberately rejected paths are documented CLI
  contracts, not crashes.
- A group-level `--help` needing a context where leaf `--help` does not is a
  per-level surface difference; the defect is the raw traceback (LLM360/comet#2878),
  not the context requirement.
- Pool live-counts moved during the session (replicas recycling). Every claim
  in the final report uses the latest re-probed value.

## Filing strategy applied

Dedupe search before each filing; most defects were already owned.

- Two new issues filed: LLM360/comet#2878 (`comet-service` group `--help`
  traceback) and LLM360/comet#2879 (`comet-admin logs` failure).
- Evidence comments added to existing owners: LLM360/comet#2709 (empty chat
  content reproduced on the current release), LLM360/comet#2175,
  LLM360/comet#2837, LLM360/comet#2106 (canonical-context requirement
  confirmed), LLM360/comet#2829, LLM360/comet#2783 (still-failing viewer
  ingest evidence), LLM360/comet#2102 (client reachability resolved on the
  current published client).
- Each comment carries: exact command, exit code, elapsed time, and the
  bounded output — no transcripts, no environment dumps.

## Evidence-bundle layout used

One session directory containing: raw command outputs (`out*.txt`), a results
TSV per sweep, drafted issue/comment bodies (`issue-*.md`, `c-*.md`), the
canonical context path note, and one authoritative report file that every
matrix row cites. The report is the single source of truth; raw files are
supporting evidence. The session directory is scratch space; the durable
artifacts are the issues, comments, and this corpus entry.

## Privacy screening applied

- Account and host names generalized ("operator account", "public client").
- Deployment roots written as `<deployment-root>` / `<operator-root>`;
  `$COMET_ROOT`-style placeholders in the workflow.
- No API key material, credentials, or per-user paths.
- Issue references use the public tracker, consistent with corpus precedent.
- The release SHA identifies public source in the public repository.
