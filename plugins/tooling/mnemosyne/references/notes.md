# Historical Mnemosyne Setup Notes

This file records the old nested-plugin and marketplace design. Do not use its
procedures for the current repository. Mnemosyne now stores a flat skill corpus.
The [Athena plugin](https://github.com/HomericIntelligence/Athena) supplies the
installed commands.

Write all new or changed explanatory prose according to the
[Mnemosyne ASD-STE100 writing policy](../../../../docs/asd-ste100.md).
Preserve exact code, commands, identifiers, outputs, quotations, and technical evidence.

The commands and file trees below are historical evidence. They are not current
installation instructions.

## Included Components

```
mnemosyne/
├── skills/
│   ├── advise/SKILL.md              # /advise command
│   ├── learn/SKILL.md               # /learn command
│   ├── documentation-patterns/SKILL.md  # How to write good skills
│   └── validation-workflow/SKILL.md     # CI/CD setup
├── hooks/
│   ├── learn-trigger.py             # SessionEnd hook
│   └── settings.json.example        # Hook configuration
├── scripts/
│   ├── validate_plugins.py          # PR validation
│   └── generate_marketplace.py      # Marketplace generation
└── references/
    └── notes.md                     # This file
```

## Historical Setup Procedure

### 1. Copy Plugin to Your Project

```bash
cp -r plugins/tooling/mnemosyne your-project/plugins/tooling/
```

### 2. Install Hooks

```bash
mkdir -p your-project/.claude/hooks

cp plugins/tooling/mnemosyne/hooks/learn-trigger.py \
   your-project/.claude/hooks/

cp plugins/tooling/mnemosyne/hooks/settings.json.example \
   your-project/.claude/settings.json
```

### 3. Install Scripts

```bash
mkdir -p your-project/scripts

cp plugins/tooling/mnemosyne/scripts/*.py \
   your-project/scripts/
```

### 4. Add Commands to CLAUDE.md

```markdown
## Commands

### /advise

Search skills registry for relevant experiments before starting work.

1. Read user's goal/question
2. Read `marketplace.json` to find matching plugins by description
3. For each match, read the plugin's SKILL.md
4. Summarize: what worked, what failed, recommended parameters
5. Always prioritize Failed Attempts - these prevent wasted effort

### /learn

Save learnings after a session (auto-creates PR).

1. Read entire conversation history
2. Extract: objective, steps taken, successes, failures, parameters
3. Prompt user for category and skill name
4. Generate plugin from template
5. Create branch: `skill/<category>/<name>`
6. Commit, push, and create PR
```

### 5. Set Up CI/CD (Optional)

Copy these workflows from the `validation-workflow` skill:

- `.github/workflows/validate-plugins.yml`
- `.github/workflows/update-marketplace.yml`

### 6. Initialize Marketplace

```bash
echo '{"version": "1.0.0", "plugins": []}' > marketplace.json

mkdir -p plugins/{training,evaluation,optimization,debugging,architecture,tooling,ci-cd,testing}
```

## Historical Components

| Component | Purpose |
| ----------- | --------- |
| `/advise` | Search registry before starting work |
| `/learn` | Capture learnings after sessions |
| `documentation-patterns` | How to write discoverable skills |
| `validation-workflow` | CI/CD for quality enforcement |
| `learn-trigger.py` | Auto-prompt on session end |
| `validate_plugins.py` | PR validation script |
| `generate_marketplace.py` | Marketplace index generator |

## Historical Hook Behavior

The `SessionEnd` hook has these behaviors:

- It starts for `/exit` and `/clear`.
- It requires a session that has more than 10 messages.
- It shows this prompt: "Would you like to save your learnings?"
- It does not block the session.

## Source

This setup is based on the
[Sionic AI article](https://huggingface.co/blog/sionic-ai/claude-code-skills-training).
