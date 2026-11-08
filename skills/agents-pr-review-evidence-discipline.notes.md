# agents-pr-review-evidence-discipline — supporting notes

## Umask evidence face (v1.2.0 case, 2026-11-08)

### Observed sequence

A release lane reported two nodes as red on the default branch. One was a genuine
regression; the other was not. The closure note for the shared issue named the
temporary-directory path as the cause.

A later audit re-ran both nodes at one commit:

| Condition | `test_release_activate_and_status_cli` |
| --- | --- |
| Host umask `0002`, temporary directory root-owned and sticky (`1777`) | fail |
| Host umask `0002`, temporary directory owned by the runner (`700`) | fail |
| `umask 022`, root-owned sticky temporary directory | **pass** |

The continuous-integration status was green at that same commit.

### Cause

The gate rejects a selected document when it is group-writable:

```python
before.st_mode & 0o022
```

A file created under `umask 0002` has mode `0o664`, so the gate refuses it. Under
`umask 0022` the file has mode `0o644`, and the gate accepts it. The check is
correct; the ambient umask is the difference.

The direct predicate check confirms it:

```text
umask 0002 -> mode 0o664 | rejected by 0o022 gate: True
umask 0022 -> mode 0o644 | rejected by 0o022 gate: False
```

### Decision value added over v1.1.0

The earlier rules cover the default-branch tip against a PR head, and the local
check against observed continuous integration. They do not cover a local red at a
commit that continuous integration passes. The new rule 5 supplies the probe
(read the ambient value, change only it, re-run the same node) and the stop
condition (do not weaken the gate).

### Disposition

Both nodes pass at one commit under a neutral umask. The reported defect was an
environment face. The environment trap is recorded separately for the host.