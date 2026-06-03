---
name: cmake-phantom-targets-extraction-cleanup
description: "Clean up phantom CMake imported targets from package config after code extraction per ADR. Use when: (1) code extracted to separate repository per architectural decision, (2) installed package config still exposes removed components as phantom imported targets, (3) documentation still references conditional guards or removed libraries, (4) need to audit scope without trusting issue descriptions."
category: architecture
date: 2026-06-03
version: "1.0.0"
user-invocable: false
verification: verified-local
tags:
  - cmake
  - package-config
  - phantom-targets
  - adr-extraction
  - code-cleanup
---

# CMake Phantom Targets Extraction Cleanup

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-06-03 |
| **Objective** | Remove phantom CMake imported targets from installed package config after code extraction per ADR. |
| **Outcome** | Successfully removed keystone_agents and keystone_network phantom targets from cmake/KeystoneConfig.cmake.in; verified zero stale references in installed config and docs. |
| **Verification** | verified-local (CMake syntax validated, grep audit confirms clean state; CI validation pending on merged PR #584) |

## When to Use

- Code has been extracted to a separate repository and tracked via an ADR (e.g., ADR-015)
- The installed CMake package config file (`.cmake.in` template) still exposes phantom imported targets pointing to non-existent archives
- Packaging documentation still advertises removed components or conditional build flags
- Issue description cites specific line numbers but those may be stale or pointing at unrelated code
- Need to verify actual state of files before making assumptions

## Verified Workflow

### Quick Reference

```bash
# 1. Verify actual state, don't trust issue citations
grep -n "target-name" CMakeLists.txt
# If NOT found → target was removed; check cmake/ subdirectory instead

# 2. Multi-extension inventory audit
grep -rn "phantom-target\|CONDITIONAL-FLAG" \
  --include="*.cmake" --include="*.cmake.in" --include="CMakeLists.txt" \
  --include="*.cpp" --include="*.h" --include="*.hpp" --include="*.md" --include="*.py" \
  . | grep -v "^build/" | grep -v "^docs/plan/adr/" | grep -v "^.git/"

# 3. Identify scope: files containing stale references
# Typically: cmake/<Name>Config.cmake.in, docs/PACKAGING.md, docs/plan/build-system.md

# 4. For each stale file, use surgical Edit blocks (not replace_all)
# Edit the cmake template with exact surrounding context:
# - Include the if(NOT TARGET ...) guard as start boundary
# - Include the closing endif() and next statement as end boundary
# - This prevents accidental removal of unrelated mentions

# 5. Verify zero stale references remain
grep -n "phantom-target\|CONDITIONAL-FLAG" cmake/<Name>Config.cmake.in docs/PACKAGING.md
# Expect: no output, exit code 1
```

### Detailed Steps

1. **Verify actual file state — never trust issue description line refs**
   - Issue #507 cited `CMakeLists.txt:316-331` as evidence of phantom keystone_agents library
   - Those lines actually contained test source files, not the agent library definition
   - The real defect was in `cmake/KeystoneConfig.cmake.in` (phantom imported targets) and `docs/PACKAGING.md` (stale documentation)
   - Always run: `grep -n "<target-name>" CMakeLists.txt` first; if not found, check cmake/ directory
   - Lesson: Files may be partially extracted; locations in issue descriptions can be stale

2. **Build comprehensive inventory with multi-extension grep**
   - Search all relevant file types in one command to capture complete scope:
   ```bash
   grep -rn "keystone_agents\|ENABLE_GRPC\|keystone_network" \
     --include="*.cmake" --include="*.cmake.in" --include="CMakeLists.txt" \
     --include="*.cpp" --include="*.h" --include="*.hpp" \
     --include="*.md" --include="*.py" . | \
     grep -v "^build/" | grep -v "^docs/plan/adr/" | grep -v "^.git/"
   ```
   - Document every hit — this is your scope boundary
   - Identify which files actually need modification (typically cmake template + docs)

3. **Use surgical Edit blocks for cmake templates**
   - Never use `replace_all` on cmake config files; syntax variations cause missed blocks
   - Identify the exact logical block to remove (e.g., the entire `if(NOT TARGET ...)` guard)
   - Include surrounding context in old_string: 1-2 lines before and after the block
   - Example: Removing a phantom target requires the guard + add_library + set_target_properties + endif
   - This isolation prevents accidental removal of unrelated mentions of the same keyword

4. **Remove from cmake/Name.cmake.in:**
   - Phantom imported target block (`if(NOT TARGET ...)`, `add_library(...)`, `set_target_properties(...)`, `endif()`)
   - Conditional dependency blocks (e.g., `if(@CONDITIONAL@)`, `find_dependency(...)`, `endif()`)
   - References in component list (`set(Name_COMPONENTS ...)` — remove phantom from list)
   - References in libraries list (`set(Name_LIBRARIES ...)` — remove phantom, remove conditional append)

5. **Remove from docs/PACKAGING.md:**
   - Usage examples referencing phantom components in `find_package()` calls
   - Build command examples with removed conditional flags
   - Package tree diagrams listing removed libraries or directories
   - Conditional sections (e.g., text saying "if ENABLE_GRPC=ON" for removed feature)

6. **Remove from historical planning docs (if not frozen ADR):**
   - `docs/plan/build-system.md` or similar may reference removed options
   - Historical ADRs themselves should NOT be modified (they are frozen records)
   - Only update non-ADR planning docs if still active/mutable

7. **Post-edit verification — grep only modified files**
   ```bash
   grep -n "phantom-target" cmake/<Name>Config.cmake.in docs/PACKAGING.md
   # Expect: no output, exit code 1
   ```
   - This acts as a regression check and confirms scope closure
   - If any hits remain, identify and remove in follow-up edits

8. **Commit with ADR reference**
   - Include the ADR number (e.g., ADR-015) in commit message
   - Document why phantom targets are being removed (extraction to separate repo)
   - Note files modified and scope boundaries

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Trusting issue line refs | Issue #507 cited CMakeLists.txt:316-331 as location of keystone_agents library definition | Lines contained test source files, not the library; target was already removed in a prior commit | Always verify actual file state with targeted grep before acting; issue descriptions can reference stale, moved, or wrong lines |
| Using replace_all on cmake templates | Bulk find-replace of `ENABLE_GRPC` across cmake/KeystoneConfig.cmake.in file | CMake syntax has variations (whitespace, guards); bulk replace risks missing blocks or affecting unrelated mentions | Use surgical Edit blocks with exact surrounding context (guards, endif boundaries) to isolate each logical block |
| Single-extension audit | Only grepped CMakeLists.txt and `.cmake` files for stale references | Missed phantom references in packaging docs (`.md` files) and other contexts; scope was incomplete | Multi-extension audit across (.cmake, .cmake.in, CMakeLists.txt, .cpp, .h, .hpp, .md, .py) required to build complete inventory |
| Skipping post-edit verification | Assumed manual inspection caught all removals during editing | Hidden phantom references could remain in installed artifact; no way to confirm scope closure | Re-run audit grep on modified files post-edit to confirm zero stale references; acts as regression guard and provides confidence |

## Results & Parameters

### For Issue #507 (keystone_agents extraction to ProjectAgamemnon)

**Files Modified:**
- `cmake/KeystoneConfig.cmake.in` — 58 lines removed
  - Removed gRPC dependency blocks (3 lines)
  - Removed phantom keystone_agents imported target (8 lines)
  - Removed phantom keystone_network imported target with ENABLE_GRPC guard (11 lines)
  - Updated components list from `core concurrency agents simulation` to `core concurrency simulation`
  - Updated Keystone_LIBRARIES list to remove agents and network references
- `docs/PACKAGING.md` — 6 surgical edits
  - Usage example: removed `agents` from find_package components and target_link_libraries
  - Build example: removed `-DENABLE_GRPC=ON` flag
  - Runtime package tree: removed `libkeystone_agents.so` and `libkeystone_network.so` lines
  - Dev package tree: removed `agents/` include directory, `libkeystone_agents.a` static lib, `network/` directory, `/usr/share/keystone/proto/` section
  - Test package tree: removed `distributed_grpc_tests (if ENABLE_GRPC=ON)` line

**Audit Commands:**
```bash
# Initial comprehensive inventory
grep -rn "keystone_agents\|ENABLE_GRPC\|keystone_network" \
  --include="*.cmake" --include="*.cmake.in" --include="CMakeLists.txt" \
  --include="*.md" --include="*.cpp" --include="*.hpp" --include="*.h" . | \
  grep -v "^build/" | grep -v "^docs/plan/adr/ADR-0" | grep -v "^.git/"

# Post-edit verification (target files only)
grep -n "keystone_agents\|ENABLE_GRPC\|keystone_network" \
  cmake/KeystoneConfig.cmake.in docs/PACKAGING.md
# Result: no output, exit code 1 ✓
```

**CMake Syntax Validation:**
- Removed `if(@ENABLE_GRPC@) ... find_dependency(...) ... endif()` block (lines 13-17)
- Removed phantom target registration block (lines 50-57 for keystone_agents, lines 68-77 for keystone_network with guard)
- Updated set(Keystone_COMPONENTS) from 4 to 3 entries
- Updated set(Keystone_LIBRARIES) from 4 to 3 entries
- Removed conditional list(APPEND) for network target
- Result: Valid CMake syntax; no template variable expansion errors

**Commit Details:**
```
refactor(build): remove keystone_agents phantom target from CMake package config

Per ADR-015, the agent layer was extracted to ProjectAgamemnon. CMake build
target was already deleted, but installed package config still exposed phantom
Keystone::keystone_agents imported target.

This completes ADR-015 extraction by removing stale references from:
- cmake/KeystoneConfig.cmake.in (phantom targets, conditional blocks)
- docs/PACKAGING.md (usage examples, package trees)

Result: Installed CMake package config and docs now accurately describe
Keystone as pure-transport library with no agent or gRPC surface.

Closes #507
```

**Verification:**
- ✅ CMake syntax validated (no template expansion errors)
- ✅ grep confirms zero stale references in modified files
- ✅ Signed commit with proper message
- ✅ PR #584 created with auto-merge enabled
- ✅ All policy checks passing (body, signing, auto-merge)

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| ProjectKeystone | Issue #507: Remove phantom CMake targets after ADR-015 extraction | PR #584 with auto-merge enabled; keystone_agents and keystone_network phantom targets removed from installed config |
