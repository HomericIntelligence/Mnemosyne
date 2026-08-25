# AGENTS.md

This file is the authoritative agent contract for Mnemosyne. Claude Code and
other agents must follow this contract.

## Project Overview

Mnemosyne stores skills and session memory for the HomericIntelligence agentic
ecosystem. It stores knowledge from experiments, debugging sessions, and
development work. The repository keeps this knowledge as flat skill files in
`skills/`.

Mnemosyne is **not** a plugin marketplace. The **Athena** plugin provides the
`/advise` and `/learn` commands. Mnemosyne stores the corpus that these commands
read and write. Do not add `.claude-plugin/marketplace.json` to this repository.

**Purpose**: Store team knowledge. This knowledge helps `/advise` prevent
repeated mistakes.

**Ecosystem**: Mnemosyne works with these projects:

- ProjectOdyssey for training.
- ProjectKeystone for DAG execution.
- ProjectScylla for testing.
- Myrmidons for agent provisioning.
- AchaeanFleet for agent images.
- ProjectHephaestus for shared utilities.

## Writing Standard

All active skill prose and repository guidance must follow
[ASD-STE100 Simplified Technical English](https://www.asd-ste100.org).
Use the current official issue. This repository uses Issue 9, dated 15 January
2025, as its review baseline.

Read the repository [ASD-STE100 writing policy](docs/asd-ste100.md). Apply the
policy to all content in its scope.
The policy applies to new prose and to prose that you change or republish. It
also applies when an agent presents information from an older skill.

Do not change these content types only to change the writing style:

- Code, commands, and configuration
- Identifiers, paths, and URLs
- Proper names and quotations
- Legal text and raw evidence.

Treat established project terms as approved technical terms. For a style-only
edit, keep all development-principles text unchanged.

Automated checks can confirm that the policy is present. They cannot certify
that prose conforms to ASD-STE100. Authors and reviewers must check the prose.

## Commands

### /advise

Before you start work, search the skill corpus.

**When to use**: At the session start, use `/advise`. Before an experiment,
also use it. When you debug an unfamiliar error, use it again.

**Workflow**:

1. Read the user goal or question.
2. Search the `skills/` corpus for related skill files.
3. Read the matching skill files.
4. Return successful methods, failed methods, and recommended parameters.

**Example**:

```text
User: /advise training a model with GRPO
Claude: Found 2 related skills...
- training/grpo-external-vllm: Use external vLLM server for GRPO training
  - Key finding: vllm_skip_weight_sync errors require separate GPU setup
  - Recommended: batch_size=4, learning_rate=1e-5
```

### /learn

Save useful session knowledge. The command creates a pull request.

**When to use**: After an experiment, use `/learn`. After a debugging session,
also use it. After you implement a new pattern, use it again.

**Workflow**:

1. Read the complete conversation history.
2. Extract the objective, steps, successes, failures, and parameters.
3. Search existing skills and open pull requests by intent.
4. If a canonical skill exists, amend it. Do not create a sibling skill.
5. Keep the reusable trigger, rule, failure mode, and parameters in the main skill.
6. Keep no more than three examples that cover different decisions.
7. Put session paths, transcripts, examples, and verification details in
   `skills/<name>.notes.md`.
8. Before replacement, archive the complete prior main skill in
   `skills/<name>.history`.
9. Append the new version and its provenance to the history file.
10. Keep only the current `version` value in the main skill frontmatter.
11. Keep each retrievable main skill at or below 30,000 bytes.
12. If no canonical skill exists, generate this filename:
    `<topic>-<subtopic>-<short-4-word-summary>`.
13. Create a Git worktree for isolation. Do all work in that worktree.
14. Write all required content to `skills/<name>.md`.
15. If supporting evidence is useful, create the notes file.
16. Create the history file for the initial or superseded main version.
17. Create the `skill/<name>` branch.
18. Commit the change.
19. Push the branch.
20. Create a pull request with a summary.
21. Run `git worktree remove` to remove the worktree.

**Automatic reminder**: The `UserPromptSubmit` hook reminds users about
`/learn`. Session-ending keywords activate the reminder.

**Format notes**:

- The command generates the category and name without a user prompt.
- The command uses one Git worktree for each branch.
- The command removes the worktree after it creates the pull request.
- A skill is one flat Markdown file with YAML frontmatter.
- The branch name is `skill/<name>`.

## Plugin Standards

### Required Structure

```text
skills/<name>.md             # Main skill file with YAML frontmatter + markdown content
skills/<name>.notes.md       # (Optional) Additional context from development session
skills/<name>.history        # Version and provenance archive for /learn writes
```

Each skill is a flat file in `skills/`. Each skill stores its metadata in YAML
frontmatter.

**Exception**: Keep `plugins/tooling/mnemosyne/` in `plugins/`. It contains
Mnemosyne-side command infrastructure and is not a corpus skill.

### Required Fields

**YAML Frontmatter** (in `skills/<name>.md`):

- `name`: Use a lowercase, kebab-case identifier.
- `description`: Give trigger conditions and specific use cases.
- `category`: Use one of the nine approved categories.
- `date`: Give the creation date in `YYYY-MM-DD` format.
- `version`: Give a semantic version such as `1.0.0`.
- `user-invocable`: For an internal skill or subskill, use `false`.
- `tags` (optional): Give an array of searchable keywords.

**Markdown Sections**:

- Overview table with the date, objective, and outcome.
- When to Use section with trigger conditions.
- Verified Workflow section with successful steps and a Quick Reference subsection.
- **Failed Attempts table (REQUIRED)** with all four required columns.
- Results & Parameters section with usable configurations and expected outputs.

The Failed Attempts columns are Attempt, What Was Tried, Why It Failed, and
Lesson Learned.

### Categories

| Category | Description |
| ---------- | ------------- |
| `training` | ML training experiments and hyperparameters |
| `evaluation` | Model evaluation and metrics |
| `optimization` | Performance tuning and speedups |
| `debugging` | Bug investigation and fixes |
| `architecture` | Design decisions and patterns |
| `tooling` | Automation and developer tools |
| `ci-cd` | Pipeline configurations and CI fixes |
| `testing` | Test strategies and patterns |
| `documentation` | Paper writing, academic reviews, knowledge docs |

### Quality Rules

1. **Specific descriptions**: Include trigger conditions. Do not use vague summaries.
2. **Failures required**: Record failed methods. Explain each failure.
3. **Ready to use**: Give parameters and configurations that users can copy.
4. **No duplication**: Link to external documents. Do not copy their content.
5. **Bounded retrieval**: Keep each retrievable main skill at or below 30,000
   bytes. Move raw evidence and long examples to the notes file. Move prior
   versions and provenance to the history file. Keep no more than three
   examples that cover different decisions in the main skill.

### Key Development Principles

1. KISS - *K*eep *I*t *S*imple *S*tupid -> Don't add complexity when a simpler solution works
1. YAGNI - *Y*ou *A*in't *G*onna *N*eed *I*t -> Don't add things until they are required
1. TDD - *T*est *D*riven *D*evelopment -> Write tests to drive the implementation
1. DRY - *D*on't *R*epeat *Y*ourself -> Don't duplicate functionality, data structures, or algorithms
1. SOLID - *S**O**L**I**D* ->
  . Single Responsibility
  . Open-Closed
  . Liskov Substitution
  . Interface Segregation
  . Dependency Inversion
1. Modularity - Develop independent modules through well defined interfaces
1. POLA - *P*rinciple *O*f *L*east *A*stonishment - Create intuitive and predictable interfaces to not surprise users

Relevant links:

- [Core Principles of Software Development](<https://softjourn.com/insights/core-principles-of-software-development>)
- [7 Common Programming Principles](<https://www.geeksforgeeks.org/blogs/7-common-programming-principles-that-every-developer-must-follow/>)
- [Software Development Principles](<https://coderower.com/blogs/software-development-principles-software-engineering>)
- [Clean Coding Principles](<https://www.pullchecklist.com/posts/clean-coding-principles>)

### Cross-Repository Compatibility

Write skills that users can apply in multiple repositories:

1. **No `source:` in frontmatter**: Remove repository-specific source fields.
2. **Use placeholders**: Replace hardcoded paths with `<project-root>`,
   `<test-path>`, and `<package-manager>`.
3. **Add a "Verified On" section**: Record where you validated the skill.
   Use this table:
   ```markdown
   ## Verified On

   | Project | Context | Details |
   |---------|---------|---------|
   | ProjectName | PR #XXX context | [notes.md](./skill-name.notes.md) |
   ```
4. **Move specifics to companions**: Put project-specific commands, paths,
   transcripts, and verification details in `skills/<name>.notes.md`. Put
   version and provenance records in `skills/<name>.history`.
5. **Generic workflows**: Write workflows that users can adapt to each
   repository structure.

**Optional plugin.json fields for cross-repo support**:

- `requires.tools`: Give an array of tool requirements. For example, use
  `[{"name": "mojo", "version": ">=0.25.0"}]`.
- `requires.languages`: Give the applicable programming languages.
- `verified_on`: Give an array of projects where you validated the skill.

## Hooks Configuration

The project uses Claude Code hooks for automatic retrospective prompts.

**Important**: `SessionEnd` hooks cannot show messages to users. Use
`UserPromptSubmit` hooks instead.

**UserPromptSubmit hook**: Session-ending keywords activate this hook. These
keywords include `exit`, `quit`, `clear`, `done`, and `finished`. The hook
reminds users about `/learn`.

**Added in v2.1.0**: Use `once: true` to run a hook one time in a session:

```json
{
  "hooks": [{
    "type": "command",
    "command": "script.sh",
    "once": true
  }]
}
```

Read `.claude/settings.json` for the active configuration. Read
`plugins/tooling/mnemosyne/hooks/settings.json.example` for an example.

**Skill location**: Keep each corpus skill as a flat file in `skills/`. For
example, use `skills/skill-name.md`. The `plugins/tooling/mnemosyne/` directory
is the only documented exception.

## Contributing a Skill

1. After a session contains useful knowledge, run `/learn`.
2. To create a skill manually, copy `templates/skill-template.md` to
   `skills/<name>.md`.
3. Complete the name, description, category, date, and version fields.
4. Complete all required Markdown sections.
5. If raw details are necessary, create `skills/<name>.notes.md`.
6. Use a flat Markdown file with YAML frontmatter. Do not use nested directories.
7. Use this filename format:
   `<topic>-<subtopic>-<short-4-word-summary>.md`.
8. Use lowercase kebab-case for the filename.
9. Before a merge, let CI validate the frontmatter and sections.

## Dependencies

`pyproject.toml` is the **canonical** dependency specification for this project.
ADR-017 defines this requirement. Runtime dependencies are in
`[project.dependencies]`. Development tools are in the uv-native
`[dependency-groups]` development group. `uv.lock` is the committed,
reproducible lockfile.

- Install all dependencies with `uv sync`. You can add `--group dev` explicitly.
- In CI, add `--locked` to the installation command.
- Run tasks with `just validate`, `just test`, `just check`, or `just package`.
- Each recipe uses `uv run`. You do not need to activate an environment.
- Equivalent commands are `uv run python scripts/validate_plugins.py`,
  `uv run python -m pytest tests/`, and `uv build`.

The canonical CI `package` check builds the Python wheel and source distribution
with `uv build`. The package contains `mnemosyne_skill_utils`, the shared skill
parser. The check installs and smoke-tests the wheel.

Mnemosyne does not supply a plugin-marketplace bundle. Athena supplies the
plugin distribution. Mnemosyne stores skills and session memory.

`[project.optional-dependencies] dev` provides pip compatibility for
`pip install .[dev]`. It mirrors the uv development group. The CI
`security/dependency-scan` job uses `pip-audit`. It audits the exact runtime
dependencies that `uv.lock` exports. Do not create separate
`requirements*.txt` mirrors.

## References

- [ProjectOdyssey](https://github.com/HomericIntelligence/ProjectOdyssey): Training platform.
- [ProjectKeystone](https://github.com/HomericIntelligence/ProjectKeystone): DAG execution and task coordination.
- [ProjectScylla](https://github.com/HomericIntelligence/ProjectScylla): Testing.
