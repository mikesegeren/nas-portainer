# NAS Portainer stacks

Docker Compose stacks for UGREEN NAS, managed via Portainer. Stacks are grouped by type under `stacks/`.

## Stacks

| Stack            | Compose path                             | Services                                                                                                                               |
| ---------------- | ---------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| **infra**        | `stacks/infra/docker-compose.yml`        | glance (8089), it-tools (8088), vaultwarden (8082), nginx-proxy-manager (80/8443/81). Glance config: `stacks/infra/glance/glance.yml`. |
| **home**         | `stacks/home/docker-compose.yml`         | home-assistant (host)                                                                                                                  |
| **media**        | `stacks/media/docker-compose.yml`        | jellyfin, ombi, sonarr, radarr, lidarr, readarr, prowlarr, qbittorrent, sabnzbd                                                        |
| **productivity** | `stacks/productivity/docker-compose.yml` | obsidian-db (5984 – CouchDB backend for Obsidian LiveSync/self-hosted)                                                                 |

**Media ports:** jellyfin 8096/8920, ombi 3579, sonarr 8989, radarr 7878, lidarr 8686, readarr 8787, prowlarr 9696, qbittorrent 8090/6881, sabnzbd 8081.

## Before connecting to Portainer

1. **Push the repo** – Commit and push to GitHub, GitLab, or another host that your NAS/Portainer can reach. Portainer will clone from this remote.
2. **Private repo** – If the repo is private, in Portainer when adding the stack you’ll need to set **Repository authentication** (username + personal access token, or SSH key).
3. **Environment variables** – Portainer does not use a `.env` file from the repo. When you add a stack from Git, you must set variables in the stack’s **Environment variables** section. Use `.env.example` as a reference; typical values:
   - `DOCKER_DATA` – e.g. `/volume2/docker`
   - `MEDIA_PATH` – e.g. `/home/Mike/media`
   - `PUID`, `PGID` – from `id` on the NAS
   - `TZ` – e.g. `Europe/Amsterdam`
   - For **infra** stack: `VAULTWARDEN_ADMIN_TOKEN`, `VAULTWARDEN_SIGNUPS_ALLOWED`, `VAULTWARDEN_DOMAIN` (HTTPS URL when using NPM; e.g. `https://vault.example.com`)
   - For **media** stack only (qbittorrent): `VPN_USER`, `VPN_PASS`, `LAN_NETWORK`

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

### HTTPS with Nginx Proxy Manager

Vaultwarden (and other services) can be exposed over HTTPS using **Nginx Proxy Manager** (NPM) in the infra stack. NPM is set to use **host port 8443** for HTTPS (instead of 443) so it doesn’t conflict with whatever is already using 443 on your NAS. To use standard HTTPS port 443, either stop that service and change the compose mapping to `443:443`, or on your router forward external port 443 to internal **8443**.

1. **Deploy the infra stack** so NPM is running. Open the admin UI at **http://&lt;NAS-IP&gt;:81**.
2. **First login:** `admin@example.com` / `changelog` — change these immediately in the profile.
3. **Add a Proxy Host for Vaultwarden:**
   - **Hosts** → **Proxy Hosts** → **Add Proxy Host**
   - **Domain name:** the hostname you’ll use (e.g. `vault.example.com` or a Duck DNS hostname). Your NAS or router must be reachable at this domain (port 80 for HTTP-01, or use DNS challenge).
   - **Scheme:** HTTP, **Forward hostname:** `vaultwarden`, **Forward port:** `80`
   - **SSL** tab: enable **SSL Certificate**, choose **Request a new Let's Encrypt certificate**, accept terms, enable **Force SSL**. If the domain doesn’t resolve publicly, use **Use a DNS Challenge** (e.g. Cloudflare) or a **Custom** self-signed cert.
   - **Advanced** tab (optional): add for WebSockets:
     ```nginx
     location /notifications/hub {
       proxy_pass http://vaultwarden:80;
       proxy_http_version 1.1;
       proxy_set_header Upgrade $http_upgrade;
       proxy_set_header Connection "upgrade";
     }
     ```
   - Save.
4. **Set Vaultwarden’s public URL:** In Portainer (or `.env`), set `VAULTWARDEN_DOMAIN=https://your-chosen-domain` (no trailing slash). Redeploy the infra stack so Vaultwarden picks it up.
5. In **Bitwarden** clients, set the server URL to `https://your-chosen-domain` and log in.

**Portainer behind HTTPS:** Portainer runs on the host (not in this stack), so you forward to the NAS IP and host port. In NPM: **Add Proxy Host** → **Domain name:** e.g. `portainer.example.com` → **Forward hostname:** your NAS IP (e.g. `192.168.1.116`) → **Forward port:** `19000` → **SSL** tab: request certificate and **Force SSL**. Save. Use `https://portainer.example.com` to access Portainer. Prefer exposing Portainer only over VPN or a non-guessable subdomain and keep a strong admin password.

NPM stores config under `DOCKER_DATA/nginx-proxy-manager` and certificates under `.../letsencrypt`. You can add more proxy hosts (Glance, Jellyfin, etc.) the same way.

### Glance

Glance config is in the repo at `stacks/infra/glance/glance.yml`. The container mounts this directory, so edits take effect automatically (no restart). If you had an existing config under `DOCKER_DATA/glance/config`, copy its contents into `stacks/infra/glance/glance.yml` before or after switching.
