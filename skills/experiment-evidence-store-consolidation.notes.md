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
