# NAS Portainer stacks

Docker Compose stacks for UGREEN NAS, managed via Portainer. Stacks are grouped by type under `stacks/`.

## Stacks

| Stack            | Compose path                             | Services                                                                                                                                 |
| ---------------- | ---------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| **infra**        | `stacks/infra/docker-compose.yml`        | glance (8089), it-tools (8088), vaultwarden (8082), nginx-proxy-manager (8880/8443/81). Glance config: `stacks/infra/glance/glance.yml`. |
| **home**         | `stacks/home/docker-compose.yml`         | home-assistant (host)                                                                                                                    |
| **media**        | `stacks/media/docker-compose.yml`        | jellyfin, ombi, sonarr, radarr, lidarr, lazylibrarian, prowlarr, qbittorrent, sabnzbd, calibre-web-automated                              |
| **productivity** | `stacks/productivity/docker-compose.yml` | obsidian-db (5984 – CouchDB backend for Obsidian LiveSync/self-hosted)                                                                   |

**Media ports:** jellyfin 8096/8920, ombi 3579, sonarr 8989, radarr 7878, lidarr 8686, lazylibrarian 5299, prowlarr 9696, qbittorrent 8090/6881, sabnzbd 8081, calibre-web-automated 8083.

### Port mapping reference (no collisions)

All host ports used by the stacks in this repo (check here before adding new services):

| Host port | Stack        | Service                        |
| --------: | ------------ | ------------------------------ |
|        81 | infra        | nginx-proxy-manager (admin UI) |
|      3579 | media        | ombi                           |
|      5299 | media        | lazylibrarian                  |
|      5984 | productivity | obsidian-db (CouchDB)          |
|      7878 | media        | radarr                         |
|      8081 | media        | sabnzbd                        |
|      8082 | infra        | vaultwarden                    |
|      8083 | media        | calibre-web-automated          |
|      8088 | infra        | it-tools                       |
|      8089 | infra        | glance                         |
|      8090 | media        | qbittorrent (Web UI)           |
|      8096 | media        | jellyfin                       |
|      8443 | infra        | nginx-proxy-manager (HTTPS)    |
|      8686 | media        | lidarr                         |
|      8880 | infra        | nginx-proxy-manager (HTTP)     |
|      8920 | media        | jellyfin (HTTPS)               |
|      8989 | media        | sonarr                         |
|      9696 | media        | prowlarr                       |
|      6881 | media        | qbittorrent (BT TCP+UDP)       |

Not in these stacks (host/other): **Portainer** 19000, **Home Assistant** 8123 (host network). The NAS may also use **80** and **443** (hence NPM uses 8880/8443).

## Before connecting to Portainer

1. **Push the repo** – Commit and push to GitHub, GitLab, or another host that your NAS/Portainer can reach. Portainer will clone from this remote.
2. **Private repo** – If the repo is private, in Portainer when adding the stack you’ll need to set **Repository authentication** (username + personal access token, or SSH key).
3. **Environment variables** – Portainer does not use a `.env` file from the repo. When you add a stack from Git, you must set variables in the stack’s **Environment variables** section. Use `.env.example` as a reference; typical values:
   - `DOCKER_DATA` – e.g. `/volume2/docker`
   - `MEDIA_PATH` – e.g. `/home/Mike/media`
   - `PUID`, `PGID` – from `id` on the NAS
   - `TZ` – e.g. `Europe/Amsterdam`
   - For **infra** stack: `VAULTWARDEN_ADMIN_TOKEN`, `VAULTWARDEN_SIGNUPS_ALLOWED`, `VAULTWARDEN_DOMAIN` (HTTPS URL when using NPM; e.g. `https://vault.example.com`)
   - For **media** stack: `VPN_USER`, `VPN_PASS`, `LAN_NETWORK` (qbittorrent)

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

All \*arrs and both download clients mount `MEDIA_PATH` as `/data`, so paths match between apps and imports can hardlink instead of copy. Recommended layout under `MEDIA_PATH`:

```
downloads/{torrents,usenet}/{tv,movies,music,books}
tv/  movies/  music/        # root folders: /data/tv, /data/movies, /data/music
books/                      # Calibre library (managed by calibre-web-automated)
books-ingest/               # drop zone for new books – emptied after import
```

In the \*arrs, add download clients by container name with the **container** port: `sabnzbd:8080`, `qbittorrent:8090`.

### Books & Kobo

Flow: **LazyLibrarian** (search/download via Prowlarr + qbittorrent/sabnzbd) → `books-ingest/` → **Calibre-Web-Automated** imports into the Calibre library and converts to kepub → **Kobo** syncs over Wi‑Fi.

1. **Calibre-Web-Automated** (`http://<NAS-IP>:8083`, first login `admin` / `admin123` – change it):
   - Admin → Edit Basic Configuration → **Feature Configuration**: enable **Kobo sync** and **Proxy unknown requests to Kobo Store**. Under **Server Configuration** set *Server External Port* to `8083`.
   - CWA Settings: enable auto-convert with target format **KEPUB** (better typography/progress tracking on Kobo).
   - Admin → Users → create a user for the Kobo owner, then in that user's profile click **Create/View** under *Kobo Sync Token* and copy the `api_endpoint=...` line. Tick *Sync only books in selected shelves* if you want to control what lands on the device (then mark a shelf "Sync with Kobo").
2. **Kobo**: connect via USB, open `.kobo/Kobo/Kobo eReader.conf`, and in the `[OneStoreServices]` section replace the `api_endpoint=` line with the one copied above. Eject, then tap **Sync** on the Kobo. Only works on the home network unless you expose CWA via NPM (HTTPS).
3. **LazyLibrarian** (`http://<NAS-IP>:5299`):
   - Config → Downloaders: qBittorrent `qbittorrent:8090` (category `books`, download dir `/data/downloads/torrents/books`) and/or SABnzbd `sabnzbd:8080` (API key from SABnzbd, category `books`).
   - Config → Processing: *eBook Library Folder* = `/data/books-ingest`. Leave torrents seeding (LazyLibrarian copies, it doesn't move).
   - Prowlarr → Settings → Apps → add **LazyLibrarian** (`http://lazylibrarian:5299`, API key from LazyLibrarian → Config → Interface) so indexers sync automatically.

Books can also be added by hand: drop an epub in `books-ingest/` or upload via the CWA web UI.

Override via `.env` (or Portainer env vars) so you don’t need to edit the YAML.

### HTTPS with Nginx Proxy Manager

Vaultwarden (and other services) can be exposed over HTTPS using **Nginx Proxy Manager** (NPM) in the infra stack. NPM is set to use **host ports 8880 (HTTP) and 8443 (HTTPS)** because 80 and 443 are already in use on the NAS. For Let’s Encrypt HTTP-01, forward external port 80 to internal **8880** on your router (or use a DNS challenge in NPM). For HTTPS, forward external 443 to **8443**, or use `https://domain:8443`. To use standard ports, free 80/443 on the host and change the compose mappings to `80:80` and `443:443`.

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

Glance config lives on the NAS at **`${DOCKER_DATA}/glance/config`** (e.g. `/volume2/docker/glance/config`). Copy the contents of `stacks/infra/glance/` from this repo into that folder once (so `glance.yml` is at `…/glance/config/glance.yml`), then deploy. Edit the config on the NAS; Glance reloads on save. The repo’s `stacks/infra/glance/` is a reference copy.

