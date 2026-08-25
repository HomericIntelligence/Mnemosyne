# `plugins/tooling/mnemosyne` Command Infrastructure

This directory contains Mnemosyne-side reference material for `/advise` and
`/learn`. It also contains skill author and validation guidance. It is not a
corpus skill or a plugin marketplace.

All new or changed active technical prose in this directory must follow the
[Mnemosyne ASD-STE100 writing policy](../../../docs/asd-ste100.md).

## Why it lives in `plugins/`, not `skills/`

Mnemosyne v2.0.0 moved all skills to flat `.md` files under `skills/`.
This directory is exempt from that migration because it contains command infrastructure.

| Sub-directory | Purpose |
|---------------|---------|
| `skills/advise/` | `SKILL.md` for the `/advise` command |
| `skills/learn/` | `SKILL.md` for the `/learn` command |
| `skills/documentation-patterns/` | Documentation authoring guidance |
| `skills/validation-workflow/` | CI/pre-commit validation guidance |
| `hooks/` | Example hook configurations (`settings.json.example`) |
| `references/` | Session notes, experiment logs, troubleshooting guides |
| `.claude-plugin/plugin.json` | Plugin manifest loaded by the Claude Code harness |

## Command Ownership

The [Athena plugin](https://github.com/HomericIntelligence/Athena) supplies the
installed `/advise` and `/learn` commands. Mnemosyne stores the corpus that the
commands use. The `SKILL.md` files in this directory are Mnemosyne-side
references. They are not command implementations.

## For contributors

- Do not convert this directory to the flat-file format. The harness requires the nested layout.
- Do not add new skills here. Add new skills to `skills/<name>.md`.
- Read the *Plugin Standards* section in `AGENTS.md` for the rationale and exception.
