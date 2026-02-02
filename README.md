# NAS Portainer stacks

Docker Compose stacks for UGREEN NAS, managed via Portainer. Stacks are grouped by type under `stacks/`.

## Stacks

| Stack            | Compose path                             | Services                                                                        |
| ---------------- | ---------------------------------------- | ------------------------------------------------------------------------------- |
| **infra**        | `stacks/infra/docker-compose.yml`        | heimdall (8080), it-tools (8088), glance (8089), homarr (7575)                  |
| **home**         | `stacks/home/docker-compose.yml`         | home-assistant (host)                                                           |
| **media**        | `stacks/media/docker-compose.yml`        | jellyfin, ombi, sonarr, radarr, lidarr, readarr, prowlarr, qbittorrent, sabnzbd |
| **productivity** | `stacks/productivity/docker-compose.yml` | obsidian (3000)                                                                 |

**Media ports:** jellyfin 8096/8920, ombi 3579, sonarr 8989, radarr 7878, lidarr 8686, readarr 8787, prowlarr 9696, qbittorrent 8090/6881, sabnzbd 8081.

## Before connecting to Portainer

1. **Push the repo** – Commit and push to GitHub, GitLab, or another host that your NAS/Portainer can reach. Portainer will clone from this remote.
2. **Private repo** – If the repo is private, in Portainer when adding the stack you’ll need to set **Repository authentication** (username + personal access token, or SSH key).
3. **Environment variables** – Portainer does not use a `.env` file from the repo. When you add a stack from Git, you must set variables in the stack’s **Environment variables** section. Use `.env.example` as a reference; typical values:
   - `DOCKER_DATA` – e.g. `/volume2/docker`
   - `MEDIA_PATH` – e.g. `/home/Mike/media`
   - `PUID`, `PGID` – from `id` on the NAS
   - `TZ` – e.g. `Europe/Amsterdam`
   - For **media** stack only (qbittorrent): `VPN_USER`, `VPN_PASS`, `LAN_NETWORK`
   - For **infra** stack (Homarr): `HOMARR_SECRET_ENCRYPTION_KEY` (64-char hex, e.g. `openssl rand -hex 32`)

## Setup

1. **Environment (for local/CLI use)**
   - Copy `.env.example` to `.env` and set paths and IDs for your NAS. For Portainer Git stacks, set these same values in the stack’s Environment variables instead.

2. **Portainer**
   - **Stacks** → **Add stack** → **Repository**.
   - **URL**: your repo URL (e.g. `https://github.com/you/nas-portainer.git`).
   - **Compose path**: `stacks/infra/docker-compose.yml`, `stacks/home/docker-compose.yml`, `stacks/media/docker-compose.yml`, or `stacks/productivity/docker-compose.yml`.
   - **Stack name**: `infra`, `home`, `media`, or `productivity`.
   - Add the **Environment variables** listed above (and qbittorrent VPN vars for the **media** stack).

3. **CLI (optional)**
   - From the repo root: `cd stacks/infra && docker compose --env-file ../../.env up -d` (same for `home`, `media`, or `productivity`).

## Paths

Compose files use defaults that match a typical UGREEN layout:

- Config: `DOCKER_DATA/<service>/config` (or similar per service).
- Media: `MEDIA_PATH` for jellyfin, \*arrs, qbittorrent, sabnzbd.

Override via `.env` (or Portainer env vars) so you don’t need to edit the YAML.
