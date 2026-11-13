# Notes: experiment-evidence-store-consolidation

Supporting evidence for the main entry. Privacy-safe: origin paths, project
names, hostnames, and recorded identity values are withheld.

## Source session

A user request consolidated a closed machine-learning research campaign. The
campaign had sealed its final decision with content-hash identities and closed
successfully after a prospective exact reproduction. The consolidation task
had three parts: locate the result, move the durable evidence to a shared
store, and delete the rest.

## Verified execution evidence

- Discovery: the sealed decision record cited each source artifact by path and
  sha256. Following those citations identified the full keep-set. A corpus
  search (about 1,300 knowledge entries) found no entry for this intent; the
  closest entries covered live service data relocation and fragile-server
  reads, both different intents.
- Move: four parallel background rsync streams covered the five categories.
  Largest stream: about 190 GB over about 7,100 files, zero rsync errors,
  roughly 280 MB/s. Per-file `--remove-source-files` deletion completed for
  every tree; emptied source directories were then removed with
  `find -depth -type d -empty -delete`.
- Verification before delete: all five key sealed records parsed as JSON at
  the destination and showed the recorded decision fields.
- Store size after the move: about 197 GB in five categories plus a README.
- Deletion: about 445 GB of superseded material removed across ten directories
  and four log files. One read-only data file inside a write-protected
  directory raised `Permission denied` under `rm -rf`; `chmod -R u+w` on that
  subtree cleared it. A final prefix listing confirmed zero remaining entries.
- Agent session logs on the shared drive were excluded from both the move and
  the delete, per user instruction.

## Corpus search terms used

remove-source-files, rsync, relocat*, sealed proof, sealed evidence, evidence
chain, hash-verified, content hash, stale absolute path.

## Addendum — second-source session (2026-11)

A user asked what could be removed from about 4 TiB held in three sibling
copies of a closed 23-cycle training campaign, plus home-side leftovers.
Details of the new decision branches, privacy-generalized:

- Duplicate trees: full file inventories (about 294.6k, 290.7k, and 1.6k
  files) proved zero unique content in two copies. One same-name file was a
  truncated prefix (about 0.3 GiB vs the 2.1 GiB complete file) that a
  name-only diff would have missed. Both copies were removed: about 2.3 TiB.
- Deliverable store found mid-task: a published store (88 sha-verified model
  trees for 149 published candidates, manifest, ranked leaderboard) changed
  the retention split. Every class prune re-verified it first: manifest entry
  count equals trees on disk, leaderboard parses, top-ranked models present.
- Winner verification: the frozen leaderboard's incumbent field named a
  candidate below its own ranking's top. The true top was an exact tie:
  identical macro, per-sample wins equal across 2,784 shared sample IDs,
  p=1.0 in every family, equal total correctness. A co-champion
  recommendation was drafted; loser classification was blocked on this
  evidence. Two families scored all-zero for every top candidate and were
  flagged as non-discriminative (possible harness fault), which the write-up
  disclosed rather than hid.
- Class pruning with manifests: intermediate stage weight files (22 payloads,
  about 218 GiB) and 127 adapter-training trees (2,556 files, about 647 GiB)
  deleted by content class; per-file TSV manifests persisted before each
  delete; remaining-count zero afterward; a separate pass removed 195 empty
  checkpoint husk directories.
- Protected-path guard: a deletion script aborted when the expected
  protected-path count read 2 of 3; investigation showed one tied candidate
  had no raw weights at all (evaluated model only). The run proceeded with
  the two existing protected directories only after that evidence.
- Payload-vs-records split for home calibration runs: only files above
  100 MiB were deleted (28 payloads, about 216 GiB); every config, log, and
  evaluation record stayed.
- Terminal cycle kept record-only: the terminal-invalid cycle's slot bulk
  (about 155 GiB) was removed while its small terminal JSONs were kept.
- Post-hoc prune record: an executed plan (288 targets) had no completion
  record; one was written post hoc citing inventory evidence of absence.
  The store's plan copy hashed differently than the plan's embedded hash;
  both values were recorded with the discrepancy disclosed.
- Cumulative accounting reconciled exactly by du: the archive store fell
  from about 2.2 TiB to about 1.05 TiB. Shared-filesystem quota reclamation
  lag was observed, matching the earlier delayed-record failure mode.
- Store READMEs were placed at both roots: one-paragraph result, layout map,
  deleted-material audit, origin-path caveat, and preserved-material list.
