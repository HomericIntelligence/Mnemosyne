# Notes: Publish Anchor Files Fully Configured

Supporting evidence for [publish-anchor-files-fully-configured.md](publish-anchor-files-fully-configured.md).
These notes supply provenance and measurements. They do not define the rule.

## Provenance

- Session date: 2026-11-02.
- Source: a control-plane repository. Product names, internal paths, host names, issue and pull-request
  identifiers are withheld.
- Verification level: `verified-local`. The repair and its regression test were executed on the
  development host. The original race was observed only in a hosted CI runner.

## Observed failure

A concurrency test that starts the component many times against a fresh state directory failed in a
hosted CI job with:

```text
FAILED <concurrency test> - PermissionError: the visible publication lock changed during acquisition
pytest failed with exit code 1.
```

The job log contained no `FAILED` line in the trimmed failed-log view; only the full job log showed it.

## Call path

```text
test entry point                       -> ensure()
startup module: startup anchor         -> _startup_lock(...)
startup module: acquisition check      -> _require_locked_lock(...)
publication module: raise site         -> raise PermissionError(...)
```

The startup module imports only the inspection, publication, and validation helpers from the
publication module. It does not call the publication module's own acquire functions. An instrumented
run of the failing test recorded 0 calls to those acquire functions.

## Defect ordering

```text
old:
  fd = os.open(final, O_RDWR|O_CREAT|O_EXCL|O_CLOEXEC|O_NOFOLLOW, 0o600)
  os.fchown(fd, uid, gid)
  os.fchmod(fd, 0o600)
  os.fsync(fd)
  os.fsync(dir)          # name visible and partially configured before this point
```

The reader compares nine fields between `os.fstat(fd)` and `os.stat(name, dir_fd=..., follow_symlinks=False)`:

```text
st_dev, st_ino, st_mode, st_uid, st_gid, st_nlink, st_size, st_mtime_ns, st_ctime_ns
```

The identity tuple includes `st_ctime_ns`. A permission or ownership change that lands between the
reader's two calls updates `st_ctime_ns` on the inode, so both calls observe the same inode but
different tuples. That raises the observed message.

The message distinguishes the paths. A stale recorded plan state raises a different error, roughly
"the lock changed after the plan". The presence of the "visible ... changed during acquisition"
message is itself evidence that the reader's two current observations disagreed.

## Repair

```text
new:
  tmp = ".anchor-<random>.tmp"
  fd = os.open(tmp, O_RDWR|O_CREAT|O_EXCL|O_CLOEXEC|O_NOFOLLOW, 0o600)
  os.fchown(fd, uid, gid)
  os.fchmod(fd, 0o600)
  os.fsync(fd)
  rename_noreplace(dir, tmp, final)    # EEXIST -> FileExistsError
  os.fsync(dir)
  return fd                            # still refers to the published inode
```

The cleanup path closes the descriptor and unlinks the temporary on any exception. The two other
create sites in the same module had the same shape, used the same helper, and kept their own
fallbacks: the publication path converts the loss into its existing permission error, and the
reconciliation path opens the published entry.

## Measurements

| Check | Result |
| --- | --- |
| Single test in parallel on the development host, probe installed | 0 failures in 144 runs; probe logged no differing fields |
| Interleaved attempts on a local block filesystem, independent reviewer | 1 mismatch in 400 attempts |
| Same interleaved attempts on the shared network mount | 0 mismatches in 200 attempts |
| Descriptor and temporary-file leak probe across 50 lost create races | file-descriptor delta 0; no leftover temporary entries |
| New invariant test on the pre-fix revision | fails at the assertion that the final name is absent |
| New invariant test on the fixed revision | passes |
| Affected suites on the fixed revision | 204 passed, 14 skipped (environment-gated) |
| Lint and format checks on the changed files | pass |

The development host does not update `st_ctime_ns` on a permission change, so the race is not
observable there. The block-filesystem result confirms the mechanism; the hosted CI traceback is the
evidence that the race occurred in practice.

## Review correction

The first revision repaired the publication module's own acquire functions and added no test. An
independent review returned NO-GO with three findings:

1. The failing test never calls the repaired functions (0 calls).
2. The repair was therefore correct in shape but aimed at the wrong site.
3. No regression test guarded the invariant.

The second revision moved the repair to the startup create site, kept the shared helper, added the
invariant test, and returned GO.

## Cross-host metadata caution

Two hosts can report different metadata for the same logical operation. A zero local failure rate is
a property of the local filesystem and kernel, not of the code. Use the ordering argument and the
traceback, not the local pass rate, to decide whether a defect exists.