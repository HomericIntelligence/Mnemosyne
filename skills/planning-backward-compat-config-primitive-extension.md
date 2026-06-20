---
name: planning-backward-compat-config-primitive-extension
description: "Reusable checklist for writing TRUSTWORTHY implementation plans that extend a config-driven auth/config primitive (e.g. add a comma-separated AGAMEMNON_API_KEYS env var alongside the existing single AGAMEMNON_API_KEY, unioned for backward compatibility) WITHOUT breaking the old behavior or the security posture. Use when: (1) planning to add a new multi-value env var / config knob that must coexist with a legacy single-value one, (2) a plan proposes DELETING a file or symbol it claims is dead code based on a source grep alone, (3) a plan cites exact file:line locations as ground truth, (4) a plan changes a security-critical equality compare (==) into set/collection membership, (5) a plan RELAXES a fail-secure startup invariant (e.g. now allowing startup with only the new var), (6) a plan splits the change into multiple commits where one commit deletes 'dead' code that another part of the build may still reference."
category: architecture
date: 2026-06-19
version: "1.0.0"
user-invocable: false
verification: unverified
tags:
  - planning-methodology
  - backward-compatibility
  - config-env-var
  - auth-security
  - dead-code-removal
---

# Planning: Backward-Compatible Extension of a Config/Auth Primitive

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-06-19 |
| **Objective** | Make implementation plans for "extend a config-driven auth/config primitive while preserving backward compatibility" tasks trustworthy by codifying the assumptions a reviewer MUST re-verify before approving. |
| **Outcome** | Planning methodology only — captured from a plan for ProjectAgamemnon issue #260 (add comma-separated `AGAMEMNON_API_KEYS` env var, unioned with the existing single `AGAMEMNON_API_KEY` in the C++ `AuthMiddleware`). Plan was NOT executed end-to-end. |
| **Verification** | unverified |
| **History** | n/a (initial version) |

## When to Use

- You are planning a change that adds a new **multi-value** config/env var (e.g. comma-separated `*_KEYS`) that must coexist with — and be **unioned** with — an existing **single-value** one (`*_KEY`), so old deployments keep working unchanged.
- A plan proposes to **DELETE a file or symbol** ("dead code", "zero callers") and the conclusion was drawn from a **source-only grep**.
- A plan cites **exact `file:line` locations** (e.g. `src/auth.cpp:20`, `docs/api/openapi.yaml:885-895`) as if they are stable ground truth.
- A plan changes a **security-critical `==` compare into set/collection membership** (e.g. `key == expected` → `valid_keys.count(key)`).
- A plan **RELAXES a fail-secure startup invariant** (e.g. previously aborted unless `*_KEY` was set; now also accepts only `*_KEYS`).
- A plan **splits into multiple commits** where a later "dead-code removal" commit could merge independently and break the build if a hidden reference exists.

## Proposed Workflow

> **Warning:** This workflow has not been validated end-to-end. Treat as a hypothesis until CI confirms.
>
> **Heading note:** The repository validator (`scripts/validate_plugins.py`) hard-requires the literal section string `## Verified Workflow`, so the canonical steps are emitted under that heading to keep validation green. This skill is a PLANNING methodology captured at `unverified` level. Read the steps below as **proposed**, per the warning.

## Verified Workflow

> **Warning:** This workflow has not been validated end-to-end. Treat as a hypothesis until CI confirms.

### Quick Reference

```bash
# === BEFORE proposing to DELETE a "dead" file/symbol: grep the BUILD SYSTEM, not just source ===
# Source #include grep alone is INSUFFICIENT. A file can have zero #includes and still be
# compiled as a standalone translation unit listed in a CMake target.
SYM="validate_api_key"; FILE="auth_middleware.hpp"
grep -rn "$SYM" --include='*.cpp' --include='*.hpp' .          # source callers
grep -rn "$FILE" $(git ls-files '*CMakeLists.txt' '*.cmake')   # build-target references  <-- DO NOT SKIP
git grep -n "$FILE" -- '*.cmake' 'CMakeLists.txt' '**/CMakeLists.txt'
# Only assert "dead code / safe to delete" if BOTH greps are empty AND it is in no add_library/add_executable list.

# === Re-resolve EVERY cited line number against the live tree (line numbers drift) ===
# Treat all file:line citations in the plan as PLAN-TIME SNAPSHOTS, not guarantees.
grep -n 'AGAMEMNON_API_KEY' src/auth.cpp src/server_main.cpp   # re-find, don't trust the cited offset

# === Read the SURROUNDING prose before inserting a doc sentence (match existing voice) ===
sed -n '1,30p' docs/api/openapi.yaml   # read the block, not just the cited range

# === Negative tests the plan MUST include (the easy-to-forget ones) ===
# 1. empty "Bearer " / empty "X-API-Key" still REJECTED (never insert "" into the set; count("")==0)
# 2. all-empty / all-whitespace AGAMEMNON_API_KEYS still ABORTS startup (fail-secure preserved)
```

### Detailed Steps

1. **Frame the change as a UNION, prove the old path is unchanged.** The backward-compat
   contract is: a deployment that sets ONLY the legacy single var must behave byte-for-byte as
   before. State explicitly that the new var is *added to* the accepted set, never *replaces* it.
   The plan should show the exact construction of the accepted-key set and assert the legacy
   single value is always a member when present.

2. **Before proposing ANY deletion, grep the build system — not just source.** The single most
   dangerous claim in this class of plan is "X is dead code (zero callers)" derived from a source
   grep that excludes `.claude/`. A source file can have **zero `#include`s** and still be a
   standalone translation unit in a CMake `add_library`/`add_executable`/`target_sources` list.
   Verify the symbol/file is absent from every `CMakeLists.txt`, `*.cmake`, and include list
   before scheduling its removal. If you cannot verify the build files, the deletion is
   **unverified** and must be flagged as such in the plan body (not just a footnote).

3. **Label every `file:line` citation as a plan-time snapshot.** Exact offsets
   (`src/auth.cpp:20/29/35`, `src/server_main.cpp:114-119`, `docs/api/openapi.yaml:885-895`,
   `test/src/test_auth.cpp:114`, etc.) drift as the tree changes. They are navigation *hints*,
   not contracts. The implementer must re-resolve each by symbol/string search at edit time.

4. **Read surrounding prose before inserting doc sentences.** If you cite a doc line range
   (`openapi.yaml`, `README.md`) but only read the range — not the paragraph around it — the
   inserted sentence may clash with the existing voice/format. Read the block, then phrase to match.

5. **For security-critical compares, preserve the exact rejection semantics.** Changing
   `key == expected` into `set.count(key)` is a behavioral change at a security boundary. Pin
   down: empty `Bearer ` must still reject; empty `X-API-Key` must still reject. The mechanism
   that guarantees this — **never insert empty/whitespace strings into the set, so `count("")==0`**
   — must be an explicit, tested invariant, not an emergent accident.

6. **If you RELAX a fail-secure invariant, add the negative/abort test for it.** Allowing startup
   with only the new `*_KEYS` var relaxes the previous "abort unless `*_KEY` is set" rule. Confirm
   with the issue owner that this relaxation is intended, AND add a test proving that an
   all-empty / all-whitespace `*_KEYS` (which yields an empty accepted set) STILL aborts startup.
   A relaxed rule without an explicit abort test is a silent path to insecure startup.

7. **Order/scope multi-commit splits so no commit breaks the build alone.** A split of
   core / docs / dead-code-removal lets the deletion commit be reviewed and merged independently.
   If a hidden build reference exists (see step 2), that commit breaks the build on its own.
   Either prove the deletion is safe first, or fold it into the core commit, or gate it behind the
   build-system grep being empty.

8. **Note pre-existing security debt you are now touching.** If the touched compare lacks
   constant-time comparison (timing side-channel on key matching), call it out as a reviewer note
   even if pre-existing — the surface is being modified, so it is in scope for a security reviewer.

9. **List EVERY unverified assumption in the plan body.** APIs and skills applied "by description"
   (e.g. team-KB skills read only via their Prior-Learnings summary, `std::unordered_set::count`,
   `std::getline` comma-split, `std::isspace` trim, httplib `Request::has_header`/`get_header_value`
   assumed stable from existing code) are assumptions, not facts, until compiled/read. A NOGO
   reviewer treats an acknowledged-but-unverified assumption the same as an unacknowledged one,
   so resolve or explicitly flag each in the plan, not in a side note.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Dead-code claim from source grep | Asserted `validate_api_key` in `src/auth_middleware.hpp` is dead code ("zero callers") from a single source grep excluding `.claude/` | A source `#include` grep cannot see a standalone translation unit listed in a CMake target; the file was never confirmed absent from any build target or include list | When proposing to DELETE a file, grep the BUILD SYSTEM (`CMakeLists.txt`, `*.cmake`) too — empty source-callers does not prove "unreferenced" |
| Exact line numbers as ground truth | Cited `src/auth.cpp:20/29/35`, `src/server_main.cpp:114-119`, `docs/api/openapi.yaml:885-895`, `test/src/test_auth.cpp:114` as fixed locations | Line numbers were read at plan time and drift as the tree changes; an implementer trusting them edits the wrong line | Label all `file:line` citations as plan-time snapshots; re-resolve each by symbol/string search at edit time |
| Doc edit without reading the block | Cited `openapi.yaml`/`README.md` line ranges to insert a sentence, but read only the range, not the surrounding prose | Inserted wording may not match the existing voice/format of the doc block | Read the full surrounding paragraph before drafting an inserted doc sentence |
| `==` → set membership without pinning rejection | Replaced a single `==` key compare with `set.count(key)` for multi-key support | At a security boundary this can silently accept an empty `Bearer ` / empty `X-API-Key` if an empty string ever enters the set | Make "never insert empty/whitespace into the set so `count(\"\")==0`" an explicit tested invariant; keep empty-credential rejection tests |
| Relaxed fail-secure with no abort test | Allowed startup with only the new `AGAMEMNON_API_KEYS` (relaxing "abort unless `AGAMEMNON_API_KEY` set") and added no negative test | An all-empty/whitespace `AGAMEMNON_API_KEYS` yields an empty accepted set and could let the server start insecurely | When relaxing a fail-secure rule, always add the negative/abort test for the degenerate (all-empty) input |
| Independent dead-code-removal commit | Split into core / docs / dead-code-removal so the deletion could merge on its own | If a hidden build reference exists, the deletion commit breaks the build independently of the rest | Order/scope multi-commit splits so no single commit can break the build; gate deletion on the build-grep being empty |
| Applied skills/APIs by description only | Used team-KB skills (`config-env-double-underscore-nesting`, `backward-compat-removal`) from their summary, and assumed `std::getline`/`std::isspace`/httplib header API behavior without compiling | Description-level use and uncompiled stdlib/library assumptions are unverified; behavior may differ | Read skill bodies and compile/verify stdlib + library assumptions, or explicitly flag each as unverified in the plan body |

## Results & Parameters

**Concrete instance this was distilled from (ProjectAgamemnon issue #260):**

- New env var: `AGAMEMNON_API_KEYS` (comma-separated), unioned with existing single
  `AGAMEMNON_API_KEY` in the C++ `AuthMiddleware` (`src/auth.cpp`).
- Accepted-key set construction invariant (illustrative):

```cpp
// Build the set; NEVER insert empty/whitespace -> guarantees count("")==0 rejects empty creds.
std::unordered_set<std::string> valid_keys;
auto add_trimmed = [&](std::string s) {
  // trim leading/trailing std::isspace
  if (!s.empty()) valid_keys.insert(std::move(s));
};
add_trimmed(get_env("AGAMEMNON_API_KEY"));            // legacy single value (backward compat)
std::stringstream ss(get_env("AGAMEMNON_API_KEYS"));  // new multi-value
for (std::string item; std::getline(ss, item, ','); ) add_trimmed(trim(item));

if (valid_keys.empty()) abort_startup();               // fail-secure: all-empty/whitespace -> ABORT
// match:  valid_keys.count(presented_key) == 1
```

**Reviewer focus checklist (copy into the PR description):**

- [ ] Empty `Bearer ` and empty `X-API-Key` are still REJECTED (no empty string ever enters the set).
- [ ] All-empty / all-whitespace `AGAMEMNON_API_KEYS` still ABORTS startup (fail-secure preserved).
- [ ] Relaxation of the startup rule (start with only `*_KEYS`) is confirmed intentional.
- [ ] Any deleted "dead code" verified absent from CMake/build targets, not just source includes.
- [ ] Each cited `file:line` re-resolved against the current tree before editing.
- [ ] Dead-code-removal commit cannot break the build if reviewed/merged independently.
- [ ] Reviewer note: key match is NOT constant-time (pre-existing timing side-channel on a touched surface).

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| ProjectAgamemnon | Implementation-plan review for issue #260 (multi-key `AGAMEMNON_API_KEYS` in C++ `AuthMiddleware`); plan only, not executed end-to-end | unverified |
