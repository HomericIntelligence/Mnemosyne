# Notes: Timeout Hierarchy — One Arbiter Plus Margin Steps

Supporting evidence for `timeout-hierarchy-arbiter-margin-ladder`. Internal
identifiers, paths, image names, and issue numbers are generalized; the failure
shapes and decision rule are the artifacts.

## Failure shapes that motivated the entry

- **Invisible default as silent policy.** Queued requests died at exactly
  `60 s` of queue wait with an explicit status; the count was steady enough to
  be mistaken for a capacity signal. The launcher had never passed the flag,
  so the value came from the router image's own default — confirmed by reading
  the pinned image's router argument definitions (the default literal and the
  CLI flag sit in the same definition file). Nobody had reviewed `60 s` as a
  platform decision.
- **Literal matched to a default, inverted by an override.** A front-door
  guardian was hardcoded to `600 s` with a comment naming the proxy read
  *default*. The deployed context overrode the proxy read to `7200 s`, so the
  front aborted at ten minutes what proxy and router would still serve for
  two hours. The comment described intent; the code contradicted it.
- **Ties at the boundary.** Proxy read-idle and runner read both equaled the
  router total (`7200 == 7200`). At exactly the total, the caller races the
  router's own terminal answer; which stage reports is timing-defined, not
  design-defined.

## Why the margin came from the drain precedent

The platform already carried a drain default of `T + 60 s` — a bound sized to
let in-flight requests and teardown complete after a generation stops
accepting work. That is exactly the quantity one guardian hop needs
(propagation plus teardown), and it was already production-trusted. Reusing it:
one margin to teach, no second constant to retune, and the ladder reads as
`T, T+60, T+120, T+180`, which is inspectable at a glance in review.

## Flag-support verification shape

Before rendering a flag that never reached the process before, the flag's
existence was proven inside the pinned runtime artifact: list the image
contents without mounting (for squashfs, `unsquashfs -l`, then extract the one
argument-definition file), and confirm the flag and its default literal. This
replaces the optimistic assumption that a documented upstream flag exists in
the deployed build.

## Verification inventory for the change under evidence

Focused, not full-suite: the owning front-door module suite, renderer contract
cases for the new flag (presence when set, absence when unset), serialization
and limits cases for the policy model, plus lint, format, and type gates on
changed files. Two behavior tests that previously monkeypatched module
constants moved to an explicit creation-time override parameter — the seam the
main entry recommends.
