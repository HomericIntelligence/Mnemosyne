---
name: homelab-nextcloud-data-dir-nfs-migration
description: "Relocate the Nextcloud /data directory between storage tiers in HomelabOS (local NVMe/USB <-> NFS NAS) while keeping core (webroot, config, apps, DB) on fast storage, with a reboot-safe live cutover. Use when: (1) moving the Nextcloud data dir from local disk to a NAS NFS share, (2) moving it OFF a slow NFS share onto a fast local disk because uploads time out, (3) HomelabOS Nextcloud compose has NFS bind mounts but NFS mounted after container start, (4) rsyncing to/from a share with root_squash, (5) making the data dir bind reboot-safe with fstab + RequiresMountsFor."
category: architecture
date: 2026-06-28
version: "1.1.0"
user-invocable: false
verification: verified-local
history: homelab-nextcloud-data-dir-nfs-migration.history
tags: []
---

# Homelab Nextcloud Data Directory Relocation (NFS <-> Local)

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-06-28 |
| **Objective** | Relocate Nextcloud's `/data` directory between storage tiers in HomelabOS — local NVMe/USB <-> NFS NAS — keeping core (webroot, config, apps, DB) on fast storage, with a reboot-safe live cutover |
| **Outcome** | Successful in both directions: 271 GB moved local NVMe -> NFS NAS (v1.0.0); `/data` moved OFF a slow NFS share onto a fast local disk to fix upload timeouts (v1.1.0) |
| **Verification** | verified-local (executed end-to-end on a live HomelabOS v1.0 host; CI validation pending) |
| **History** | [changelog](./homelab-nextcloud-data-dir-nfs-migration.history) |

## When to Use

- Moving the Nextcloud data directory from local disk to a NAS NFS share
- Moving the Nextcloud data directory OFF a slow NFS share onto a fast local disk because uploads/metadata are timing out (only `/data` is slow; core + DB are already on fast storage)
- HomelabOS Nextcloud compose already has the NFS path in the bind mount but NFS was mounted after container start (data silently stayed on local disk)
- Rsyncing large data sets to/from an NFS share with root_squash (files must be owned by the Nextcloud uid, not root)
- Making the `/data` bind reboot-safe so Nextcloud never starts against an empty mountpoint (fstab + systemd `RequiresMountsFor`)
- Changing a HomelabOS service bind persistently (must edit BOTH the Jinja template and the rendered compose)

## Verified Workflow

> Verified locally only — CI validation pending.

This skill covers relocating `/data` in **either direction**. Scenario A (Quick Reference +
Detailed Steps below) moves data **local -> NFS**. Scenario B moves data **off slow NFS ->
fast local disk** and adds the reboot-safety hardening. The same core gotchas apply to both:
rsync as the data-owner uid (root_squash), keep the `.ocdata` marker, and keep the old copy as
a fail-safe/rollback.

### HomelabOS service structure (read first)

Each HomelabOS service is rendered from
`roles/<svc>/templates/docker-compose.<svc>.yml.j2` -> `/var/homelabos/<svc>/docker-compose.yml`
(the rendered file, owned by the `homelab` user) and run by a systemd unit `<svc>.service`
whose `ExecStart` is `docker-compose -p <svc> up` (`WorkingDirectory=/var/homelabos/<svc>`).
So you restart a service with `systemctl restart <svc>`, and any change must go in **BOTH**:

- the **template** (`roles/<svc>/templates/...j2` + `settings/config.yml`) — for persistence across `ansible` redeploys, and
- the **rendered compose** (`/var/homelabos/<svc>/docker-compose.yml`) — for immediate effect.

The rendered compose is owned by `homelab`, so the Edit/Write tool fails with EACCES — edit it
with `sudo sed` / `sudo tee`.

### Quick Reference

```bash
# --- Scenario A: relocate local data -> NFS NAS ---
# 1. Expose hidden local data beneath NFS mount
sudo mount --bind / /mnt/root-view

# 2. Pass 1 rsync (online, no downtime) — run as Nextcloud uid 1002
sudo -u '#1002' -g '#1002' rsync -rltD --partial --info=progress2 \
  /mnt/root-view/mnt/nas/Documents/NextCloud/ \
  /mnt/nas/Documents/NextCloud/

# 3. Enable maintenance mode + stop container
docker exec nextcloud_nextcloud_1 php occ maintenance:mode --on
docker compose -f /var/homelabos/nextcloud/docker-compose.yml stop nextcloud

# 4. Pass 2 rsync (delta, while offline)
sudo -u '#1002' -g '#1002' rsync -rltD --partial --info=progress2 \
  /mnt/root-view/mnt/nas/Documents/NextCloud/ \
  /mnt/nas/Documents/NextCloud/

# 5. Verify before cutover
diff <(cd /mnt/root-view/mnt/nas/Documents/NextCloud && find . | sort) \
     <(cd /mnt/nas/Documents/NextCloud && find . | sort)
# Must produce no output

# 6. Start container (NFS already mounted, bind resolves to NFS)
docker compose -f /var/homelabos/nextcloud/docker-compose.yml up -d nextcloud

# 7. Confirm data is on NAS
docker exec nextcloud_nextcloud_1 df -h /data
# Must show NFS server IP (e.g., 192.168.2.11:/data/Documents/NextCloud)

# 8. Disable maintenance mode, then scan files
docker exec nextcloud_nextcloud_1 php occ maintenance:mode --off
docker exec nextcloud_nextcloud_1 php occ files:scan --all
```

### Detailed Steps (Scenario A: local -> NFS)

1. **Understand the root cause (if data is on local disk despite NFS bind in compose)**

   HomelabOS Nextcloud compose may already have the correct NFS path as the bind source
   (e.g., `/mnt/nas/Documents/NextCloud:/data`). If NFS was not mounted when Docker started
   the container, Docker resolved the bind to the bare local directory at that path — silently
   writing 271 GB locally. The compose is correct; only the startup order needs fixing.

2. **Expose the hidden local data**

   The live NFS mount sits on top of the local directory, hiding it. Use a bind view of the
   root filesystem to access it:

   ```bash
   sudo mkdir -p /mnt/root-view
   sudo mount --bind / /mnt/root-view
   # Local data is now visible at:
   # /mnt/root-view/mnt/nas/Documents/NextCloud/
   ```

3. **Identify Nextcloud's container uid**

   ```bash
   docker exec nextcloud_nextcloud_1 id www-data
   # uid=1002(www-data) gid=1002(www-data)
   ```

   All rsync runs must use this uid because the NFS export has `root_squash` — root writes
   land as `nobody` (99:99).

4. **Pass 1 rsync — online, no downtime**

   ```bash
   sudo -u '#1002' -g '#1002' rsync -rltD --partial --info=progress2 \
     /mnt/root-view/mnt/nas/Documents/NextCloud/ \
     /mnt/nas/Documents/NextCloud/
   ```

   This catches the bulk of the data while Nextcloud is still serving users.

5. **Take Nextcloud offline for the delta pass**

   ```bash
   docker exec nextcloud_nextcloud_1 php occ maintenance:mode --on
   docker compose -f /var/homelabos/nextcloud/docker-compose.yml stop nextcloud
   ```

6. **Pass 2 rsync — delta only**

   Same command as Pass 1. Catches files changed during Pass 1.

7. **Verify file tree is identical**

   ```bash
   diff <(cd /mnt/root-view/mnt/nas/Documents/NextCloud && find . | sort) \
        <(cd /mnt/nas/Documents/NextCloud && find . | sort)
   ```

   Output must be empty. Also confirm `.ocdata` is owned by uid 1002:

   ```bash
   ls -la /mnt/nas/Documents/NextCloud/.ocdata
   ```

8. **Restart container**

   With NFS already mounted, Docker resolves the bind to the NFS share:

   ```bash
   docker compose -f /var/homelabos/nextcloud/docker-compose.yml up -d nextcloud
   docker exec nextcloud_nextcloud_1 df -h /data
   # 192.168.2.11:/data/Documents/NextCloud  ...
   ```

9. **Reclaim local disk space (fail-safe first)**

   Move local data to `.OLD` rather than deleting immediately. An empty local mountpoint
   acts as a fail-safe: if NFS fails at boot, Nextcloud sees no `.ocdata` and halts instead
   of silently re-forking 271 GB locally.

   ```bash
   sudo mv /mnt/root-view/mnt/nas/Documents/NextCloud \
           /mnt/root-view/mnt/nas/Documents/NextCloud.OLD
   sudo mkdir -p /mnt/root-view/mnt/nas/Documents/NextCloud
   # After verification period, delete OLD:
   sudo rm -rf /mnt/root-view/mnt/nas/Documents/NextCloud.OLD
   ```

10. **Harden boot startup order**

    Create a systemd drop-in so Docker waits for NFS before starting containers:

    ```bash
    sudo mkdir -p /etc/systemd/system/docker.service.d/
    sudo tee /etc/systemd/system/docker.service.d/wait-nas.conf <<'EOF'
    [Unit]
    RequiresMountsFor=/mnt/nas/Documents
    EOF
    sudo systemctl daemon-reload
    ```

11. **Disable maintenance mode and reconcile DB**

    ```bash
    docker exec nextcloud_nextcloud_1 php occ maintenance:mode --off
    docker exec nextcloud_nextcloud_1 php occ files:scan --all
    # Scan completes in ~33 seconds for 271 GB / 48,346 files
    ```

### Relocating off a slow NFS share onto a fast local disk (Scenario B)

Use this when `/data` is on a slow NFS share (e.g. ~8 MB/s, multi-second metadata) and uploads
are timing out, while core (webroot/config/apps/themes) and MariaDB are already on fast NVMe.

1. **Make the data dir configurable in the template, then mirror into the rendered compose**

   In `roles/nextcloud/templates/docker-compose.nextcloud.yml.j2` change the `/data` bind so
   it reads a config value (keep the separate `{{ storage_dir }}:/mnt/homelabos` external-storage
   mount untouched):

   ```diff
   - - "{{ storage_dir }}/Documents/NextCloud:/data"
   + - "{{ nextcloud.data_dir | default(storage_dir + '/Documents/NextCloud') }}:/data"
   ```

   Set the new value under the `nextcloud:` block in `settings/config.yml`:

   ```yaml
   nextcloud:
     data_dir: /media/<user>/<disk>/.../NextCloud
   ```

   Mirror the same `/data` source change in the rendered compose. It is owned by `homelab`, so
   the Edit/Write tool fails with EACCES — use `sudo`:

   ```bash
   sudo sed -i \
     's#- "[^"]*:/data"#- "/media/<user>/<disk>/.../NextCloud:/data"#' \
     /var/homelabos/nextcloud/docker-compose.yml
   sudo grep -n ':/data"' /var/homelabos/nextcloud/docker-compose.yml   # verify
   ```

2. **Make the mount reboot-safe (critical — so Nextcloud never starts against an empty dir)**

   a. Add the target disk to `/etc/fstab` (`nofail` so a missing disk does not block boot):

   ```bash
   # find the UUID
   lsblk -o NAME,UUID,FSTYPE,MOUNTPOINT
   # add (then validate, do NOT reboot on a bad fstab):
   echo 'UUID=<uuid> <mountpoint> ext4 defaults,nofail,noatime,nosuid,nodev 0 2' | sudo tee -a /etc/fstab
   findmnt --verify
   ```

   b. Add a systemd drop-in so `nextcloud.service` refuses to start until the data mount is
   present. `RequiresMountsFor` makes systemd order the unit after — and depend on — the
   generated `<mount>.mount` unit (which adopts the already-mounted fs):

   ```bash
   sudo mkdir -p /etc/systemd/system/nextcloud.service.d
   sudo tee /etc/systemd/system/nextcloud.service.d/usb-data-mount.conf <<'EOF'
   [Unit]
   RequiresMountsFor=/media/<user>/<disk>/.../NextCloud
   EOF
   sudo systemctl daemon-reload
   ```

3. **Migrate with a live cutover (rsync as the data OWNER, not root)**

   ```bash
   PUID=1002   # the apache/www-data uid that owns the data
   # bulk copy while Nextcloud is live
   sudo -u "#${PUID}" -g "#${PUID}" rsync -aH --info=progress2 \
     /path/to/nfs/NextCloud/ /media/<user>/<disk>/.../NextCloud/

   # quiesce, then a FINAL consistent pass (additive — NO --delete, so the .ocdata marker and
   # regenerable caches are never removed)
   docker exec -u "$PUID" nextcloud_nextcloud_1 php occ maintenance:mode --on
   sudo -u "#${PUID}" -g "#${PUID}" rsync -aH --info=progress2 \
     /path/to/nfs/NextCloud/ /media/<user>/<disk>/.../NextCloud/

   systemctl restart nextcloud           # recreates the container with the new /data bind
   docker exec -u "$PUID" nextcloud_nextcloud_1 php occ maintenance:mode --off
   ```

4. **Verify, then keep the old copy as an instant rollback**

   ```bash
   # confirm /data now resolves to the new disk
   docker inspect nextcloud_nextcloud_1 \
     --format '{{range .Mounts}}{{if eq .Destination "/data"}}{{.Source}}{{end}}{{end}}'

   ls -la /media/<user>/<disk>/.../NextCloud/.ocdata    # marker must be present
   docker exec -u 1002 nextcloud_nextcloud_1 php occ status

   # real upload test against the LAN path (NOT the public URL — see Failed Attempts)
   curl --resolve <domain>:443:<lan-ip> -T testfile \
     -u <user>:<pass> https://<domain>/remote.php/dav/files/<user>/testfile
   ```

   Keep the old NFS copy untouched: rolling back is just flipping the `/data` bind back to the
   NFS path (template + rendered compose) and `systemctl restart nextcloud`.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| rsync as root to NFS | `sudo rsync ... /mnt/nas/Documents/NextCloud/` | NFS export has root_squash; all files landed owned nobody (99:99); Nextcloud cannot read them | Always rsync to/from NFS as the Nextcloud uid (`sudo -u '#1002' -g '#1002'`), never as root. With root_squash, client root is squashed to anon and cannot even read the uid-1002-owned `770` files |
| rsync without bind view | `sudo -u '#1002' rsync /mnt/nas/Documents/NextCloud/ ...` | Source path is the live NFS mount itself, not the local data hidden beneath it — copies NFS back to NFS | Mount a bind view of `/` first to expose the hidden local directory |
| occ files:scan in maintenance mode | `docker exec ... php occ files:scan --all` while `maintenance:mode --on` | Returns "database isn't accessible" | Disable maintenance mode before running `occ files:scan`; maintenance mode blocks DB access |
| Edit rendered compose with the file tool | Opened `/var/homelabos/nextcloud/docker-compose.yml` with the Edit/Write tool | EACCES — the rendered compose is owned by the `homelab` user, not the current user | Edit rendered HomelabOS files with `sudo sed` / `sudo tee`; also mirror the change into the Jinja template + `settings/config.yml` so `ansible` does not revert it |
| Public-URL upload speed test | Uploaded to `https://<domain>/...` from inside the LAN to "prove" the move helped | Saw ~5.7 MB/s and assumed the relocation failed — but the LAN client hairpinned out the WAN and was capped by upload bandwidth (~5 MB/s), masking real storage speed | Re-test with `curl --resolve <domain>:443:<lan-ip>` to force the local path (showed ~30 MB/s LAN DAV). For LAN clients, fix the slow public path with split-DNS (e.g. a Tailscale custom DNS record to the tailnet IP, since traefik answers there with a valid cert) |
| Rely on the desktop automount for the bind | Let udisks auto-mount the disk at `/media/<user>/...` and pointed the docker bind there | After a reboot the disk may not be auto-mounted before Docker starts, so Nextcloud would start against an empty `/data` and re-fork data locally | Add an `/etc/fstab` entry (`nofail`) + a `nextcloud.service` `RequiresMountsFor` drop-in so Nextcloud refuses to start until the data mount is present |

## Results & Parameters

```text
Nextcloud container user:  uid=1002 gid=1002 (rsync/occ must run as this uid)

--- Scenario A (local NVMe -> NFS NAS), v1.0.0 ---
Total data:                271 GB, 610 folders, 48,346 files
files:scan duration:       ~33 seconds
NFS fstab entry:
  192.168.2.11:/data/Documents  /mnt/nas/Documents  nfs  defaults,_netdev,soft,timeo=30,retrans=3  0  0
docker.service drop-in (/etc/systemd/system/docker.service.d/wait-nas.conf):
  [Unit]
  RequiresMountsFor=/mnt/nas/Documents
Confirm: docker exec nextcloud_nextcloud_1 df -h /data
  # 192.168.2.11:/data/Documents/NextCloud  ...

--- Scenario B (slow NFS -> fast local disk), v1.1.0 ---
Before / after (only /data moved; core + MariaDB already on NVMe):
  storage write throughput:  8 MB/s   -> 214 MB/s
  rename / metadata op:      1.7 s    -> 5 ms
  LAN DAV upload:            timing out -> ~30 MB/s
  (public-URL upload stayed ~5 MB/s — WAN-hairpin capped, not a storage limit)

Template change (roles/nextcloud/templates/docker-compose.nextcloud.yml.j2):
  - "{{ nextcloud.data_dir | default(storage_dir + '/Documents/NextCloud') }}:/data"
settings/config.yml:
  nextcloud:
    data_dir: /media/<user>/<disk>/.../NextCloud

fstab entry (local disk):
  UUID=<uuid> <mountpoint> ext4 defaults,nofail,noatime,nosuid,nodev 0 2
  # validate with: findmnt --verify

systemd drop-in (/etc/systemd/system/nextcloud.service.d/usb-data-mount.conf):
  [Unit]
  RequiresMountsFor=/media/<user>/<disk>/.../NextCloud
  # then: sudo systemctl daemon-reload

Live cutover (additive final rsync — no --delete, keep .ocdata):
  docker exec -u 1002 nextcloud_nextcloud_1 php occ maintenance:mode --on
  sudo -u '#1002' -g '#1002' rsync -aH --info=progress2 SRC/ DST/
  systemctl restart nextcloud
  docker exec -u 1002 nextcloud_nextcloud_1 php occ maintenance:mode --off

Verify /data source disk (one-liner):
  docker inspect nextcloud_nextcloud_1 \
    --format '{{range .Mounts}}{{if eq .Destination "/data"}}{{.Source}}{{end}}{{end}}'

Force LAN upload test (bypass WAN hairpin):
  curl --resolve <domain>:443:<lan-ip> -T testfile -u <user>:<pass> \
    https://<domain>/remote.php/dav/files/<user>/testfile
```

Notes:

- The `.ocdata` validity marker may be MISSING on the old data dir yet present on the migrated
  copy. Nextcloud 34 runs without it, but newer versions check for it and refuse to start if it
  is absent — keep it. Its presence also doubles as a safety net: if the mount is ever missing,
  Nextcloud sees no `.ocdata` and halts instead of writing to an empty mountpoint.
- Cross-reference the NFS no_root_squash / root_squash skill for why rsync must run as the data
  owner uid.

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| HomelabOS Nextcloud | apollo homelab server, NVMe to TrueNAS NFS (v1.0.0, 2026-06-23) | End-to-end migration; Nextcloud serving from NAS confirmed |
| HomelabOS Nextcloud | live HomelabOS v1.0 host, slow NFS to fast local disk (v1.1.0, 2026-06) | End-to-end live cutover; `docker inspect` confirmed `/data` on the new disk; 8 -> 214 MB/s write, real upload test passed |
