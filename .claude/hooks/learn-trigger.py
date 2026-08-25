#!/usr/bin/env python3
"""Remind a user about /learn after a session-ending prompt.

This UserPromptSubmit hook adds context. It does not block the prompt.

The reminder requires generated skill prose to follow the repository
ASD-STE100 writing policy at docs/asd-ste100.md.

The hook receives JSON input with these fields:

- prompt: The user's prompt text
- session_id: Session identifier
- cwd: Current working directory

The hook writes JSON to standard output for Claude to process.

Installation:

1. Copy this file to the project .claude/hooks/ directory.
2. Add the hook configuration to .claude/settings.json.
3. Read settings.json.example for an example.
"""

import json
import re
import sys


def main():
    """Main entry point for the hook."""
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    prompt = input_data.get("prompt", "").lower()

    # Check for session-ending keywords
    ending_patterns = [
        r"\b(exit|quit|bye|goodbye)\b",
        r"^/clear\b",
        r"\b(done|finished|wrapping up)\b",
        r"\b(end.*session|session.*end)\b",
    ]

    for pattern in ending_patterns:
        if re.search(pattern, prompt):
            output = {
                "hookSpecificOutput": {
                    "hookEventName": "UserPromptSubmit",
                    "additionalContext": (
                        "[Learn Reminder] Before you end this session, consider "
                        "running /learn to save useful information. If you run "
                        "/learn, write the generated skill prose in ASD-STE100 "
                        "Simplified Technical English. Follow docs/asd-ste100.md."
                    ),
                }
            }
            print(json.dumps(output))
            sys.exit(0)

    # No match, exit silently
    sys.exit(0)


if __name__ == "__main__":
    main()
