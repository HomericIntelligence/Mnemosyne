# Mnemosyne

[![Validate Plugins](https://github.com/HomericIntelligence/Mnemosyne/actions/workflows/validate-plugins.yml/badge.svg)](https://github.com/HomericIntelligence/Mnemosyne/actions/workflows/validate-plugins.yml)

Mnemosyne is the skills and session-memory store for the HomericIntelligence
agentic ecosystem. Named after Mnemosyne, the Greek goddess of memory, this
repository is the collective memory where team learnings are preserved and made
searchable as flat skill files under `skills/`.

> **Mnemosyne is not a plugin marketplace.** The plugins/commands (`/advise`,
> `/learn`, and the rest) live in **[Athena](https://github.com/HomericIntelligence/Athena)**,
> which is the marketplace. Mnemosyne only stores the skill corpus that those
> Athena commands read from and write to. Do not re-introduce a
> `.claude-plugin/marketplace.json` here.

## Installation

Mnemosyne itself is not installed as a plugin. Install the **Athena** plugin
marketplace (which provides `/advise` and `/learn`), and those commands read and
write the skills stored in this repository.

To work on the corpus directly, clone it:

```bash
git clone https://github.com/HomericIntelligence/Mnemosyne.git
```

## Quick Start

These commands come from the **Athena** plugin and work inside any Claude Code
session where Athena is installed. All skill discovery and authoring is handled
through the `/advise` and `/learn` commands.

### Search for Knowledge

```text
/advise <your goal or question>
```

Claude will search the skills corpus for relevant prior learnings and return:

- What worked in similar situations
- What failed and why (critical!)
- Recommended parameters and configurations

### Save Your Learnings

```text
/learn
```

After an experiment or debugging session, capture your learnings in the existing canonical skill when one
matches the intent; create a new skill only when no canonical exists.
Claude automatically:

1. Analyzes your entire session conversation
2. Extracts successes, failures, and parameters
3. Keeps reusable guidance and at most three materially distinct examples in the main skill, routes
   useful session evidence to notes, and archives prior versions and version-control narrative in history
4. Creates a branch and opens a PR

**Auto-trigger**: On `/exit` or `/clear`, you'll be prompted to save learnings.

## Repository Structure

```text
skills/
├── <name>.md               # Flat skill files with YAML frontmatter
├── <name>.notes.md         # (Optional) Additional session context
├── <name>.history          # (Optional) Version and provenance history
└── ...
```

The `/advise` and `/learn` commands themselves live in the **Athena** plugin, not
in this repository. Each skill is a flat markdown file with YAML frontmatter:

```text
skills/<name>.md             # Main skill file with YAML frontmatter + markdown content
skills/<name>.notes.md       # (Optional) Additional context from development session
skills/<name>.history        # Version/provenance archive for /learn writes
```

Retrievable main skills are limited to 30,000 bytes. Keep reusable rules and at most three high-value
examples in the main file. Before replacing it, archive its complete prior retrievable content in
`.history`; keep raw session detail in `.notes.md`. Keep only the current schema-required `version`
identifier in main frontmatter. Athena excludes both companion types from normal retrieval.

## Available Skills

The `skills/` directory is the complete corpus. The `/advise` command (from the
Athena plugin) automatically searches and retrieves relevant skills for your
queries.

## Contributing a Skill

### Option 1: Automatic (Recommended)

1. Complete an experiment or debugging session
2. Run `/learn`
3. Follow the prompts to categorize and name the skill
4. PR is created automatically

### Option 2: Manual

1. Copy `templates/skill-template.md` to `skills/<name>.md`
2. Fill in YAML frontmatter (name, description, category, date, version)
3. Fill all required markdown sections
4. **Include "Failed Attempts" table** (required!)
5. Create PR

### Required Sections in Skill Files

- **Overview table**: Date, objective, outcome
- **When to Use**: Specific trigger conditions
- **Verified Workflow**: Step-by-step that worked
- **Failed Attempts**: What didn't work and why (REQUIRED)
- **Results & Parameters**: Copy-paste ready configs
- **References**: Links to issues, docs

## Validation

All PRs are validated by CI:

- YAML frontmatter has required fields (name, description, category, date, version)
- All required markdown sections are present
- Failed Attempts section is present with proper table format
- Description is specific (20+ chars)
- Category is valid
- New or changed retrievable main skill files are no larger than 30,000 bytes; unchanged oversized
  legacy files are ratcheted and must be compacted when next amended

Run validation locally:

```bash
python3 scripts/validate_plugins.py
```

## Ecosystem

### Core Platform

| Project | Purpose |
| --------- | --------- |
| [Odysseus](https://github.com/HomericIntelligence/Odysseus) | Ecosystem orchestrator and architecture documentation |
| **Mnemosyne** | Knowledge, skills, and memory (this repo) |
| [ProjectHephaestus](https://github.com/HomericIntelligence/ProjectHephaestus) | Shared utilities and foundational tools used across the ecosystem |

### Agent Mesh Infrastructure

| Project | Purpose |
| --------- | --------- |
| [Myrmidons](https://github.com/HomericIntelligence/Myrmidons) | GitOps agent provisioning — agent definitions as code, reconciliation against ai-maestro API |
| [AchaeanFleet](https://github.com/HomericIntelligence/AchaeanFleet) | Container images for the heterogeneous agent mesh — base images, Dockerfiles, Compose, Nomad/Dagger CI |

### Services

| Project | Purpose |
| --------- | --------- |
| [ProjectKeystone](https://github.com/HomericIntelligence/ProjectKeystone) | DAG execution and task coordination |
| [ProjectHermes](https://github.com/HomericIntelligence/ProjectHermes) | Webhook-to-NATS messaging bridge |
| [ProjectTelemachy](https://github.com/HomericIntelligence/ProjectTelemachy) | Workflow engine |
| [ProjectProteus](https://github.com/HomericIntelligence/ProjectProteus) | CI/CD pipeline management |
| [ProjectArgus](https://github.com/HomericIntelligence/ProjectArgus) | Observability and monitoring |

### Training & Testing

| Project | Purpose |
| --------- | --------- |
| [ProjectOdyssey](https://github.com/HomericIntelligence/ProjectOdyssey) | Training framework written in Mojo |
| [ProjectScylla](https://github.com/HomericIntelligence/ProjectScylla) | Testing, optimization, and resilience evaluation |

> **Note**: Skills produced by any of the above repositories can be contributed to Mnemosyne via `/learn` so that learnings are shared across the ecosystem.

## Why Mnemosyne?

Mnemosyne embodies memory, continuity, and the preservation of wisdom. This repository
ensures that learnings compound over time - every experiment, debugging session, and
architectural decision becomes searchable knowledge for the team.

The most valuable section in any skill is **Failed Attempts** - knowing what didn't
work saves more time than knowing what did.

## Citation

If you use Mnemosyne in your research or work, please cite:

```bibtex
@misc{mnemosyne2026,
  title={Mnemosyne: A Skills and Memory Store for HomericIntelligence},
  author={{HomericIntelligence Team}},
  year={2026},
  note={Skills corpus and collective memory system},
  url={https://github.com/HomericIntelligence/Mnemosyne}
}
```
