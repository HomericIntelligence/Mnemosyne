---
name: security-escape-untrusted-values-in-logs
license: BSD-3-Clause
description: "Untrusted free-text values (filenames, paths, branch names, agent output) logged or printed with a raw %s / f-string can forge log lines (embedded newline) or emit terminal escape sequences (embedded ESC/BEL) — log-injection & terminal-injection. Fix by rendering the untrusted value with %r (or !r in an f-string) so repr() C-escapes control characters into ONE quoted single-line record; do NOT change the stored/downstream value. Use when: (1) a %s/{value} log or print carries a value derived from a filename, VCS path, git status --porcelain payload, branch name, issue body, or agent output, (2) that payload can legally contain \\n, \\t, \\r, \\x1b (ESC), \\x07 (BEL), or other C0/C1 control bytes, (3) a parser upstream deliberately PRESERVES those bytes literally (e.g. NUL-delimited porcelain) so they reach the log verbatim, (4) you must keep path-selection / filtering / hashing semantics identical while only changing what the LOG renders. Distinct from stripping NUL for a subprocess crash: here you ESCAPE (repr) for a display sink, you do NOT delete — see subprocess-embedded-null-byte-sanitize."
category: debugging
date: 2026-07-17
version: "1.0.0"
user-invocable: false
verification: verified-local
tags:
  - security
  - log-injection
  - terminal-injection
  - control-characters
  - repr
  - untrusted-input
  - logging
  - porcelain-paths
  - filename-injection
  - egress-rendering
---

# Escape Untrusted Values (repr / %r) Before Logging or Printing

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-07-17 |
| **Objective** | Stop untrusted free-text values (filenames, VCS paths, branch names, agent output) from forging log lines or emitting terminal escape sequences when written to a log/console, by rendering them with `%r`/`!r` (repr) instead of raw `%s`/f-string. |
| **Outcome** | The untrusted value is C-escaped into one quoted single-line record; a `\n` in a filename can no longer inject a fake log line and an `\x1b]0;…\x07` OSC sequence can no longer retitle/attack the terminal. Path-selection and filtering semantics are unchanged — only the rendered text differs. |
| **Verification** | verified-local — pattern validated against `hephaestus/automation/pr_manager.py` `_select_commit_paths()` (ProjectHephaestus issue #2231, refs PR #2208). `repr()`'s control-character escaping is a stable Python-stdlib guarantee. |
| **History** | n/a (initial version) |

## When to Use

- A `logger.debug/info/warning(...)` or `print(...)` uses `%s` (or an f-string `{value}`) whose value is derived from **untrusted free text**: a filename, a `git status --porcelain` path, a branch name, an issue/PR body, or agent output.
- That value can legally contain control characters — newline (`\n`), carriage return (`\r`), tab (`\t`), ESC (`\x1b`), BEL (`\x07`), or other C0/C1 bytes — because an upstream parser **preserves them literally**. Example: a NUL-delimited porcelain parser that keeps quote/newline/tab/UTF-8 bytes verbatim (see `test_preserves_literal_paths`), so `dir/forged\nFAKE: allow-listed` reaches the log intact.
- A security/audit reviewer flags that "a malicious filename can forge log lines or terminal output."
- You must keep **path-selection, secret-filtering, staging, and hashing semantics identical** — the fix may ONLY change what the log renders, never the value passed downstream.

Do NOT reach for this when the untrusted bytes crash a **subprocess** (`ValueError: embedded null byte`): that sink needs deletion, not escaping — see [[subprocess-embedded-null-byte-sanitize]]. The two are complementary: **escape for a display sink, strip for a subprocess argv/stdin sink.**

## Root Cause

Log records and terminals are **line-and-control-code oriented sinks**. A logging call like:

```python
logger.warning("Skipping potential secret file: %s", path)
```

writes `path` verbatim. If `path` is `evil\nWARNING: nothing to see here`, the log gains a **second, attacker-controlled line** that looks like a genuine record (log forgery). If `path` contains an OSC/CSI sequence such as `\x1b]0;pwned\x07`, a terminal tailing the log **executes** it (retitle the window, move the cursor, hide text — terminal injection). The value is untrusted precisely because it originated from a filename or agent output, and an upstream parser deliberately preserved the bytes.

`%r` (equivalently `!r` in an f-string) applies Python's `repr()`, which:

- wraps the value in quotes, and
- **C-escapes every control byte** — `\n`→`\\n`, `\r`→`\\r`, `\t`→`\\t`, `\x1b`→`\\x1b`, `\x07`→`\\x07` —

collapsing the payload into **one printable, single-line, unambiguous record**. Forgery and terminal escapes are neutralised without touching the real value.

## Verified Workflow

The key insight: **the fix belongs at the render/egress site (the log call), not at the data source.** Sanitizing the source would corrupt the value used for path selection/staging; here the value must stay byte-exact for `git add`, and only its *rendering* must be safe. Change `%s` → `%r` (or `{x}` → `{x!r}`).

This is a sibling-consumer pattern: audit **every** log/print of the same untrusted value, not just one line — see the mirror-sibling discipline in [[subprocess-embedded-null-byte-sanitize]].

### Quick Reference

| Symptom | Root Cause | One-line Fix |
| --------- | ------------ | -------------- |
| Log line forged by a filename with `\n` | `logger.x("... %s", path)` writes newline verbatim | `logger.x("... %r", path)` |
| Terminal retitled / cursor moved by a tailed log | ESC/BEL (`\x1b`, `\x07`) in path passed through `%s` | `%r` C-escapes the control bytes |
| f-string prints raw control chars | `f"skip {path}"` | `f"skip {path!r}"` |
| Path selection changed after "fixing" the log | someone sanitized the *value* not the *render* | escape at the log site; keep the value byte-exact downstream |

### Detailed Steps

1. **Grep for the raw-format log/print of the untrusted value across ALL sibling sites:**

   ```bash
   grep -rnE 'logger\.(debug|info|warning|error|critical)\(.*%s' hephaestus/ \
     | grep -iE 'path|file|name|branch|body|title'
   grep -rnE 'print\(f?".*\{[a-z_]+\}' hephaestus/ | grep -iE 'path|file|name'
   ```

2. **Confirm the value is untrusted and control-char-bearing.** Trace it to a filename / porcelain path / branch name / agent output whose upstream parser preserves literal bytes (e.g. a test asserting `dir/line\nbreak.py` survives parsing).

3. **Change only the format conversion:** `%s` → `%r` in the logging call's format string, or `{value}` → `{value!r}` in an f-string. **Do not** alter the argument, the log level, the surrounding control flow, or the value handed to any downstream consumer (`git add`, hashing, comparison).

4. **Follow the in-repo convention.** If the module already uses `!r`/`%r` for other untrusted values (e.g. `f"...for branch {branch_name!r}"`), matching it satisfies DRY / POLA and needs no new helper (KISS / YAGNI).

5. **Add a regression test that exercises BOTH the injection payloads and the unchanged semantics** (see Results). RED-verify it: with `%s` it must fail (raw `\n` / `\x1b` present in the emitted message); with `%r` it passes.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Sanitize the value | Strip/replace control chars from `path` before selection so the log is clean | Corrupts the value used for `git add --`, secret-filtering, and comparison; changes path-selection semantics the issue explicitly required to stay identical | Fix the **render** (`%r` at the log site), not the value; the downstream value must stay byte-exact. |
| Delete the control chars (as for NUL) | Reused the `strip_null_bytes`-style deletion from the subprocess-crash fix | Wrong sink: a log/terminal needs the value **displayed safely** (escaped), and deletion still loses information and can mask the attack; the sibling NUL skill itself says "strip for subprocess, don't escape" — the inverse holds here | Escape (`repr`) for a **display** sink; strip only for a **subprocess argv/stdin** sink. See [[subprocess-embedded-null-byte-sanitize]]. |
| Test only the `.env` basename with control chars | Wrote the secret-path fixture as `.env\x1b]0;pwned\x07` | `_is_secret_path` matches on `Path(path).name`; that basename is `.env\x1b]0;pwned\x07`, which is NOT the exact secret name `.env`, so the warning branch never fired and the test proved nothing | Keep the control payload in a path SEGMENT and let the basename stay a real secret (`sub/\x1b]0;pwned\x07/.env`, basename `.env`) so the secret branch is honestly exercised. |

## Results & Parameters

The fix — change the format conversion only:

```python
# hephaestus/automation/pr_manager.py  (_select_commit_paths)
for status, path in entries:
    if allowed is not None and path not in allowed:
        logger.debug("Skipping non-allowlisted file: %r", path)   # was %s
        continue
    if _is_secret_path(path):
        logger.warning("Skipping potential secret file: %r", path)  # was %s
        continue
    ...  # path handed to git add / staging UNCHANGED
```

Regression test — assert both branches escape, and selection is unchanged. Note the secret payload keeps a real `.env` basename so `_is_secret_path` still fires:

```python
import logging

def test_escapes_control_characters_in_skip_logs(caplog):
    newline_path = "src/forged\nINJECTED log line.py"       # non-allowlisted branch
    control_path = "sub/\x1b]0;pwned\x07/.env"               # basename .env -> secret branch
    entries = ((" M", newline_path), ("??", control_path))

    with caplog.at_level(logging.DEBUG, logger=pr_manager.logger.name):
        paths = pr_manager._select_commit_paths(entries, allowed_paths=(control_path,))

    # semantics unchanged: newline_path filtered (not allow-listed), control_path filtered (secret)
    assert paths == pr_manager._CommitPaths(add_paths=(), update_paths=())

    messages = [r.getMessage() for r in caplog.records]
    assert any(repr(newline_path) in m for m in messages)   # rendered via repr
    assert any(repr(control_path) in m for m in messages)
    for m in messages:                                       # one escaped record, no raw controls
        assert "\n" not in m
        assert "\x1b" not in m
```

Escaping-behaviour reference (Python stdlib guarantee, no dependency needed):

| Input byte | `%s` renders | `%r` renders |
|------------|--------------|--------------|
| `\n` (newline) | actual line break → forged record | `\n` |
| `\r` (CR) | carriage return | `\r` |
| `\t` (tab) | tab | `\t` |
| `\x1b` (ESC) | starts a terminal escape sequence | `\x1b` |
| `\x07` (BEL) | terminal bell / OSC terminator | `\x07` |

Parameters / invariants:

- **Change only the format conversion** (`%s`→`%r`, `{x}`→`{x!r}`). Everything else — argument, level, control flow, downstream value — is identical.
- **Audit every sibling log/print** of the same untrusted value in the module, not just the flagged line.
- Escape at the **display** sink; strip at the **subprocess** sink ([[subprocess-embedded-null-byte-sanitize]]).

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| ProjectHephaestus | Issue #2231 (refs PR #2208) | `_select_commit_paths()` in `hephaestus/automation/pr_manager.py` logged skipped porcelain paths with `%s`; the NUL-porcelain parser preserves literal newlines/control bytes, enabling log-line forgery and terminal escapes. Fix: render the two skip logs with `%r`; add a `caplog` regression test asserting escaped single-line records and unchanged path selection. Module already used `!r` for untrusted branch names — the fix matches that existing convention. |
