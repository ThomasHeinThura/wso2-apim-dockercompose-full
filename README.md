# WSO2 API Manager 4.7.0 — local PostgreSQL + Traefik

An all-in-one WSO2 runtime serves the control-plane portals on
`apim.example.com` and API gateway traffic on `api.example.com`.
The WSO2 Docker image is pinned by digest and runs natively on ARM64 or AMD64.
PostgreSQL 17 contains separate `shared_db` and `apim_db` databases, initialized
with the SQL scripts extracted from that exact WSO2 image. The JDBC driver is
PostgreSQL 42.7.14.

## First-time setup

Requires Docker Compose, Python 3, curl, and OpenSSL supporting `-addext`.

```sh
git clone git@github.com:ThomasHeinThura/wso2-apim-dockercompose-full.git
cd wso2-apim-dockercompose-full
python3 scripts/setup.py
```

Setup generates `.env`, a local TLS certificate for both hostnames, and downloads
the pinned JDBC driver with SHA-256 verification. These generated files are
excluded from Git. Rerunning setup preserves existing credentials and certificates.

## Start on this Mac

```sh
docker compose -f compose.yaml -f compose.local.yaml up -d --build
./scripts/install-hosts.sh
python3 scripts/smoke-test.py --system-dns
python3 scripts/test-api.py
```

The hosts script prompts for your local sudo password and adds:

```text
127.0.0.1 apim.example.com api.example.com
```

The correct OS file is `/etc/hosts` (plural). This changes resolution on this
machine only. The smoke test uses curl's `--resolve` so it can also run before
the hosts entry is installed (omit `--system-dns`). It verifies TLS using
`certs/bimats.crt`. The optional `test-api.py` creates a temporary OAuth client
and API, publishes and invokes it, then deletes both.

This Mac already has the TaskDesk Traefik bound to loopback ports 80 and 443.
`compose.local.yaml` adds this stack's Traefik to its `taskdesk` network and
advertises a TCP SNI passthrough router for just these two domains. The existing
Traefik passes encrypted traffic to this stack; this stack terminates TLS and
routes CP traffic to WSO2 port 9443 and gateway traffic to port 8243.
The existing edge proxy and network must remain running for this mode.
HTTP requests use the existing edge's HTTPS redirect.

## URLs and credentials

- Publisher: https://apim.example.com/publisher/
- Developer Portal: https://apim.example.com/devportal/
- Admin Portal: https://apim.example.com/admin/
- Gateway: https://api.example.com/ (an unpublished path returns WSO2 HTTP 404)

Username is `admin`. The generated password is `APIM_ADMIN_PASSWORD` in `.env`.
Keep `.env` private. It also contains the database password and stable API-M
encryption key. Preserve that key together with the database backup; changing it
can prevent existing encrypted credentials from being read.
Changing the admin password in `.env` does not change an already-created admin
account; use the product's password-change flow for an existing database.

The generated certificate is self-signed with SANs for both domains. Browsers
will show a trust warning unless you explicitly trust it locally. Replace
`certs/bimats.crt` and `certs/bimats.key` with a trusted certificate when needed,
then restart this stack's Traefik. WSO2's upstream certificate remains the image's
self-signed certificate; its verification is disabled only inside this stack's
Traefik upstream transport. This is a local development configuration.

## Standalone host

After first-time setup, on a machine where loopback ports 80 and 443 are free, use:

```sh
docker compose -f compose.yaml -f compose.standalone.yaml up -d --build
```

Use one override at a time. The base file intentionally publishes no ports.
The standalone override binds only to loopback, matching `/etc/hosts` usage.

## Operations and persistence

```sh
docker compose -f compose.yaml -f compose.local.yaml ps
docker compose -f compose.yaml -f compose.local.yaml logs -f apim
docker compose -f compose.yaml -f compose.local.yaml down
```

Named volumes preserve PostgreSQL, local Carbon data, Synapse artifacts, and
execution plans. `down` preserves these volumes. Do not use `down -v` unless you
intend to delete the stack's stored data. SQL initialization runs only for a new
PostgreSQL data volume. The PostgreSQL service is internal and exposes no host port.
Allow around 1–3 minutes for API-M startup; the healthcheck validates its Version
service. The JVM heap is configured for 1–2 GiB.

## References

- WSO2 image: https://hub.docker.com/r/wso2/wso2am
- Proxy configuration: https://apim.docs.wso2.com/en/4.7.0/install-and-setup/setup/setting-up-proxy-server-and-the-load-balancer/configuring-the-proxy-server-and-the-load-balancer/
- PostgreSQL setup: https://apim.docs.wso2.com/en/4.7.0/install-and-setup/setup/setting-up-databases/changing-default-databases/changing-to-postgresql/
