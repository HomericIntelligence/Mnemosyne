# Ambient Partial-Clone Lazy-Fetch Read Hazard — Notes

Supporting evidence for `ambient-partial-clone-lazy-fetch-read-hazard`.
All identifiers are generalized; repository and review identities stay out
of the durable record.

## Source session evidence

One review session on a shared multi-lane repository checked out its primary
project work an ambient `blob:none` clone. The evidence run unfolded as
follows:

1. A snapshot-preparation helper failed closed with only a generic message.
   The host could not establish the bounded size enclosure the helper
   requires, and a complete non-partial store is a hard prerequisite of the
   helper's verification path.
2. The ambient clone still held both review revisions as commits, so commit
   probes passed and a reviewer continued structure reads locally.
3. A command that looked metadata-only — a one-commit listing in the ambient
   checkout — started a silent lazy fetch of about 765 blob objects, about
   29 MB, running as a background process with no progress report.
4. The lane's own evidence policy forbids acquiring objects through the
   ambient checkout remote. Lazily completing the ambient store was therefore
   unavailable both as a size hazard and as a lane violation.
5. Read-heavy verification moved into an explicitly acquired complete,
   non-shallow disposable store, where the reviewed base, head, merge base,
   and tree identifiers were verified before any file read.

## Decision record

- Classify commands inside a partial clone. A `blob:none` filter keeps
  commits and trees local; anything that needs blob content fetches it on
  demand.
- Do not trust blob-typed probes as completeness answers. They succeed by
  fetching, which proves only that the remote can serve the object.
- Move bulk reads (tree walks, full-file diffs, multi-file audits) into the
  explicitly acquired immutable source for the task.
- Acquisition boundaries of a verification lane override convenience: the
  ambient checkout remote stays read-limited even when a fetch looks cheap.
- Record the observed command and byte count once; later lanes then decide
  with one config probe instead of one accident.

## Verification record

- `git config remote.origin.partialclonefilter` printed the active filter;
  promisor-pack markers were present under the object store.
- One lazy-fetch event measured: roughly 765 objects, about 29 MB, from a
  single metadata-looking command.
- Verification completed from the explicitly acquired store; the remote
  fetched `base-ref` and pull-request ref matched their captured object
  identifiers, the store was non-shallow, and the merge base was unique.
- No verification read ran from the ambient checkout afterward.

## Provenance

- Affected dispositions in the same delivery: one create (this entry) and
  one amend (peer-completion audit, digest-reproduction clause). The two
  share one session evidence base but keep different intents: ambient read
  pricing here, delivered-evidence reproduction there.
