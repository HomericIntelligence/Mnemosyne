#!/usr/bin/env python3
"""Shared pytest configuration and validator test content."""

import sys
from pathlib import Path

_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

CLEAN_SKILL_MD = """\
---
name: test-skill
description: "A test skill."
category: tooling
date: 2026-01-01
version: "1.0.0"
user-invocable: false
---

# Test Skill

## Overview

| Field | Value |
|-------|-------|
| Date | 2026-01-01 |
| Objective | Test |
| Outcome | Pass |

## When to Use

- When testing

## Verified Workflow

### Step 1

Do the thing.

## Failed Attempts

| Attempt | Why Failed | Lesson |
|---------|------------|--------|
| N/A | No failures | Document as they occur |

## Results & Parameters

N/A
"""
