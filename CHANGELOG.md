# Changelog

Notable changes to this project are listed here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [2.0.0] - 2026-10-22

Faster to deploy, harder to attack, and users stay connected while the hub restarts.

### Upgrading from 1.0

1. Add `PROXY_AUTH_TOKEN` to `.env`. The random-value command in the README's quick start fills it in and leaves your other values alone.
2. Update and restart:

   ```bash
   git fetch --tags
   git checkout v2.0.0
   docker compose pull
   docker compose up -d --remove-orphans
   ```

3. Open Grafana through an SSH tunnel, as described in [docs/operations.md](docs/operations.md#monitoring). You can delete the `grafana.<DOMAIN>` DNS record.

Users' files, the hub database and Grafana's data are kept.

### Added

- The proxy runs in its own container, so open notebooks keep working while the hub restarts.
- A ready-made hub image on GitHub's container registry, published by a release workflow with signed build provenance and a software bill of materials.
- A vulnerability scan of the hub image in CI.
- The hub downloads notebook images in the background when it starts.
- A command in the quick start that generates the random values in `.env`.

### Changed

- Traefik reads its routes from `traefik/dynamic.yml` and no longer has access to Docker. The maintenance page is now a Traefik failover for hub pages.
- Grafana listens on the host's localhost only and is opened through an SSH tunnel.
- The hub's Python packages are pinned by hash, including every dependency the base image lacks.
- User containers can no longer use swap on top of their memory limit.
- The quick start checks out the latest release.

### Removed

- The public `grafana.<DOMAIN>` address.

### Fixed

- Grafana still contacted grafana.com to install and update plugins, despite the privacy settings. Plugin downloads, signing-key checks and the plugin catalog are now turned off.

### Security

- Services reach each other only through `.invalid` aliases, which no DNS server resolves, and containers no longer use the host's DNS search domains. Before, while a container was down, its plain name could resolve to an outside host through a DNS search domain, and requests with cookies or tokens could go there. In 1.0.0 this affected user containers' requests to the hub.
- The smoke test runs every container behind a canary resolver. Tests can't contact real servers, and they fail if any name is looked up outside Docker.

## [1.0.0] - 2026-10-22

The first general-purpose release. Earlier commits were an unversioned deployment for a single site, the MOSAiC Virtual Research Environment. This release does not upgrade that deployment in place: settings, volumes and hostnames have changed.

### Added

- Login through any OpenID Connect provider, set up in `.env`. Only the users or groups you list can log in.
- Automatic Let's Encrypt certificates, and redirection from HTTP to HTTPS.
- Hub state that survives restarts, and one persistent volume per user.
- CPU, memory and process limits for each user's container.
- A Grafana dashboard and Prometheus data source, set up from the repository.
- Host metrics through Node Exporter.
- A maintenance page while the hub is starting or stopped.
- A smoke test, CI workflow and Dependabot configuration.
- Documentation for configuration, operations, security and privacy.

### Changed

- Upgraded to Traefik 3.7, JupyterHub 6.1, OAuthenticator 17.4, DockerSpawner 14.0 and jupyterhub-idle-culler 2.0, and pinned every image and package.
- Restarting the hub no longer stops users' servers.
- Idle servers stop after one hour by default, instead of one week.
- Prometheus and the Traefik dashboard are no longer published. Grafana is served over HTTPS at `grafana.<DOMAIN>`.
- Renamed `docker-compose.yml` to `compose.yaml`.

### Removed

- Site-specific branding, login page, logos, data mounts and images.
- Requests to third parties from the browser, such as Google Fonts.

[Unreleased]: https://github.com/irfan-farmer/dockerized-jupyterhub/compare/v2.0.0...HEAD
[2.0.0]: https://github.com/irfan-farmer/dockerized-jupyterhub/compare/v1.0.0...v2.0.0
[1.0.0]: https://github.com/irfan-farmer/dockerized-jupyterhub/releases/tag/v1.0.0
