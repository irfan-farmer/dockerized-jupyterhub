# Operations

Run all commands from the repository directory.

## Everyday commands

| Task | Command |
|---|---|
| Start, or apply changes to `.env` | `docker compose up -d` |
| Show the state of each service | `docker compose ps` |
| Follow the hub's logs | `docker compose logs -f jupyterhub` |
| Restart the hub | `docker compose restart jupyterhub` |
| Stop everything | `docker compose down` |

Restarting the hub doesn't stop users' servers. Their running kernels keep their state, and their browsers reconnect once the hub is back. A restart takes 10–20 seconds. During that time users first see a short proxy error while the hub shuts down, then the maintenance page.

Docker keeps up to 50 MB of logs per service (5 files of 10 MB) and deletes older entries.

## Updating

1. Read [CHANGELOG.md](../CHANGELOG.md) for the versions between yours and the new one. A new major version can need manual steps.
2. Back up the hub data (see [Backups](#backups)).
3. Fetch the release and restart:

   ```bash
   git fetch --tags
   git checkout v1.2.3
   docker compose pull --ignore-buildable
   docker compose up -d --build
   ```

The hub upgrades its database on start, after saving a copy of the old one next to it.

To change the notebook image, edit `NOTEBOOK_IMAGE` and run `docker compose up -d`. Users get the new image the next time they start their server.

## Backups

| Volume | Contents | Back up? |
|---|---|---|
| `jupyterhub_hub_data` | User list, hub database, cookie secret | Yes |
| `jupyterhub-user-<username>` | Each user's `~/work` directory | Yes |
| `jupyterhub_grafana_data` | Grafana accounts and settings | Optional; the dashboard is in git |
| `jupyterhub_prometheus_data` | Metrics history | Optional |
| `jupyterhub_letsencrypt` | Certificates | No; they are issued again automatically |

Also keep a copy of `.env`.

This writes one archive per volume into the current directory:

```bash
backup() {
  docker run --rm -v "$1":/data:ro -v "$PWD":/backup alpine:3 \
    tar czf "/backup/$1-$(date +%F).tar.gz" -C /data .
}

# Stop the hub briefly so its database is copied in a consistent state.
docker compose stop jupyterhub
backup jupyterhub_hub_data
docker compose start jupyterhub

for volume in $(docker volume ls --quiet --filter name=jupyterhub-user-); do
  backup "$volume"
done
```

To restore a volume, stop the service that uses it and unpack the archive into it:

```bash
docker run --rm -v jupyterhub_hub_data:/data -v "$PWD":/backup alpine:3 \
  tar xzf /backup/jupyterhub_hub_data-2026-01-31.tar.gz -C /data
```

Store backups encrypted and off the host. Decide how long you keep them; they also contain the data of users you have deleted.

## Managing users

Admins manage users at `https://DOMAIN/hub/admin`. From there they can start and stop servers and add or remove users.

**To export a user's files**, copy their volume into an archive:

```bash
docker run --rm -v jupyterhub-user-alice:/data:ro -v "$PWD":/backup alpine:3 \
  tar czf /backup/alice.tar.gz -C /data .
```

**To delete a user and their files:**

1. Delete the user in the admin panel. This also stops their server.
2. Delete their volume: `docker volume rm jupyterhub-user-alice`.
3. Remove them from `ALLOWED_USERS` or from the group in your identity provider. Otherwise they can log in again and get a new, empty volume.

Volume names contain the username. Characters that Docker doesn't allow in names are escaped. List all user volumes with `docker volume ls --filter name=jupyterhub-user-`.

## Maintenance mode

Stop the hub to show the maintenance page, and start it again when you're done:

```bash
docker compose stop jupyterhub
docker compose start jupyterhub
```

The page text is in [maintenance/index.html](../maintenance/index.html).

## Monitoring

The **JupyterHub** dashboard in Grafana shows running servers, active users, failed server starts, server start times, HTTPS traffic, and host CPU, memory and disk usage. Prometheus keeps 30 days of metrics.

Set up alerts in Grafana under **Alerting**. At a minimum, alert on disk usage above 90%: user volumes grow over time, and a full disk stops the hub.

## Troubleshooting

| Symptom | Likely cause |
|---|---|
| The browser warns about the certificate | Let's Encrypt couldn't validate the domain. Check that DNS points to the host and port 80 is open, then look at `docker compose logs traefik`. |
| The identity provider shows an error before login | The redirect URI doesn't match. It must be exactly `https://DOMAIN/hub/oauth_callback`. |
| "403 Forbidden" after login | The user isn't allowed. `docker compose logs jupyterhub` shows the username the provider sent; compare it with `ALLOWED_USERS` and the other rules. |
| A server start times out | The notebook image is still downloading. Pull it in advance with `docker pull`. |
| The maintenance page doesn't go away | The hub is unhealthy. Check `docker compose ps` and `docker compose logs jupyterhub`. |
