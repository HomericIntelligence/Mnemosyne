# Notes: backup-before-state-mutation

Privacy-safe supporting evidence. Hostnames, paths, account names, product
names, and internal identifiers are intentionally generalized.

## Origin

Mid-operation, while an agent was preparing a credential revocation against a
shared production database, the owning user interjected: "don't make any
changes to the database without backing it up first." The rule was adopted on
the spot as a standing gate and a procedure had to be engineered immediately —
the mutation could not proceed without it.

## Environment facts that shaped the procedure

- Datastore volume ~0.4 TB; table-size inspection showed the top tables were
  append-only telemetry (one table alone ~150 GB). The mutable domain —
  accounts, credentials/entitlements, registry, desired-state — was ~70 tables
  each small enough to dump in seconds.
- The platform's native dump client was not installed on the access nodes and
  installing system packages was out of scope; the application's own client
  library exposed `COPY <table> TO STDOUT (FORMAT csv, HEADER)`, which is
  restore-friendly per-table and needs no new dependencies.
- Access nodes could reach the datastore only through a network shim; all
  backup traffic flowed through the same route as the application.

## Procedure used (generalized)

1. Enumerate tables below a size threshold (e.g. 64 MiB total relation size)
   in the mutable schema; record tables above the threshold as `excluded_by_size`.
2. For each included table: `COPY` to per-table gzip CSV via the application
   client library (binary-mode writer — a text-mode writer crashed the first
   run on a type mismatch; see Failed Attempts in the main skill).
3. Per-table live `count(*)` recorded; snapshot directory mode 0700; each dump
   file 0600.
4. Manifest (JSON): created timestamp, purpose, size threshold, per-table
   `{rows, file}`, excluded table list.
5. Restore README in the snapshot directory: one `psql \copy <table> FROM
   '<file>' WITH (FORMAT csv, HEADER true)` skeleton per table.
6. Verification before mutating: `gzip -t` on spot files, CSV row counts vs
   live counts (parity confirmed for the two most sensitive tables), then the
   mutation (an audited single-row revocation) proceeded. The snapshot was not
   needed for a revert that day, but the same gate now precedes every
   mutation.

## Numbers (representative)

- 71 tables dumped, 23 excluded by the size threshold (all telemetry history).
- Most sensitive tables: entitlements ~85 rows, accounts ~36 rows — total dump
  wall time under a minute.
- First snapshot attempt failed partway (writer mode bug); the whole attempt
  directory was removed and the snapshot rerun from scratch rather than
  resumed into the same directory.

## Design notes

- Coupling record: the operations log entry for each mutation names the
  snapshot timestamp; the manifest names the intended mutation. Either side is
  discoverable from the other.
- Exclusions are explicit, not silent: "we did not back up telemetry" is a
  recorded decision, not an accident, and it is safe only because telemetry is
  never in a credential/configuration mutation path. Any mutation whose effect
  surface touches history tables would void that justification.
- Restore executability is tested cheaply (format + counts), not by actually
  restoring into production; a fuller restore drill belongs in scheduled
  maintenance, not in the pre-mutation gate.
