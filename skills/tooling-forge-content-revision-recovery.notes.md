# Forge Content Revision Recovery — Notes

## Source incident (2026-10-28/29)

A pull request in a cross-org coordination exchange carried a body of about 14.5 KB with
protocol bindings and a rebase note. An external system emptied the body, while its
author-facing event text from the same window read "the body is updated". The live
readback length was zero bytes.

The revision history (`userContentEdits`, three edits) showed:

- edit 1: the body set (about 10.8 KB of content),
- edit 2: a note section added (about 14.5 KB of content),
- edit 3: the content removed (empty body).

The destructive edit occurred about seven minutes after the last full-body edit. The
second edit's content was saved to a file (about 14.5 KB, sha256 recorded). Restoration
used the CLI edit command with a body file. The readback body was compared byte-for-byte
with the file: identical apart from the line terminator that the API applies. Four
marker strings were grep-verified present. A later fix round appended an incident note
that states the destructive timestamp and the revision-history restoration, with the
checksum. No labels or review state were changed during the recovery.

## Verification limits

The procedure was executed once, end-to-end, with the byte-level readback verified. The
verification field is `verified-local` for this reason. Exhaustion behavior for
artifacts with many edits (paged history) was reviewed but not executed. Restoration of
deleted (not edited) artifacts is out of scope.

The source case identifiers (repository, pull request, exact timestamps) are
intentionally omitted. The coordination lane retained the recovery file and checksum for
a terminal review record in the same lane.
