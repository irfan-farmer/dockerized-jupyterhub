"""Test-only hub configuration (see tests/compose.test.yaml).

Loads the real configuration, then adds what the tests need: an API token for
starting servers, the images to start them from, and the canary resolver for
user containers.
"""

c = get_config()  # noqa: F821 - provided by JupyterHub
load_subconfig("/srv/jupyterhub/config/jupyterhub_config.py")  # noqa: F821

c.JupyterHub.services.append({"name": "tester", "api_token": "test-api-token"})
c.JupyterHub.load_roles.append(
    {"name": "tester", "scopes": ["admin:users", "admin:servers", "access:servers"], "services": ["tester"]}
)
c.DockerSpawner.allowed_images = {
    # Built from examples/environment by tests/repo2docker-test.sh.
    "environment": "jupyterhub-test-environment:local",
    "docker-stacks": "quay.io/jupyter/minimal-notebook:2026-10-19",
}
c.DockerSpawner.extra_host_config["dns"] = ["198.18.0.53"]
