"""Check the Git provenance and retrieval contract after history migration."""

import json
import re
from pathlib import Path

from mnemosyne_skill_utils import parse_frontmatter

ROOT = Path(__file__).resolve().parent.parent


def test_removed_histories_have_immutable_sources_and_existing_owners():
    manifest = json.loads((ROOT / "docs/history-migration.json").read_text())
    commit = manifest["source_commit"]
    assert re.fullmatch(r"[0-9a-f]{40}", commit)
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", manifest["cleanup_date"])
    records = manifest["histories"]
    assert len({item["source"] for item in records}) == len(records)
    for item in records:
        assert not (ROOT / item["source"]).exists()
        assert (ROOT / item["owner"]).is_file()
        assert item["source_url"] == (
            f"https://github.com/HomericIntelligence/Mnemosyne/blob/{commit}/{item['source']}"
        )
        assert item["bytes"] > 0
        owner = (ROOT / item["owner"]).read_text()
        assert item["source_url"] in owner
        if item["source"].removesuffix(".history") + ".md" == item["owner"]:
            frontmatter, _, errors = parse_frontmatter(owner)
            assert errors == []
            assert frontmatter["history-source"] == item["source_url"]
            assert frontmatter["history-cleanup-date"] == manifest["cleanup_date"]
            assert "history" not in frontmatter


def test_history_links_resolve_to_git_instead_of_removed_local_companions():
    assert not list((ROOT / "skills").glob("*.history*"))
    for path in (ROOT / "skills").glob("*.md"):
        for target in re.findall(r"\]\(([^)]+)\)", path.read_text()):
            assert not re.fullmatch(r"(?:\./|skills/)?[^/]+\.history(?:#.*)?", target), (path, target)
