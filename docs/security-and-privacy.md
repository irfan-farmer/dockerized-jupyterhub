# Security and privacy

This page explains how the stack is secured and what personal data it processes. It is meant to help you assess the deployment. It is not legal advice.

## Security

**Network exposure.** Traefik is the only service reachable from the internet. Port 80 does nothing except redirect to HTTPS and answer Let's Encrypt's checks. Grafana listens on the host's localhost only, so admins reach it through an SSH tunnel, and it still requires its own login. Prometheus, Node exporter and Traefik's metrics endpoint run on an internal Docker network that has no internet access.

**TLS.** Certificates come from Let's Encrypt. Traefik accepts TLS 1.2 or newer and adds HSTS (one year), `X-Content-Type-Options: nosniff` and a strict referrer policy to every response.

**Login.** Users sign in through your identity provider, using the authorization code flow with PKCE. Until you allow users or groups, only `ADMIN_USERS` can log in.

**User containers.** Each user's server runs in its own container as the unprivileged `jovyan` user. The container has `no-new-privileges` set, and limits on CPU, memory and number of processes. User containers can reach the hub, but not Traefik, Prometheus or Grafana directly. They do have outbound internet access so users can install packages; block it with a host firewall if your data requires that.

**One domain for all users.** By JupyterHub's default design, every user's server is served from the same domain. If users don't trust each other, enable JupyterHub's [subdomain isolation](https://jupyterhub.readthedocs.io/en/stable/explanation/websecurity.html), which needs wildcard DNS and a wildcard certificate.

**Docker socket.** Only the hub has access to Docker, which it needs to start user containers. That access is equivalent to root on the host, so keep the hub updated, don't add software to its image, and restrict who can log in to the host. Traefik reads its routes from `traefik/dynamic.yml` and has no Docker access, so a flaw in the internet-facing service doesn't reach Docker.

**Internal names.** Services reach each other through names ending in `.internal`, a domain reserved for private use. While a container is down, its plain service name could resolve to a host on the internet through your DNS search domain. A `.internal` name can't, so requests carrying cookies or tokens never leave the server.

**Proxy.** The proxy's API, which the hub uses to add routes for users' servers, requires `PROXY_AUTH_TOKEN`. User containers can reach the proxy, so keep that token secret and random.

**Secrets.** All secrets are in `.env`. Git ignores it; keep its permissions at `600`. The metrics token reaches the hub and Prometheus as a Compose secret file. The proxy token is passed as an environment variable, which is how the proxy expects it.

**Supply chain.** Every image and package is pinned to a version, and the hub's Python packages are also pinned by hash. CI scans the hub image for critical vulnerabilities on every change. Each release's hub image is built by GitHub Actions, with a signed build provenance and a software bill of materials. You can check that an image was built from this repository:

```bash
gh attestation verify oci://ghcr.io/irfan-farmer/dockerized-jupyterhub:<version> --repo irfan-farmer/dockerized-jupyterhub
```

**Updates.** Dependabot proposes updates weekly, and CI tests them. Install new releases promptly; see [Updating](operations.md#updating).

**The host.** The stack can only be as secure as the server it runs on:

- Allow only SSH, HTTP and HTTPS through the firewall.
- Use SSH keys rather than passwords.
- Turn on automatic security updates for the operating system.
- Keep encrypted backups somewhere other than the host.

## Privacy and GDPR

The organization that runs the hub is the controller of the personal data it processes. The stack helps by keeping that data minimal, local and easy to delete.

**No tracking or third-party requests.** The hub's pages, the maintenance page and Grafana load no external fonts, scripts, analytics or avatars. Grafana's Gravatar, news feed, update checks and usage reporting are turned off, as is Traefik's anonymous usage reporting. Inside users' servers, JupyterLab asks each user before it fetches its news feed. Content that users add themselves, such as notebooks that embed web resources, is outside the stack's control.

**Cookies.** JupyterHub and Grafana set only the cookies needed for login and request security. They set no tracking cookies.

**Personal data processed:**

| Data | Stored in | Kept for |
|---|---|---|
| Username and groups, from your identity provider | Hub database (`jupyterhub_hub_data`) | Until you delete the user |
| Files users create | The user's volume | Until you delete the volume |
| IP addresses, usernames and requested URLs | Container logs | Up to 50 MB per service, then deleted as logs rotate |
| `ACME_EMAIL` | Sent to Let's Encrypt | Under [Let's Encrypt's privacy policy](https://letsencrypt.org/privacy/) |
| Usage counts, with no usernames | Prometheus | 30 days |

**Where data goes.** Everything stays on your host, with three exceptions:

- Your identity provider handles the login.
- Let's Encrypt issues the certificates.
- Images are downloaded from Docker Hub, quay.io and GitHub's container registry. These downloads contain no user data.

**Requests from data subjects.** [Operations](operations.md#managing-users) shows how to export a user's files and how to delete a user and their data. Log entries disappear as logs rotate. Copies in backups last as long as your backup retention.

**Your responsibilities.** This list isn't complete:

- Keep a record of processing activities.
- Give users a privacy notice.
- Sign data processing agreements with your hosting provider and identity provider.
- Set a retention period for backups.
- Decide whether users' servers may reach the internet.
