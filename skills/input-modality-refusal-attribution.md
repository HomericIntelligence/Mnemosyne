---
name: input-modality-refusal-attribution
description: "Attribute a model input-modality refusal to the serving engine before you change a gateway, proxy, or client. Use when: (1) a client receives a 'model only supports text input' or unsupported content-type error for an image part, (2) a gateway forwards text and image requests unchanged and the engine refuses one, (3) you must choose between a vision-capable model, a declared modality capability with admission refusal, routing by modality, or content conversion."
category: debugging
date: 2026-11-26
version: "1.0.0"
user-invocable: false
tags: [inference, gateway, proxy, modality, image-input, capability, error-attribution, request-validation, text-only-model]
---

# Input-Modality Refusal Attribution

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-26 |
| **Objective** | Choose the correct layer to add image support, or to return a clear refusal, when a text-only model receives an image part. |
| **Outcome** | Operational. One read-only investigation separated the gateway, the model registration, and the engine as possible sources of the refusal. |

## When to Use

- A chat request contains an image part and the response says that the model supports text input only, or that the content type is unsupported.
- A gateway or proxy is a transparent body forwarder, but an operator asks it to "support images".
- A model registration declares no vision encoder and still receives image traffic.
- A review proposes to strip, replace, or rewrite image parts in the proxy.

## Verified Workflow

### Quick Reference

Find the emitter of the refusal first. A transparent gateway does not create a modality refusal.

```text
1. Capture the failing request and the response source.
2. Read the gateway request path. Does it parse content parts, or forward the bytes?
3. Read the model registration. Is a vision encoder configured?
4. Select the support layer from that evidence.
5. Never remove content parts without an explicit, recorded policy.
```

### Suggested Approach

- **Attribute before you modify.** Search the gateway source and its vendored dependencies for the error text. If the text is absent, the refusal comes from the engine or the model template. Change the layer that owns the decision.
- **Separate metering from capability.** A gateway can count image parts for usage, tokens, or per-model limits without validating the model's input modalities. A counter is not a capability check. Read the request path to confirm which one exists.
- **Read the model registration.** A checkpoint that has no vision tower, no image processor, and no multimodal engine flags is text-only. A model that is up with the expected context length can still refuse a content type, so a healthy status line does not prove input support.
- **Select the layer by the required outcome:**
  1. Serve a vision-capable model. This is the only path that accepts images end to end.
  2. Declare the supported input modalities for each model and refuse at admission. The refusal is clear and fail-closed, but image support does not exist.
  3. Route by input modality to a model that supports the part.
  4. Convert the content in the client. Use OCR or a vision model to make text, and send the text. Do this only when an explicit policy accepts the loss.
- **Give the declaration an enforcement reader.** A modality field that no code reads is inert. Add the reader in the same change, and test with the exact content part that fails.
- **Keep a request refusal separate from component health.** A refused request is allowed to fail closed. The gateway process must stay up, and the refusal must not stop the model or the lane.
- **Do not strip silently.** Removal of an image part changes the user's input. Without an explicit policy and a signal to the client, the answer looks correct but ignores the image.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Treat the gateway as the emitter | Searched the gateway and its vendored code for a way to accept image parts. | The error text was not in the gateway or its vendors. The gateway forwarded the body unchanged, and the engine refused it. | Find the emitter before you change a layer. |
| Treat the refusal as a capacity or admission fault | Checked replicas, queue state, and capacity. | The model was up with the expected context length, and the error named the content type. | Read the error class. A content-type error is not a load error. |
| Look for existing work that handles text-only models | Searched the work tracker for image, vision, and multimodal items. | The open work covered multiple images on one model, not models that accept no images. | Do not infer in-flight work from a related error. Confirm the scope. |
| Declare the capability without a reader | Considered a registration field as the full fix. | A declaration that no request path reads changes no behavior. | Add the enforcement reader and a test in the same change. |
| Strip image parts to make the request pass | Considered proxy-side removal of the image parts. | The model would answer without the image content, and the client could not tell. | Do not remove content silently. |

## Results & Parameters

### Configuration

Declare the accepted input modalities on the model record, and enforce the set at admission:

```yaml
model: example-text-only-model
input_modalities: [text]
```

```json
{"error": "example-text-only-model supports text input only; remove the image parts or use a vision-capable model"}
```

### Expected Output

- A text-only model returns a `400`-class error that names the model and the accepted modalities.
- The error names the unsupported content type or the content position when the request parser can identify it.
- The gateway process and the model replica stay healthy.
- A vision-capable model or a routed request accepts the same content without a gateway change.

## Verified On

| Project | Context | Details |
| --------- | --------- | ------- |
| An inference gateway and a text-only model deployment | Read-only inspection of the gateway request path, the model registration, and a live client refusal | See [notes](input-modality-refusal-attribution.notes.md). |

## References

- [Runtime checks degrade, they do not stop](runtime-component-checks-degrade-not-stop.md) — the request-refusal and component-health boundary.
- [Inference gateway backlog with low engine load](inference-gateway-backlog-low-engine-load-diagnosis.md) — the separate capacity and admission error class.