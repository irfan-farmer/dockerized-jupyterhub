# Changelog

Notable changes to this project are listed here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses [Semantic Versioning](https://semver.org/).

## [Unreleased]

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

[Unreleased]: https://github.com/irfan-farmer/dockerized-jupyterhub/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/irfan-farmer/dockerized-jupyterhub/releases/tag/v1.0.0
