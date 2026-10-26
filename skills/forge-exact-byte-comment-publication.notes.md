# Notes: forge exact-byte comment publication

Supporting evidence for `forge-exact-byte-comment-publication.md`. Main-file rules stay in the main file; this file holds the session-grade detail.

## Verified context (privacy-generalized)

Source session: a canonical plan–review exchange on an issue tracker inside a private monorepo. The exchange helper prepares each comment body (visible text plus a signed carrier), the author posts it with the GitHub CLI, and a verifier compares the live comment with the prepared operation byte for byte and checks the one-comment-per-role invariant. Repository name, issue number, and comment IDs are withheld by policy; the byte counts and diagnostics below are the useful invariant.

## The failing write path

The prepared body string (6579 bytes) was placed into a file with this shape of code:

```python
print(prepared["operation"]["body"])   # writes body + "\n" -> 6580 bytes
```

`gh issue comment <number> --body-file` then posted exactly those 6580 bytes. The verifier compared and reported an identity conflict:

```
{"code":"publication_identity_conflict","message":"The prepared issue-comment outcome was not verified exactly."}
```

Diagnosis commands that found the real difference in seconds:

```python
live = <read-back body>; op = <prepared body>
print(len(live), len(op))          # 6580 6579
print(repr(live[-30:]), repr(op[-30:]))  # tail shows the extra "\n"
```

First differing byte search found none: `live[:-1] == op`. The whole conflict was the terminator.

## The repair that verified

```bash
python3 -c "import json; open('body-exact.md','w').write(json.load(open('prepared.json'))['operation']['body'])"
gh api -X PATCH repos/{owner}/{repo}/issues/comments/<comment_id> -F body=@body-exact.md
# refresh the snapshot, then re-run the verifier against the same prepared operation
```

Verifier then returned a verified publication receipt with the comment's digest. No second comment was created.

## Snapshot completeness failure mode

A second, earlier failure in the same flow came from an incomplete snapshot, not from bytes:

```
issue comments[0].author has invalid fields: missing is_authority.
```

The snapshot builder had to supply each comment author with its stable numeric ID, login, and an authority boolean, plus an explicit `comments_complete: true` after paginating every page (page size 100; log the last page length). Schema validation runs before any body comparison, so this failure surfaces first and can be mistaken for a content problem.

## Re-preparation equality gate

Before each write, the session re-fetched the snapshot and re-ran preparation; the gate used was:

```python
assert new["operation"] == previous["operation"]
assert new["precondition_sha256"] == previous["precondition_sha256"]
```

Both held across every write that verified. This equality check is cheap and catches snapshot drift (a new comment, an edited body) before a stale write.

## Non-issues ruled out

- The forge did not normalize or alter the body on create; the drift was introduced locally before the write.
- `-F body=@file` reads the file literally. It was not the source of the newline; `print()` was.
