# Notes: registry-map-total-lookup-silent-empty-fallback

## Evidence basis

The lesson comes from one defect in a release deployment system, in this session.

Symptoms:

- A published deployment context held zero per-key registry entries for every cluster.
- The render step indexed the registry directly and crashed with `KeyError` when a key was absent.
- The image-selection helper then returned no image, so the rendered script used a host virtual environment path.
- That path existed only in a conventional native deployment. The directory was absent in the container deployment.

Diagnosis:

- A repository search found no writer that filled the registry.
- The per-unit configuration files held correct weights paths and images for every unit.
- A production fallback to those files was a local workaround, not the shipped design.

Repair shape:

1. Registration of registry entries at context activation.
2. Activation refusal with a per-unit reason when a configured unit had no entry, and when the cluster declared images but the registry was empty.
3. Removal of the host virtual environment fallback for container deployments.
4. Documentation of one authority for weights and image paths.
5. Behavior tests for the fill, the refusal, and the rendered output.

## Verification limits

- The evidence is one defect. Confirm the rule in other registries before you widen its scope.
- Local tests covered the changed behavior. Full-suite CI results were not part of this lesson.

## Related guidance

- `service-startup-precondition-bootstrap-deadlock`: same first-start failure. Different trigger: a dependency cycle where only the service creates the precondition. Here the trigger is an unpopulated registry and a silent fallback.
- `shared-default-fallback-single-source` and `cli-format-output-pola-silent-fallback`: control fallback precedence and invalid input. They do not require a fill or an activation refusal.
