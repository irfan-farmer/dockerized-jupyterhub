# Security and privacy

This page explains how the stack is secured and what personal data it processes. It is meant to help you assess the deployment. It is not legal advice.

## Security

**Network exposure.** Only Traefik publishes ports. Port 80 does nothing except redirect to HTTPS and answer Let's Encrypt's checks. Prometheus, Node exporter and Traefik's metrics endpoint run on an internal Docker network that has no internet access and isn't published. Grafana is published at `grafana.DOMAIN` and requires its own login.

**TLS.** Certificates come from Let's Encrypt. Traefik accepts TLS 1.2 or newer and adds HSTS (one year), `X-Content-Type-Options: nosniff` and a strict referrer policy to every response.

**Login.** Users sign in through your identity provider, using the authorization code flow with PKCE. Until you allow users or groups, only `ADMIN_USERS` can log in.

**User containers.** Each user's server runs in its own container as the unprivileged `jovyan` user. The container has `no-new-privileges` set, and limits on CPU, memory and number of processes. User containers can reach the hub, but not Traefik, Prometheus or Grafana directly. They do have outbound internet access so users can install packages; block it with a host firewall if your data requires that.

**One domain for all users.** By JupyterHub's default design, every user's server is served from the same domain. If users don't trust each other, enable JupyterHub's [subdomain isolation](https://jupyterhub.readthedocs.io/en/stable/explanation/websecurity.html), which needs wildcard DNS and a wildcard certificate.

**Docker socket.** The hub must control Docker to start user containers, and Traefik reads Docker to discover services. Access to the Docker socket is equivalent to root on the host. Keep both images up to date, don't add software to the hub image, and restrict who can log in to the host.

**Secrets.** All secrets are in `.env`. Git ignores it; keep its permissions at `600`. The metrics token reaches the hub and Prometheus as a Compose secret file, not as an environment variable.

**Updates.** Every image and package is pinned to a version. Dependabot proposes updates weekly and CI tests them. Install new releases promptly; see [Updating](operations.md#updating).

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
- Images are downloaded from Docker Hub and quay.io. These downloads contain no user data.

**Requests from data subjects.** [Operations](operations.md#managing-users) shows how to export a user's files and how to delete a user and their data. Log entries disappear as logs rotate. Copies in backups last as long as your backup retention.

**Your responsibilities.** This list isn't complete:

- Keep a record of processing activities.
- Give users a privacy notice.
- Sign data processing agreements with your hosting provider and identity provider.
- Set a retention period for backups.
- Decide whether users' servers may reach the internet.
