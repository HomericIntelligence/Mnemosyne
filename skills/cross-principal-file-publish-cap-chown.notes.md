# Notes: cross-principal-file-publish-cap-chown

Supporting evidence for the main entry. Generalized; session-specific
identifiers, paths, and tracker numbers are removed.

## Measured capability boundary

On the live lane, as the unprivileged publishing principal:

```text
creator uid/gid:  <service-uid> <service-uid>
chown to foreign uid:  EPERM (errno 1)
chgrp to own auxiliary group:  OK
CapEff:  0000000000000000
```

The kernel rule behind the observation: a process may change a file's group
to any group it belongs to, but an owner change to a different uid requires
`CAP_CHOWN` in the process's effective set (or root). An empty `CapEff`
therefore guarantees the EPERM for every foreign-owner request.

## The failure shape on the lane

- The publish step wrapped the `EPERM` into a typed error
  ("ownership transfer is unavailable"), and the worker mapped that class to
  a generic publish-failure cause. The generic label hid the specific call
  until the probe above ran.
- The claim (lease) taken before the publish was not released on that
  failure path, so the request id stayed blocked until manual removal by the
  service principal. The worker's own comment documented that a kept claim
  blocks a later request with the same id — the code knew the hazard and
  still only released on the success path.
- Every request on the lane came from a foreign owner, so the failure rate
  was 100% and no weights or results moved through the designed path.

## Why the suite stayed green

- The test module defined its principal as the effective uid
  (`UID = os.geteuid()`) and built every fixture's requester from that same
  constant, so the transfer under test was a self-chown.
- The suite contained a guard test that *refuses* a foreign requester on a
  different path (intent ownership), which shows the cross-principal case
  was considered — but only as a rejection, never as a required success.
- No mock covered the ownership boundary, so the kernel's capability check
  never appeared in tests.

## Wrong first patch, reverted

The first fix moved the transfer target to the service uid, with the claim
that the reader already required the service owner. Re-reading the reader
showed it compared the file owner against its requester argument, and a
guard test asserted foreign requesters are refused on intake. The patch
broke the guard and was reverted; the corrected diagnosis (design-level
options, not a one-line change) replaced it. Lesson recorded in the main
entry: read both predicates and the guard tests before patching a trust
boundary.

## Disposition evidence

- Intent search over the corpus found no entry covering the cross-uid
  chown constraint or the single-uid test blind spot; closest entries cover
  publication ordering and directory-repair scope, not the capability
  boundary.
- Privacy screen: generalized per the learning policy before this file was
  written.
