import os
import sys
import logging

c = get_config()

# Logging configuration
c.JupyterHub.log_level = logging.DEBUG
c.JupyterHub.log_format = "[%(levelname)1.1s %(asctime)s.%(msecs).03d %(name)s] %(message)s"

# Template paths for customization
c.JupyterHub.template_paths = ['/usr/local/share/jupyterhub/custom_templates/']
c.JupyterHub.extra_static_paths = ['/usr/local/share/jupyterhub/static/']
c.JupyterHub.logo_file = '/usr/local/share/jupyterhub/static/logo.png'

# Using Helmholtz AAI to authenticate users
from oauthenticator.generic import GenericOAuthenticator
c.JupyterHub.authenticator_class = GenericOAuthenticator
c.GenericOAuthenticator.authorize_url = 'https://login.helmholtz.de/oauth2-as/oauth2-authz'
c.GenericOAuthenticator.oauth_callback_url = f'https://{os.environ.get("HOST")}/hub/oauth_callback'
c.GenericOAuthenticator.client_id = os.environ.get('CLIENT_ID')
c.GenericOAuthenticator.client_secret = os.environ.get('CLIENT_SECRET')
c.GenericOAuthenticator.login_service = 'Helmholtz AAI'
c.GenericOAuthenticator.userdata_url = 'https://login.helmholtz.de/oauth2/userinfo'
c.GenericOAuthenticator.token_url = 'https://login.helmholtz.de/oauth2/token/'
c.GenericOAuthenticator.username_key = 'email'
c.GenericOAuthenticator.refresh_pre_spawn = True
c.GenericOAuthenticator.userdata_token_method = "url"
c.GenericOAuthenticator.scope = ['openid', 'profile', 'email']
c.GenericOAuthenticator.custom_403_message = 'Login Failed'

# Load admin users from environment
admin_users = os.getenv("ADMIN_USERS", "")  # Read as string
admin_users = {user.strip() for user in admin_users.split(",") if user.strip()}  # Convert to set

# Debugging logs (visible in Docker logs)
print(f"DEBUG: Loaded admin users: {admin_users}")

# Set admin users
c.GenericOAuthenticator.admin_users = admin_users
c.GenericOAuthenticator.auth_refresh_age = 300

# Using DockerSpawner to spawn single user servers
c.JupyterHub.spawner_class = 'dockerspawner.DockerSpawner'
c.DockerSpawner.network_name = os.environ['DOCKER_NETWORK_NAME']
c.JupyterHub.hub_ip = os.environ['HUB_IP']
c.JupyterHub.cleanup_proxy = True
c.JupyterHub.cleanup_servers = True
c.DockerSpawner.debug = True
c.DockerSpawner.remove = True
c.DockerSpawner.name_template = "mvre-{username}"

# Directories mounted to JupyterLab
c.DockerSpawner.notebook_dir = '/home/jovyan'
c.DockerSpawner.volumes = {
    '/mnt/p_mvre_workspace/{username}': '/home/jovyan/work',
    '/mnt/mosaic_data': {'bind': '/home/jovyan/mosaic_data', 'mode': 'ro'},
    '/mnt/extra_files': {'bind': '/home/jovyan/extra_files', 'mode': 'ro'},
    '/mnt/mosaic_netCDF': {'bind': '/home/jovyan/mosaic_netCDF', 'mode': 'ro'},
    '/mnt/mosaic_notebooks': {'bind': '/home/jovyan/mosaic_notebooks', 'mode': 'ro'},
    '/mnt/DIVA_Guidelines.pdf': {'bind': '/home/jovyan/DIVA_Guidelines.pdf', 'mode': 'ro'},
}

# Images to spawn
c.DockerSpawner.allowed_images = {
    'DIVA': 'abarth/divand-jupyterhub:latest',
    'minimal-notebook': 'jupyter/minimal-notebook:x86_64-ubuntu-22.04',
    'dkrz-wps': 'dkrz_wps'
}

# Spawn command
c.DockerSpawner.cmd = os.environ.get("DOCKER_SPAWN_CMD", "start-singleuser.sh")

# Template variables for useful announcements 
c.JupyterHub.template_vars = {
    'announcement_spawn': 'Select drop down for options',
    'announcement_home': 'To ensure that your data and notebooks are properly saved, please make sure to store them inside the designated "work" folder. Any data created outside of this folder will not be saved.'
}

# Define environment
c.DockerSpawner.environment = {
    'JUPYTERHUB_USER': '{username}',
    'DEBUG': 'True',  # This will print more info during container launch
}

# Test cnfig for enabling jupyterhub metrics
c.JupyterHub.metrics_enabled = True
c.JupyterHub.metrics_port = 80
c.JupyterHub.metrics_path = '/hub/metrics'

# Define roles with the necessary permissions
c.JupyterHub.load_roles = [
    {
        "name": "jupyterhub-idle-culler-role",
        "scopes": [
            "list:users",
            "read:users:activity",
            "read:servers",
            "delete:servers",
        ],
        "services": ["jupyterhub-idle-culler-service"],
    },
    {
        'name': 'prometheus-admin',
        'scopes': ['read:metrics'],
        'services': ['prometheus-service'],
    },
]

# Define the services
c.JupyterHub.services = [
    {
        "name": "jupyterhub-idle-culler-service",
        "command": [
            sys.executable,
            "-m", "jupyterhub_idle_culler",
            "--timeout=604800",  # Timeout to one week
        ],
    },
    {
        "name": "prometheus-service",
        "api_token": os.environ.get('API_TOKEN'),  
    },
]
