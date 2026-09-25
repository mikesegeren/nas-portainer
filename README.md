# NAS Portainer stacks

Docker Compose stacks for UGREEN NAS, managed via Portainer. Stacks are grouped by type under `stacks/`.

## Stacks

| Stack            | Compose path                             | Services                                                                                                                                 |
| ---------------- | ---------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| **infra**        | `stacks/infra/docker-compose.yml`        | glance (8089), it-tools (8088), nginx-proxy-manager (8880/8443/81), diun (no UI – image update checks, see logs). Glance config: `stacks/infra/glance/glance.yml`. |
| **home**         | `stacks/home/docker-compose.yml`         | home-assistant (host)                                                                                                                    |
| **media**        | `stacks/media/docker-compose.yml`        | jellyfin, seerr, sonarr, radarr, lidarr, lazylibrarian, prowlarr, sabnzbd, calibre-web-automated, audiobookshelf              |

**Media ports:** jellyfin 8096/8920, seerr 5055, sonarr 8989, radarr 7878, lidarr 8686, lazylibrarian 5299, prowlarr 9696, sabnzbd 8081, calibre-web-automated 8083, audiobookshelf 13378.

### Port mapping reference (no collisions)

All host ports used by the stacks in this repo (check here before adding new services):

| Host port | Stack        | Service                        |
| --------: | ------------ | ------------------------------ |
|        81 | infra        | nginx-proxy-manager (admin UI) |
|      5055 | media        | seerr                          |
|      5299 | media        | lazylibrarian                  |
|      7878 | media        | radarr                         |
|      8081 | media        | sabnzbd                        |
|      8083 | media        | calibre-web-automated          |
|      8088 | infra        | it-tools                       |
|      8089 | infra        | glance                         |
|      8096 | media        | jellyfin                       |
|      8443 | infra        | nginx-proxy-manager (HTTPS)    |
|      8686 | media        | lidarr                         |
|      8880 | infra        | nginx-proxy-manager (HTTP)     |
|      8920 | media        | jellyfin (HTTPS)               |
|      8989 | media        | sonarr                         |
|      9696 | media        | prowlarr                       |
|     13378 | media        | audiobookshelf                 |

Not in these stacks (host/other): **Portainer** 19000, **Home Assistant** 8123 (host network). The NAS may also use **80** and **443** (hence NPM uses 8880/8443).

## Before connecting to Portainer

1. **Push the repo** – Commit and push to GitHub, GitLab, or another host that your NAS/Portainer can reach. Portainer will clone from this remote.
2. **Private repo** – If the repo is private, in Portainer when adding the stack you’ll need to set **Repository authentication** (username + personal access token, or SSH key).
3. **Environment variables** – Portainer does not use a `.env` file from the repo. When you add a stack from Git, you must set variables in the stack’s **Environment variables** section. Use `.env.example` as a reference; typical values:
   - `DOCKER_DATA` – e.g. `/volume2/docker`
   - `MEDIA_PATH` – e.g. `/home/Mike/media`
   - `PUID`, `PGID` – from `id` on the NAS
   - `TZ` – e.g. `Europe/Amsterdam`

## Setup

1. **Environment (for local/CLI use)**

   - Copy `.env.example` to `.env` and set paths and IDs for your NAS. For Portainer Git stacks, set these same values in the stack’s Environment variables instead.

2. **Portainer**

   - **Stacks** → **Add stack** → **Repository**.
   - **URL**: your repo URL (e.g. `https://github.com/you/nas-portainer.git`).
   - **Compose path**: `stacks/infra/docker-compose.yml`, `stacks/home/docker-compose.yml`, or `stacks/media/docker-compose.yml`.
   - **Stack name**: `infra`, `home`, or `media`.
   - Add the **Environment variables** listed above.

3. **CLI (optional)**
   - From the repo root: `cd stacks/infra && docker compose --env-file ../../.env up -d` (same for `home` or `media`).

## Paths

Compose files use defaults that match a typical UGREEN layout:

- Config: `DOCKER_DATA/<service>/config` (or similar per service).
- Media: `MEDIA_PATH` for jellyfin, \*arrs, sabnzbd.

All \*arrs and sabnzbd mount `MEDIA_PATH` as `/data`, so paths match between apps and imports can hardlink instead of copy. Recommended layout under `MEDIA_PATH`:

```
downloads/usenet/{tv,movies,music,books}
tv/  movies/  music/        # root folders: /data/tv, /data/movies, /data/music
books/                      # Calibre library (managed by calibre-web-automated)
books-ingest/               # drop zone for new books – emptied after import
audiobooks/                 # Audiobookshelf library (LazyLibrarian audio folder)
```

In the \*arrs, add the download client by container name with the **container** port: `sabnzbd:8080`.

### Books & Kobo

Flow: **LazyLibrarian** (search/download via Prowlarr + sabnzbd) → `books-ingest/` → **Calibre-Web-Automated** imports into the Calibre library and converts to kepub → **Kobo** syncs over Wi‑Fi.

1. **Calibre-Web-Automated** (`http://<NAS-IP>:8083`, first login `admin` / `admin123` – change it):
   - Admin → Edit Basic Configuration → **Feature Configuration**: enable **Kobo sync** and **Proxy unknown requests to Kobo Store**. Under **Server Configuration** set *Server External Port* to `8083`.
   - CWA Settings: enable auto-convert with target format **KEPUB** (better typography/progress tracking on Kobo).
   - Admin → Users → create a user for the Kobo owner, then in that user's profile click **Create/View** under *Kobo Sync Token* and copy the `api_endpoint=...` line. Tick *Sync only books in selected shelves* if you want to control what lands on the device (then mark a shelf "Sync with Kobo").
2. **Kobo**: connect via USB, open `.kobo/Kobo/Kobo eReader.conf`, and in the `[OneStoreServices]` section replace the `api_endpoint=` line with the one copied above. Eject, then tap **Sync** on the Kobo. Only works on the home network unless you expose CWA via NPM (HTTPS).
3. **LazyLibrarian** (`http://<NAS-IP>:5299`):
   - Config → Downloaders: SABnzbd `sabnzbd:8080` (API key from SABnzbd, category `books`).
   - Config → Processing: *eBook Library Folder* = `/data/books-ingest`.
   - Prowlarr → Settings → Apps → add **LazyLibrarian** (`http://lazylibrarian:5299`, API key from LazyLibrarian → Config → Interface) so indexers sync automatically.

### Audiobooks

Flow: **LazyLibrarian** → `audiobooks/` → **Audiobookshelf** (`http://<NAS-IP>:13378`) → Audiobookshelf app (iOS/Android) with offline downloads and progress sync per user.

1. First visit creates the root (admin) account. Add a user per listener under Settings → Users.
2. Libraries → Add library → type **Books**, folder `/audiobooks`. Enable *Watch for changes* (default) so new downloads appear automatically.
3. LazyLibrarian → Config → Processing: *Audio Library Folder* = `/data/audiobooks`, *Audiobook folder format* `$Author/$Title` (ABS expects `Author/Title/files`).
4. In the app, set the server address to `http://<NAS-IP>:13378`.

Books can also be added by hand: drop an epub in `books-ingest/` or upload via the CWA web UI.

Override via `.env` (or Portainer env vars) so you don’t need to edit the YAML.

### HTTPS with Nginx Proxy Manager

Services can be exposed over HTTPS using **Nginx Proxy Manager** (NPM) in the infra stack. NPM is set to use **host ports 8880 (HTTP) and 8443 (HTTPS)** because 80 and 443 are already in use on the NAS. For Let’s Encrypt HTTP-01, forward external port 80 to internal **8880** on your router (or use a DNS challenge in NPM). For HTTPS, forward external 443 to **8443**, or use `https://domain:8443`. To use standard ports, free 80/443 on the host and change the compose mappings to `80:80` and `443:443`.

1. **Deploy the infra stack** so NPM is running. Open the admin UI at **http://&lt;NAS-IP&gt;:81**.
2. **First login:** `admin@example.com` / `changelog` — change these immediately in the profile.
3. **Add a Proxy Host** (example: Jellyfin):
   - **Hosts** → **Proxy Hosts** → **Add Proxy Host**
   - **Domain name:** e.g. `jellyfin.example.com`. Must resolve to the NAS (public DNS, or a local DNS record on the router).
   - **Scheme:** HTTP, **Forward hostname:** NAS IP (e.g. `192.168.1.116`), **Forward port:** `8096`. Services in other stacks aren't on `infra-network`, so use IP + host port.
   - **SSL** tab: **Request a new Let's Encrypt certificate**, enable **Force SSL**. For LAN-only hostnames use **Use a DNS Challenge** (e.g. Cloudflare).
   - Save.

**Portainer behind HTTPS:** Portainer runs on the host (not in this stack), so you forward to the NAS IP and host port. In NPM: **Add Proxy Host** → **Domain name:** e.g. `portainer.example.com` → **Forward hostname:** your NAS IP (e.g. `192.168.1.116`) → **Forward port:** `19000` → **SSL** tab: request certificate and **Force SSL**. Save. Use `https://portainer.example.com` to access Portainer. Prefer exposing Portainer only over VPN or a non-guessable subdomain and keep a strong admin password.

NPM stores config under `DOCKER_DATA/nginx-proxy-manager` and certificates under `.../letsencrypt`. You can add more proxy hosts (Glance, Jellyfin, etc.) the same way.

### Diun

Diun checks every 6 hours whether a newer image exists for any running container and only reports it; it never updates anything. Without a notifier the results only appear in the `diun` container logs. Add a notifier via env vars (e.g. `DIUN_NOTIF_NTFY_*`, `DIUN_NOTIF_TELEGRAM_*`, see the Diun docs), then update by redeploying the stack in Portainer with *Re-pull image* enabled.

### Glance

Glance config lives on the NAS at **`${DOCKER_DATA}/glance/config`** (e.g. `/volume2/docker/glance/config`). Copy the contents of `stacks/infra/glance/` from this repo into that folder once (so `glance.yml` is at `…/glance/config/glance.yml`), then deploy. Edit the config on the NAS; Glance reloads on save. The repo’s `stacks/infra/glance/` is a reference copy.

Glance deliberately does not mount the host root filesystem, `/proc` or `/sys`; CPU/RAM stats come from the (shared) kernel anyway. It does mount the Docker socket read-only for the containers widget: that's effectively root on the host, so never expose Glance outside the LAN.

