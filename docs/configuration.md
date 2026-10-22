# Configuration

Routine settings live in `.env`, and [.env.example](../.env.example) describes each one. This page covers the settings that need more explanation.

After changing `.env`, apply the change with `docker compose up -d`. This restarts the hub, but users stay connected to their servers.

## Identity provider

The hub works with any OpenID Connect provider. Create a confidential client that uses the authorization code flow, set its redirect URI to `https://<DOMAIN>/hub/oauth_callback`, and copy the client ID and secret into `.env`. Then add the provider's endpoints:

**Keycloak**

```ini
OAUTH_AUTHORIZE_URL=https://keycloak.example.org/realms/<realm>/protocol/openid-connect/auth
OAUTH_TOKEN_URL=https://keycloak.example.org/realms/<realm>/protocol/openid-connect/token
OAUTH_USERDATA_URL=https://keycloak.example.org/realms/<realm>/protocol/openid-connect/userinfo
```

**Authentik**

```ini
OAUTH_AUTHORIZE_URL=https://authentik.example.org/application/o/authorize/
OAUTH_TOKEN_URL=https://authentik.example.org/application/o/token/
OAUTH_USERDATA_URL=https://authentik.example.org/application/o/userinfo/
```

**Microsoft Entra ID**

```ini
OAUTH_AUTHORIZE_URL=https://login.microsoftonline.com/<tenant-id>/oauth2/v2.0/authorize
OAUTH_TOKEN_URL=https://login.microsoftonline.com/<tenant-id>/oauth2/v2.0/token
OAUTH_USERDATA_URL=https://graph.microsoft.com/oidc/userinfo
OAUTH_USERNAME_CLAIM=email
```

**Google**

```ini
OAUTH_AUTHORIZE_URL=https://accounts.google.com/o/oauth2/v2/auth
OAUTH_TOKEN_URL=https://oauth2.googleapis.com/token
OAUTH_USERDATA_URL=https://openidconnect.googleapis.com/v1/userinfo
OAUTH_USERNAME_CLAIM=email
```

**Helmholtz AAI**

```ini
OAUTH_AUTHORIZE_URL=https://login.helmholtz.de/oauth2-as/oauth2-authz
OAUTH_TOKEN_URL=https://login.helmholtz.de/oauth2/token
OAUTH_USERDATA_URL=https://login.helmholtz.de/oauth2/userinfo
OAUTH_USERNAME_CLAIM=email
OAUTH_GROUPS_CLAIM=eduperson_entitlement
```

### Usernames

`OAUTH_USERNAME_CLAIM` chooses which claim becomes the JupyterHub username. The default, `preferred_username`, suits Keycloak and Authentik. Google and Entra ID don't send that claim, so use `email` for them.

The username is also used in the names of each user's container and volume. If you change the claim after people have logged in, they get new, empty volumes.

## Who may log in

A user can log in if they match any of these rules:

| Setting | Allows |
|---|---|
| `ADMIN_USERS` | The listed usernames, with admin rights |
| `ALLOWED_USERS` | The listed usernames |
| `ALLOWED_GROUPS` | Members of the listed groups |
| `ADMIN_GROUPS` | Members of the listed groups, with admin rights |
| `ALLOW_ALL_USERS=true` | Everyone your identity provider authenticates |

With none of these set except `ADMIN_USERS`, only admins can log in.

The group rules need the provider to send group membership in the userinfo response:

- **Keycloak**: add a *Group Membership* mapper to the client, with token claim name `groups`, *Full group path* off and *Add to userinfo* on.
- **Authentik**: groups are included in the `profile` scope.
- **Other providers**: set `OAUTH_GROUPS_CLAIM` to the claim that lists groups. Add a scope to `OAUTH_SCOPE` if the provider only sends groups when asked.

Use `ALLOW_ALL_USERS=true` only if the provider itself limits who can use the client. For example, Entra ID can require users to be assigned to the application.

## Notebook image

`NOTEBOOK_IMAGE` sets the image used for user servers. Any image from [Jupyter Docker Stacks](https://jupyter-docker-stacks.readthedocs.io/) works, as does your own image built on one of them. Pin a dated tag rather than `latest`, so that every user gets the same environment.

When the hub starts, it downloads the image in the background, so the first server start doesn't have to wait for it. A new image is used the next time a user starts their server.

To let users choose between images, create `jupyterhub/jupyterhub_config.local.py`. The hub downloads these images at startup too:

```python
c.DockerSpawner.allowed_images = {
    "Python": "quay.io/jupyter/scipy-notebook:2026-10-19",
    "R": "quay.io/jupyter/r-notebook:2026-10-19",
}
```

## Resources

- `USER_MEM_LIMIT` (default `2G`) and `USER_CPU_LIMIT` (default `1`) cap each user's container. A user who goes over the memory limit sees their kernel restart. Containers can't use swap on top of the limit, so one user can't slow down the whole host.
- Each container can run at most 1024 processes and threads, which stops runaway scripts from exhausting the host.
- `IDLE_TIMEOUT` (default `3600` seconds) stops servers that have had no activity for that long. The user's files stay; they start the server again on their next visit.

## Shared data

Set `SHARED_DATA_DIR` to a directory on the host to mount it read-only at `~/work/shared` in every user's server. The files must be readable by user ID 1000, the `jovyan` user in the notebook images.

## Storage

Each user's `~/work` directory is stored in a Docker volume named `jupyterhub-user-<username>`. Users land in `~/work` when they open JupyterLab. Anything they create outside it, such as packages installed with `pip install --user`, is lost when the server stops.

Docker volumes have no size limit per user, so one user can fill the disk. Keep Docker's data directory on a disk with room to spare, ideally separate from the operating system, and set up the disk alert described in [Monitoring](operations.md#monitoring).

To use a different location, such as a network file system, change `c.DockerSpawner.volumes` in `jupyterhub_config.local.py`.

## Branding

Put a logo in `jupyterhub/`, the directory mounted into the hub container, and reference it in `jupyterhub_config.local.py`. You can also show a banner on every page:

```python
c.JupyterHub.logo_file = "/srv/jupyterhub/config/logo.png"
c.JupyterHub.template_vars = {"announcement": "Scheduled maintenance on Friday, 18:00–19:00."}
```

For deeper changes, see [Working with templates and UI](https://jupyterhub.readthedocs.io/en/stable/howto/templates.html) in the JupyterHub docs.

## Using your own TLS certificate

If you can't use Let's Encrypt, for example because the host isn't reachable from the internet, give Traefik your certificate:

1. Mount the certificate directory in `compose.override.yaml`:

   ```yaml
   services:
     traefik:
       volumes:
         - /etc/ssl/jupyterhub:/certs:ro
   ```

2. Add the files at the end of `traefik/dynamic.yml`:

   ```yaml
   tls:
     certificates:
       - certFile: /certs/fullchain.pem
         keyFile: /certs/privkey.pem
   ```

Traefik uses a matching certificate from this list and only asks Let's Encrypt for names it doesn't cover.
