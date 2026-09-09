# Mnemosyne command runner — wraps Python scripts for consistent developer experience.
# All path variables are configurable at the top of the file.
# Recipes run under uv (ADR-017): `uv run` resolves the locked environment from
# pyproject.toml + uv.lock, so no separate activation step is needed.

# Directory containing skill markdown files
skills_dir := "skills"

# Directory containing test files
test_dir := "tests"

# === Default ===

# List available recipes
default:
    @just --list

# === Validation ===

# Validate all skill files in the skills/ directory
validate:
    uv run python scripts/validate_plugins.py

# === Packaging ===

# Build the Python wheel + sdist (mnemosyne_skill_utils) into dist/
package:
    uv build

# === Testing ===

# Run the fast test tier used by pull-request CI
test:
    uv run python -m pytest {{ test_dir }} -m 'not nightly' -q

# Run the nightly test tier
test-nightly:
    uv run python -m pytest {{ test_dir }} -m nightly -v

# === Composite ===

# Run validate + test (full check)
check: validate test

# === Containerized CI (podman by default) ===

# Build the CI container image (podman first, docker fallback)
ci-build:
    podman build -f ci/Containerfile -t mnemosyne-ci:local . || docker build -f ci/Containerfile -t mnemosyne-ci:local .

# Run CI skill-file validation in container
ci-validate:
    ./scripts/run_ci_local.sh validate

# Run the fast CI test tier in container
ci-test:
    ./scripts/run_ci_local.sh test

# Run the nightly CI test tier in container
ci-test-nightly:
    ./scripts/run_ci_local.sh nightly-test

# Run CI lint (yamllint, mypy, PII) in container
ci-lint:
    ./scripts/run_ci_local.sh lint

# Run CI workflow schema validation in container
ci-schema:
    ./scripts/run_ci_local.sh schema

# Run CI version-sync checks in container
ci-version:
    ./scripts/run_ci_local.sh version

# Run CI release-contract dry-run in container
ci-release:
    ./scripts/run_ci_local.sh release

# Run all CI checks in container
ci-all:
    ./scripts/run_ci_local.sh all
