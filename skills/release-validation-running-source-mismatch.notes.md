# Release Validation Running-Source Mismatch — Supporting Notes

These notes record the evidence and the readings behind the main skill. They do not
add rules.

## Observation

A production lane was hot-swapped to a prepared tree. The operating question was
whether release validation proved the running content.

- Lane status JSON showed `generation` in the form
  `<scheduler-job>:<color>:<source_sha>:<publish-stamp>`. The `source_sha` value was
  the swapped source commit.
- The remote tag list contained only the prior annotated tag. It had no tag for the
  swapped source.
- The production tip was 16 commits after the prior tag.
- Deployment validation reported overall **ready** with counts pass 5, fail 0,
  pending 5, unknown 0.
- The version-tag check was in pass, and its `observed` text named the prior annotated
  tag.
- The release check was in pass, and its `observed` text said that the release for the
  prior tag is published.
- The remaining pending checks were delivery checks that run on the deployment
  targets, not source-identity checks.

## Interpretation

The two pass checks are accurate about the prior tag. They do not assert that the
lane runs the prior tag. The lane status names a different source. The correct report
is a mismatch: the lane runs untagged content, and the tag and release checks describe
the older release.

Behavior probes against the running source succeeded for the new content. The mismatch
therefore changed the release record, not the serving result.

## Review Limits

- The hot-swap record is service-private on that deployment. The reviewer could not
  read `release-runs/<run>/hot-swap.json` as an ordinary user. The report named the
  record and the passing outcome (`stopped`) as the required next check for the
  service account.
- The validation was read-only. It did not contact the production targets for the
  pending delivery checks.

## Reusable Signals

| Signal | Reading |
| -------- | --------- |
| `generation` contains a `source_sha` | The lane names the commit it runs. Compare it with the tag commit. |
| Tag check pass with an older tag in `observed` | The check is about the older tag only. |
| Release check pass naming an older tag | Publication evidence is about the older tag only. |
| No tag for the swapped source | The running content is untagged. Report it. |
| Delivery checks pending | They do not verify the running source identity. |