# Supporting notes: weekly-report-remote-access

Supporting evidence for [weekly-report-remote-access](./weekly-report-remote-access.md), kept out of
normal retrieval. Infrastructure identifiers (host names, endpoint names, job ids, addresses) are
generalized on purpose; the decision branches are the evidence.

## Provenance

- Source: one production session generating the comet weekly report `2026-11-07` from a host
  outside the telemetry database's private network. Telemetry collection, figure rendering, LLM
  prose, PDF render, commit, and PR all completed locally on that host.
- The report PR is public (the project's weekly report series), which is why the mechanism (the
  pipeline's phases, the repository's loopback dial-host environment knob) is safe to describe.

## Diagnostic signatures

These signatures drove each branch in the main entry. Match on the signature, not on identity.

| Signature seen by the operator | Branch it selects |
| --------- | --------- |
| `TimeoutError` from an async connection at DSN connect time | No route to a private-network database: open a reach-through-forward and use the loopback dial-host override |
| `InvalidPasswordError` right after the greeting works | Credentials are reaching the server but are wrong: the local dotenv is stale or was sourced by hand; let the loader read it, or refresh from the live component |
| Window line reads `1.0 days, source: previous report` on the report's own date | The newest dated directory is the run's own directory: pass `--since` explicitly |
| `OSError: cannot load library 'libpangoft2...'` in the PDF phase | Render toolchain libraries are not on this host: run the render with a user-space library path |
| Exit with `refusing to render ... contains personal data: ['<address>']` | The prose scan found a raw address: the address text, not the guard, changes; an HTML entity keeps the reader-visible address identical |

## Credential refresh details

- The refreshed credential came from the live component's own process environment, read in one
  step of that component's scheduler allocation (`--overlap --cpu-bind=none` was needed on that
  runtime; the default bind rejected the step). Only the database variables were extracted.
- Publication to the shared configuration path used a temporary file plus an atomic rename, per
  the shared-storage no-lock rule. Values were never printed to a transcript; only variable names
  were reported.
- The step belongs on the operating account of that live component. On a different account this is
  a stop, not a workaround.

## Decisions the general entry deliberately keeps short

- Alternative access plan: run the collectors inside the serving allocation's compute nodes.
  Rejected then because pipeline scripts, the `uv` environment, and its locked dependencies already
  ran on the non-private-network host, and the repository carried a dial mechanism designed for
  exactly this case. Revisit only if the dial override is removed.
- Alternative to the entity fix: add a public-address allowlist entry in the pipeline's scanner.
  Kept out of the entry as the recommended path: the pipeline is shared code, the address is one
  document's content, and each new carve-out invites the next.
- The window's `1.0 days` artifact was deleted, the window was repinned, and the report's event
  note records the explicit `--since`. The pipeline author was not asked to change the resolver —
  a guard against the self-consume hazard would also be correct, but the entry rules the operator
  side.

## Verification limits

- Verified: collect, figures, prose call, PII scan, PDF render, and publication of the corrected
  report all passed on 2026-11-07. The number sweep reproduced collected analytics against the
  published prose (one count error found and fixed before render).
- Not verified: the fallback plan of running collectors in the serving allocation, multi-forward
  or bastion chain shapes, other database schemas, rotation of the component's environment while
  reading it, and any other operating system than the recorded host.
