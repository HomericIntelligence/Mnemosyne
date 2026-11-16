---
name: image-launcher-absolute-path-preflight
description: "Prove a container image contains every absolute interpreter or binary path that a launcher names before a start rehearsal depends on it. Use when a renderer hard-codes a path inside an image, an image pin or version changes, or a front process is healthy while a backend component exits 127."
category: ci-cd
date: 2026-11-13
version: "1.0.0"
user-invocable: false
verification: verified-local
tags: [container, image, interpreter, entrypoint, start-rehearsal, digest, fail-closed, exit-127]
---

# Verify the Launcher Absolute Path Inside the Admitted Image

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-13 |
| **Objective** | Prove that a containerized component can start from an admitted image before a release gate depends on the start result. |
| **Outcome** | Successful after correction. A start rehearsal failed with exit `127` on an interpreter path that the admitted image did not contain. An image with the required layout produced a verified activation. |

## When to Use

- A renderer or launcher template names an interpreter, module runner, or binary by absolute path inside a container image.
- An image pass a digest or version check, and a first start or start rehearsal is the next evidence item.
- A component has a separate front process and backend process, and the front is healthy while the backend does not start.
- An image pin or image version changes, or a new image is admitted to a lane.
- A container step fails with exit `127` or a "No such file or directory" line for a path that the renderer produced.

## Verified Workflow

### Quick Reference

```bash
# 1. Read every absolute path that the launcher names.
# 2. List the admitted image read-only and require the exact path.
unsquashfs -l IMAGE.sqsh | grep -F '/opt/RUNTIME/bin/python'

# 3. A digest or version match is not content proof.
# 4. Start the real component and require a verified activation.
```

### Suggested Approach

1. Collect the absolute paths from the launcher or renderer, not from a run-time
   error. Include the interpreter, the module runner, and any helper binary.
2. Record the image digest and the version label for traceability. Do not treat
   either value as proof that the image contains a path.
3. List the image contents with a read-only tool. Require each named path to
   exist as a regular file and to be executable.
4. If a path is absent, stop before the start attempt. Build or admit an image
   with the required layout, or change the launcher under review. Do not change
   the image tag to imply a layout that the bytes do not have.
5. Run the real start. A container step that exits `127` is a missing path, not
   a slow start. Read the per-step log; it usually names the path in one line.
6. Require a verified activation of the backend component. A healthy front
   process, a successful health probe, or a running allocation does not prove
   that the backend started.
7. Keep the failing step log as evidence. It separates a missing image path
   from a policy, quota, or scheduler refusal.

A start rehearsal is the proof. Static render and CI cannot show that the image
contains the path that the launcher names.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Attempt 1 | Treated the admitted image digest and version label as proof that the launch path exists. | The launcher named an absolute interpreter path that the image did not contain. The backend step exited `127` while the front step was healthy. | Verify image contents, not only image identity. |
| Attempt 2 | Read only the rendered command and accepted it as correct. | The rendered path was syntactically valid and matched the launcher contract, but it did not exist in the admitted image. | A correct render does not prove a correct image. |
| Attempt 3 | Treated a pending activation as a slow start and waited. | The backend candidate was rejected and retried; waiting could not produce a verified activation. | Read the first failing step. A pending activation with a failed step is a failure. |

## Results & Parameters

### Configuration

```yaml
image_preflight:
  identity: record digest and version for traceability
  content_check: list the image and require each launcher absolute path
  start_check: require a verified backend activation
  failure_signal: container step exit 127 or "No such file or directory"
```

### Expected Output

- The image listing contains every absolute path that the launcher names.
- The backend start reports a verified activation.
- The front health probe passes only together with the verified activation.
- The start evidence names the image digest and the exact source revision.

## Verified On

| Project | Context | Details |
| --------- | --------- | ------- |
| Containerized control plane | Release start rehearsal on a development lane | One image failed the path check; a replacement image with the required layout passed. See [notes](image-launcher-absolute-path-preflight.notes.md). |

## References

- Related skill: [machine-local-container-artifact-validation-lane.md](machine-local-container-artifact-validation-lane.md)
- Related skill: [service-startup-precondition-bootstrap-deadlock.md](service-startup-precondition-bootstrap-deadlock.md)
- Related skill: [github-pr-review-head-bound-check-evidence.md](github-pr-review-head-bound-check-evidence.md)