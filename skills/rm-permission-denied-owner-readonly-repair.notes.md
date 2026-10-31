# Notes: rm-permission-denied-owner-readonly-repair

Session evidence, generalized. No internal paths, hostnames, project names, or account identifiers.

## Source operation

- Multi-terabyte cleanup of a personal scratch root on a parallel shared filesystem.
- First tier: 38,393 compiler-driver temp files (about 36 GB), 119 scratch directories (about 2.5 GB), and 88 read-only shared-object cache files (about 0.8 GB). About 39 GB freed.
- Second tier: archive-copy of three run trees, about 2.3 TB and 302,000 entries, to a group-shared area, then source deletion with a keep-filter that retained the newest run generation.

## Evidence for the failure modes

- `rm -rf` reported `Permission denied` on owner-owned entries. Observed modes: file `r--r--r--`, parent directory `dr-xr-xr-x`. Sources: container test fixtures with pinned read-only modes, and model-hub cache blobs and directories set read-only.
- The first pass chained three deletions with `&&`. The middle failure stopped the chain, and the final deletion never ran until re-issued separately.
- A final unfiltered shell glob removed three scratch directories younger than one day, after an age-filtered pass had kept them. This was not recoverable. The archive copy was not affected.

## Verification evidence

- Dual-side inventory after the archive copy: identical directory count, file count, symlink count, and byte sum for each tree, matching the transfer statistics.
- After mode repair and deletion: only the keep-filter matches remained, confirmed by a directory listing.
- A process-name scan confirmed no compiler or related process was running before the deletion started.
