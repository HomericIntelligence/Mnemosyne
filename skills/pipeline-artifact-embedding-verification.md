---
name: pipeline-artifact-embedding-verification
license: BSD-3-Clause
description: "Verify that a pipeline keeps embedded parts when it assembles an artifact with string substitution and embedding; use when a generator runs green but figures, images, or sections are silently missing, or when a byte-level scan of a compressed container claims absence."
category: debugging
date: 2026-10-23
version: "1.0.0"
user-invocable: false
verification: verified-local
tags: [generated-artifacts, string-substitution, container-formats, verification, test-assertions, automation]
---

# Pipeline Artifact Embedding Verification

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-10-23 |
| **Objective** | Find why every figure was missing from a report pipeline PDF output, and keep the defect found by a regression test |
| **Outcome** | ✅ Success — a one-character class defect in a regex replacement string had corrupted every embedded reference; a substitution-boundary test and loader instrumentation exposed it |
| **Verification** | verified-local (unit tests plus artifact size and loader-call evidence) |

## When to Use

- A pipeline builds an artifact (document, PDF, archive, image) from parts: templates, string substitutions, and embedded files.
- The generator exits with success, but consumers report that figures, images, or sections are missing.
- A change to string or regex replacement code produces references that a second system resolves: file paths, URLs, or object names.
- You want to prove that content is absent or present inside a container that has compressed or encoded members.
- A first "fix" changed nothing measurable. That is a signal that the diagnosis evidence could not tell the two states apart.

## Verified Workflow

### Quick Reference

```python
# ❌ WRONG: the raw replacement keeps the backslash; the output path ends in `png\"` and resolves to nothing
html = re.sub(r'(src="assets/[^"]+)\.svg"', r"\1.png\"", html)

# ✅ CORRECT: quote the raw literal with the other quote character so no escape is necessary
html = re.sub(r'(src="assets/[^"]+)\.svg"', r'\1.png"', html)

# ✅ AND pin the boundary with an exact-output unit test
def test_refs():
    out = rewrite(figure_html)
    assert 'src="assets/fig01.png"' in out
    assert "\\" not in out  # no stray escape can ride through
    assert ".svg" not in out
```

```python
# ❌ NON-DISCRIMINATING: count signature bytes in a compressed container
data.count(b"/Subtype /Image")  # 0 matches "missing" AND "embedded with different encoding"

# ✅ DISCRIMINATING probes (one is enough; two are proof):
# 1. Instrument the loader that the renderer calls (spy on open)
# 2. Decode the compressed object streams, then scan
# 3. Size-delta sanity: embedding N known inputs must move the artifact by about their (re)compressed size
```

### Detailed Steps

#### Step 1: Treat every transform boundary as lossy until proven

A string substitution that feeds an external resolver (filesystem, URL parser, container embedder) can corrupt its output with no exception. In Python `re.sub`, the replacement string processes escapes: a raw literal that ends with an escaped quote, `r"...\""`, keeps the backslash in the value. The corrupted path then fails to resolve downstream, and the embedder drops the part silently.

Write a unit test that asserts the exact output string of the transform, including the delimiter characters. Do not assert only that the call completes.

#### Step 2: Verify absence claims with a format-aware probe

A byte-pattern count over a compressed or encoded container is non-discriminating: zero is compatible with "part is absent" and with "part is present but encoded differently". Before you accept an absence diagnosis, use a probe that understands the format:

1. Instrument the decoder or loader that the build calls, and count its invocations.
2. Decode the container members (for example, inflate each stream), then scan the decoded content.
3. Compare artifact size before and after a change; embedded parts move the size by approximately their (re)compressed total.

If the probe still cannot separate the two states, upgrade the probe. Do not patch the pipeline from non-discriminating evidence.

#### Step 3: Prove presence after the fix with the same class of probe

Exit-code success is not content evidence. After a fix, show presence in the final artifact, not only in intermediate strings: loader calls, decoded-stream content, or a size delta consistent with the embedded inputs.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| 1 | Counted image-signature bytes in raw and decompressed PDF streams to decide whether figures were embedded | The count was zero in both the broken and the working artifact, because the writer encodes the image dictionaries in a form the pattern does not match | A scan that gives the same result in both states cannot support a diagnosis; build a probe that separates the states before you act on it |
| 2 | Changed the base-URL construction of the HTML-to-PDF step because the byte scan suggested relative image paths failed | The change was behavior-neutral; both path forms resolved, and the real defect was in the substitution output | Non-discriminating evidence invites patches in the wrong layer; verify the claim against the exact string the next system receives |
| 3 | Trusted run success and a plausible file size as evidence that figures were embedded | A replacement-string escape had corrupted every figure reference in every build for weeks; the PDF was a valid document with zero figures | Success of the build is not content evidence; pin every transform boundary with an exact-output assertion and verify presence in the final artifact |

## Results & Parameters

- **Exact-output test pattern**: assert the full rendered reference (with its quotes), assert the absence of the escape character, and assert the old form is gone. Three assertions separate correct, corrupted, and un-transformed output.
- **Loader spy pattern**: wrap the decoder entry point (for example `PIL.Image.open`) with a counter before the build runs; the count must equal the number of inputs. This works with any renderer that routes embedding through one loader.
- **Size-delta pattern**: `new_size - old_size` should be about the sum of recompressed inputs. A 17-figure report moved from ≈44 KB to ≈949 KB when the embedding started to work; a flat size across a "fix" means nothing was embedded.
- **Related guidance**: when generator inputs or generator code change, re-derive downstream artifacts with the final code rather than reusing them; see `generated-artifacts-stale-after-input-change-pinned-regeneration`.
