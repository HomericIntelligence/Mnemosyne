# inert-registration-policy-omission — Evidence Notes

Privacy-safe supporting evidence for the main skill. Repository, organization,
issue, and pull-request identifiers are generalized per the privacy rules.

## Source Context

A production model-serving control plane registers a model through a cookbook
file and activates it through a deployment-context policy. A registration-only
change added:

1. a cookbook with a pinned model repository revision, no image, no weights
   path, and no checkpoint manifest, with both autoscale bounds at zero;
2. a routing entry and an admission partition in the production context;
3. a dashboard alias migration;
4. one new model key in a proxy guard that limits a request to one image.

A plan review approved this scope in an earlier round: registration without
activation, because the launch cannot start without an image and a manifest.

## The Required Finding

A source review of the implementation found one required issue. The activation
section of the model documentation set the image, the image digest, the weights
path, the checkpoint manifest, the measured engine arguments, and the replica
bounds. It did not add the model to the deployment policy allow-list.

The gate is an early refusal with a stable error code that means "the
deployment does not serve the model". The same allow-list also builds the
per-model replica job name and raises a configuration error for a model that
the policy does not allow. Before the change, every routed and partitioned
model was also an allowed model. The change broke that invariant, and the
documented activation path still ended at the refusal.

The author repaired it by removing the routing entry and the admission
partition until the model is allow-listed, and by making the activation steps
name the allow-list entry and the layers that arrive with the image and the
manifest.

## Why This Is a Separate Branch

The related zero-floor skill covers a lane that is already registered and keeps
its registration while its replica floor drops to zero. This case is the
inverse: no image and no weights exist, so activation is a future change. The
same intent-level idea ("stay registered, do not start") does not supply the
decision for which policy layers to omit. The gate, the job-name derivation,
and the activation-step ordering are new decision value.

## How the Finding Was Found

The reviewer read the refusal path in the deployment-context module, then
listed each model named in the routing map and the admission partitions, and
compared that list with the allow-list. A cookbook-only review would not find
the omission, because the cookbook correctly has no image.

## Evidence Limits

- The finding is from one review round on one change. The repair was not
  re-reviewed at the time of this note.
- The render-list behavior was established from the current test catalog, not
  from a run of the new cookbook. The catalog holds a glob test over every
  cookbook file, and one render list names active models explicitly.
- Activity identifier and reason for this note: `learning-write` on a direct
  learn request, 2026-11-07.