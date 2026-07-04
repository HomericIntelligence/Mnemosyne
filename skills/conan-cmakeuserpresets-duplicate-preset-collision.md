---
name: conan-cmakeuserpresets-duplicate-preset-collision
description: "Fix 'Duplicate preset: \"conan-debug\"' errors after a second conan install in the same repo. Use when: (1) cmake --preset, cmake --build --preset, or ctest --preset suddenly fails with Duplicate preset: \"conan-debug\" (or conan-release etc.), (2) running conan install into a SECOND --output-folder with the same build_type in one repo, (3) deciding how to get a compile_commands.json/second build dir (e.g. for clang-tidy) without breaking existing preset invocations."
category: tooling
date: 2026-07-02
version: "1.0.0"
user-invocable: false
verification: verified-local
tags:
  - conan
  - cmake
  - cmake-presets
  - CMakeUserPresets
  - duplicate-preset
  - ninja
  - toolchain
  - build-system
---

# Conan CMakeUserPresets Duplicate Preset Collision

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-07-02 |
| **Objective** | Set up a second Debug build dir (compile_commands.json for clang-tidy) alongside an existing coverage preset without breaking preset invocations |
| **Outcome** | Successful — pruned `CMakeUserPresets.json` include list; preset commands returned to green (171/171 tests); second build dir configured directly via the Conan toolchain file, bypassing presets |
| **Verification** | verified-local (ProjectNestor issue #29 / PR #118, Conan 2.x + CMake 3.28 + Ninja on Ubuntu WSL2) |

## When to Use

- `cmake --preset <name>`, `cmake --build --preset <name>`, or `ctest --preset <name>` suddenly fails with `Duplicate preset: "conan-debug"` (or `conan-release`, etc.) — including preset commands that worked minutes earlier
- You just ran `conan install` into a SECOND `--output-folder` with the same `build_type` in one repo (e.g. `build/coverage` and `build/debug`, both Debug)
- You need a `compile_commands.json` or a second build directory of the same build type (e.g. for clang-tidy) and must decide how to configure it without breaking existing preset invocations
- A previously-green preset command fails right after a `conan install` and the error looks unrelated to the command being run

## Root Cause

Each `conan install ... --output-folder build/<dir>` generates `build/<dir>/CMakePresets.json` defining a preset named `conan-<build_type>` AND appends that file to the repo-root `CMakeUserPresets.json` `include` array. Two output folders with the same `build_type` (e.g. `build/coverage` and `build/debug`, both Debug) means two included files each defining `conan-debug`. CMake rejects the duplicate name, so EVERY preset command in the repo fails with `Duplicate preset: "conan-debug"` — including previously-working ones like `cmake --build --preset coverage` and `ctest --preset coverage`. The failure appears mid-session and looks unrelated to the command being run.

## Verified Workflow

### Quick Reference

```bash
# Symptom
cmake --build --preset coverage   # -> Duplicate preset: "conan-debug"
# Diagnose + fix: keep only the include you use with presets
python3 - <<'EOF'
import json
p = 'CMakeUserPresets.json'
d = json.load(open(p))
d['include'] = [i for i in d['include'] if 'coverage' in i]
json.dump(d, open(p, 'w'), indent=4)
EOF
# Second build dir without presets (clang-tidy compile_commands):
cmake -S . -B build/debug -G Ninja -DCMAKE_TOOLCHAIN_FILE=build/debug/conan_toolchain.cmake \
  -DCMAKE_BUILD_TYPE=Debug -DCMAKE_EXPORT_COMPILE_COMMANDS=ON
```

### Detailed Steps

1. **Diagnose** — inspect the include list in the repo-root `CMakeUserPresets.json`:

   ```bash
   python3 -c "import json; print(json.load(open('CMakeUserPresets.json'))['include'])"
   ```

   The failure signature is two entries whose generated `CMakePresets.json` files both define the same `conan-<build_type>` preset name (e.g. `build/coverage/CMakePresets.json` and `build/debug/CMakePresets.json`, both defining `conan-debug`).

2. **Fix** — prune the `include` array to the one output-folder you actually use with presets:

   ```bash
   python3 - <<'EOF'
   import json
   p = 'CMakeUserPresets.json'
   d = json.load(open(p))
   d['include'] = [i for i in d['include'] if 'coverage' in i]
   json.dump(d, open(p, 'w'), indent=4)
   EOF
   ```

   After this, preset commands (`cmake --preset`, `cmake --build --preset`, `ctest --preset`) work again.

3. **Second same-build_type build dir without presets** — if you need another build directory of the same build type (e.g. `compile_commands.json` for clang-tidy), bypass the preset layer for it and configure directly against the Conan-generated toolchain file:

   ```bash
   cmake -S . -B build/debug -G Ninja \
     -DCMAKE_TOOLCHAIN_FILE=build/debug/conan_toolchain.cmake \
     -DCMAKE_BUILD_TYPE=Debug \
     -DCMAKE_EXPORT_COMPILE_COMMANDS=ON \
     # plus any project cache vars your build needs
   ```

   The generated `conan_toolchain.cmake` works fine without the preset layer.

4. **Prevention** — keep one Conan output-folder per build_type per repo. When a wrapper script (e.g. `scripts/lint.sh`) wants to run `cmake --preset debug`, check whether its `conan install` will collide with an existing same-type output folder BEFORE running it.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Run existing preset after second conan install | Running `cmake --preset debug` after a second `conan install --output-folder build/debug` | `CMakeUserPresets.json` now included two files both defining `conan-debug` → "Duplicate preset" on EVERY preset command | Conan appends to the include list per output-folder; same build_type collides |
| Blame the most recent code change | Assuming the coverage preset build broke because of the code change just made | The failure was environmental (preset collision), unrelated to the edit | When a previously-green preset command fails right after a conan install, check `CMakeUserPresets.json` first |

## Results & Parameters

```yaml
# Environment
conan: 2.x
cmake: 3.28
generator: Ninja
os: Ubuntu (WSL2)

# Symptom
error: 'Duplicate preset: "conan-debug"'
trigger: second `conan install --output-folder build/debug` with build_type=Debug
existing_folder: build/coverage  # also Debug
blast_radius: every preset command in the repo (cmake/ctest --preset)

# Fix
action: prune CMakeUserPresets.json include array to the one preset-driven folder
kept_include: build/coverage/CMakePresets.json

# Second build dir (no presets)
configure: >-
  cmake -S . -B build/debug -G Ninja
  -DCMAKE_TOOLCHAIN_FILE=build/debug/conan_toolchain.cmake
  -DCMAKE_BUILD_TYPE=Debug -DCMAKE_EXPORT_COMPILE_COMMANDS=ON

# Verification
after_fix: "cmake --build --preset coverage and ctest --preset coverage green"
tests: 171/171 passing
```

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| ProjectNestor | issue #29 / PR #118 coverage work, setting up a clang-tidy compile_commands dir alongside the coverage preset | 2026-07-02 |
