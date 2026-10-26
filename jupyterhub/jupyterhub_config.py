"""JupyterHub configuration.

Settings that differ between deployments are read from .env (see .env.example).
For anything else, create jupyterhub_config.local.py next to this file. It is
loaded last and ignored by git, so this file can be updated without conflicts.
"""

import logging
import os
import sys
import threading
from pathlib import Path

import docker
from dockerspawner import DockerSpawner

c = get_config()  # noqa: F821 - provided by JupyterHub


def env(name, default=""):
    """Return an environment variable, or `default` if it is unset or empty."""
    return os.environ.get(name) or default


def required_env(name):
    value = env(name)
    if not value:
        sys.exit(f"{name} is not set. Add it to .env (see .env.example).")
    return value


def required_secret(name):
    """Return a Compose secret (see compose.yaml), exiting if it is empty."""
    value = Path("/run/secrets", name.lower()).read_text().strip()
    if not value:
        sys.exit(f"{name} is not set. Add it to .env (see .env.example).")
    return value


def env_set(name):
    """Return a comma-separated environment variable as a set."""
    return {item.strip() for item in env(name).split(",") if item.strip()}


def pull_images(images):
    """Download images, so the first server start doesn't wait for them."""
    log = logging.getLogger("JupyterHub")
    for image in images:
        try:
            docker.from_env().images.pull(image)
            log.info("Notebook image %s is ready", image)
        except docker.errors.DockerException as e:
            log.warning("Could not pull notebook image %s: %s", image, e)


class EnvironmentSpawner(DockerSpawner):
    """DockerSpawner that also runs images built by repo2docker.

    Those images lack the start scripts of Jupyter Docker Stacks images and keep
    their repository's files in the home directory. For them, start
    jupyterhub-singleuser directly and open the home directory, where users see
    the repository's files next to their persistent work/ folder.
    """

    async def start(self):
        if not hasattr(self, "_configured"):
            self._configured = (self.cmd, self.notebook_dir)
        # Resolve the chosen image the same way DockerSpawner.start() does.
        option = self.user_options.get("image")
        image = await self.check_allowed(option) if option else self.image
        await self.pull_image(image)
        labels = (await self.docker("inspect_image", image))["Config"].get("Labels") or {}
        if "repo2docker.version" in labels:
            self.cmd, self.notebook_dir = ["jupyterhub-singleuser"], "/home/jovyan"
        else:
            self.cmd, self.notebook_dir = self._configured
        return await super().start()


domain = required_env("DOMAIN")
c.JupyterHub.public_url = f"https://{domain}/"

# Hub state (user database, cookie secret) lives on the hub_data volume.
c.JupyterHub.db_url = "sqlite:////srv/jupyterhub/data/jupyterhub.sqlite"
c.JupyterHub.cookie_secret_file = "/srv/jupyterhub/data/jupyterhub_cookie_secret"
# Apply database migrations after upgrades. SQLite is backed up first.
c.JupyterHub.upgrade_db = True
# Keep user servers running while the hub restarts.
c.JupyterHub.cleanup_servers = False
# User containers and the proxy reach the hub through its .invalid alias
# (see compose.yaml).
c.JupyterHub.hub_ip = "0.0.0.0"
c.JupyterHub.hub_connect_ip = "hub.invalid"

# The proxy runs in its own container (see compose.yaml).
c.ConfigurableHTTPProxy.should_start = False
c.ConfigurableHTTPProxy.api_url = "http://proxy.invalid:8001"
c.ConfigurableHTTPProxy.auth_token = required_env("PROXY_AUTH_TOKEN")
# Also re-adds proxy routes every minute, for example after the proxy restarts.
c.JupyterHub.last_activity_interval = 60

# Login through any OpenID Connect provider.
c.JupyterHub.authenticator_class = "oauthenticator.generic.GenericOAuthenticator"
c.GenericOAuthenticator.client_id = required_env("OAUTH_CLIENT_ID")
c.GenericOAuthenticator.client_secret = required_env("OAUTH_CLIENT_SECRET")
c.GenericOAuthenticator.authorize_url = required_env("OAUTH_AUTHORIZE_URL")
c.GenericOAuthenticator.token_url = required_env("OAUTH_TOKEN_URL")
c.GenericOAuthenticator.userdata_url = required_env("OAUTH_USERDATA_URL")
c.GenericOAuthenticator.oauth_callback_url = f"https://{domain}/hub/oauth_callback"
c.GenericOAuthenticator.username_claim = env("OAUTH_USERNAME_CLAIM", "preferred_username")
c.GenericOAuthenticator.scope = env("OAUTH_SCOPE", "openid profile email").split()
c.GenericOAuthenticator.login_service = env("OAUTH_LOGIN_SERVICE", "SSO")

# Who may log in. Admins always can; everyone else must be allowed explicitly.
c.GenericOAuthenticator.admin_users = env_set("ADMIN_USERS")
c.GenericOAuthenticator.allowed_users = env_set("ALLOWED_USERS")
c.GenericOAuthenticator.allow_all = env("ALLOW_ALL_USERS").lower() == "true"
if env("ALLOWED_GROUPS") or env("ADMIN_GROUPS"):
    c.GenericOAuthenticator.manage_groups = True
    c.GenericOAuthenticator.auth_state_groups_key = "oauth_user." + env("OAUTH_GROUPS_CLAIM", "groups")
    c.GenericOAuthenticator.allowed_groups = env_set("ALLOWED_GROUPS")
    c.GenericOAuthenticator.admin_groups = env_set("ADMIN_GROUPS")

# One container per user, with a persistent volume mounted as ~/work.
c.JupyterHub.spawner_class = EnvironmentSpawner
c.DockerSpawner.image = env("NOTEBOOK_IMAGE", "quay.io/jupyter/scipy-notebook:2026-10-19")
c.DockerSpawner.network_name = "jupyterhub-users"
c.DockerSpawner.remove = True
c.DockerSpawner.notebook_dir = "/home/jovyan/work"
c.DockerSpawner.volumes = {"jupyterhub-user-{username}": "/home/jovyan/work"}
if shared_data_dir := env("SHARED_DATA_DIR"):
    c.DockerSpawner.volumes[shared_data_dir] = {"bind": "/home/jovyan/work/shared", "mode": "ro"}
c.DockerSpawner.mem_limit = env("USER_MEM_LIMIT", "2G")
c.DockerSpawner.cpu_limit = float(env("USER_CPU_LIMIT", "1"))
c.DockerSpawner.extra_host_config = {
    "security_opt": ["no-new-privileges:true"],
    "pids_limit": 1024,
    # No swap on top of the memory limit.
    "memswap_limit": c.DockerSpawner.mem_limit,
    # Don't append the host's DNS search domains (see compose.yaml).
    "dns_search": ["."],
}
# A server may still need to pull its image, for example right after an update.
c.DockerSpawner.start_timeout = 300

c.JupyterHub.load_roles = [
    {
        "name": "idle-culler",
        "scopes": ["list:users", "read:users:activity", "read:servers", "delete:servers"],
        "services": ["idle-culler"],
    },
    {
        "name": "prometheus",
        "scopes": ["read:metrics"],
        "services": ["prometheus"],
    },
]
c.JupyterHub.services = [
    {
        # Stops servers without activity for IDLE_TIMEOUT seconds.
        "name": "idle-culler",
        "command": [
            sys.executable,
            "-m",
            "jupyterhub_idle_culler",
            f"--timeout={env('IDLE_TIMEOUT', '3600')}",
        ],
    },
    {
        # Prometheus reads /hub/metrics with this token.
        "name": "prometheus",
        "api_token": required_secret("METRICS_TOKEN"),
    },
]

local_config = Path(__file__).with_name("jupyterhub_config.local.py")
if local_config.exists():
    load_subconfig(str(local_config))  # noqa: F821 - provided by JupyterHub

# Pull the notebook images in the background, including any offered through
# allowed_images in jupyterhub_config.local.py.
images = {c.DockerSpawner.image}
if isinstance(c.DockerSpawner.get("allowed_images"), dict):
    images.update(c.DockerSpawner.allowed_images.values())
threading.Thread(target=pull_images, args=(images,), daemon=True).start()
