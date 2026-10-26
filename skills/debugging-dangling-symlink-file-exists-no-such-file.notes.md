# Notes: debugging-dangling-symlink-file-exists-no-such-file

Supporting evidence for the main skill. All paths sanitized to generic forms.

## Incident summary

- Host context: a Linux workstation where the home directory is quota-bound, so the
  OpenCode data directory had been replaced by a symlink into scratch space:
  `~/.local/share/opencode -> /var/tmp/$USER/opencode`.
- The scratch tree was later removed (cleanup/reimage), leaving a dangling symlink.
- Every OpenCode command (`opencode`, `opencode upgrade`, `opencode run ...`) then crashed
  at startup with:

```text
PlatformError: NotFound: FileSystem.makeDirectory (~/.local/share/opencode/log)
[cause]: Error: ENOENT: no such file or directory, mkdir '~/.local/share/opencode/log'
```

## Contradictory manual-fix sequence (as observed)

```text
$ mkdir ~/.local/share/opencode/log
mkdir: cannot create directory '~/.local/share/opencode/log': No such file or directory
$ mkdir ~/.local/share/opencode/
mkdir: cannot create directory '~/.local/share/opencode/': File exists
$ ls -la ~/.local/share/
... opencode -> /var/tmp/$USER/opencode
$ rm ~/.local/share/opencode      # removes only the link
$ opencode                        # starts normally, recreates data directory
```

## Controlled reproduction (this session, OpenCode 2.1.3)

```bash
REPRO=<temp-dir>
rm -rf "$REPRO" && mkdir -p "$REPRO"
ln -s /this/target/does/not/exist "$REPRO/opencode"
cd "$REPRO" && XDG_DATA_HOME="$REPRO" timeout 15 opencode run "say hi"
# => PlatformError: NotFound: FileSystem.makeDirectory (<temp-dir>/opencode/log) [ENOENT]

# Control: valid symlink target
rm -rf "$REPRO" && mkdir -p "$REPRO" <temp-target>
ln -s <temp-target> "$REPRO/opencode"
cd "$REPRO" && XDG_DATA_HOME="$REPRO" timeout 15 opencode run "say hi"
# => runs normally; log directory created at <temp-target>/log

# Mechanism cross-check with the shell only:
mkdir -p "$REPRO/opencode/log"
# => mkdir: cannot create directory '$REPRO/opencode': File exists
```

## Why the standard recovery advice misleads

The errno path in the crash names `<data-dir>/opencode/log`, so the natural fix is
`mkdir` of that path. Because the `opencode` component is a dangling symlink:

- `mkdir <data-dir>/opencode` -> EEXIST: the entry exists (lstat sees the link).
- `mkdir <data-dir>/opencode/log` -> ENOENT: resolution descends to the missing target.
- `mkdir -p` combines both failures: stops at EEXIST, then fails with ENOENT.

Signature rule: **EEXIST on the component plus ENOENT through it == dangling symlink.**

## Upstream disposition

- Filed a sanitized public upstream issue (anomalyco/opencode issue 58212) with the
  minimal repro, the valid-target control, the contradictory mkdir output, the workaround,
  and a suggested fix (realpath-resolve the data directory and create the target, or print
  an actionable error naming the link and its missing target).
- Session work also confirmed that removing the dangling link (`rm <path>`) is safe: `rm`
  on a symlink removes only the link.

## Scope notes

- The lesson generalizes beyond OpenCode: any tool whose data/state path crosses a
  symlink into cleaned scratch space shows the same crash signature, and the same
  diagnostic and recovery commands apply.
- The `XDG_DATA_HOME` isolation technique (fresh temp dir containing only the suspect
  symlink, plus a valid-target control) is reusable for attributing path-class failures
  to the environment rather than to a tool regression, without touching live data.
