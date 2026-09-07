"""Test CI runner status through a controlled container executable."""

import json
import os
import shlex
import subprocess
import sys
from pathlib import Path

import pytest

RUNNER = Path(__file__).resolve().parents[1] / "scripts" / "run_ci_local.sh"


@pytest.fixture
def run_ci(tmp_path):
    engine_dir = tmp_path / "container tools"
    engine_dir.mkdir()
    engine = engine_dir / "podman"
    calls = tmp_path / "calls.jsonl"
    engine_script = tmp_path / "engine.py"
    engine_script.write_text(
        "import json, os, sys\n"
        "args = sys.argv[1:]\n"
        "if args == ['image', 'exists', 'mnemosyne-ci:local']:\n"
        "    sys.exit(0)\n"
        "assert args[0] == 'run', args\n"
        "with open(os.environ['CI_TEST_CALLS'], 'a') as output:\n"
        "    output.write(json.dumps(args) + '\\n')\n"
        "with open(os.environ['CI_TEST_CALLS']) as recorded:\n"
        "    count = len(recorded.readlines())\n"
        "sys.exit(7 if count == int(os.environ['CI_TEST_FAIL_AT']) else 0)\n",
        encoding="utf-8",
    )
    engine.write_text(
        f'#!/bin/sh\nexec {shlex.quote(sys.executable)} {shlex.quote(str(engine_script))} "$@"\n',
        encoding="utf-8",
    )
    engine.chmod(0o755)

    def invoke(subset, fail_at=0):
        env = {
            "PATH": str(engine_dir) + os.pathsep + os.defpath,
            "CONTAINER_ENGINE": "podman",
            "CI_TEST_CALLS": str(calls),
            "CI_TEST_FAIL_AT": str(fail_at),
        }
        result = subprocess.run(
            ["bash", str(RUNNER), subset],
            env=env,
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
        assert calls.exists(), result.stderr
        commands = [json.loads(line) for line in calls.read_text().splitlines()]
        for args in commands:
            assert args[:2] == ["run", "--rm"]
            assert args[2] == "--userns=keep-id:uid=1000,gid=1000"
            assert args[3:8] == [
                "--volume",
                f"{RUNNER.parents[1]}:/workspace:Z",
                "--workdir",
                "/workspace",
                "mnemosyne-ci:local",
            ]
        return result, [args[8:] for args in commands]

    return invoke


@pytest.mark.parametrize("subset,fail_at", [("lint", 1), ("lint", 2), ("lint", 3), ("version", 1), ("version", 2)])
def test_each_failed_command_fails_subset(run_ci, subset, fail_at):
    result, commands = run_ci(subset, fail_at)
    assert result.returncode != 0
    assert f"Failed: {subset}" in result.stderr
    assert "All CI checks passed." not in result.stdout
    assert len(commands) >= fail_at


@pytest.mark.parametrize("subset,count", [("lint", 3), ("version", 2), ("all", 9)])
def test_success_runs_every_command(run_ci, subset, count):
    result, commands = run_ci(subset)
    assert result.returncode == 0, result.stderr
    assert len(commands) == count
    assert "All CI checks passed." in result.stdout
    if subset == "lint":
        assert commands[0] == ["uv", "run", "yamllint", "-c", ".yamllint.yaml", ".github/workflows/"]
        assert commands[1] == [
            "bash",
            "-c",
            "if [ -d scripts ] || [ -d tests ]; then uv run python -m mypy; "
            'else echo "No scripts/ or tests/ — skipping mypy"; fi',
        ]
        assert commands[2] == ["uv", "run", "python", "scripts/check_pii.py"]
    if subset == "version":
        assert commands[0] == ["uv", "run", "python", "scripts/validate_plugins.py"]
        assert commands[1][:2] == ["bash", "-c"]


@pytest.mark.parametrize("fail_at,subset", [(3, "lint"), (4, "lint"), (5, "lint"), (7, "version"), (8, "version")])
def test_all_continues_after_failed_subset(run_ci, fail_at, subset):
    result, commands = run_ci("all", fail_at)
    assert result.returncode != 0
    assert f"Failed: {subset}" in result.stderr
    assert "All CI checks passed." not in result.stdout
    assert commands[-1] == ["uv", "run", "python", "scripts/validate_release_contract.py"]
