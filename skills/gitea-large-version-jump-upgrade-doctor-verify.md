---
name: gitea-large-version-jump-upgrade-doctor-verify
description: "Upgrade a Dockerized Gitea directly across a very large version gap (e.g. 15 releases, ~6 years) in a single jump, backed by a mandatory pre-flight backup and Gitea's own `gitea doctor check --all` for verification. Use when: (1) a homelab/self-hosted Gitea instance has sat unpatched for years and needs to reach current in one operation, (2) you are unsure whether Gitea enforces staged one-major-at-a-time upgrades like some other self-hosted apps, (3) you need a stronger post-upgrade health signal than 'container is Up' or an HTTP 200 on the login page, (4) `gitea doctor` fails with a root-user error and you need the correct invocation."
category: tooling
date: 2026-07-06
version: "1.0.0"
user-invocable: false
verification: verified-local
tags: []
---

# Gitea Large Version-Jump Upgrade with `doctor` Verification

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-07-06 |
| **Objective** | Upgrade a Dockerized Gitea instance (MySQL/MariaDB backend, ~20GB of repos + LFS across 12 repositories) directly from 1.11.8 (~January 2020) to 1.26.4 in a single jump, rather than staging through ~15 intermediate releases |
| **Outcome** | Successful — single-jump upgrade completed cleanly, confirmed via `gitea doctor check --all` returning all checks OK with zero broken repo units |
| **Verification** | verified-local (executed end-to-end on a live homelab Gitea instance; CI validation pending) |
| **History** | N/A — initial version |

## When to Use

- A Dockerized Gitea instance has been left on an old version for years and needs to reach current in one operation, instead of manually stepping through every intermediate release.
- You are unsure whether Gitea enforces staged, one-major-at-a-time upgrades the way some other self-hosted apps do (e.g. Nextcloud — see `dockerized-nextcloud-major-upgrade.md`, which is NOT applicable here; Gitea's upgrade model is different).
- You need to decide whether a big version jump is safe before attempting it, and want to know Gitea's actual documented failure mode for "too old to migrate."
- The upgraded container reports "healthy" (`Up`, HTTP 200 on login) but you need a stronger, more authoritative signal that repo metadata, DB consistency, and Git object state actually survived the migration.
- `gitea doctor check --all` fails immediately with a root-user error and you need the correct way to invoke it inside the container.

## Verified Workflow

### Quick Reference

```bash
# 1. Mandatory pre-flight backup -- BEFORE touching the running instance.
#    Downgrading after an upgraded DB migration is never possible per Gitea's own docs,
#    so this backup is the only rollback path.

# DB dump (use mariadb-dump on newer MariaDB images, not mysqldump -- binaries removed
# in MariaDB 11.x; see the separate dockerized-mariadb-version-upgrade skill)
docker exec <gitea-db-container> sh -c 'exec mariadb-dump --single-transaction -ugitea -p"$MYSQL_PASSWORD" gitea' > gitea-db-backup.sql

# Full data directory (repos, LFS, ssh host keys, gitea config -- everything under
# Gitea's bind-mounted /data path)
tar -cf gitea-data-backup.tar -C /path/to/parent gitea-data-dir

# VERIFY both before proceeding -- non-empty dump with real SQL content, and a tar
# with a large (not 0 or 1) file count:
head -c 200 gitea-db-backup.sql   # should show real INSERT/CREATE TABLE statements
tar -tf gitea-data-backup.tar | wc -l   # should be in the thousands for a real repo set

# 2. Bump the image tag in the compose file to the target version, then recreate:
docker compose pull gitea
docker compose up -d gitea

# 3. Watch startup logs specifically for the one documented failure signature:
docker logs <gitea-container> 2>&1 | grep -i "too old for auto-migration"
# If this appears: STOP, restore from backup, do not attempt a direct jump -- go through
# an intermediate version first (Gitea's docs mention 1.6.4 as a known-good intermediate
# stop for pre-1.6-era databases specifically).

# 4. The REAL proof of a healthy upgrade -- run Gitea's own built-in health check as the
#    container's actual configured uid (NOT root -- gitea doctor refuses to run as root):
docker exec -u <gitea-uid> <gitea-container> gitea doctor check --all
# A healthy upgrade shows "All done (checks: N)" with every individual check OK.
```

### Detailed Steps

1. **Research the actual failure mode before attempting anything.** Gitea's documentation does not state a maximum number of releases you can skip in one jump for a healthy, moderately-old database. It DOES document what happens when the database is genuinely too old: on startup, if the schema version predates Gitea's supported auto-migration floor (historically around the 1.6.x era, ~2018), Gitea refuses to start with an explicit `DB version is too old for auto-migration` error, rather than silently corrupting data or partially migrating. Gitea's migration system runs ALL pending migrations sequentially at every startup regardless of how many releases behind the DB is — the size of the gap is not itself the blocking factor, only whether the starting version is above Gitea's floor. A 2020-era database (1.11.8) is well past that floor, so a direct jump to 1.26.4 was expected to work, and did.
2. **Take a full backup first, unconditionally.** This is a hard requirement independent of how confident you are in step 1: Gitea's own docs state that downgrading after an upgraded DB migration is never possible. Dump the DB with `mariadb-dump` (not `mysqldump` — removed in newer MariaDB images) and tar the full bind-mounted data directory (repos, LFS objects, SSH host keys, config). Verify both artifacts are non-trivial before proceeding — a near-empty dump or a tar with a handful of entries means the backup itself is broken, and proceeding on a broken backup defeats the entire point of taking one.
3. **Bump the image tag and recreate.** `docker compose pull gitea && docker compose up -d gitea`. Note: recreating a service via a modern `docker compose` binary when the stack was originally created by an older v1 `docker-compose` binary can also recreate a sibling `db` service that has no explicit `container_name` — this is a separate, already-known naming-convention gotcha and does NOT indicate the Gitea upgrade itself is broken, as long as the DB's data lives on a bind-mounted host path rather than an anonymous volume.
4. **Grep startup logs for the one documented failure signature**, not just "did the container start." `docker logs <container> | grep -i "too old for auto-migration"`. If present, stop immediately, restore from backup, and go through an intermediate version instead (1.6.4 is Gitea's documented known-good intermediate stop for pre-1.6-era databases).
5. **Verify with `gitea doctor check --all`, run as the container's actual configured uid.** This is a far stronger signal than "container is Up" or an HTTP 200 on the login page — a broken migration could still serve a login page while repo metadata or DB consistency is actually corrupted underneath. `gitea doctor` refuses to run as root with `Gitea is not supposed to be run as root`, so it must be invoked with `docker exec -u <uid>` using the container's actual configured `USER_UID`/`USER_GID` (commonly something like 1002, not the default `www-data` or root). A healthy upgrade prints `All done (checks: N)` with every individual check OK — including repo HEAD consistency, merge-base recalculation, commit-graph state, user email/username validity, and orphaned actions-run status.
6. **Do not treat absence of "migrating..." log lines as a red flag.** For a modest-sized DB (~200MB), Gitea's migrations can complete fast enough that there is no distinguishable "migrating..." log line at all. Trust `gitea doctor check --all` and the actual web/API response over grep'ing for a specific log phrase that may not appear even on a fully successful migration.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Assumed a 15-version jump would need manual staging through intermediate releases | Based on vague memory of other self-hosted apps (e.g. Nextcloud) enforcing "one major at a time" | Gitea's actual architecture (a sequential migration runner keyed off the DB schema version, not a hard per-release gate) does not work that way — only researched this properly instead of assuming | Don't carry an assumption from one self-hosted app's upgrade model over to another. Nextcloud genuinely cannot skip majors; Gitea can, as long as the starting DB version is above its auto-migration floor |
| `docker exec <container> gitea doctor check --all` with no `-u` flag | Ran the doctor command against the container using its default entrypoint user | Failed immediately with `mustNotRunAsRoot` — a red herring that looks like a real upgrade problem but is just an invocation mistake | Gitea images commonly run via a `USER_UID`/`USER_GID` env var (e.g. 1002), not `www-data` or root. Always pass `-u <uid>` matching the container's actual configured uid to get the real doctor result |
| Treated `docker logs <container> \| grep -i migrat` returning nothing as ambiguous or concerning | Searched logs for a generic "migrat" substring expecting to see progress output | For a modest-sized DB (~200MB), migrations complete fast enough that no distinguishable "migrating..." log line appears at all, even on full success | Absence of migration-log-noise is not itself a red flag. Trust `gitea doctor check --all` and the actual web/API response instead of grep'ing for a specific log phrase that may not appear even on success |

## Results & Parameters

```bash
# Versions
FROM_VERSION=1.11.8   # released ~January 2020
TO_VERSION=1.26.4     # target, 15 releases / ~6 years later

# Scale
REPO_COUNT=12
DATA_SIZE=~20GB       # repos + LFS objects

# Backup verification thresholds
MIN_SQL_DUMP_NONEMPTY=true       # head -c 200 must show real INSERT/CREATE TABLE statements
MIN_TAR_ENTRY_COUNT_THOUSANDS=true  # tar -tf ... | wc -l should be in the thousands

# The one documented hard-failure signature to grep startup logs for:
FAILURE_SIGNATURE="DB version is too old for auto-migration"
# Known-good intermediate stop if that signature appears (pre-1.6-era DBs only):
INTERMEDIATE_VERSION=1.6.4

# Doctor invocation (must use the container's real configured uid, not root/www-data)
docker exec -u <gitea-uid> <gitea-container> gitea doctor check --all
```

### Expected Output

- `gitea doctor check --all` on a healthy upgrade: `All done (checks: N)`, with every individual check OK — repo HEAD consistency, merge-base recalculation, commit-graph state, user email/username validity, orphaned actions-run status all clean. Observed this session: 28 checks OK, zero broken repo units, correct merge bases, synced HEADs, valid user records.
- Startup logs: absence of `DB version is too old for auto-migration` means the jump is proceeding past Gitea's auto-migration floor; presence means stop and restore from backup.
- A broken migration can still return an HTTP 200 on the login page — do not treat that as sufficient evidence of a healthy upgrade on its own.

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| Homelab | Live production Dockerized Gitea, 1.11.8 to 1.26.4, 12 repositories, ~20GB | Executed end-to-end this session; verified-local via `gitea doctor check --all` (28 checks OK) |

## References

- [Gitea upgrade documentation](https://docs.gitea.com/installation/upgrade-from-gitea)
- [`gitea doctor` command reference](https://docs.gitea.com/administration/command-line#doctor)
- [dockerized-mariadb-version-upgrade.md](dockerized-mariadb-version-upgrade.md) — companion skill for the underlying MariaDB version upgrade and `mariadb-dump` vs `mysqldump` gotcha
- [dockerized-nextcloud-major-upgrade.md](dockerized-nextcloud-major-upgrade.md) — contrast only: Nextcloud's upgrade model requires strict one-major-at-a-time steps and does NOT apply to Gitea
