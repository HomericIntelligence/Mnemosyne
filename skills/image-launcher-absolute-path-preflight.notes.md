# Notes: image-launcher-absolute-path-preflight

Supporting evidence for [the skill](image-launcher-absolute-path-preflight.md).
All names, hosts, and paths are generalized.

## Session shape

- A release candidate changed a containerized launcher to name an interpreter
  inside a runtime virtual environment by absolute path.
- The lane already pinned an admitted image. Its digest and version were valid.
- A start rehearsal submitted a real allocation on a development lane.

## Measurements

Image A (admitted, digest verified):

- The runtime package was installed in the system Python site-packages.
- The image contained no runtime virtual environment at the path the launcher
  named.
- The listing command returned zero matches for the launcher path.

First start attempt:

- The front step logged `gateway front child pid=... is healthy`.
- The backend step logged:
  - `<absolute interpreter path>: No such file or directory`
  - `Exited with exit code 127`
- The gateway logged `candidate rejected: process readiness failed` and retried.
- The start tool reported `activation: pending` and the rehearsal failed.
- The submitted job was stopped by the start tool. No other job was stopped.

Image B (admitted after the correction):

- The image contains the runtime virtual environment and the exact interpreter
  path the launcher names.
- The same source revision with Image B produced `activation: verified` and a
  healthy front probe.
- The start tool exited `0` and the receipt recorded a pass.

## Decision boundary

- A digest match proves the bytes that were admitted. It does not prove that
  those bytes contain a path that a new launcher names.
- A healthy front process proves only the front process. The backend needs its
  own verified activation.
- A pending activation with a failed container step is a failure. Do not wait
  for it, and do not convert it to a pass.

## Recovery order

1. Read the first failing step log.
2. Compare each launcher absolute path with the image listing.
3. If a path is absent, stop. Build or admit an image with the required layout,
   or change the launcher under review.
4. Re-run the start after the image or launcher changes. Require a verified
   activation.

## Related evidence

- The start receipt and step logs are the durable record.
- Keep the failed attempt as evidence. Do not edit or delete it.