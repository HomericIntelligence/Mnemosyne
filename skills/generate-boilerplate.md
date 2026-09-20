---
name: generate-boilerplate
license: BSD-3-Clause
description: Create starter code from templates. Use when setting up new modules or
  test files.
category: tooling
date: '2026-03-19'
version: "1.1.0"
mcp_fallback: none
tier: 1
history-source: "https://github.com/HomericIntelligence/Mnemosyne/blob/1956c91d76867bc2e484eaf573a57051855186f8/skills/generate-boilerplate.history"
history-cleanup-date: "2026-09-20"
---
# Generate Boilerplate

## Overview

| Item | Details |
| ------ | --------- |
| Date | N/A |
| Objective | Create standard starter code templates for new modules, test files, and configuration files to accelerate development. |
| Outcome | Operational |

Create standard starter code templates for new modules, test files, and configuration files to accelerate development.

## When to Use

- Creating new modules or packages
- Setting up test file structure
- Initializing configuration files
- Standardizing code structure across project

### Quick Reference

```bash
# Generate from templates
cat > new_module.py << 'EOF'
"""Module docstring describing purpose."""

def main():
    """Main function."""
    pass

if __name__ == "__main__":
    main()
EOF

# Or use template generator
python3 << 'PYSCRIPT'
import os
def generate_module_boilerplate(name):
    return f'"""Module {name}."""\n\nclass {name.title()}:\n    pass\n'
PYSCRIPT
```

## Verified Workflow

1. **Select template type**: Module, test, config, etc.
2. **Customize parameters**: Name, class structure, default content
3. **Generate file**: Create from template with substitutions
4. **Add to project**: Place in correct location
5. **Check useful structure**: Confirm imports and basic syntax as appropriate; when implementation is requested, continue from the scaffold to working behavior

## Output Format

Generated boilerplate:

- File(s) created with correct naming
- Standard header comments and docstrings
- Basic structure (class/function stubs)
- Import statements included
- Ready to compile/run (no syntax errors)

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| N/A | Direct approach worked | N/A | Solution was straightforward |
## Results & Parameters

N/A — this skill describes a workflow pattern.

## References

- See templates/ directories in skill folders for examples
- See `generate-docstrings` skill for docstring templates
- See CLAUDE.md > Code Standards for project conventions
