---
name: tooling-athena-installed-plugin-missing-helper-fallback
description: "Continue Athena learn/advise workflows when the harness's installed skill plugin tree disappears mid-session. Use when: (1) skill IDs become unavailable in the harness or a harness reload unloads them; (2) the installed skills root (for example ~/.local/share/opencode/skills/) is gone; (3) learn/advise helper scripts are unreachable at their installed path but a trusted Athena source checkout exists."
category: tooling
date: 2026-10-30
version: "1.0.0"
user-invocable: false
tags: [athena, learn, advise, helper-resolution, fallback, opencode, plugin]
---

# Athena installed plugin missing: resolve helpers from the source checkout

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-30 |
| **Objective** | Finish an in-flight or newly requested learn/advise delivery when the harness has removed its installed Athena skill plugin tree, without stopping the workflow or substituting a different knowledge repository. |
| **Outcome** | Successful. A complete learn delivery cycle (discovery, write-mode resolution, worktree, draft, validation, DCO commit, push, PR) executed twice with every helper resolved from a trusted Athena source checkout after the installed plugin tree vanished mid-session. Validation results were identical in shape to installed-helper runs, and the delivered PR merged. Verified with the public Athena checkout against HomericIntelligence/Mnemosyne. |

## When to Use

- The harness reports that previously available skill IDs are unavailable, unloaded, or removed, while a learn or advise task is open.
- The installed skills root (for example `~/.local/share/opencode/skills/`) no longer exists — not merely one plugin directory, but the root — so helper scripts such as `resolve_knowledge_checkout.py` and `list_retrievable_skills.py` are unreachable at their installed paths.
- The learn skill's contract ("resolve the installed advise skill directory") cannot be satisfied literally and you need a same-grade fallback without skipping discovery.
- A trusted Athena source checkout exists on the host (any checkout of the public Athena repository carries the canonical `skills/<name>/scripts/` helpers).

Do not pause the durable workflow only for this reason. The helpers are standalone local tools; the harness plugin registry is not part of their execution path.

## Verified Workflow

### Quick Reference

```bash
ls ~/.local/share/opencode/skills/            # 1. classify the loss at the ROOT first
CHECKOUT=<trusted-athena-checkout>            # 2. any Athena source checkout
python3 "$CHECKOUT/skills/advise/scripts/resolve_knowledge_checkout.py" \
  --mode read-only --knowledge-root "$HOME/.agent_brain/knowledge" --json
python3 "$CHECKOUT/skills/advise/scripts/list_retrievable_skills.py" \
  "$HOME/.agent_brain/knowledge"
```

### Suggested Approach

1. **Classify at the shallowest level first.** List the installed skills root before probing any nested helper path. Whole-root absence means plugin-tree removal (uninstall, upgrade, or harness-managed relocation); one missing plugin means per-skill change. Nested-first probing produced a misleading "helper missing" signal here when in fact the entire plugin tree was gone.
2. **Recover the skill contract from source.** Read the needed `skills/<name>/SKILL.md` directly from the checkout (a user-attached directory is equivalent). The contract travels with the source tree, not with the harness registry; an unloaded skill ID does not revoke instructions already read.
3. **Resolve helpers by absolute path from the checkout.** `resolve_knowledge_checkout.py` and `list_retrievable_skills.py` under `skills/advise/scripts/` run on stdlib plus git; they take `--knowledge-root` and need no plugin runtime. Record which checkout supplied helpers in the delivery report.
4. **Change nothing else about the contract.** Keep read-only vs write dependency modes, knowledge-checkout binding, corpus classification, worktree isolation, validation, DCO, and PR delivery exactly as the skill specifies. The fallback changes only where scripts are found, never what they verify.
5. **Do not switch helper sources mid-delivery.** If the installed plugin reappears (for example an upgrade finished), note the restoration in the report but finish the current delivery with the helper set you validated against, so the evidence chain stays uniform.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Probing the nested helper directory as the first check after the unload | `ls <installed-root>/athena/skills/advise/scripts/` immediately after the harness reported skills unavailable. | It failed with "No such file or directory" — but a later root listing showed the whole skills root was gone, so the nested error hid the true scope (plugin-tree removal, not a per-plugin problem) and could have sent recovery down a wrong path (reinstalling one plugin, relocating one directory). | Classify the loss at the shallowest level (the installed root) before deeper probes; the depth of the first error sets the wrong mental model of what disappeared. |

## Results & Parameters

### Configuration

- Helper resolution order: installed plugin path → trusted Athena source checkout path (absolute). There is no third fallback; if no checkout exists, report the limit instead of substituting another repository.
- The source checkout need not be fully current for helper execution, because delivery re-resolves the knowledge checkout with `--mode write` and binds all writes to the resolved default-branch commit, not to helper vintage.

### Expected Output

- `resolve_knowledge_checkout.py --json` prints the same fields regardless of helper source: `repository`, `revision`, `local_revision`, `refresh_state`, `refresh_verified`, `checkout`, `checkout_state`, and any `limitations`/`freshness_limit`.
- Repository validation output is unchanged versus installed-helper runs (in the verified delivery: `validate_plugins` 814/814, `check_pii` OK, full `pytest` suite 253 passed / 4 skipped).

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Public Athena checkout + HomericIntelligence/Mnemosyne | OpenCode harness removed its installed Athena plugin tree mid-session (skills root absent); two complete learn deliveries ran on checkout-resolved helpers, one merged (PR #3486) | [notes.md](../skills/tooling-athena-installed-plugin-missing-helper-fallback.notes.md) |

## References

- [Athena repository (public)](https://github.com/HomericIntelligence/Athena): canonical `skills/<name>/scripts/` helpers and skill contracts
- Related: [tooling-opencode-v2-local-plugin-loading](tooling-opencode-v2-local-plugin-loading.md) (how the harness loads plugins from local paths)
- Related: [mnemosyne-skill-pr-ci-gate-first-pass-green](mnemosyne-skill-pr-ci-gate-first-pass-green.md) (Mnemosyne delivery validation ordering, including the untracked-file inventory-closure artifact)
