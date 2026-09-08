#!/usr/bin/env python3
"""Render the pinned Athena agent-contract block."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import re
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

CONTRACT_TAG = "agent-contract-v1.0.0"
EXPECTED_RELEASE_INPUT_SHA256 = {
    "scripts/policies/agent_contract.py": "525b845689034544b58176b5e45e60a416e81f017c3bc90f60dcd61e0a50c3d4",
    "docs/principles/README.md": "c79a2824661546182b6fbc0541ca5bd08b666644e74590bf92c7a504abc022b3",
}
CATALOG_HEADING = re.compile(r"^### (P\d{3})$")
CATALOG_ENTRY = re.compile(r"^\[(?P<name>[^\]]+)\]\((details/p\d{3}-[a-z0-9-]+\.md)\)(?:\s+—.*)?$")


def _download_text(url: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url, timeout=30) as response:
        destination.write_bytes(response.read())


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


def _prepare_remote_catalog(root: Path, tag: str) -> Path:
    release_base = f"https://raw.githubusercontent.com/HomericIntelligence/Athena/{tag}"
    module_path = root / "scripts" / "policies" / "agent_contract.py"
    readme_path = root / "docs" / "principles" / "README.md"

    _download_text(f"{release_base}/scripts/policies/agent_contract.py", module_path)
    _download_text(f"{release_base}/docs/principles/README.md", readme_path)
    _verify_release_inputs(root)

    detail_paths: list[str] = []
    pending_identifier: str | None = None
    for line in readme_path.read_text(encoding="utf-8").splitlines():
        heading_match = CATALOG_HEADING.fullmatch(line)
        if heading_match is not None:
            pending_identifier = heading_match.group(1)
            continue
        if pending_identifier is None:
            continue
        entry_match = CATALOG_ENTRY.fullmatch(line)
        if entry_match is None:
            continue
        detail_path = entry_match.group(2)
        if not detail_path.startswith(f"details/{pending_identifier.casefold()}-"):
            raise RuntimeError(f"unexpected detail path {detail_path!r} for {pending_identifier}")
        detail_paths.append(detail_path)
        pending_identifier = None

    for detail_path in detail_paths:
        _download_text(
            f"{release_base}/docs/principles/{detail_path}",
            root / "docs" / "principles" / detail_path,
        )

    return module_path


def render_agent_contract(catalog_root: Path | None = None, tag: str = CONTRACT_TAG) -> str:
    if catalog_root is None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            module_path = _prepare_remote_catalog(root, tag)
            module = _load_module(module_path)
            principles, errors = module.parse_principles_catalog(root)
            if errors:
                lines = "\n".join(f"{error.path}: {error.reason}" for error in errors)
                raise RuntimeError(lines)
            return str(module.render_principles_block(principles))

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
        default=None,
        help="Path to an Athena checkout that contains docs/principles and scripts/policies.",
    )
    parser.add_argument(
        "--tag",
        default=CONTRACT_TAG,
        help="Pinned Athena release tag to fetch when no catalog root is supplied.",
    )
    args = parser.parse_args(argv)

    try:
        block = render_agent_contract(args.catalog_root, args.tag)
    except (OSError, RuntimeError, urllib.error.URLError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1

    sys.stdout.write(block)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
