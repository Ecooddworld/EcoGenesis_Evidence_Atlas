# Production Caddy Deployment

Hosted contest demo:

- https://ecooddworld.eu
- https://www.ecooddworld.eu

The hosted stack uses `docker-compose.caddy.yml` rather than the local development compose file.

```bash
docker compose -f docker-compose.caddy.yml up -d --build
```

## Security Boundary

- Caddy is the only public web entrypoint.
- Ports `80` and `443` are open for HTTP redirect, HTTPS, and certificate renewal.
- The FastAPI backend is exposed only inside the Docker network on port `8000`.
- `http://ecooddworld.eu` redirects to `https://ecooddworld.eu`.
- `http://89.167.66.248` redirects to `https://ecooddworld.eu`.
- Production CORS is restricted to `https://ecooddworld.eu` and `https://www.ecooddworld.eu`.
- Caddy persists certificates in Docker volumes `caddy_data` and `caddy_config`.

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
