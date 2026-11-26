# Input-Modality Refusal Attribution — Supporting Notes

These notes hold the privacy-safe evidence for the main entry. They do not add
rules.

## Observed Case

A coding client attached an image to a chat request. The serving deployment
answered with a refusal of this shape:

```text
Model only supports text input; received unsupported content type 'image_url'.
```

The client status line showed the model as available and showed the expected
524,288-token context. The failure named the content type only.

## Inspection Result

- The gateway request path parsed the body only to read the stream flag and the
  model, and to inject a usage option for streamed responses. It then sent the
  original bytes to the engine.
- The request path counted image parts in OpenAI, Responses, and Anthropic
  shapes. The count fed usage accounting. One model had an admission cap of one
  image per request because a multi-image request had crashed its engine
  earlier.
- The model registration had no vision encoder, no image processor, and no
  multimodal engine flag.
- The exact error text was not present in the gateway source or its vendored
  patches. The refusal came from the engine or its chat template.
- A search of the work tracker for image, vision, and multimodal items found
  only multi-image handling for one model family. No item covered models that
  accept no images.

## Decision Value

The case shows three traps:

1. A gateway that counts image parts looks like it validates image support. It
   does not.
2. A healthy model with the right context length still refuses an input
   modality. Availability is not capability.
3. A model-name check (for example, a cap on images per request for one model)
   is a special case. It is not a general modality capability.

## Limits

- The inspection was read-only. No gateway change, model change, or capability
  field was implemented or tested.
- The engine source that emits the refusal was not available for inspection.
  The attribution rests on the absence of the text in the gateway and its
  vendors, and on the unchanged request body.
- The recommended layers were selected from the repository contract and the
  observed behavior. Their operation under live traffic was not verified.