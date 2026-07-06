---
name: nextcloud-appapi-harp-deploy-daemon
description: "Register a Nextcloud AppAPI deploy daemon on a single Docker host using HaRP (HTTP+Reverse Proxy), the current non-deprecated method required to install External Apps (Ex-Apps). Use when: (1) the Nextcloud admin overview shows an 'AppAPI deploy daemon' warning and you need Ex-Apps to install, (2) occ warns that Direct Docker access / Docker Socket Proxy is deprecated and prints 'please register a HaRP-based daemon instead (pass --harp)', (3) migrating a Nextcloud 34 install off the removed-in-NC35 docker-socket-proxy daemon (ghcr.io/nextcloud/nextcloud-appapi-dsp) onto HaRP, (4) app_api:daemon:register fails to reach Ex-App containers because --net used the short compose alias instead of the real compose-prefixed docker network name, (5) the HaRP shared key silently registers blank because the haproxy password file was created root-owned by a container and read back empty."
category: tooling
date: 2026-06-25
version: "1.0.0"
user-invocable: false
verification: verified-local
tags: []
---

# Nextcloud AppAPI HaRP Deploy Daemon (Single Docker Host)

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-06-25 |
| **Objective** | Register a Nextcloud AppAPI "deploy daemon" (required to install External Apps / Ex-Apps) on one Docker host using HaRP, the current non-deprecated method. |
| **Outcome** | Success. `docker_harp` daemon registered as default with `Is HaRP: yes`; admin-overview "AppAPI deploy daemon" warning cleared. Verified live this session on NC34. |

## When to Use

Apply this skill when:
- The Nextcloud admin **Overview** page shows an "AppAPI deploy daemon" warning and you cannot install Ex-Apps.
- `occ` prints: `Direct Docker access (Docker Socket Proxy) is deprecated and will be removed in Nextcloud 35. Please register a HaRP-based daemon instead (pass --harp).`
- You are on a single Docker host (Nextcloud + Ex-Apps colocated) and want the deploy daemon that survives the NC35 upgrade.
- You previously registered the old **docker-socket-proxy** daemon (image `ghcr.io/nextcloud/nextcloud-appapi-dsp`) and need to replace it — that image is deprecated on NC34 and **removed in NC35**.

## Verified Workflow

### Quick Reference

```bash
# 1. Run the HaRP container: image ghcr.io/nextcloud/nextcloud-appapi-harp:release
#    Env: HP_SHARED_KEY=<key>, NC_INSTANCE_URL=https://<nextcloud-domain>
#    Mounts: /var/run/docker.sock + a /certs volume. Same docker network as Nextcloud.
#    NO published host ports: Ex-Apps tunnel OUT to HaRP over FRP.
#    Internal ports only: 8780 (NC<->HaRP HTTP), 8782 (FRP tunnel).

# 2. Find the REAL compose-prefixed docker network name (NOT the short alias):
docker network ls
docker inspect -f '{{range $k,$v := .NetworkSettings.Networks}}{{$k}} {{end}}' nextcloud_nextcloud_1

# 3. Read the shared key correctly (chown first so a plain cat is not empty):
#    (the haproxy password file may be root-owned from a container-run deploy)

# 4. Register the daemon, running occ as the web PUID (e.g. 1002):
docker exec -u 1002 nextcloud_nextcloud_1 php occ \
  app_api:daemon:register docker_harp "HaRP (Host)" docker-install http \
  appapi-harp:8780 https://<nextcloud-domain> \
  --net=<REAL_DOCKER_NETWORK> --harp --harp_shared_key="<key>" \
  --harp_frp_address=appapi-harp:8782 --set-default --compute_device=cpu

# 5. Validate:
docker exec -u 1002 nextcloud_nextcloud_1 php occ app_api:daemon:list
```

### Detailed Steps

1. **Run the HaRP container** on the same host, attached to the **same docker network** as the
   Nextcloud container. Image `ghcr.io/nextcloud/nextcloud-appapi-harp:release`. Required env:
   `HP_SHARED_KEY=<key>` and `NC_INSTANCE_URL=https://<nextcloud-domain>`. Mount
   `/var/run/docker.sock:/var/run/docker.sock` and a `/certs` volume. Do **not** publish host
   ports: Ex-Apps tunnel outward to HaRP over FRP ("no need to expose any ports or open any
   firewall rules"). HaRP uses port 8780 for NC-to-HaRP HTTP and 8782 for the FRP tunnel,
   internally on the docker network.
2. **Resolve the real docker network name.** Run `docker network ls` and
   `docker inspect -f '{{range $k,$v := .NetworkSettings.Networks}}{{$k}} {{end}}' <nc-container>`.
   Compose prefixes network names with the project name, so the real name is e.g.
   `nextcloud_nextcloud`, **not** the short compose alias `nextcloud`.
3. **Obtain the shared key value.** If the haproxy password / `HP_SHARED_KEY` file was created by a
   container-run deploy it may be root-owned; `chown` it to the host user (or read via the
   container) before you `cat` it, otherwise you get an empty string.
4. **Register the daemon** by running `occ` as the web PUID (e.g. `docker exec -u 1002 <nc-container> php occ`)
   with `app_api:daemon:register` using `--harp`, `--harp_shared_key`, `--harp_frp_address`,
   `--set-default`, and the **real** `--net` value. See Results & Parameters for the full command.
5. **Validate** with `occ app_api:daemon:list` (expect `Is HaRP: yes` and Default `*`), confirm the
   admin-overview "AppAPI deploy daemon" warning clears, and check HaRP container logs for
   `Starting FRP server on 0.0.0.0:8782`, `login to server success`, and
   `proxy added: [bundled-deploy-daemon]`. Optionally install a small Ex-App to exercise
   pull -> create -> start.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Socket-proxy daemon first | Registered the old docker-socket-proxy deploy daemon (`ghcr.io/nextcloud/nextcloud-appapi-dsp`). Works on NC34. | Left a persistent "not using HaRP, please switch" warning and is **removed in Nextcloud 35**. | Use HaRP (`--harp`) from the start; do not register the socket-proxy daemon on NC34+. |
| Blank shared key | Read `HP_SHARED_KEY` / haproxy password file with a plain `cat`; the file was root-owned from the container-run deploy. | `cat` returned empty, so register succeeded with a BLANK key -> auth mismatch between NC and HaRP. | `chown` the password file to the host user (or read it through the container) before reading; pass the real value. |
| Short network alias in `--net` | Passed `--net=nextcloud` (the short compose service/alias). | AppAPI could not reach the Ex-App containers it creates: `--net` must be the compose-PREFIXED network (e.g. `nextcloud_nextcloud`). | Always resolve the real network via `docker network ls` / `docker inspect`; never use the short alias. |
| Relied on `daemon:check` | Trusted `app_api:daemon:check` to confirm success. | Its output was unhelpful / garbled. | Use `app_api:daemon:list` (shows `Is HaRP: yes`, Default `*`), the admin-overview row going green, and HaRP logs as the authoritative success signals. |

## Results & Parameters

### Configuration

Register command (run `occ` as the web PUID, e.g. `1002`):

```bash
docker exec -u 1002 nextcloud_nextcloud_1 php occ \
  app_api:daemon:register docker_harp "HaRP (Host)" docker-install http \
  appapi-harp:8780 https://<nextcloud-domain> \
  --net=<REAL_DOCKER_NETWORK> --harp --harp_shared_key="<key>" \
  --harp_frp_address=appapi-harp:8782 --set-default --compute_device=cpu
```

Key parameters:
- Image: `ghcr.io/nextcloud/nextcloud-appapi-harp:release`
- Env: `HP_SHARED_KEY=<key>`, `NC_INSTANCE_URL=https://<nextcloud-domain>`
- Mounts: `/var/run/docker.sock:/var/run/docker.sock` and a `/certs` volume
- Internal ports: `8780` (NC<->HaRP HTTP), `8782` (FRP tunnel) — **no host publishing needed**
- `--net` MUST be the compose-prefixed network (e.g. `nextcloud_nextcloud`), not the alias
- `--harp_frp_address=appapi-harp:8782`, `--set-default`, `--compute_device=cpu`

### Expected Output

Success signals:
- `occ app_api:daemon:list` shows the `docker_harp` daemon with `Is HaRP: yes` and Default `*`.
- Admin **Overview** "AppAPI deploy daemon" warning clears (row goes green ✓).
- HaRP container logs show `Starting FRP server on 0.0.0.0:8782`, `login to server success`,
  `proxy added: [bundled-deploy-daemon]`, and a healthy container.
- Optional: a small Ex-App installs cleanly (pull -> create -> start).

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| homelab (Nextcloud 34, single Docker host) | Registered `docker_harp` HaRP deploy daemon live; admin-overview warning cleared | Deployed this session |
