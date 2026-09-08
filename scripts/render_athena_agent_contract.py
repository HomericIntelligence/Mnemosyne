#!/usr/bin/env python3
"""Render the pinned Athena agent-contract block."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import sys
from pathlib import Path

CONTRACT_TAG = "agent-contract-v1.0.0"
EXPECTED_RELEASE_INPUT_SHA256 = {
    "scripts/policies/agent_contract.py": "525b845689034544b58176b5e45e60a416e81f017c3bc90f60dcd61e0a50c3d4",
    "docs/principles/README.md": "c79a2824661546182b6fbc0541ca5bd08b666644e74590bf92c7a504abc022b3",
}


def _load_module(module_path: Path):
    spec = importlib.util.spec_from_file_location("athena_agent_contract", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module from {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _verify_release_inputs(root: Path) -> None:
    for relative_path, expected_digest in EXPECTED_RELEASE_INPUT_SHA256.items():
        path = root / relative_path
        actual_digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual_digest != expected_digest:
            raise RuntimeError(
                f"{relative_path} SHA-256 is {actual_digest}; expected {expected_digest} from {CONTRACT_TAG}"
            )


def render_agent_contract(catalog_root: Path) -> str:
    module_path = catalog_root / "scripts" / "policies" / "agent_contract.py"
    if not module_path.is_file():
        raise FileNotFoundError(module_path)

    _verify_release_inputs(catalog_root)
    module = _load_module(module_path)
    principles, errors = module.parse_principles_catalog(catalog_root)
    if errors:
        lines = "\n".join(f"{error.path}: {error.reason}" for error in errors)
        raise RuntimeError(lines)
    return str(module.render_principles_block(principles))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render the Athena release agent-contract block.")
    parser.add_argument(
        "--catalog-root",
        type=Path,
        required=True,
        help="Path to an Athena checkout that contains docs/principles and scripts/policies.",
    )
    args = parser.parse_args(argv)

    try:
        block = render_agent_contract(args.catalog_root)
    except (OSError, RuntimeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1

    sys.stdout.write(block)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
