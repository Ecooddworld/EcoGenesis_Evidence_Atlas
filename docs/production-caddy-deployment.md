# Production Caddy Deployment

Hosted contest demo:

- https://ecooddworld.eu
- https://www.ecooddworld.eu

The hosted stack uses `docker-compose.caddy.yml` rather than the local development compose file.

Operational limits, default bearer authentication and artifact retention are documented in [`production-security.md`](production-security.md).

```bash
export API_AUTH_TOKEN="$(openssl rand -hex 32)"
docker compose -f docker-compose.caddy.yml up -d --build
```

The Caddy stack defaults `API_AUTH_REQUIRED=true` and
`API_AUTH_PROTECT_RUN_READS=true`. It fails closed if the token is missing. The
static browser UI can still read public status endpoints, but authenticated mutations
need a trusted client or a future session/token broker. A public interactive contest
demo can explicitly set `API_AUTH_REQUIRED=false`; that is a demo posture, not the
production default.

## Security Boundary

- Caddy is the only public web entrypoint.
- Ports `80` and `443` are open for HTTP redirect, HTTPS, and certificate renewal.
- The FastAPI backend is exposed only inside the Docker network on port `8000`.
- `http://ecooddworld.eu` redirects to `https://ecooddworld.eu`.
- `http://89.167.66.248` redirects to `https://ecooddworld.eu`.
- Production CORS is restricted to `https://ecooddworld.eu` and `https://www.ecooddworld.eu`.
- Caddy persists certificates in Docker volumes `caddy_data` and `caddy_config`.
- Caddy and FastAPI run as non-root users with dropped capabilities and bounded CPU, memory and PID resources.
- Runtime evidence and privacy-preserving analytics remain in the explicit `./data:/data/evidence` bind mount so they can be backed up and retained across in-place releases; the directory is never served publicly.
- Application-level request, upload, search-timeout and rate limits remain active behind Caddy.
- Mutations and run/export reads require bearer authentication by default.

## Server Baseline

The Hetzner host is configured for key-only SSH access through the `ecogenesis` user. Root SSH login and password authentication are disabled. UFW allows only SSH, HTTP and HTTPS, and Fail2ban plus unattended security upgrades are enabled.

## Production Smoke

```bash
curl -fsSI https://ecooddworld.eu/
curl -fsS https://ecooddworld.eu/health
curl -fsS https://ecooddworld.eu/api/barcode/search-status
```

Expected:

- HTTPS returns `200`.
- HTTP returns a redirect to HTTPS.
- `/health` returns `{"status":"ok","service":"ecogenesis-barcode-gbif-compiler"}`.
- `/api/barcode/search-status` reports `vsearch` or `blastn` availability in the backend image.

Also verify the safe security configuration (no secret values are returned):

```bash
curl -fsS https://ecooddworld.eu/api/system/limits
```
