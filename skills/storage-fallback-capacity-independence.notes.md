# Notes: storage fallback capacity independence

Supporting evidence for [storage-fallback-capacity-independence.md](storage-fallback-capacity-independence.md).
These notes keep the measurements and command detail out of the main entry.

## Source context

A service ran on a multi-tenant shared filesystem and needed a spill target for
non-critical writes while its primary deployment root filled with `ENOSPC`.
The primary store had already been moved several times, and the last move placed
the spill tree next to the model store. An operator questioned the target size,
which led to a broader writable-location audit.

## Measurements that shaped the rule

- `df` and `statvfs` reported the same whole-mount figures for every subtree:
  about 5.0 PiB total and about 0.66 PiB free. The values did not change between
  the primary root, the store, an unrelated team tree, and the shared parent.
- The declared allocation for the service store subtree was 256 GiB. Current
  usage of the model tree alone was about 214 GiB, so the spill sibling had
  about 42 GiB of headroom. The spill tree shares that allocation.
- A scan of the shared top level found three group-writable trees from the
  process groups: the platform's own tree (it contains the failing deployment
  roots, so it shares the primary allocation), the store tree above, and one
  other team's tree. A world-writable backup area existed outside the shared
  tree; it had no owner decision for this use.
- A read-only public team tree and a platform deployment tree were writable only
  for their owners. Mode and group inspection was enough to reject them, but
  the candidates that mattered were confirmed with a real create and unlink.

## Command detail

Access probe, portable to any POSIX shell:

```bash
for d in "$@"; do
  p="$d/.write-probe.$$"
  if (umask 077; printf 'probe' > "$p") 2>/dev/null; then
    echo "$d: writable"
    rm -f "$p"
  else
    echo "$d: refused"
  fi
done
```

Candidate enumeration:

```bash
id
for d in /shared/*; do stat -c '%n group=%G gid=%g mode=%a' "$d"; done
du -sh /store/subtree
```

Keep the probe name unique per process and remove it in the same command. Do not
leave probe files in a shared tree.

## Why the audit was necessary

The first spill design used `<store-parent>/spill` because it looked like a
separate location and had passed a write probe. The probe proves access only.
The audit showed that the sibling shares the store allocation, so a full store
takes the spill tree with it. The correct outcomes were a dedicated allocation
or a quota increase, not another sibling.

## Escalation shape

Give the storage owner these inputs:

- the failing primary path and the failure class (`ENOSPC`/`EDQUOT`);
- the declared allocation and measured usage of every candidate;
- the independence result for each candidate;
- the requested outcome: a dedicated allocation, or a specific quota increase.

When the owner creates a new allocation, re-run the access probe, measure the new
usage, and update the fallback configuration and its runbook. If the fallback
path is derived in code, the derivation needs an explicit override for the new
allocation instead of another relative sibling.

## Evidence limits

The environment had no client-side quota tooling, so quota values came from the
operators and from usage measurement. Treat an unstated quota as unproven. The
audit was read-only; the only writes were probe files that were removed in the
same command.