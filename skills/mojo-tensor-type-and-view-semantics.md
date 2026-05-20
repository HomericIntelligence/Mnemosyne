---
name: mojo-tensor-type-and-view-semantics
description: "Design and migrate Mojo tensor/ExTensor types with parametric dtypes,
  view semantics, stride-aware slices, and safe load/store APIs. Use when: (1)
  designing ExTensor/AnyTensor subscript assignment with compile-time dtype
  parameterization, (2) implementing zero-copy view semantics (transpose, slice,
  ravel) for stride-aware tensor access, (3) eliminating raw _data.bitcast UAF
  patterns via parametric load/store API, (4) inverting runtime-typed wrapper ops
  to Tensor[dtype] typed cores with AnyTensor dispatch, (5) fixing vacuous-loop
  bugs in broadcastability helpers or refactoring validate() to return tuple results."
category: architecture
date: 2026-05-19
version: "1.0.0"
user-invocable: false
history: mojo-tensor-type-and-view-semantics.history
tags:
  - mojo
  - tensor
  - extensor
  - anytensor
  - dtype
  - parametric
  - view-semantics
  - bitcast
  - uaf
  - strides
  - load-store
  - broadcasting
  - slice
  - transpose
---

# Mojo Tensor Type and View Semantics

Consolidated reference for ExTensor/AnyTensor compile-time dtype parameterization,
zero-copy view semantics, stride-aware element access, safe load/store APIs,
typed-core architecture, and companion tensor API patterns.

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-05-19 |
| **Objective** | Unified guide for Mojo tensor design: parametric dtype, view semantics, safe element access, typed-op inversion, and shape API patterns |
| **Outcome** | Merged from 7 skills: all ASAN/UAF errors resolved, zero-copy views working, typed-core architecture implemented (~6,500 lines across 20+ files) |
| **Mojo Version** | 0.26.1 |
| **Repository** | ProjectOdyssey |

## When to Use

- Designing ExTensor subscript assignment (`tensor[i] = val`) that works without casts (parametric dtype)
- Debugging "cannot implicitly convert" errors on ExTensor subscript assignment
- Implementing zero-copy tensor views: `transpose()`, `slice()`, `ravel()` on Mojo ExTensor
- Fixing element access bugs in non-contiguous (transposed/strided) tensors
- Eliminating raw `_data.bitcast[T]()` patterns that cause ASAP-destruction UAF
- Designing safe per-element and bulk-pointer API (`load[dtype]`, `store[dtype]`, `data_ptr[dtype]`)
- Migrating from runtime-typed (`var _dtype: DType`) to compile-time typed (`struct T[dtype: DType]`) ops
- Adding typed-core 3-layer architecture: public API → dtype dispatch → `Tensor[dtype]` core
- Fixing a `are_shapes_broadcastable` helper that silently returns `True` for fewer-dim targets
- Refactoring `validate()` to return `Tuple[Float64, Float64]` instead of discarding accuracy

## Verified Workflow

### Quick Reference

```text
1. Parametric ExTensor dtype
   ExTensor[DType.float32] — __getitem__ returns Scalar[dtype], SIMD-like assignment
   Short-term: Float32(expr), .set(i, val), ._set_float64(i, val) for parallelize[]

2. View semantics (zero-copy)
   tensor.view_with_strides(new_shape, new_strides)  — base primitive for all views
   tensor._nd_index_to_flat_offset(linear_idx)       — byte offset for non-contiguous

3. Stride-aware accessor pattern
   if self.is_contiguous():
       offset = index * self._get_dtype_size()
   else:
       offset = self._nd_index_to_flat_offset(index)

4. Safe load/store API (no raw bitcast)
   tensor.load[DType.float32](index)
   tensor.store[DType.float32](index, Float32(val))
   tensor.data_ptr[DType.float32]()  — bulk pointer (caller keeps tensor alive)

5. Typed-core 3-layer architecture
   Layer 1: AnyTensor public API
   Layer 2: dtype_to_ordinal() dispatch
   Layer 3: fn _add_typed[dt: DType](a: Tensor[dt], b: Tensor[dt]) -> Tensor[dt]

6. Broadcasting guard
   if ndim2 < ndim1: return False  — first check in are_shapes_broadcastable

7. Tuple return from validate()
   fn validate(...) raises -> Tuple[Float64, Float64]  — (loss, accuracy)
```

### Step 1: Parametric DType Migration (ExTensor)

Mojo's `obj[i] = val` does **not** call `__setitem__`. It calls `__getitem__(i)` to get
an lvalue reference and then assigns to that lvalue. This means `__setitem__` overloads
are **dead code** for subscript assignment syntax.

ExTensor stores `_dtype` as `var _dtype: DType` (runtime). `__getitem__` must return a
fixed type (currently `Float32`), so all RHS values in `tensor[i] = val` must be `Float32`.

**Solution — parametric struct:**

```mojo
struct ExTensor[dtype: DType]:
    var _data: UnsafePointer[UInt8, origin=MutAnyOrigin]
    var _shape: List[Int]
    var _strides: List[Int]

    fn __getitem__(self, index: Int) raises -> Scalar[Self.dtype]:
        return self._data.bitcast[Scalar[Self.dtype]]()[resolved_index]
```

**Short-term workaround (pre-migration):**

```text
Pattern 1: result[i] = Float32(expr)         — raising contexts, same-type
Pattern 2: result.set(i, expr)               — non-Float32 values
Pattern 3: result._set_float64(i, expr)      — parallelize[] closures (can't raise)
```

Migration scope: ~100+ functions across all modules. Every signature changes from
`fn relu(tensor: ExTensor)` to `fn relu[dtype: DType](tensor: ExTensor[dtype])`.

### Step 2: View Semantics — Core Primitives

Add `_nd_index_to_flat_offset` after `is_contiguous()`:

```mojo
fn _nd_index_to_flat_offset(self, linear_idx: Int) -> Int:
    var dtype_size = self._get_dtype_size()
    var ndim = len(self._shape)
    var remaining = linear_idx
    var element_offset = 0
    for i in range(ndim - 1, -1, -1):
        var coord = remaining % self._shape[i]
        remaining //= self._shape[i]
        element_offset += coord * self._strides[i]
    return element_offset * dtype_size
```

Add `view_with_strides` as the shared primitive for all zero-copy view creation:

```mojo
fn view_with_strides(
    self, new_shape: List[Int], new_strides: List[Int]
) -> ExTensor:
    var result = self.copy()      # __copyinit__ increments refcount
    result._is_view = True
    result._shape = List[Int]()
    for i in range(len(new_shape)):
        result._shape.append(new_shape[i])
    result._strides = List[Int]()
    for i in range(len(new_strides)):
        result._strides.append(new_strides[i])
    var n = 1
    for i in range(len(new_shape)):
        n *= new_shape[i]
    result._numel = n
    return result^
```

**Refcount safety**: `var result = self` triggers `__copyinit__` (refcount++).
Mutating `result._shape`, `result._strides` in place keeps refcount at N+1.
`return result^` moves without another increment.

### Step 3: Fix All Accessor Methods

For `_get_float32`, `_set_float32`, `_get_float64`, `_set_float64`, `_get_int64`,
`_set_int64` — replace `var offset = index * dtype_size` with:

```mojo
var offset: Int
if self.is_contiguous():
    offset = index * self._get_dtype_size()
else:
    offset = self._nd_index_to_flat_offset(index)
```

The `is_contiguous()` fast-path preserves performance for the common case.

### Step 4: Implement Transpose and Slice as Views

```mojo
fn transpose(tensor: ExTensor, perm: Optional[List[Int]] = None) -> ExTensor:
    # ... resolve perm ...
    var result_shape = List[Int](capacity=ndim)
    for axis in resolved_perm:
        result_shape.append(input_shape[axis])
    var result_strides = List[Int](capacity=ndim)
    for axis in resolved_perm:
        result_strides.append(tensor._strides[axis])
    return tensor.view_with_strides(result_shape, result_strides)

fn slice(self, axis: Int, start: Int, end: Int) raises -> ExTensor:
    var new_shape = self._shape.copy()   # REQUIRED: always .copy(), not =
    new_shape[axis] = end - start
    var result = self.view_with_strides(new_shape, self._strides)
    var offset_bytes = start * self._strides[axis] * self._get_dtype_size()
    result._data = self._data + offset_bytes
    return result^
```

Contiguify inputs before flat-buffer kernels (e.g. matmul):

```mojo
var a_cont = a if a.is_contiguous() else as_contiguous(a)
var b_cont = b if b.is_contiguous() else as_contiguous(b)
```

### Step 5: Safe Load/Store API (AnyTensor)

Insert after the existing `_set_int32` method in `any_tensor.mojo`:

```mojo
@always_inline
fn load[dtype: DType](self, index: Int) -> Scalar[dtype]:
    debug_assert(self._dtype == dtype, "AnyTensor.load[dtype] mismatch")
    return self._data.bitcast[Scalar[dtype]]()[index]

@always_inline
fn store[dtype: DType](self, index: Int, value: Scalar[dtype]):
    debug_assert(self._dtype == dtype, "AnyTensor.store[dtype] mismatch")
    self._data.bitcast[Scalar[dtype]]()[index] = value

@always_inline
fn data_ptr[dtype: DType](self) -> UnsafePointer[Scalar[dtype], origin=MutAnyOrigin]:
    debug_assert(self._dtype == dtype, "AnyTensor.data_ptr[dtype] mismatch")
    return self._data.bitcast[Scalar[dtype]]()
```

**Key design**: `self` not `mut self` (MutAnyOrigin allows writes). No bounds check
(matches existing `_get_float32` for inner loop performance). `debug_assert` catches dtype
mismatches in debug, compiles away in release.

Migrate UAF patterns:

```mojo
# BEFORE (UAF risk):
var loss_value = Float64(loss_tensor._data.bitcast[Float32]()[0])

# AFTER (safe):
var loss_value = Float64(loss_tensor.load[DType.float32](0))
```

After migration, grep the ENTIRE codebase: `grep -rn "bitcast\[Float32\]" shared/`.

### Step 6: Typed-Core 3-Layer Architecture

```text
shared/base/                    <- Layer 0: Zero tensor dependencies (stdlib only)
shared/tensor/                  <- Layer 1: struct Tensor[dtype: DType]
shared/core/                    <- Layer 2: Typed ops + AnyTensor dispatch
  any_tensor.mojo                   struct AnyTensor (runtime-typed)
  arithmetic.mojo                   add[dt]() typed core + ordinal dispatch
  elementwise.mojo                  exp[dt](), relu[dt](), ...
```

Typed core pattern:

```mojo
fn _add_typed[dt: DType](a: Tensor[dt], b: Tensor[dt]) raises -> Tensor[dt]:
    var result_shape = broadcast_shapes(a.shape(), b.shape())
    var result = Tensor[dt](result_shape)
    # ... broadcasting index logic, direct _data pointer access ...
    return result^
```

Ordinal dispatch:

```mojo
fn add(a: AnyTensor, b: AnyTensor) raises -> AnyTensor:
    var ordinal = dtype_to_ordinal(a._dtype)
    if ordinal == DTYPE_FLOAT32:
        return _add_typed[DType.float32](
            a.as_tensor[DType.float32](), b.as_tensor[DType.float32]()
        ).as_any()
    # ... remaining dtypes ...
```

AnyTensor delegation with local-scope imports (avoids circular deps):

```mojo
fn __iadd__(mut self, other: Self) raises:
    from shared.core.arithmetic import add  # Local import — no circular dep
    self = add(self, other)
```

**PR sequence**: Extract `shared/base/` first, then typed ops in parallel PRs (arithmetic,
elementwise, matrix, shape), then AnyTensor delegation last (highest conflict risk).

### Step 7: Broadcasting ndim Guard

Add as the **first** check in `are_shapes_broadcastable`, before any other logic:

```mojo
fn are_shapes_broadcastable(shape1: List[Int], shape2: List[Int]) -> Bool:
    var ndim1 = len(shape1)
    var ndim2 = len(shape2)

    # Broadcasting cannot reduce the number of dimensions
    if ndim2 < ndim1:
        return False

    var max_ndim = max(ndim1, ndim2)
    # ... rest of loop unchanged ...
```

Update docstring examples: `[3,4,5] vs [4,5] -> False` (not True).
If a caller (e.g. `broadcast_to`) has its own guard that raises a descriptive error,
add a comment noting both guards exist for different UX reasons.

### Step 8: Tuple Return from validate()

```mojo
fn validate(
    model_forward: fn (ExTensor) raises -> ExTensor,
    compute_loss: fn (ExTensor, ExTensor) raises -> ExTensor,
    mut val_loader: DataLoader,
    compute_accuracy: Bool = True,
    compute_confusion: Bool = False,
    num_classes: Int = 10,
) raises -> Tuple[Float64, Float64]:
    """Returns: Tuple of (avg_loss, accuracy). accuracy=0.0 when compute_accuracy=False."""
    var avg_loss = total_loss / Float64(num_batches)
    var accuracy = Float64(0.0)
    if compute_accuracy:
        accuracy = accuracy_metric.compute()
    return (avg_loss, accuracy)
```

Caller destructuring (all forms work in Mojo v0.26.1+):

```mojo
var result = validate(...)        # result[0], result[1]
var (loss, acc) = validate(...)   # full destructuring
var (loss, _) = validate(...)     # discard unused component
```

This eliminates the second full data-loader pass: `3×` → `2×` forward passes per batch.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Add `__setitem__` overloads | Added 9 overloads for Float16, Int, Int8, etc. | Mojo never dispatches `obj[i]=val` to `__setitem__` — dead code | `__setitem__` is not called via subscript assignment in Mojo |
| Change `__getitem__` to return Float64 | Wider type to accept more assignments | Float32 can't implicitly convert to Float64 in Mojo, broke 108 call sites | Mojo doesn't allow implicit widening between float types |
| Proxy/reference return type | Return a proxy struct from `__getitem__` | "expression must be mutable in assignment" — Mojo ownership prevents mutable references | Can't return mutable references to internal data in Mojo |
| Route `set()` through Float64 | All `set()` overloads called `__setitem__(index, Float64(value))` | Float32 -> Float64 -> Float32 round-trip changes values (3.14159 -> 3.141590118408203) | Never introduce precision-losing conversion round-trips |
| Sub-agents for bulk fixes (round 1) | Launched 8 parallel agents to fix all files | Agents only fixed ~60% of errors, missed Float16 paths and arithmetic mismatches | Sub-agents need explicit error line numbers and all categories enumerated |
| `Float32()` casts everywhere | Changed `result[i] = Float64(x)` to `result[i] = Float32(x)` | "cannot call function that may raise" in `@parameter fn` closures for `parallelize[]` | Float32() constructor raises; can't use in non-raising contexts |
| `var new_shape = self._shape` in slice() | Direct assignment to copy shape | Mojo `List[Int]` is not `ImplicitlyCopyable`; compiler error | Always use `.copy()` when assigning a `List[Int]` field to a new variable |
| Docstrings starting with method name | `"""view_with_strides returns..."""` | Mojo compiler: "doc string summary should begin with a capital letter or non-alpha character" | Prefix with `The`, `A`, `An`, or a non-alpha character |
| Only fixing slice() without fixing accessor methods | Assumed `view_with_strides` alone was sufficient | Transposed-view slices returned wrong values because `_get_float32` still used `index * dtype_size` | Non-contiguous view correctness requires fixing ALL element accessor methods |
| Raw buffer access in tests | `result._data.bitcast[Float32]()[i]` to read transposed view | Reads underlying buffer in non-permuted order, gives wrong values | Always use `_get_float32(i)` for stride-aware access in view tests |
| Named `get[dtype]`/`set[dtype]` for safe API | Used get/set as method names on AnyTensor | Conflicts with existing 12 `set()` overloads on AnyTensor | Use `load`/`store` (LLVM/SIMD terminology) to avoid name conflicts |
| Both agents adding load/store/data_ptr independently | Parallel sub-agents both added the API to `any_tensor.mojo` | Cherry-pick created duplicate blocks with conflicting signatures | When agents modify the same file, one adds API and the other only uses it |
| `data_ptr` without `origin=MutAnyOrigin` | Returned `UnsafePointer[Scalar[dtype]]` | Compile error — return type doesn't match `_data.bitcast` which has `origin=MutAnyOrigin` | Always include `origin=MutAnyOrigin` on returned pointers from AnyTensor |
| Pooling bitcast[Float32] on float16 tensors | `x._data.bitcast[Float32]()[in_idx]` in pooling functions | Float16 = 2 bytes but bitcast[Float32] reads 4 bytes — wrong offsets, garbage NaN/Inf | Use `_get_float64/_set_float64` which handles all dtypes via proper byte sizing |
| Missed pooling module in bitcast migration | Migrated shared/training/ (101 patterns) but left pooling.mojo | Pooling crash: "max pooling output contains NaN or Inf" on float16 tensors | After any bitcast migration, grep the ENTIRE codebase for remaining patterns |
| Top-level circular import in any_tensor.mojo | `from shared.core.arithmetic import add` at module level | Circular import: any_tensor.mojo <- arithmetic.mojo <- any_tensor.mojo | Use local-scope imports inside method bodies (deferred to call time) |
| Auto-parameterization for return types | `fn relu(t: Tensor) -> Tensor` (no explicit `[dt: DType]`) | Mojo error: "failed to infer parameter 'dtype'" for return types | All functions returning Tensor must use explicit `[dt: DType]` parameter |
| Single-PR approach for all typed op inversions | Bundle all typed ops + AnyTensor delegation in one PR | Too many merge conflicts when parallel agents work on overlapping files | Split by operation category with separate PRs; AnyTensor delegation last |
| He init with uniform weights in test | `full(shape, sqrt(2/fan_in))` for all-same weights | Exponential growth: gain per layer = `sqrt(2*fan_in)` >> 1.0 through 13 VGG16 layers | He init assumes random (cancellation); uniform weights need `1/fan_in` for unit gain |
| Fix broadcastability only in `broadcast_to` caller | Original bug fix added guard only to `broadcast_to` | Other callers of `are_shapes_broadcastable` could still get silently wrong `True` | Guards belong in the helper, not only in one caller |
| Returning named struct from validate() | Considered creating `ValidationResult` struct | Adds unnecessary type complexity for a 2-value return | Prefer Tuple for small fixed-arity returns |

## Results & Parameters

### Mojo Subscript Assignment Key Facts

```text
- obj[i] = val uses __getitem__ lvalue, NOT __setitem__
- __setitem__ overloads are dead code for subscript syntax
- No implicit conversion between float types (Float16/32/64)
- FloatLiteral and IntLiteral implicitly convert to any Scalar[dtype]
- Parametric dtype (compile-time) is required for SIMD-like subscript behavior
- Float32 -> Float64 -> Float32 round-trip is NOT lossless for all values
```

### Error Distribution (Pre-Fix, ExTensor Parametric Migration)

```text
267 errors: cannot implicitly convert 'Float64' to 'Float32'
 24 errors: cannot implicitly convert 'Float16' to 'Float32'
 16 errors: invalid call to '__add__' (Float64/Float32 mismatch)
  6 errors: cannot implicitly convert 'Int64' to 'Float32'
```

### load/store API Design

```yaml
load[dtype: DType](self, index: Int) -> Scalar[dtype]
store[dtype: DType](self, index: Int, value: Scalar[dtype])
data_ptr[dtype: DType](self) -> UnsafePointer[Scalar[dtype], origin=MutAnyOrigin]
inline: "@always_inline"
bounds_check: "none (caller responsible)"
dtype_check: "debug_assert only (compiles away in release)"
self_mutability: "self (not mut self) — MutAnyOrigin allows writes"
```

### Migration Statistics (Bitcast UAF Elimination)

```yaml
training_module:
  files_modified: 12
  bitcast_patterns_replaced: 101+
  asan_errors_before: "bad-free + heap-use-after-free"
  asan_errors_after: 0
pooling_module:
  file: "shared/core/pooling.mojo"
  functions_fixed: 6
  root_cause: "Float16 = 2 bytes; bitcast[Float32] reads 4 bytes at wrong offsets"
broader_codebase:
  shared_core_remaining: ~389 patterns (future PRs)
  tests_remaining: ~2458 patterns (future PRs)
```

### Uniform Weight Scaling (Fix for VGG16 Test Overflow)

```yaml
random_he_init: "sqrt(2 / fan_in)"      # For random normal weights
uniform_scaling: "1.0 / fan_in"          # For all-same uniform weights (full())
gain_per_layer_uniform_with_he: "sqrt(2 * fan_in) >> 1.0  # OVERFLOW"
gain_per_layer_uniform_correct: "1.0 (stable)"
```

### Typed-Op Inversion: PR Sequence and Scale

```yaml
pr_sequence:
  - "shared/base/ extraction (~250 lines) — break circular imports"
  - "Arithmetic typed ops (~1,000 lines)"
  - "Elementwise + activation (~1,500 lines, parallelizable)"
  - "Matrix + reduction (~1,300 lines, parallelizable)"
  - "Shape + comparison + remaining (~1,200 lines)"
  - "AnyTensor delegation (~500 lines) — LAST, highest conflict risk"
  - "Audit minor fixes (~100 lines)"
  - "Tests (51 functions, ~600 lines)"
total_lines: "~6,450"
supported_dtypes: [float16, float32, float64, int8, int16, int32, int64, uint8, uint16, uint32, uint64]
circular_import_fix: "local-scope imports inside method bodies"
```

### ASAN Verification Command

```bash
pixi run mojo build --sanitize address -g -I "$(pwd)" -I . \
    -o /tmp/test_asan <test_file.mojo>
/tmp/test_asan
# Expected: all tests pass, zero UAF/bad-free errors
```

### validate() Performance Impact

| Scenario | Before | After |
| ---------- | -------- | ------- |
| `compute_accuracy=True` | 3× forward passes per batch | 2× forward passes per batch |
| `compute_accuracy=False` | 2× forward passes per batch | 2× forward passes per batch (unchanged) |

### Test Commands

```bash
just test-group "tests/shared/core" "test_extensor_slicing_view_strides.mojo"
just test-group "tests/shared/core" "test_extensor_slicing_view.mojo"
just test-group "tests/shared/core" "test_broadcasting_part5.mojo"
just test-mojo  # full typed-op inversion suite
```

### GitHub References

```text
ExTensor dtype migration:     ProjectOdyssey PR #4997, Issue #4998
ExTensor view semantics:      ProjectOdyssey PR #3794, Issue #3236
ExTensor stride slice:        ProjectOdyssey PR #4801, Issue #3799
AnyTensor load/store API:     ProjectOdyssey PRs #5097, #5175
Typed-op inversion (8 PRs):   ProjectOdyssey PRs #5030–#5035, #5049–#5050, ADR-012
Broadcasting ndim guard:      ProjectOdyssey PR #4816, Issue #3859
validate() tuple return:      ProjectOdyssey PR #4895, Issue #3683
```

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| ProjectOdyssey | PRs #3794, #4801, #4997 | ExTensor view semantics and dtype migration |
| ProjectOdyssey | PRs #5097, #5175 | AnyTensor load/store API, 101+ bitcast patterns replaced |
| ProjectOdyssey | PRs #5030–#5035, #5049–#5050 | 8-PR typed-op inversion, ~6,450 lines, ADR-012 |
| ProjectOdyssey | PR #4816 | Broadcasting ndim guard, 9 tests |
| ProjectOdyssey | PR #4895 | validate() tuple return, 3×→2× forward pass reduction |
