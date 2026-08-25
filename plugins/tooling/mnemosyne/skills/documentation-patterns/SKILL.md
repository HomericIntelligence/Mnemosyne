---
name: documentation-patterns
license: BSD-3-Clause
description: When you create skill documentation, use this skill. When you improve skill discovery, use this skill. When you record failed methods, use this skill.
user-invocable: false
---

# Skill Documentation Patterns

Use these patterns to write skills that Claude can find and use.
Write all new or changed active technical prose according to the
[Mnemosyne ASD-STE100 writing policy](../../../../../docs/asd-ste100.md).

## Overview

| Item | Details |
| ------ | --------- |
| Date | 2025-12-29 |
| Objective | Document patterns for high-quality skill documentation |
| Outcome | Improved skill discoverability and reuse |
| Source | Sionic AI HuggingFace blog |

## When to Use

- Review a skill that `/learn` creates or amends.
- Improve the discovery of an existing skill.
- Write trigger conditions for `/advise` matching.
- Record failed attempts.
- Make configurations and parameters ready to copy.

## Verified Workflow

### 1. Write Specific Trigger Conditions

The `description` field controls whether `/advise` finds the skill.
Write specific trigger conditions.

**Bad (vague):**
```
"description": "Pruning experiments"
```

**Good (specific):**
```
"description": "When you run vLLM on separate GPUs, use this skill for GRPO training. When vllm_skip_weight_sync errors or OpenAI API parsing issues occur, use this skill again. The team verified it on gemma-3-12b-it."
```

For each description, put the trigger condition first. Then state the required
action. If you give a verified environment, use a complete sentence.

### 2. Document Failed Attempts (Most Valuable)

Failed attempts can prevent repeated work. Use this table format:

```markdown
| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Missing served name | Ran vLLM without --served-model-name | 404 Model 'default' not found | Add --served-model-name default |
| Missing sync flag | Ran without vllm_skip_weight_sync | 404 /update_flattened_params/ error | Use the flag with vllm serve |
```

### 3. Use Concrete Numbers

**Bad:**
```
Use a small learning rate
```

**Good:**
```
RoPE theta=100 works well for short sequences. d_proj=64+ prevents information loss. ksim=4 optimal with 16-bucket token distribution.
```

### 3.5. Include Environment Details in Overview

Add environment data to make the results reproducible:

```markdown
## Overview

| Item | Details |
|------|---------|
| Date | YYYY-MM-DD |
| Objective | [What was the goal] |
| Outcome | [What happened] |
| Hardware | NVIDIA A100-SXM4-80GB |
| Software | PyTorch 2.0.1, CUDA 11.8 |
| Dataset | 100K train / 10K eval |
| Runtime | 24 GPU hours |
| Source | [Blog/paper/issue link] |
```

Environment data is necessary for reproducibility.
For example, "Works on A100-80GB" can fail on V100-16GB because of memory limits.

### 4. Make Configs Copy-Paste Ready

```yaml
# GRPO Training Config (Ready to copy-paste)
rlhf_type: grpo
use_vllm: true
vllm_mode: server
vllm_skip_weight_sync: true  # Mandatory when using standard vllm serve
tensor_parallel_size: 2
gpu_memory_utilization: 0.9
dtype: bfloat16
```

### 5. Include Error-to-Solution Mappings

Use this structure to document errors:

```markdown
## Error: [Error Title/Message]

**Symptom**: [What the user sees/experiences]
**Cause**: [Root cause explanation]
**Solution**: [Step-by-step fix]
**Prevention**: [How to avoid in future]
**Related Errors**: [Links to similar issues]
```

**Example:**

```markdown
## Error: RuntimeError - RoPE freqs dimension mismatch

**Symptom**:
```
RuntimeError: The size of tensor a (32) must match the size of tensor b (16)
at non-singleton dimension 3
```

**Cause**: Standard RoPE implementations output freqs with shape `[seq_len, head_dim/2]`, but attention layer expects `[seq_len, head_dim]` for broadcasting.

**Solution**:
```python
# In apply_rotary_pos_emb function
freqs = torch.cat((freqs, freqs), dim=-1)  # Duplicate to match head dimension
freqs = freqs.unsqueeze(0).unsqueeze(0)    # Add batch and head dims [1, 1, seq, dim]
```

**Prevention**:
- Always verify RoPE freqs shape before attention computation
- Add assertion: `assert freqs.shape[-1] == head_dim`

**Related Errors**:
- Attention mask broadcasting errors
- Position embedding shape mismatches
```
```

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Vague description | Used text such as "ML training" | Claude could not match user queries | Include numbered trigger conditions |
| Optional failures section | Let authors omit failure evidence | Teams lost valuable information | Require the Failed Attempts section |
| Pseudocode | Used commands that users could not run | Users could not copy the workflow | Use real tested commands |
| Missing environment details | Omitted software and hardware versions | Users could not reproduce the result | Include the environment details |
| Long explanation | Used dense prose | Users could not scan it quickly | Use tables and lists |

## Results & Parameters

```yaml
# Skill quality checklist
required_sections:
  - "When to Use"           # Trigger conditions
  - "Verified Workflow"     # What worked
  - "Failed Attempts"       # What failed (most valuable)
  - "Results & Parameters"  # Copy-paste configs

description_pattern: "When {trigger condition}, use this skill to {purpose}. The team verified it on {environment}."

# Anti-patterns to avoid
avoid:
  - Vague trigger conditions
  - Optional failures section
  - Pseudo-code instead of real commands
  - Missing version/environment info
  - Prose-heavy explanations

# Metrics that matter
skill_quality_indicators:
  - Times surfaced by /advise
  - Times referenced in subsequent experiments
  - Copy-paste success rate
```

## Cultural Notes

From the Sionic AI blog:

1. **Easy contribution**: `/learn` can create the skill quickly.
2. **Specific descriptions**: Precise descriptions improve discovery and reuse.
3. **Failed methods**: A failed method and its cause provide useful evidence.
4. **Timely capture**: At the end of the session, record the knowledge.

## References

- Source blog: https://huggingface.co/blog/sionic-ai/claude-code-skills-training
- Template gist: https://gist.github.com/sigridjineth/2f0ef5d1d56e884a84f1580de21db597
