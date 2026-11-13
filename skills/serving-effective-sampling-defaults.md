---
name: serving-effective-sampling-defaults
license: BSD-3-Clause
description: "Resolve the effective sampling defaults of a served model from the engine default mode and the checkpoint generation config, not from a recipe's optional defaults block. Use when: (1) an operator asks what temperature or top_p a served model uses, (2) a serving recipe omits or declares sampling defaults, (3) server metadata redacts sampling settings, or (4) two engines serve one checkpoint."
category: tooling
date: 2026-11-13
version: "1.0.0"
user-invocable: false
tags: [serving, sampling, temperature, top-p, generation-config, engine-defaults, checkpoint, recipe]
---

# Serving Effective Sampling Defaults

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-13 |
| **Objective** | Report the sampling defaults that a served model uses, and identify the layer that supplies each value. |
| **Outcome** | Operational. A read-only audit traced the effective temperature and top_p to the checkpoint generation config when the recipe declared no defaults and the engine default mode selected the model file. |

## When to Use

- An operator asks for the temperature, top_p, or top_k of a served model.
- A serving recipe has a sampling-defaults field, and you must know if the engine enforces it.
- The engine server-info endpoint redacts sampling fields.
- A client reports different output when it omits a sampling value.
- Two serving engines load the same checkpoint and you must compare their defaults.
- The recipe has a per-cluster weight path, and the current cluster does not mount the other cluster's path.

## Verified Workflow

### Quick Reference

```bash
# 1. Find the declared defaults and the default-selection flag.
grep -n 'sampling_defaults\|sampling-defaults\|generation-config' <recipe> <launch-script>

# 2. Read the checkpoint values that the engine can load.
jq '{temperature, top_p, top_k}' <weights-path>/generation_config.json
```

### Suggested Approach

1. Read the resolved recipe for the current cluster. Do not use a schema default as an effective value. A schema can define a field with a null default and a comment that the engine does not enforce it.
2. Check the launch command for an explicit default-sampling flag. Record the engine name and version. Examples are a mode that selects the model generation config and a mode that selects engine constants.
3. If the mode selects the model, read `generation_config.json` in the checkpoint directory. Report `temperature`, `top_p`, and `top_k` from that file.
4. If the mode selects engine constants, report the constants of that engine version. Do not read the checkpoint file as the source.
5. Treat a client value as the final override. The default applies only when the request omits the field.
6. If the server metadata redacts sampling fields, do not report "unset". Use the checkpoint file and the documented engine mode. State the evidence and the redaction limit.
7. If two engines serve one checkpoint, repeat steps 2 through 4 for each engine. The checkpoint file is shared. The default mode and the constants are not.
8. Report the layer that supplied each value. A recipe value is effective only when the launch passes it to the engine or the engine documents enforcement.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Attempt 1 | Read the sampling-defaults field in the recipe schema and reported its null default as "unset". | The field was advisory. The engine did not enforce it. The engine default mode read the checkpoint. | A declared defaults block is not effective unless the launch passes it to the engine. Follow the engine default mode. |
| Attempt 2 | Read the live server-info response for the sampling values. | The deployment redacted the sampling fields. | Redaction is not absence. Use the checkpoint file and the documented engine mode. |
| Attempt 3 | Used the first weight path in the recipe. | The recipe listed per-cluster paths. The selected path was not mounted on the current cluster. | Resolve the path for the current cluster and verify the checkpoint directory before you read its generation config. |

## Results & Parameters

### Configuration

```yaml
sampling_default_resolution:
  recipe_layer:
    field: sampling_defaults
    effective_when: the launch passes it to the engine or the engine documents enforcement
  engine_layer:
    default_mode_flag: --sampling-defaults
    model_mode: read <weights-path>/generation_config.json
    engine_mode: use the constants of the installed engine version
  checkpoint_layer:
    file: generation_config.json
    fields: [temperature, top_p, top_k]
  request_layer:
    precedence: a client value overrides the default
  evidence_limit:
    redacted_server_info: use the checkpoint file and the documented engine mode
```

### Expected Output

- The layer that supplied each sampling value.
- The checkpoint path and revision that you read.
- The engine name and version.
- A statement that a client value overrides the default.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| An internal serving platform | Read-only operational audit | A recipe declared no sampling defaults. The engine default mode selected the checkpoint generation config. The recipe schema described its defaults field as advertised, not enforced. Live server metadata redacted the sampling fields. |

## References

- [SGLang sampling parameters](https://docs.sglang.io/basic_usage/sampling_params.html)
