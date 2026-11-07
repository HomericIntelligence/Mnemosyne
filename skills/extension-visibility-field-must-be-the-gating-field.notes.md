# Notes: extension-visibility-field-must-be-the-gating-field

Supporting evidence for [extension-visibility-field-must-be-the-gating-field](extension-visibility-field-must-be-the-gating-field.md).
Current rules stay in the main skill. This file holds the execution evidence.

## Privacy check

This file is a generalized record. It holds no person, account, organization,
repository, host, path, issue, or product identifier. It holds no proprietary
source. The commands are the generic form of the commands that were run.

## Provenance

- Lesson date: 2026-11-06.
- Source: one agent session that repaired a provider extension for a
  self-hosted model gateway. A model that read as down was disabled in the
  extension output, then enabled, then still hidden by the host.
- Review evidence: two independent review rounds. The first round gave a
  favorable verdict and a documentation finding. The second round found the
  host filter. The author then proved the filter by execution.

## Host filter evidence

The installed host package held these filters in its bundled code:

```text
.find((f)=> ... && d.status!=="deprecated")
.filter((R)=> R.status!=="deprecated" && <other-predicate>(R))
.filter((ee)=> ee.status!=="deprecated")
```

The other predicate in the second filter was a minified helper that repeats
with different bodies in the same bundle. Reading the filter text was enough
to form a hypothesis. It was not enough to close the finding.

## Execution proof

Two entries were published to the host through a stub provider. They differed
only in the state word. Both had the config switch set to true.

```text
state word = visible, config switch = true   -> entry listed
state word = hidden,  config switch = true   -> entry not listed
```

The probe process was:

1. Create an isolated home with a single host configuration file.
2. Write one provider block with the two entries and a local endpoint that does
   not answer. The list command does not contact the endpoint.
3. Run the host list command with `env -i`, the isolated `HOME` and config
   directory, and a bounded timeout.
4. Remove the isolated home.

## Failure detail: managed service port

The first two probe runs stopped before they listed any entry. The host starts a
managed service and read its port from its own state directory. The port was
already in use by another host process. The environment variable and the
configuration key did not change the port. The host command that changes the
port in its own state worked.

## Consequences applied

- The published entry kept the visible state word for every state.
- The degraded word moved into the display name.
- The registration key included the observed value, so a recovery refreshed the
  host list.
- The documentation named the refusal that the host returns and the action that
  the user takes. It did not promise a retry that the extension does not make.
- The test that pinned the hidden state word changed to assert the visible state
  word and the display-name token.

## Verification limits

- The host package was a local installed binary, not source. The filters and
  the run apply to that host version. A different host version can differ.
- The probe did not run a request against a real endpoint. It proved list
  visibility only.

## Related lessons

- A review that finds a filter on a config field needs host evidence before any
  party dismisses it.
- A review exchange that forks on one head needs the close-and-replace recovery
  that the review-delivery entry states. It is not a separate lesson here.