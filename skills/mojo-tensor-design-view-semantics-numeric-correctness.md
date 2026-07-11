---
name: mojo-tensor-design-view-semantics-numeric-correctness
description: "Use when: (1) designing ExTensor/AnyTensor types with parametric dtypes, view semantics, and stride-aware slices, (2) implementing or debugging zero-copy view operations (transpose, slice, ravel) for stride-aware tensor access, (3) diagnosing silent correctness bugs in tensor numeric operations (strided layout, dtype mismatch, bitcast corruption, NaN hashing), (4) adding NumPy-style truncation to Mojo tensor __str__ methods, (5) fixing DataLoader N-D batch slicing or shape assumptions, (6) SIMD-vectorizing element-wise tensor ops in Mojo for throughput gains, (7) adding Apple Silicon BF16 runtime guards to dtype/precision factory methods, (8) implementing or testing __hash__ on Mojo tensors with float/int fields and empty-tensor edge cases."
category: architecture
date: 2026-07-11
version: "1.2.0"
user-invocable: false
history: mojo-tensor-design-view-semantics-numeric-correctness.history
tags:
  - mojo
  - tensor
  - extensor
  - anytensor
  - dtype
  - parametric
  - view-semantics
  - strides
  - bitcast
  - nan
  - hash
  - simd
  - vectorization
  - bfloat16
  - numeric-correctness
  - dataloader
---

# Mojo Tensor Design, View Semantics, and Numeric Correctness

Canonical reference for designing Mojo ExTensor/AnyTensor types (parametric dtypes,
zero-copy views, stride-aware element access, safe load/store), diagnosing silent
numeric-correctness bugs (strided layout, bitcast corruption, NaN hashing, PRNG seed
wiring), SIMD-vectorizing element-wise ops, and adding hardware/precision guards.

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-06-07 |
| **Objective** | Unified guide for Mojo tensor design, view semantics, numeric correctness, SIMD vectorization, and dtype/hardware guards |
| **Outcome** | Merged from 7 skills covering type design, stride access, numeric bugs, hashing, vectorization, and BF16 guards |
| **Verification** | verified-ci |
| **Mojo Version** | 0.26.1 / 0.26.3 |

## When to Use

- Designing `ExTensor[dtype]`/`AnyTensor` types with compile-time parametric dtypes and stride-aware slices
- Implementing zero-copy views: `transpose()`, `slice()`, `ravel()` on Mojo tensors
- Debugging wrong values from non-contiguous (transposed/strided) tensor element access (`i * dtype_size` bug)
- Eliminating raw `_data.bitcast[T]()` UAF patterns via a safe `load`/`store`/`data_ptr` API
- Diagnosing dtype-mismatch bitcast corruption (float bits read as int), missing bfloat16 branches, 1-byte-per-element copies
- Canonicalizing NaN bit patterns for stable `__hash__`; wiring an unused PRNG `seed` parameter
- Implementing/testing `__hash__` on tensors with float/int fields and empty-tensor (numel=0) edge cases
- Adding NumPy-style truncation to a tensor `__str__` that loops all elements
- Fixing `DataLoader.next()` N-D batch slicing (replacing a hardcoded 2D shape assumption)
- SIMD-vectorizing element-wise scans (NaN/Inf detection, gradient clipping, L2 norm) for 4-16x throughput
- Adding Apple Silicon BF16 runtime guards to dtype/precision factory methods
- Resolving a Mojo dtype-conversion that accepts a dtype in its outer guard but whose inner dispatch raises for it (accept-then-raise asymmetry) — e.g. block-quant `to_mxfp4()`/`to_nvfp4()` accepting bf16 then raising "Invalid dtype for MXFP4 quantization"

## Verified Workflow

### Quick Reference

```text
# Type design
ExTensor[dtype]                                   parametric struct; __getitem__ returns Scalar[dtype]
tensor.view_with_strides(new_shape, new_strides)  base primitive for all zero-copy views
tensor._nd_index_to_flat_offset(linear_idx)       byte offset for non-contiguous access
tensor.load[DType.float32](i) / store / data_ptr  safe API — no raw bitcast UAF

# Stride-aware accessor
if self.is_contiguous(): offset = index * dtype_size
else:                    offset = self._nd_index_to_flat_offset(index)

# Numeric correctness
dtype guard before bitcast loop (int32/int64 labels only)
bfloat16: fix size + read + write branches together; cast via Float32 intermediary
NaN canonicalize hash-side only (never mutate stored data)
seed > 0 -> random_seed(seed); never leave seed unwired
batch copy: _set_float64(dst, _get_float64(src))  — NOT byte-pointer (ptr+i).store((ptr+i).load())

# Vectorization & guards
vectorize[simd_w] for counting/reduction; manual while-loop for early-exit detection
_check_bf16_platform_support(is_apple_silicon())  testable hardware guard
```

### Detailed Steps

#### 1. Parametric DType and View Semantics (type design)

Mojo's `obj[i] = val` does **not** call `__setitem__`; it calls `__getitem__(i)` for an
lvalue and assigns to it, so `__setitem__` overloads are dead code for subscript syntax.
A runtime `var _dtype: DType` forces `__getitem__` to return one fixed type. Make the
struct parametric instead:

```mojo
struct ExTensor[dtype: DType]:
    var _data: UnsafePointer[UInt8, origin=MutAnyOrigin]
    var _shape: List[Int]
    var _strides: List[Int]

    fn __getitem__(self, index: Int) raises -> Scalar[Self.dtype]:
        return self._data.bitcast[Scalar[Self.dtype]]()[resolved_index]
```

Build all zero-copy views from one stride primitive:

```mojo
fn _nd_index_to_flat_offset(self, linear_idx: Int) -> Int:
    var dtype_size = self._get_dtype_size()
    var remaining = linear_idx
    var element_offset = 0
    for i in range(len(self._shape) - 1, -1, -1):
        var coord = remaining % self._shape[i]
        remaining //= self._shape[i]
        element_offset += coord * self._strides[i]
    return element_offset * dtype_size

fn view_with_strides(self, new_shape: List[Int], new_strides: List[Int]) -> ExTensor:
    var result = self.copy()      # __copyinit__ increments refcount
    result._is_view = True
    result._shape = new_shape.copy()
    result._strides = new_strides.copy()
    return result^                # move, no extra increment
```

`transpose()` and `slice()` become views over `view_with_strides`; `slice()` additionally
offsets the data pointer: `result._data = self._data + start * strides[axis] * dtype_size`.
Always `.copy()` a `List[Int]` field — Mojo `List[Int]` is not `ImplicitlyCopyable`.

#### 2. Stride-Aware Element Access

The canonical correctness bug: every accessor computing `offset = i * dtype_size` assumes
stride-1 layout. For a transposed `(4,3)` tensor with strides `[1,4]`, element `(0,1)` is
at byte offset `1*4*dtype_size`, not `1*dtype_size`. Fix **all** accessors
(`_get_float32/64`, `_set_float32/64`, `_get_int64`, ...), not just `slice()`:

```mojo
var offset: Int
if self.is_contiguous():
    offset = index * self._get_dtype_size()
else:
    offset = self._nd_index_to_flat_offset(index)
```

Audit `as_contiguous()`, `concatenate()`, `tile()`, `repeat()`, `broadcast_to()`,
`permute()`, `reshape()`, `stack()`. Regression test: `arange(0..12).reshape(3,4)`,
transpose, then assert all 12 element values — a test that only checks `is_contiguous()`
and `_strides` will NOT catch the bug. Contiguify flat-buffer kernels (matmul) on input.

`concatenate()` is only **partially** stride-fixed: the stride-based decomposition above
covers the `if actual_axis == 0` branch only. The general-axis branch (non-zero
`actual_axis`) still uses raw flat-offset memcpy and is a knowingly-unfixed flat-offset bug
scoped out by design in issue #4083 — do NOT present `concatenate()` as fully fixed for all axes.

#### 3. Safe Load/Store API (eliminate bitcast UAF)

Raw `loss_tensor._data.bitcast[Float32]()[0]` causes ASAP-destruction UAF. Add a typed API
to AnyTensor (names `load`/`store`/`data_ptr`, not `get`/`set` — those collide with existing
overloads):

```mojo
@always_inline
fn load[dtype: DType](self, index: Int) -> Scalar[dtype]:
    debug_assert(self._dtype == dtype, "AnyTensor.load[dtype] mismatch")
    return self._data.bitcast[Scalar[dtype]]()[index]

@always_inline
fn data_ptr[dtype: DType](self) -> UnsafePointer[Scalar[dtype], origin=MutAnyOrigin]:
    return self._data.bitcast[Scalar[dtype]]()
```

`self` (not `mut self`) — `MutAnyOrigin` permits writes. Include `origin=MutAnyOrigin` on
returned pointers or the bitcast return type won't match. After migrating, grep the ENTIRE
codebase: `grep -rn "bitcast\[Float32\]"` — a missed `pooling.mojo` produced
"max pooling output contains NaN or Inf" on float16 (2-byte) tensors read as 4 bytes.

#### 4. Numeric-Correctness Bugs

**Bitcast corruption (dtype mismatch):** A metric reading float labels through
`bitcast[Int64]` gets garbage class indices — `float32(1.0)` bits `0x3F800000` = 1065353216.
Guard before the loop:

```mojo
if labels._dtype != DType.int32 and labels._dtype != DType.int64:
    raise Error("update() requires int32 or int64 labels, got " + str(labels._dtype))
```

**1-byte-per-element batch copy:** `AnyTensor._data` is `UnsafePointer[UInt8]`;
`(ptr + i).store((ptr + i).load())` moves 1 byte per element regardless of dtype, leaving
3/4 of a float32 silently uninitialized. Training looks "close" then asymptotes to chance.
Use `batch_images._set_float64(dst, train_images._get_float64(src))`. Sentinel check:
`t._set_float64(0, 1.25); assert _get_float64(0) == 1.25` (a 1-byte bug shows 0.0 or ~0.198).

**Missing bfloat16:** Fix three sites together — `_get_dtype_size_static` (return 2),
`_get_float64` read branch, `_set_float64` write branch. Direct `BFloat16 <-> Float64` is
wrong in 0.26.1; cast through Float32 (bf16 shares float32's 8-bit exponent). Note there is
no `BFloat16` scalar alias — use `SIMD[DType.bfloat16, 1]`.

**Slice view bad-free:** `__del__` frees an offset slice-view `_data` pointer. ASAN reports
"free on address... N bytes inside of region". Guard: `if not self._is_view: pooled_free(...)`.

**Multi-dim slice step ignored:** the variadic `__getitem__(*slices)` reads start/end but
not step, so `tensor[::2, :]` returns all elements. Fail-fast in a pre-loop:

```mojo
for dim in range(num_dims):
    if slices[dim].step.or_else(1) != 1:
        raise Error("Multi-dimensional slicing does not support step != 1 ...")
```

#### 5. NaN Hashing and PRNG Seed Wiring

IEEE 754 has many NaN bit patterns (sign, quiet/signaling, payload), all semantically equal
but bit-different — they break hash stability. Canonicalize **hash-side only**, never mutate
stored data. If `_get_float64()` unifies all dtypes to Float64, one pass covers all dtypes:

```mojo
alias CANONICAL_NAN_F64: UInt64 = 0x7FF8000000000000
alias F64_INF_BITS: UInt64     = 0x7FF0000000000000
alias F64_ABS_MASK: UInt64     = 0x7FFFFFFFFFFFFFFF
if (int_bits & F64_ABS_MASK) > F64_INF_BITS:
    int_bits = CANONICAL_NAN_F64
```

Hash float fields via bitcast (not `Int(val*1e6)` — overflows/collides). Assign to a named
local first (taking the address of a temporary dangles):
`UnsafePointer[Float64](to=local_val).bitcast[UInt64][]`. Always fold
`dtype_to_ordinal(self._dtype)` into the chain so same-data different-dtype tensors differ.

Run the shape loop **before** the data loop so empty tensors (`numel=0`) still hash distinctly:
`[0]`, `[0,0]`, and `[0,1]` produce different hashes via shape + dtype ordinal alone. There is
no `assert_not_equal` for UInt — use `if hash(a) == hash(b): raise Error(...)`.

Wire an unused `seed` parameter:

```mojo
from random import random_float64, seed as random_seed
if seed > 0:
    random_seed(seed)   # call BEFORE any random_float64()
```

Find offenders: `grep -rn "seed: Int"` vs `grep -rn "random_seed("`. Convention: `seed=0`
system random, `seed>0` reproducible.

#### 6. SIMD Vectorization

```mojo
from sys import simd_width_of
from algorithm import vectorize
from math import isnan

# Counting/reduction: vectorize[] handles the tail automatically
fn count_nan[dtype: DType](tensor: Tensor[dtype]) -> Int:
    var count = 0
    comptime simd_w = simd_width_of[dtype]()
    @parameter
    fn _count[width: Int](idx: Int) unified {mut}:
        count += Int(isnan(tensor._data.load[width=width](idx)).cast[DType.uint8]().reduce_add())
    vectorize[simd_w](tensor.numel(), _count)
    return count
```

Pattern selection: **manual `while` loop** for early-exit detection (`has_nan`) — a
`vectorize[]` closure cannot `return` from the outer function; **`vectorize[]`** for counting
and arithmetic reduction (norm/scale/clamp) with a `unified {mut}` closure. Use a Float64
accumulator for L2 norm stability. Bitcast the `UInt8` `_data` once outside the loop. Use
`@parameter if` to compile-out the check for integer dtypes. float32 -> 8 lanes (AVX-256),
float64 -> 4. Test non-SIMD-aligned sizes (1, 7, 13, 33) and boundary placements.

#### 7. ExTensor `__str__` Truncation

A `__str__` that loops all `_numel` elements is slow for 1M+ tensors. Add NumPy-style
truncation (`numpy.set_printoptions(threshold=1000)`): threshold is **exclusive** (`> 1000`):

```mojo
alias TRUNCATE_THRESHOLD = 1000   # exclusive: exactly 1000 shows all values
alias SHOW_ELEMENTS = 3           # head and tail count
if self._numel > TRUNCATE_THRESHOLD:
    for i in range(SHOW_ELEMENTS): ...           # first 3
    result += ", ..."
    for i in range(self._numel - SHOW_ELEMENTS, self._numel): ...  # last 3
```

Output: `ExTensor([0.0, 1.0, 2.0, ..., 997.0, 998.0, 999.0], dtype=float32)`.

#### 8. DataLoader N-D Batch Slicing

`DataLoader.next()` hardcoding a 2D shape collapses `(N,C,H,W)` to `(batch, width)`. Replace
the manual shape construction with the existing view-returning `slice()`:

```mojo
var batch_data = self.data.slice(start_idx, end_idx)     # preserves ALL trailing dims
var batch_labels = self.labels.slice(start_idx, end_idx)
```

Import the submodule directly (`from shared.training.trainer_interface import DataLoader`) —
Mojo re-export limits block the parent-package import.

#### 9. Apple Silicon BF16 Hardware Guard

Make precision factory methods fail loudly (not silently fall back to FP16) and keep the guard
testable on Linux CI by injecting the platform bool:

```mojo
fn _check_bf16_platform_support(is_apple: Bool) raises:
    if is_apple:
        raise Error("BF16 (bfloat16) is not supported on Apple Silicon. Use PrecisionConfig.fp16() instead.")

@staticmethod
fn bf16(initial_scale: Float32 = 65536.0) raises -> PrecisionConfig:
    from sys.info import is_apple_silicon
    _check_bf16_platform_support(is_apple_silicon())
    return PrecisionConfig(...)
```

`is_apple_silicon()` is a runtime function — a `@parameter if` compile-time guard does not
work in 0.26.1. Adding `raises` requires auditing callers: `grep -rn "\.bf16()" --include="*.mojo"`.
Confirm the stdlib symbol via `strings .pixi/envs/default/lib/mojo/std.mojopkg | grep is_apple`.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Add `__setitem__` overloads | 9 overloads for subscript assignment | Mojo decomposes `obj[i]=val` into `__getitem__` lvalue + assign; `__setitem__` never called | Add a matching `__getitem__`; make the struct parametric for SIMD-like assignment |
| Widen `__getitem__` to Float64 | Return wider type to accept more RHS | No implicit float widening in Mojo; broke 108 call sites | Mojo has no implicit conversion between Float16/32/64 |
| Route `set()` through Float64 | `__setitem__(i, Float64(v))` | Float32->Float64->Float32 round-trip changes values (3.14159 -> 3.14159011...) | Never introduce precision-losing conversion round-trips |
| `Float32()` cast in `@parameter fn` | Wrapped RHS for `parallelize[]` | `Float32()` constructor raises; parallel closures cannot raise | Use non-raising `_set_float64` in parallel/`@parameter` contexts |
| `var new_shape = self._shape` | Direct assignment of a `List[Int]` field | `List[Int]` is not `ImplicitlyCopyable` | Always `.copy()` when assigning a `List[Int]` field |
| Fix `slice()` only, not accessors | Assumed `view_with_strides` sufficed | Transposed-view reads still used `i * dtype_size` | Non-contiguous correctness requires fixing ALL element accessors |
| Treat `concatenate()` as fully stride-fixed | Applied the stride decomposition and assumed all axes covered | Only the `actual_axis == 0` branch was fixed; the non-zero-axis branch still uses raw flat-offset memcpy (knowingly unfixed, issue #4083) | Document partial fixes explicitly; concatenate is stride-correct on axis 0 only |
| Named API `get[dtype]`/`set[dtype]` | Method names on AnyTensor | Collide with existing 12 `set()` overloads | Use `load`/`store`/`data_ptr` (LLVM/SIMD terminology) |
| `data_ptr` without `origin=MutAnyOrigin` | `UnsafePointer[Scalar[dtype]]` return | Doesn't match `_data.bitcast` origin | Include `origin=MutAnyOrigin` on returned AnyTensor pointers |
| Missed pooling in bitcast migration | Migrated training but left `pooling.mojo` | float16 read as 4-byte float32 -> "NaN or Inf" crash | After any bitcast migration, grep the ENTIRE codebase |
| `BFloat16` scalar alias | Used `BFloat16` like `Float32` | No such alias in stdlib | Use `SIMD[DType.bfloat16, 1]` |
| Direct BFloat16<->Float64 cast | `ptr[].cast[DType.float64]()` from bf16 | Wrong values in Mojo 0.26.1 | Cast through Float32 as intermediary |
| Fix only bf16 I/O branches | Skipped `_get_dtype_size_static` | 4-byte default -> wrong byte offsets | Fix size + read + write branches together for any new dtype |
| Add a bf16 support branch to block-quant | Widen bf16->Float32 (like float16) in the inner MXFP4/NVFP4 dispatch to resolve the accept-then-raise | Inconsistent with sibling `to_fp8`/`to_bf8` which REJECT bf16 for the same reason; relies on the exact distrusted Float32-intermediate path | REJECT bf16 at the outer guard to match the sibling conversion family's established policy — don't invent a support path the codebase already rejected elsewhere |
| `bitcast[BFloat16]()` a bf16 scalar | Used `BFloat16` as the bitcast target for `tensor._data.bitcast[...]()[i]` | No `BFloat16` scalar alias exists (unlike `Float16`, which IS a stdlib alias) | Use `bitcast[Scalar[DType.bfloat16]]()` |
| Overclaim the rejection comment | Wrote the bf16 reject comment stating bf16->Float32 "doesn't round-trip" as fact | The widening cast bf16->Float32 is mathematically exact; the real cause is a distrusted Mojo-version-specific bf16 READ path | Word it as matched-from-precedent (copied from the FP8 family's rationale), don't independently re-derive or overclaim |
| `Int(val * 1e6)` float hash | Multiply then truncate to int | Overflows large values; collides small (`0.1` -> 0) | Bitcast to UInt64 to preserve all 64 IEEE bits |
| Address-of return value | `UnsafePointer.address_of(self._get_float64(i))` | Temporary has no stable address (dangling) | Assign to a named local before taking its address |
| `UnsafePointer.address_of()` static | Called as a static method | Not a static method in 0.26.1 | Use `UnsafePointer[T](to=val)` constructor |
| Skip dtype in hash | Hashed shape and data only | Same-data different-dtype tensors collide | Fold `dtype_to_ordinal(self._dtype)` into the chain |
| Two-instance hash stability test | `hash(a) == hash(b)` two instances | Passes even with per-instance side effects | Single-instance repeated calls are a stronger guarantee |
| `assert_not_equal` for hash | Used it for UInt inequality | No such helper for UInt | Use `if hash(a) == hash(b): raise Error(...)` |
| Per-dtype NaN canonicalization | float16/32/64 branches in `__hash__` | `_get_float64()` already unifies in Float64 space | Canonicalize once in Float64 — no per-dtype branches |
| Canonicalize stored tensor data | Modify `_data` bytes to fix NaN | Mutates stored data; breaks roundtrip fidelity | NaN canonicalization is hash-side only |
| Dtype guard inside the loop | Validation per element | Redundant; raises on iter 1 instead of fast-fail | Validate inputs before iterating |
| Generic bitcast error message | `raise Error("invalid dtype")` | Forces callers to read source | Include accepted values: "requires int32 or int64, got X" |
| Full strided multi-dim slice copy | Build stride-aware copy instead of raising | Large surface area, no immediate caller need | Prefer fail-fast unless strided multi-dim access is required |
| Trust accessors protect bad bytes | Assumed `_get_float64` surfaces garbage | Zero-filled high bytes decode to valid denormals — no NaN/error | Dtype-correct accessors guard type confusion, not pre-corrupted storage |
| Byte-pointer batch copy | `(ptr+i).store((ptr+i).load())` on float32 | Copies 1 byte/element; 3/4 of each float uninitialized | Use `_set_float64(dst, _get_float64(src))` |
| `vectorize[]` for `has_nan` | Closure with a `found` flag | Cannot `return` from the outer fn inside a `vectorize[]` closure | Manual SIMD `while` loop when early exit is needed |
| Inclusive `__str__` threshold (`>= 1000`) | Considered `>= 1000` | Design decision; 1000 should show all per analysis | Use `> 1000` (exclusive) |
| Manual N-D batch shape construction | Loop over `self.data.shape()` to build batch shape | More complex; still allocates a new tensor | `slice()` already returns a shape-preserving view |
| Silent BF16 -> FP16 fallback | Return `fp16()` on Apple Silicon | Changes semantics without warning | Fail loudly; let the caller choose FP16 explicitly |
| Compile-time `@parameter` BF16 guard | `@parameter if is_apple_silicon()` | It is a runtime function in 0.26.1 | Use a runtime `raises` guard |
| Inline BF16 guard in `bf16()` | `if is_apple_silicon(): raise` directly | Untestable on Linux CI (always False) | Extract a helper taking `is_apple: Bool` for injection |
| Run `mojo`/`mojo test` locally | Direct local execution | GLIBC 2.32/2.33/2.34 not found on host | Mojo tests run in Docker/CI; verify by inspection + pre-commit |

## Results & Parameters

### Mojo Subscript & DType Facts

```text
- obj[i] = val uses __getitem__ lvalue, NOT __setitem__
- No implicit conversion between Float16/32/64
- FloatLiteral/IntLiteral implicitly convert to any Scalar[dtype]
- Float32 -> Float64 -> Float32 round-trip is NOT lossless
- No BFloat16 scalar alias; use SIMD[DType.bfloat16, 1] / Scalar[DType.bfloat16]; cast bf16 via Float32 (Float16 IS a stdlib alias, BFloat16 is NOT)
- Scalar conversion: .cast[DType.float64]() (constructor does not implicitly convert)
```

### Accept-Then-Raise Dtype Guard (block-quant bf16 reject)

When an outer floating-point guard accepts a dtype the inner dispatch cannot handle,
make the outer guard reject it — matching the sibling conversion family's policy — and
delete the now-dead inner branch.

| Aspect | Pattern |
| ------ | ------- |
| Symptom | Outer guard accepts bf16; inner MXFP4/NVFP4 `else` raises "Invalid dtype for MXFP4 quantization" |
| Precedent | Sibling `_convert_to_fp8_family_impl` (same file) already REJECTS bf16 with a documented reason |
| Fix | Reject bf16 at the OUTER guard with a message identical to the FP8 family; remove the dead inner branch |
| Test discriminator | Raised error CONTAINS `"bfloat16"` (outer-guard message) AND does NOT contain `"Invalid dtype for MXFP4/NVFP4 quantization"` (inner message) — distinguishes clean-reject from old accept-then-raise |
| Non-vacuous proof | Removing the outer guard makes bf16 fall through to the inner `else` and the test fails |
| bf16 scalar bitcast | `tensor._data.bitcast[Scalar[DType.bfloat16]]()[i]` — no `BFloat16` alias (`Float16` IS an alias) |
| Comment honesty | bf16->Float32 is an exact widening cast; the "doesn't round-trip" wording is matched-from-precedent (distrusted Mojo bf16 read path), not independently re-derived |

### Safe load/store API Design

```yaml
load[dtype](self, index) -> Scalar[dtype]
store[dtype](self, index, value: Scalar[dtype])
data_ptr[dtype](self) -> UnsafePointer[Scalar[dtype], origin=MutAnyOrigin]
inline: "@always_inline"
self_mutability: "self (MutAnyOrigin allows writes)"
dtype_check: "debug_assert only (compiles away in release)"
bounds_check: "none (caller responsible)"
```

### Canonical NaN Bit Patterns

| Type | Canonical Quiet NaN | Infinity Bits | NaN Condition |
| ------ | --------------------- | --------------- | --------------- |
| Float16 | `0x7E00` | `0x7C00` | `(bits & 0x7FFF) > 0x7C00` |
| Float32 | `0x7FC00000` | `0x7F800000` | `(bits & 0x7FFFFFFF) > 0x7F800000` |
| Float64 | `0x7FF8000000000000` | `0x7FF0000000000000` | `(bits & 0x7FFFFFFFFFFFFFFF) > 0x7FF0000000000000` |

### SIMD Performance (float32, AVX-256 width 8)

| Metric | Scalar | SIMD | Improvement |
| -------- | -------- | ------ | ------------- |
| Iterations per 1M elements | ~1,000,000 | ~125,000 | ~8x fewer |
| Memory accesses per training step | 20M+ | 2.5M | ~8x reduction |
| float32 lanes / float64 lanes | — | 8 / 4 | — |

### Seed Convention

| Seed Value | Behavior |
| ------------ | ---------- |
| `seed = 0` | System randomness (non-reproducible) |
| `seed > 0` | Fixed PRNG seed (reproducible) |
| `seed = -1` | Alternative convention for system random |

### ASAN Build & Audit Commands

```bash
# ASAN build (catches bad-free / UAF immediately)
pixi run mojo build --sanitize address -g -I "$(pwd)" -I . -o /tmp/repro <file.mojo>
/tmp/repro

# Audit numeric-correctness bugs
grep -rn "bitcast\[Float32\]"                    # remaining UAF/byte-width risk
grep -n "_get_float64(i)" shared/core/shape.mojo # flat-index stride bug
grep -rn "_data + " examples/ shared/ | grep -E "\.(load|store)\("  # byte-pointer copy
grep -rn "seed: Int" ; grep -rn "random_seed("   # unwired seeds
strings .pixi/envs/default/lib/mojo/std.mojopkg | grep is_apple   # confirm guard API
```

### Test Strategy Summary

| Pattern | Minimum Tests |
| --------- | --------------- |
| Stride access | All element values on a transposed `arange` tensor |
| Bad-free | ASAN build of a 3-line slice-view reproducer |
| Dtype guard | float32/float64 rejection, int32/int64 acceptance, 2D float exemption |
| bfloat16 I/O | Re-enable skipped bf16 test; verify special-value invariants |
| Slice step | step=2 both dims, step=-1, step=3 (3D), step=1 explicit, no step |
| NaN hash | +qNaN vs -qNaN, payload variants, sNaN vs qNaN, shape/dtype sensitivity |
| Empty hash | `[0]` vs `[0,0]` vs `[0,1]` differ; same shape/dtype equal |
| Seed | Two calls with same seed identical; seed=0 non-reproducible |
| Byte-pointer copy | Sentinel `_set_float64(0,1.25)` -> `_get_float64(0)==1.25`; end-to-end loss matches reference (<0.2 pp/epoch) |
| SIMD | Sizes 1,7,13,33; first/last/boundary NaN placement; float32 + float64 |
| `__str__` | 1000 elements (no `...`), 1001 (`...` + boundary values present) |

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| ProjectOdyssey | PRs #3794, #4801, #4997 | ExTensor view semantics and parametric dtype migration |
| ProjectOdyssey | PRs #5097, #5175 | AnyTensor load/store API, 101+ bitcast patterns replaced |
| ProjectOdyssey | Issues #3391/#4083, PR #4079/#4865 | Non-contiguous stride access (as_contiguous + concatenate) |
| ProjectOdyssey | Issue #3686, PR #4769 | Confusion-matrix dtype guard |
| ProjectOdyssey | Issue #3300, PR #3903 | ExTensor bfloat16 I/O fix |
| ProjectOdyssey | Issue #4463, PR #4884 | Multi-dim slice step validation |
| ProjectOdyssey | Issue #3382, PR #4058 | NaN hash canonicalization |
| ProjectOdyssey | PR #2980 | Fix unused randn seed parameter |
| ProjectOdyssey | PR #5466 | 1-byte-per-element batch copy fix (lenet_emnist) |
| ProjectOdyssey | Issues #4910/#4911, PRs #5119/#5120 | SIMD-vectorized numeric safety + gradient clipping |
| ProjectOdyssey | Issue #3375, PR #4037 | ExTensor `__str__` NumPy-style truncation |
| ProjectOdyssey | Issue #3277, PR #3846 | DataLoader N-D batch slicing |
| ProjectOdyssey | Issue #3203, follow-up #3088 | Apple Silicon BF16 runtime guard |
| ProjectOdyssey | Issue #5564, PR #5577 | Block-quant bf16 accept-then-raise → clean outer-guard reject (verified-local) |
