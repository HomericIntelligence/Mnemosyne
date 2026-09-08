#!/usr/bin/env python3
"""Regenerate the root AGENTS.md agent-contract block."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
RENDERER = REPO_ROOT / "scripts" / "render_athena_agent_contract.py"
BLOCK_START = "<!-- BEGIN ATHENA DEVELOPMENT PRINCIPLES: agent-contract-v1.0.0 -->"
BLOCK_END = "<!-- END ATHENA DEVELOPMENT PRINCIPLES -->"


def _extract_block_bounds(text: str) -> tuple[int, int]:
    start = text.find(BLOCK_START)
    end = text.find(BLOCK_END)
    if start == -1 or end == -1 or end <= start:
        raise ValueError("AGENTS.md must contain one generated development-principles block.")
    start_line_end = text.find("\n", start)
    end_line_start = text.rfind("\n", 0, end)
    if start_line_end == -1 or end_line_start == -1:
        raise ValueError("AGENTS.md generated block markers must stand alone on their own lines.")
    return start, end + len(BLOCK_END)


def _render_block(catalog_root: Path) -> str:
    command = [sys.executable, str(RENDERER), "--catalog-root", str(catalog_root)]
    result = subprocess.run(command, capture_output=True, check=False, text=True)
    if result.returncode != 0:
        message = result.stderr.strip() or "Athena contract renderer failed."
        raise RuntimeError(message)
    return result.stdout


def _regenerate(root: Path, catalog_root: Path) -> str:
    agents_path = root / "AGENTS.md"
    content = agents_path.read_text(encoding="utf-8")
    block_start, block_end = _extract_block_bounds(content)
    block = _render_block(catalog_root)
    return content[:block_start] + block + content[block_end:]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Regenerate root AGENTS.md.")
    parser.add_argument("--root", type=Path, default=REPO_ROOT)
    parser.add_argument("--athena-root", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)

    try:
        regenerated = _regenerate(args.root, args.athena_root)
    except (OSError, RuntimeError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1

    current = (args.root / "AGENTS.md").read_text(encoding="utf-8")
    if args.check:
        if regenerated != current:
            print("AGENTS.md differs from the Athena release regeneration.", file=sys.stderr)
            return 1
        return 0

    sys.stdout.write(regenerated)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
