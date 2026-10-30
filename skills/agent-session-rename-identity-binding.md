---
name: agent-session-rename-identity-binding
license: BSD-3-Clause
description: "Bind the exact session identifier before a session-rename ceremony; never select the target session by title match."
category: tooling
date: 2026-10-30
version: "1.0.0"
user-invocable: false
verification: verified-local
tags: [session-rename, session-id, completion-ceremony, fleet, identity-binding, opencode]
---

# Agent Session Rename Identity Binding

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-30 |
| **Objective** | Select the correct session for a rename ceremony when a host runs many agent sessions |
| **Outcome** | Successful — exact identifier bound from the environment; rename applied to the intended session |
| **Verification** | verified-local |

## When to Use

- A completion or done protocol requires renaming the current session, for example replacing a
  leading status prefix in its title.
- Several sessions on the same host carry similar or identical titles.
- A rename must preserve the remainder of the current title unchanged.

## Core Rule

A session title is not an identity. Fleet hosts run many sessions with near-duplicate titles at
the same time. Before any rename, bind the exact session identifier from the environment of the
current session. Rename by identifier, never by a title match.

## Procedure

1. Read the session identifier from the environment. In an OpenCode context the variable is
   `OPENCODE_SESSION_ID`.
2. Confirm the binding with the session list interface (for example `opencode session list`).
   Match on the identifier, not on the title. Read the exact current title for that identifier.
3. Build the new title from the read title: change only the required prefix and keep every other
   character unchanged.
4. Apply the rename to the bound identifier. Report the old title, the new title, and the
   identifier.
5. If the environment variable is absent, stop and report. Do not guess a session from a partial
   title match.

## Failure Modes

| Failure | Cause | Result | Mitigation |
| ------- | ----- | ------ | ---------- |
| Rename by title substring | Assumed a unique title | A parallel session with a near-identical title receives or loses the rename | Bind the identifier from the environment first |
| Reconstruct the title from memory | Assumed the session summary holds the exact title | Remainder drift: the new title differs from the old in more than the prefix | Read the live title for the bound identifier before the write |
| Best-guess rename without an identifier | Environment variable not read | Wrong-session write, discovered only after the fact | No identifier, no rename; stop and report |

## Evidence

A done protocol required one session rename on a host that ran several sessions whose titles
shared the same status prefix and similar wording. A title-based search could not isolate the
target. Reading the session identifier from the environment gave an exact binding, and the live
title for that identifier gave the exact remainder to preserve. The rename touched the intended
session only.
