---
name: architecture-metaclass-threadlocal-thread-safety
license: BSD-3-Clause
description: "Thread-safe patterns for class-level access and shared caches, including a proposed terminal-color policy that layers process-wide NO_COLOR, force-color, CLICOLOR, and TTY detection beneath calling-thread overrides. Use when: (1) preserving Class.ATTR access, (2) adding accessible automatic CLI color, (3) testing TTY policy with PTYs, or (4) protecting shared caches under thread pools."
category: architecture
date: 2026-08-06
version: "2.0.0"
user-invocable: false
verification: unverified
history: architecture-metaclass-threadlocal-thread-safety.history
tags:
  - thread-safety
  - metaclass
  - threading-local
  - threading-lock
  - shared-cache
  - repo-keyed-cache
  - module-global-state
  - thread-pool-executor
  - gil-not-atomic
  - load-bearing-lock
  - planning-risks
  - nogo-recovery
  - resolve-risk-not-reflag
  - verify-resolver-signature
  - dont-overscope-safe-callers
  - defensive-copy
  - concurrency-boundary
  - python
  - immutable-state
  - terminal-color
  - no-color
  - clicolor
  - force-color
  - tty
  - pty
  - curses
  - ansi-accessibility
  - shell-installer
---

# Thread-Safe Shared State and Automatic Terminal Color Policy

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-08-06 |
| **Objective** | Capture three related state-policy shapes: (A) verified per-thread class state via metaclass + `threading.local()`; (A2) proposed automatic terminal-color capability beneath explicit per-thread overrides; (B) proposed shared cache protection via a `threading.Lock`-guarded keyed dict |
| **Outcome** | (A) Success — backward-compatible, thread-safe, 15 tests pass (verified-local). (A2) Architecture-first implementation plan completed with full Python, curses, Bash/PTY, and accessibility coverage specified, but no code or tests executed. (B) Plan-only R1 design with its deepest risks resolved from source evidence, but no implementation or tests. |
| **Verification** | Mixed: only the original pattern (A) is **verified-local**. Patterns (A2) and (B) are **unverified** and live under `## Proposed Workflow`. Top-level frontmatter remains `unverified`; do not treat either proposed extension as proven until implementation and CI complete. |
| **History** | [changelog](./architecture-metaclass-threadlocal-thread-safety.history) |

## When to Use

**Pattern (A) — per-thread isolated class state (verified):**

- A class stores configuration as **mutable class attributes** (e.g., ANSI color codes, feature flags)
- Methods like `disable()` **mutate class attributes**, affecting all threads and modules simultaneously
- You need **per-thread state isolation** (one thread disabling doesn't affect others)
- You want to preserve the **`Class.ATTR` access pattern** (no API change for consumers)
- Python 3.10+ (no `__class_getattr__` available until 3.12)

**Pattern (A2) — automatic terminal policy beneath explicit thread overrides (proposed):**

- A public `Colors.ATTR` API already uses access-time metaclass lookup, but defaults to
  color-on or requires every entry point to call an opt-in `auto()` method.
- CLI output must honor `NO_COLOR`, `FORCE_COLOR`, `CLICOLOR_FORCE`, `CLICOLOR`, and
  `stdout.isatty()` without losing calling-thread `enable()` / `disable()` isolation.
- Python CLI output, a curses TUI, and a bootstrap shell installer must share one
  documented precedence even though the installer runs before the Python package exists.
- Tests must prove genuine TTY and non-TTY behavior and preserve status meaning after
  ANSI codes are removed.

**Pattern (B) — shared-but-repo-keyed cache under a thread pool (proposed / plan-only):**

- A **module-global cache** (bare `set[str] | None`, or a `dict`) is read AND written **without a lock** and is now touched by a `ThreadPoolExecutor` (e.g. a pipeline coordinator running stages across repos)
- The cache must be **shared** across threads (per-thread caches would defeat caching) but its entries are **partitioned by a key that is NOT the thread** — e.g. per repo
- Thread A's cache entry masks thread B's → dropped durable writes → crash/restart re-seeds at the wrong state
- You are deciding between `threading.local()` (wrong here — gives each thread an empty cache) and a `threading.Lock`-guarded, key-partitioned `dict` (correct)
- You are about to key the cache by the *current-directory* repo and need to check whether that key actually varies per thread under a **shared-CWD** thread pool

## Verified Workflow

> Pattern (A) below is **verified-local** (ProjectHephaestus issue #30 / PR #68, 15/15 tests, full suite 394/394). Its original default-enabled behavior is historical. The recommended automatic terminal policy (A2) and shared-cache pattern (B) are under `## Proposed Workflow` and remain unverified.

### Quick Reference

```python
import threading

_state = threading.local()

_CODES: dict[str, str] = {"OKGREEN": "\033[92m", "FAIL": "\033[91m"}

class _Meta(type):
    def __getattr__(cls, name: str) -> str:
        if name in _CODES:
            return _CODES[name] if getattr(_state, "enabled", True) else ""
        raise AttributeError(f"type object {cls.__name__!r} has no attribute {name!r}")

class Colors(metaclass=_Meta):
    @staticmethod
    def disable() -> None:
        _state.enabled = False

    @staticmethod
    def enable() -> None:
        _state.enabled = True
```

### Detailed Steps

1. **Extract values to an immutable dict**: Move all mutable class attributes into a module-level `dict[str, str]` that is never mutated.

2. **Add `threading.local()` state**: Create a module-level `_state = threading.local()` to hold per-thread boolean flags.

3. **Create a metaclass with `__getattr__`**: The metaclass intercepts attribute access on the class itself (not instances). Since the color names are no longer class attributes, Python falls through to `__getattr__` on every access.

4. **Compute on access**: In `__getattr__`, check the thread-local flag and return either the real value or an empty string.

5. **Replace mutating methods**: `disable()` and `enable()` now just set `_state.enabled = False/True` instead of overwriting 9+ class attributes.

6. **Historical default**: The verified implementation used `getattr(_state, "enabled", True)` so new threads started enabled. For terminal styling, do not copy that default unchanged; use the proposed automatic environment/TTY policy below while keeping `_state` as the sole explicit-state owner.

### Why Metaclass (Not Other Approaches)

| Approach | Problem |
| ---------- | --------- |
| `threading.Lock` around mutations | Still global state — all threads share one enable/disable flag |
| Instance-based `Colors()` | Breaks the `Colors.ATTR` class-level access pattern used everywhere |
| `__class_getattr__` (PEP 657) | Python 3.12+ only, not available in 3.10 |
| Module-level `__getattr__` | Changes API from `Colors.ATTR` to `colors.ATTR` (module access) |
| **Metaclass `__getattr__`** | Works on 3.10+, preserves `Colors.ATTR`, per-thread via `threading.local()` |

### threading.local() vs Lock-Guarded Keyed Cache — which shape?

The two patterns in this skill are **opposites**, and picking wrong is the core mistake:

| You want… | Tool | Why |
| ----------- | ------ | ----- |
| Each thread to have **its own** isolated value (colors on/off) | `threading.local()` | Per-thread storage; no lock needed; one thread's write is invisible to others |
| A cache **shared** across threads but partitioned by a **non-thread** key (repo) | `threading.Lock` + keyed `dict` | `threading.local()` would give each thread an empty cache and defeat caching; the lock serializes read-modify-write of the shared dict |

If the partition key is "the thread," use `threading.local()`. If the partition key is anything else (repo, tenant, URL), use a lock-guarded keyed dict — see Proposed Workflow.

### Testing Thread Safety

```python
import threading

def test_disable_does_not_affect_other_thread():
    barrier = threading.Barrier(2)
    results = {}

    def disabler():
        Colors.disable()
        barrier.wait(timeout=5)
        results["disabler"] = Colors.OKGREEN

    def reader():
        barrier.wait(timeout=5)
        results["reader"] = Colors.OKGREEN

    t1 = threading.Thread(target=disabler)
    t2 = threading.Thread(target=reader)
    t1.start(); t2.start()
    t1.join(timeout=5); t2.join(timeout=5)

    assert results["disabler"] == ""
    assert results["reader"] == "\033[92m"
```

Use `threading.Barrier` to synchronize threads so the reader checks *after* the disabler has called `disable()`.

## Proposed Workflow

> **Warning:** The workflows in this section have not been validated end-to-end. Pattern
> (A2) is an implementation plan for automatic color policy, and pattern (B) is a design
> for a module-global shared-cache bug. No proposed code was applied, no listed tests were
> run, and CI was not confirmed. Treat each step as a hypothesis until CI confirms it.
> Source coordinates were read once and will drift; **re-grep before relying on them.**

### Pattern (A2): automatic terminal policy with thread-local explicit state

The durable design is a **three-state per-thread override** layered over process-wide
environment and stream capability. Keep `threading.local()` as the only owner of explicit
state: `True` for `enable()`, `False` for `disable()`, and absence of the attribute for
automatic mode. Evaluate the environment and `sys.stdout.isatty()` on every public color
attribute access so all callers receive current policy without entry-point wiring.

Use this precedence exactly:

1. Calling-thread `enable()` or `disable()`.
2. Non-empty `NO_COLOR` disables color (even the string `"0"`).
3. Non-empty `FORCE_COLOR`, or non-empty/non-zero `CLICOLOR_FORCE`, forces color into a
   non-TTY.
4. `CLICOLOR=0` disables color.
5. Otherwise use `sys.stdout.isatty()`; `CLICOLOR=1` permits normal TTY color but does not
   force ANSI into a pipe.

Empty values are ignored. `CLICOLOR_FORCE=0` does not force color. `auto()` deletes the
calling thread's override instead of storing a third sentinel, restoring live evaluation.

```python
import os
import sys
import threading

_state = threading.local()


def _automatic_colors_enabled() -> bool:
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("FORCE_COLOR"):
        return True
    clicolor_force = os.environ.get("CLICOLOR_FORCE")
    if clicolor_force and clicolor_force != "0":
        return True
    if os.environ.get("CLICOLOR") == "0":
        return False
    return sys.stdout.isatty()


class _ColorsMeta(type):
    def __getattr__(cls, name: str) -> str:
        if name in _CODES:
            override = getattr(_state, "enabled", None)
            enabled = _automatic_colors_enabled() if override is None else override
            return _CODES[name] if enabled else ""
        raise AttributeError(f"type object 'Colors' has no attribute {name!r}")


class Colors(metaclass=_ColorsMeta):
    @staticmethod
    def disable() -> None:
        _state.enabled = False

    @staticmethod
    def enable() -> None:
        _state.enabled = True

    @staticmethod
    def auto() -> None:
        if hasattr(_state, "enabled"):
            del _state.enabled
```

#### Apply the policy at each real styling boundary

1. **Discover emitters before editing.** Search literal ANSI escapes and curses color
   pairs separately. In the ProjectHephaestus plan, `rg -n -F '\033[' hephaestus scripts`
   found the Python `Colors` module and the bootstrap helper; curses pairs were confined
   to `automation/curses_ui.py`. Unstyled entry points needed no edits.
2. **Centralize Python behavior at access time.** This makes every existing `Colors.ATTR`
   consumer automatic without changing each console script. Environment and TTY state are
   process-wide inputs; only explicit overrides are thread-local.
3. **Combine curses and shared policy once during initialization.** Cache
   `curses.has_colors() and bool(Colors.ENDC)`, initialize pairs only when true, and use
   the cached boolean during drawing. When disabled, use non-color attributes such as
   `A_DIM`/`A_NORMAL` while retaining labels like `[idle]` and `failed`.
4. **Mirror precedence in bootstrap Bash.** A shell installer sourced before package
   installation cannot import Python policy. Evaluate the same environment/TTY order at
   source time, assign ANSI variables only when enabled, and leave glyph/message helpers
   structurally unchanged.
5. **Document accessibility as a contract.** Styling may reinforce status, never encode
   it. Tests should strip ANSI and assert the semantic text is identical.

#### Test the policy without false seams

- In Python tests, clear all four control variables and call `Colors.auto()` before and
  after each test. Replace `sys.stdout` with a minimal object whose `isatty()` returns the
  desired value; do not patch `isatty` on pytest's slotted capture wrapper.
- Use `threading.Barrier` to prove one thread's explicit disable does not affect another
  thread still following automatic TTY policy. Retain concurrent-read and mixed override
  stress cases.
- For Bash, run isolated subprocesses with ambient controls and the script's source guard
  removed. Use a real POSIX PTY (`pty.openpty()`), not an `isatty` mock, for default TTY,
  `CLICOLOR`, force precedence, and `NO_COLOR` precedence.
- Assert semantic output after removing `\x1b\[[0-9;]*m`; JSON and other structured output
  must remain independent of styling.

### Pattern (B): lock-guarded shared cache under a thread pool

### The bug shape (module-global unguarded cache under a thread pool)

`github_api/labels.py` `gh_list_labels()` reads/writes an unguarded module global
`_api._label_cache` (a bare `set[str] | None`) that is neither repo-keyed nor
lock-protected. Once a pipeline coordinator runs stages **multi-threaded across repos**
(`ThreadPoolExecutor` in `worker_pool.py`; one `PipelineGitHub` per repo in
`coordinator.py`), thread A's cache masks thread B's labels → dropped durable `state:*`
label writes → a crash-restart re-seed lands at the wrong stage.

### Proposed fix (two parts)

1. **Make the org-scoped path always refresh.** Have `PipelineGitHub._label_names()`
   call `gh_list_labels(refresh=True)` so the org-scoped `_gh --repo` path (which is
   already per-repo safe) never serves a stale process-global cache.

2. **Replace the global with a lock-guarded, repo-keyed dict.** Swap
   `_label_cache: set[str] | None` for `_label_cache: dict[str | None, set[str]]`
   guarded by a module-level `threading.Lock`. Resolve the repo slug via
   `get_repo_info(repo_root)` — **which returns a `tuple[str, str]` `(owner, repo_name)`,
   NOT an object with `.owner`/`.name`** (R1 ground truth, see RISK 4). Return
   **defensive copies** (`set(cached)`) so callers cannot mutate cached entries.

```python
import threading

_label_cache: dict[str | None, set[str]] = {}
_label_cache_lock = threading.Lock()

def _repo_key(repo_root=None) -> str | None:
    try:
        # git_utils.py:76 — get_repo_info(repo_root: Path | None = None)
        #                     -> tuple[str, str]  (owner, repo_name)
        # Memoized per resolved root (git_utils.py:124), so this is a dict
        # lookup after warmup — NOT a fresh shell-out per call (R1, RISK 2/4).
        owner, name = get_repo_info(repo_root)
        return f"{owner}/{name}"
    except Exception:
        return None

def gh_list_labels(refresh: bool = False) -> set[str]:
    key = _repo_key()
    with _label_cache_lock:                  # LOAD-BEARING — read-modify-write is NOT atomic
        if not refresh and key in _label_cache:
            return set(_label_cache[key])    # defensive copy
    labels = _fetch_labels_from_gh(key)      # do slow I/O OUTSIDE the lock
    with _label_cache_lock:
        _label_cache.setdefault(key, set()).update(labels)  # atomic-under-lock add
        return set(_label_cache[key])                       # defensive copy
```

### Risks & Load-Bearing Assumptions — R1 (post-NOGO) resolution

> **R0 → R1.** The R0 form of this section was a bare risk register that mostly said
> "verify whether…". That plan was graded **F / NOGO**. A re-plan that merely REPEATS the
> reviewer's open questions re-earns the NOGO — so the R1 pass RESOLVED the deepest risks
> below with grep/read evidence and converted each into a DECISION the implementer can act
> on without re-deriving. (Meta-lesson cross-linked from
> `tooling-plan-artifact-delivery-nogo` and the
> `architecture-executable-convention-guard-pattern` NOGO→GO sub-pattern.)

1. **[RESOLVED] The per-repo KEY is a NO-OP under this shared-CWD `ThreadPoolExecutor` —
   the LOCK, not the key, is the real isolation (deepest risk).** R0 asked "verify whether
   worker threads `chdir` per repo." R1 ran the grep:
   `grep -n chdir hephaestus/automation/pipeline/**` → **ZERO hits**; every subprocess is
   launched with an EXPLICIT `cwd=` (`worker_pool.py:246,303,419,451`; stages pass
   `cwd=_worktree_path(item, ctx)`). **Decision:** a CWD-derived key WOULD collide across
   threads, so under the pipeline the "repo-keyed cache" framing is illusory — isolation
   comes from (a) the org-path `refresh=True` and (b) the lock. The key stays meaningful
   ONLY because the legacy (non-pipeline) callers are single-repo-per-process. Do NOT sell
   the key as the isolation mechanism; the structural fix is the repo-SCOPED `_gh --repo`
   path plus the lock.

2. **[RESOLVED] The repo-slug resolver is memoized and cheap per call.** R0 said its
   cost was unverified. R1 read `git_utils.py:124`: `get_repo_info` is memoized via
   `_repo_info_cache.get_or_compute` keyed on the resolved root, and it accepts an
   EXPLICIT `repo_root` (`git_utils.py:76`) so it need not read CWD. Per-call cost after
   warmup is a dict lookup, not a fresh `git`/`gh` shell-out — safe to call on the hot path.

3. **[HARDENED] The lock is load-bearing — the GIL does NOT make it optional.** R0 carried
   a "GIL makes bare dict writes mostly safe" aside; R1 REMOVED it. Read-modify-write
   (`entry.add(...)`, get-then-set) is **NOT atomic** even under the GIL — a thread can be
   suspended between the read and the write. Do all mutation inside the lock (create's add
   is now atomic-under-lock via `setdefault(...).update(...)`); do slow I/O (the `gh` fetch)
   *outside* it to avoid serializing network calls. A returned set is a **defensive copy**
   (`set(_label_cache[key])`) so a caller mutating the result cannot corrupt the cache —
   pinned by `test_returned_set_is_a_defensive_copy`.

4. **[RESOLVED] Resolver return SHAPE confirmed — it is a TUPLE, not an object.** R0
   assumed `getattr(info, "owner")` / `.name` and hid the guess behind `getattr`. R1 read
   `git_utils.py:76`: `get_repo_info(repo_root: Path | None = None) -> tuple[str, str]`
   returning `(owner, repo_name)`. The R0 attribute slug would have SILENTLY produced
   `"None/None"` for every key. **Rule: for any helper you build the fix around, open it
   and confirm return TYPE + params before writing the caller — an assumed attribute shape
   is a silent NOGO.** Use tuple unpack `owner, name = get_repo_info(repo_root)`. (Other
   coordinates — `labels.py:24-31,52-53`, `pipeline_github.py:192,204-215`,
   `__init__.py:28,42-44`, test reset sites `test_github_api.py:1115,1167,1179,1235` — were
   read once and will drift; re-grep before relying on them.)

5. **Test-seam migration touches multiple sites.** Tests reset the cache with
   `_label_cache = None`; migrating to a dict means every reset site must become
   `_label_cache = {}` (or `_label_cache.clear()`). Missing one leaves a test resetting
   to the wrong type and silently poisoning later tests.

### Locate the concurrency boundary — fix the library minimally, don't churn the safe callers

R0's instinct was to consider forcing every caller onto a new API. R1's key scoping
decision: **find WHO is actually multi-repo-per-process before choosing "fix the library"
vs "fix the one caller."** `gh_list_labels` / `gh_create_label` have MANY legacy callers
(`loop_runner`, `pr_manager`, `_review_phase`, `implementer_phase_runner`,
`planner_review_loop`) that are single-repo-per-process and were **never broken** by the
un-keyed cache. The multi-repo hazard is ONLY the pipeline coordinator. The minimal correct
fix therefore does BOTH, minimally:

- **Fix the library** backward-compatibly (repo-keyed `dict` + lock + defensive copy) so
  existing single-repo callers keep working with no signature change; AND
- **Fix the one multi-repo caller** structurally (org-path `refresh=True` in
  `PipelineGitHub._label_names()`).

Do NOT migrate the safe legacy callers onto a new API "for consistency" — that is churn on
code that was correct, and it widens the blast radius of a bug-fix PR for no benefit
(KISS/YAGNI). **Rule: locate the ACTUAL concurrency boundary (who is multi-repo-per-process)
before deciding library-fix vs caller-fix; do both minimally, and leave the callers that
were never at risk untouched.**

### Proposed test plan (unvalidated)

- A `ThreadPoolExecutor` test that concurrently calls `gh_list_labels` for two different
  repo slugs and asserts neither masks the other (guards against the RISK-1 no-op key —
  set distinct keys explicitly rather than relying on CWD).
- `test_returned_set_is_a_defensive_copy`: mutate a returned label set and assert the
  cached entry is unchanged (guards the defensive-copy contract of RISK 3).
- A concurrent add/read stress test under the lock to catch the non-atomic
  read-modify-write of RISK 3.
- A test that the safe legacy callers (single-repo-per-process) still work unchanged
  against the new keyed dict — proving the library change is backward-compatible and the
  callers were correctly left untouched (guards the concurrency-boundary scoping decision).

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| `typing.Dict` import | Used `from typing import Dict` for type annotation | Ruff UP035/UP006 flags it as deprecated in 3.10+ | Use builtin `dict[str, str]` directly |
| Import ordering | Put `from hephaestus... import Colors, _CODES, _state` | Ruff I001 wants underscore-prefixed names sorted first | Ruff sorts `_CODES` before `Colors` (leading underscore sorts before uppercase) |
| Opt-in automatic color at selected entry points | Require each console script to call `Colors.auto()` before rendering | New and indirect `Colors` consumers can miss the call, leaving behavior inconsistent across CLI surfaces | Put environment/TTY evaluation in metaclass access so the public API enforces policy everywhere |
| Treat `CLICOLOR=1` as a force switch | Emit ANSI whenever `CLICOLOR` is non-zero | This leaks control codes into pipes; `CLICOLOR=1` conventionally permits color but still follows terminal capability | Only `FORCE_COLOR` and non-zero `CLICOLOR_FORCE` bypass non-TTY detection |
| Replace pytest capture's `isatty` method in place | Monkeypatch `sys.stdout.isatty` on pytest's slotted encoded stream | The capture object may reject attribute replacement, coupling the test to pytest internals | Replace `sys.stdout` itself with a minimal stream double |
| Fix only the installed Python CLI | Apply automatic policy in `Colors` but leave the bootstrap shell helper unconditional | The installer executes before the Python package is available and remains a separate color emitter | Mirror the same precedence in the sourced Bash helper and cover it with subprocess + genuine PTY tests |
| Re-check curses color capability on every draw | Call `curses.has_colors()` while rendering and ignore the shared CLI policy | `NO_COLOR` and force policy diverge from other CLI output, and repeated capability checks can change within one screen lifecycle | Cache `curses.has_colors() and bool(Colors.ENDC)` at curses initialization and render text meaningfully in both modes |
| Encode status only through color | Remove styling without preserving labels, glyphs, or wording | Non-color terminals and users who cannot distinguish the colors lose the status meaning | Keep semantic text identical and test output with ANSI stripped |
| `threading.local()` for a shared cache | (Plan-only, considered) Give each thread its own label cache to "avoid the lock" | `threading.local()` gives every thread an EMPTY cache — it defeats caching entirely and never shares a fetched label set across threads; wrong tool when the partition key is the repo, not the thread | If the partition key is anything other than "the thread," use a `threading.Lock`-guarded keyed `dict`, not `threading.local()` |
| Repo-key a process-global cache under a shared-CWD pool | (Plan-only) Key `_label_cache` by `get_repo_info()` (current-dir repo) assuming it differs per worker thread | If all worker threads share one process CWD, the CWD-derived key does NOT vary per thread — the key is a no-op and only the lock isolates; the "per-repo cache" is illusory | Verify threads `chdir` per-repo before claiming the key isolates; if they share CWD, prefer making every path repo-SCOPED (`_gh --repo <slug>`) over keying a global cache |
| Rely on the GIL for "mostly safe" bare dict writes | (Plan-only, tempting aside) Skip the lock because "CPython dict writes are atomic under the GIL" | Read-modify-write (`entry.add()`, get-then-set) is NOT atomic — a thread can be preempted between read and write, corrupting the shared dict | The `threading.Lock` is load-bearing; do mutation inside the lock and slow I/O outside it |
| Build the key from `getattr(info, "owner")` / `.name` (R0) | (Plan-only) Assumed `get_repo_info()` returns an object with `.owner`/`.name` and hid the guess behind defensive `getattr(..., None)` | `git_utils.py:76` shows it returns a `tuple[str, str]` `(owner, repo_name)` — the `getattr` would have silently produced `"None/None"` for every key (a silent NOGO) | For any helper you build the fix around, open it and confirm return TYPE + params BEFORE writing the caller; use tuple unpack `owner, name = get_repo_info(repo_root)` |
| Re-flag the reviewer's deepest risk instead of resolving it (R0) | (Plan-only) R0 left "verify whether worker threads `chdir`" as an open risk in the re-plan | A re-plan that repeats the reviewer's open question re-earns the NOGO (the R0 plan graded F) | RESOLVE it: run the grep (`grep -n chdir …/pipeline/**` → 0 hits; explicit `cwd=` everywhere), state the answer, convert the risk into a design decision — the lock, not the key, isolates under shared CWD |
| Force every label-cache caller onto a new API "for consistency" (R0 instinct) | (Plan-only) Considered migrating all `gh_list_labels`/`gh_create_label` callers to a repo-scoped API | Most callers (loop_runner, pr_manager, _review_phase, implementer_phase_runner, planner_review_loop) are single-repo-per-process and were NEVER broken; churning them widens the bug-fix blast radius for no benefit | Locate the ACTUAL concurrency boundary (only the pipeline coordinator is multi-repo-per-process); fix the library backward-compatibly + fix that one caller structurally; leave the safe callers untouched (KISS/YAGNI) |

## Results & Parameters

**Pattern (A) — verified-local:**

- **Files changed**: 2
  - `hephaestus/cli/colors.py`: Replaced 9 mutable class attributes + `disable()` mutation with metaclass + `threading.local()` pattern
  - `tests/unit/cli/test_colors.py`: Rewrote 5 existing tests, added 5 thread-safety tests (15 total)
- **Test results**: 15/15 pass, 100% coverage on `colors.py`, full suite 394/394 pass
- **PR**: HomericIntelligence/ProjectHephaestus#68

**Pattern (A2) — unverified / plan-only (ProjectHephaestus loop-1950 context):**

- **Proposed source scope**: `hephaestus/cli/colors.py`,
  `hephaestus/automation/curses_ui.py`, `scripts/shell/lib/install_helpers.sh`, and
  `COMPATIBILITY.md`.
- **Proposed tests**: Python environment/TTY precedence and synchronized thread isolation;
  curses policy initialization and color-independent worker labels; Bash subprocess and
  genuine PTY coverage for the same precedence and accessible plain text.
- **Static checks proposed**: focused pytest, Ruff, mypy, `bash -n`, and configured
  ShellCheck validation.
- **Status**: implementation was not applied, tests were not run, and CI was not observed.

**Pattern (B) — unverified / plan-only (ProjectHephaestus issue #1858):**

- **Proposed files to change** (coordinates unverified — re-grep):
  - `github_api/labels.py` — replace `_label_cache: set[str] | None` with a
    `threading.Lock`-guarded `dict[str | None, set[str]]`; return defensive copies
  - `github_api/pipeline_github.py` (~`:192`) — `_label_names()` calls
    `gh_list_labels(refresh=True)`
  - `github_api/__init__.py` (~`:28`) — `get_repo_info()` import already present
  - `tests/.../test_github_api.py` — migrate `_label_cache = None` reset sites to `{}`
- **Status**: NO code applied, NO tests run, CI NOT confirmed. This is a design + risk
  register only.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| ProjectHephaestus | Issue #30 — thread-safe Colors class (pattern A) | PR #68, all 394 tests pass (verified-local) |
| ProjectHephaestus | loop-1950 — automatic terminal color policy (pattern A2) | Architecture-first plan only; no implementation, local test, or CI evidence yet |
| ProjectHephaestus | Issue #1858 — module-global label-cache corruption under multithreaded coordinator (pattern B) | Plan-only; unverified, no PR yet. R0 plan graded F/NOGO → R1 re-plan resolved deepest risks with grep/read evidence (see `## Proposed Workflow` R1 resolution) |
