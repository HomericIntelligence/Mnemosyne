#!/bin/bash
# Run the Mnemosyne CI suite locally inside a container.
#
# Mirrors what GitHub Actions runs, using the same CI container image.
# Supports both Podman (rootless, no SU — preferred) and Docker.
#
# Usage:
#   ./scripts/run_ci_local.sh                 # Run all CI checks
#   ./scripts/run_ci_local.sh validate        # Skill-file validation
#   ./scripts/run_ci_local.sh test            # pytest unit tests
#   ./scripts/run_ci_local.sh lint            # yamllint + mypy + PII check
#   ./scripts/run_ci_local.sh schema          # Workflow YAML schema validation
#   ./scripts/run_ci_local.sh version         # deps/version-sync checks
#   ./scripts/run_ci_local.sh release         # Release-contract dry-run
#
# Container engine: auto-detected (podman first, docker fallback).
# Override: CONTAINER_ENGINE=docker ./scripts/run_ci_local.sh
#
# Image: built locally from ci/Containerfile — run `just ci-build` first.

set -euo pipefail

# ============================================================================
# Configuration
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
SUBSET="${1:-all}"

LOCAL_IMAGE="mnemosyne-ci:local"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info()  { echo -e "${GREEN}[CI]${NC} $*"; }
log_warn()  { echo -e "${YELLOW}[CI]${NC} $*"; }
log_error() { echo -e "${RED}[CI]${NC} $*" >&2; }
log_step()  { echo -e "\n${BLUE}==>${NC} $*"; }

# ============================================================================
# Container engine detection
# ============================================================================

detect_engine() {
    if [ -n "${CONTAINER_ENGINE:-}" ]; then
        if ! command -v "${CONTAINER_ENGINE}" &> /dev/null; then
            log_error "CONTAINER_ENGINE=${CONTAINER_ENGINE} not found in PATH"
            exit 1
        fi
        log_info "Container engine: ${CONTAINER_ENGINE} (from env)"
        return
    fi

    if command -v podman &> /dev/null; then
        CONTAINER_ENGINE="podman"
        log_info "Container engine: podman (rootless)"
    elif command -v docker &> /dev/null; then
        CONTAINER_ENGINE="docker"
        log_info "Container engine: docker"
    else
        log_error "No container engine found. Install podman (recommended) or docker."
        log_error "  Podman: https://podman.io/getting-started/installation"
        exit 1
    fi
    export CONTAINER_ENGINE
}

# ============================================================================
# Image resolution
# ============================================================================

resolve_image() {
    if "${CONTAINER_ENGINE}" image exists "${LOCAL_IMAGE}" 2>/dev/null || \
       "${CONTAINER_ENGINE}" images -q "${LOCAL_IMAGE}" 2>/dev/null | grep -q .; then
        CI_IMAGE="${LOCAL_IMAGE}"
        log_info "Using local CI image: ${CI_IMAGE}"
    else
        log_error "Local image '${LOCAL_IMAGE}' not found."
        log_error "Build it first: just ci-build"
        log_error "  (podman build -f ci/Containerfile -t ${LOCAL_IMAGE} .)"
        exit 1
    fi
    export CI_IMAGE
}

# ============================================================================
# Run a command inside the CI container
# ============================================================================
# Volume mounts:
#   /workspace  — the full repo (rw, :Z for SELinux/Podman)
# --userns=keep-id:uid=1000,gid=1000 — run as the image's non-root 'ci' user
# while mapping it to the invoking host UID, so mounted-file ownership works on
# both dev hosts (uid 1000) and GitHub runners (uid 1001).

run_in_container() {
    local cmd=("$@")
    local engine_flags=()

    if [ "${CONTAINER_ENGINE}" = "podman" ]; then
        engine_flags+=(--userns=keep-id:uid=1000,gid=1000)
    fi

    "${CONTAINER_ENGINE}" run --rm \
        "${engine_flags[@]}" \
        --volume "${PROJECT_ROOT}:/workspace:Z" \
        --workdir /workspace \
        "${CI_IMAGE}" \
        "${cmd[@]}"
}

# ============================================================================
# CI steps
# ============================================================================

run_validate() {
    log_step "Validate skill files"
    run_in_container uv run python scripts/validate_plugins.py
}

run_test() {
    log_step "Unit tests (pytest)"
    run_in_container uv run python -m pytest tests/ -v
}

run_lint() {
    log_step "Lint (yamllint, mypy, PII check)"
    run_in_container uv run yamllint -c .yamllint.yaml .github/workflows/
    run_in_container bash -c 'if [ -d scripts ] || [ -d tests ]; then uv run python -m mypy; else echo "No scripts/ or tests/ — skipping mypy"; fi'
    run_in_container uv run python scripts/check_pii.py
}

run_schema() {
    log_step "Workflow YAML schema validation"
    run_in_container uvx check-jsonschema --builtin-schema vendor.github-workflows .github/workflows/*.yml
}

run_version() {
    log_step "Version-sync checks"
    run_in_container uv run python scripts/validate_plugins.py
    run_in_container bash -c 'ver=$(uv run python -c '\''import tomllib; print(tomllib.load(open("pyproject.toml", "rb"))["project"]["version"])'\''); echo "pyproject version: $ver"; printf "%s" "$ver" | grep -qE "^[0-9]+\.[0-9]+\.[0-9]+$" || { echo "pyproject version is not semver: $ver"; exit 1; }'
}

run_release() {
    log_step "Release-contract dry-run"
    run_in_container uv run python scripts/validate_release_contract.py
}

# ============================================================================
# Main
# ============================================================================

FAILED=()

run_step() {
    local name="$1"
    local fn="$2"
    if ! "${fn}"; then
        FAILED+=("${name}")
        log_error "${name} FAILED"
    fi
}

detect_engine
resolve_image

log_info "CI subset: ${SUBSET}"
log_info "Project root: ${PROJECT_ROOT}"

case "${SUBSET}" in
    validate)
        run_step "validate" run_validate
        ;;
    test)
        run_step "test" run_test
        ;;
    lint)
        run_step "lint" run_lint
        ;;
    schema)
        run_step "schema" run_schema
        ;;
    version)
        run_step "version" run_version
        ;;
    release)
        run_step "release" run_release
        ;;
    all)
        run_step "validate" run_validate
        run_step "test" run_test
        run_step "lint" run_lint
        run_step "schema" run_schema
        run_step "version" run_version
        run_step "release" run_release
        ;;
    *)
        log_error "Unknown subset: ${SUBSET}"
        log_error "Valid values: all, validate, test, lint, schema, version, release"
        exit 1
        ;;
esac

echo ""
if [ "${#FAILED[@]}" -eq 0 ]; then
    log_info "All CI checks passed."
else
    log_error "Failed: ${FAILED[*]}"
    exit 1
fi
