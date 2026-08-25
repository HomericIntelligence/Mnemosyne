# Mnemosyne

[![Validate Plugins](https://github.com/HomericIntelligence/Mnemosyne/actions/workflows/validate-plugins.yml/badge.svg)](https://github.com/HomericIntelligence/Mnemosyne/actions/workflows/validate-plugins.yml)

Mnemosyne stores skills and session memory for the HomericIntelligence agentic
ecosystem. It preserves team knowledge as searchable flat skill files in
`skills/`. Its name comes from Mnemosyne, the Greek goddess of memory.

> **Mnemosyne is not a plugin marketplace.**
> [Athena](https://github.com/HomericIntelligence/Athena) provides `/advise`,
> `/learn`, and the other plugin commands. Mnemosyne stores the skill corpus
> that these commands use. Do not add `.claude-plugin/marketplace.json` to this
> repository.

## Writing standard

All active technical prose in Mnemosyne must follow the
[ASD-STE100 writing policy](docs/asd-ste100.md). This requirement applies to
skills, agent directions, contributor instructions, templates, and technical
policies.

## Installation

Do not install Mnemosyne as a plugin. Install the **Athena** plugin marketplace
to get `/advise` and `/learn`. These commands read and write the skills in this
repository.

To work on the corpus directly, clone the repository:

```bash
git clone https://github.com/HomericIntelligence/Mnemosyne.git
```

## Quick Start

The **Athena** plugin provides these commands. You can use them in a Claude Code
session that has Athena installed. Use `/advise` to find skills. Use `/learn` to
create skills.

### Search for Knowledge

```text
/advise <your goal or question>
```

Claude searches the skill corpus and returns this information:

- Methods that worked in similar situations
- Methods that failed and the causes of the failures
- Recommended parameters and configurations

### Save Knowledge

```text
/learn
```

After an experiment or a debugging session, use `/learn` to save the knowledge.
Claude does these tasks:

1. Analyzes the complete session conversation.
2. Searches existing skills and open pull requests by intent.
3. Extracts successes, failures, and parameters.
4. If a canonical skill exists, amends that skill.
5. Keeps reusable guidance and no more than three different examples in the
   main skill.
6. Puts useful session evidence in `.notes.md`.
7. Before replacement, archives the complete prior main skill in `.history`.
8. Puts version and provenance records in `.history`.
9. If no canonical skill exists, creates a new skill.
10. Creates a branch and opens a pull request.

**Automatic reminder**: `/exit` and `/clear` prompt you to save the session
knowledge.

## Repository Structure

```text
skills/
├── <name>.md               # Flat skill files with YAML frontmatter
├── <name>.notes.md         # (Optional) Additional session context
├── <name>.history          # (Optional) Version and provenance history
└── ...
```

The **Athena** plugin contains the `/advise` and `/learn` commands. This
repository does not contain these commands. Each skill is a flat Markdown file
with YAML frontmatter:

```text
skills/<name>.md             # Main skill file with YAML frontmatter + markdown content
skills/<name>.notes.md       # (Optional) Additional context from development session
skills/<name>.history        # Version/provenance archive for /learn writes
```

Keep each retrievable main skill at or below 30,000 bytes. Keep reusable rules
and no more than three high-value examples in the main skill. Before you replace
the main skill, archive its complete prior content in `.history`. Keep raw
session details in `.notes.md`. In the frontmatter, keep only the current
`version` identifier. Athena excludes both companion types from normal
retrieval.

## Available Skills

The `skills/` directory contains the complete corpus. The `/advise` command from
Athena searches the corpus and returns relevant skills.

## Contributing a Skill

### Option 1: Automatic (Recommended)

1. Complete an experiment or a debugging session.
2. Run `/learn`.
3. Let Claude select the skill category.
4. Let Claude name the skill.
5. Let Claude create the pull request automatically.

### Option 2: Manual

1. Copy `templates/skill-template.md` to `skills/<name>.md`.
2. Complete the YAML frontmatter.
3. Complete all required Markdown sections.
4. Include the required **Failed Attempts** table.
5. Create a pull request.

### Required Sections in Skill Files

- **Overview table**: Give the date, objective, and outcome.
- **When to Use**: Give specific trigger conditions.
- **Verified Workflow**: Give the steps that worked.
- **Failed Attempts**: Identify failed methods and their causes. This section is
  required.
- **Results & Parameters**: Give configurations that users can copy and use.
- **References**: Link to related issues and documents.

## Validation

CI validates all pull requests:

- YAML frontmatter contains all required fields.
- The skill contains all required Markdown sections.
- The Failed Attempts section contains the required table.
- The description field is present.
- The category is valid.
- Each retrievable main skill is at or below 30,000 bytes.

Authors and reviewers must confirm that each description contains specific trigger
conditions.

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
| [Myrmidons](https://github.com/HomericIntelligence/Myrmidons) | GitOps agent provisioning with agent definitions as code and ai-maestro API reconciliation |
| [AchaeanFleet](https://github.com/HomericIntelligence/AchaeanFleet) | Agent mesh images with base images, Dockerfiles, Compose, and Nomad/Dagger CI |

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

> **Note**: Use `/learn` to add skills from these repositories to Mnemosyne.
> This action shares the knowledge across the ecosystem.

## Why Mnemosyne?

Mnemosyne preserves knowledge from experiments, debugging sessions, and
architecture decisions. The team can search and reuse this knowledge.

The **Failed Attempts** section records methods that did not work and explains
their causes. This information helps the team to prevent repeated work.

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
