FROM jupyterhub/jupyterhub:4.0.0

COPY jupyterhub_config.py . 

# Create directories for custom templates and static files
RUN mkdir -p /usr/local/share/jupyterhub/custom_templates

# Copy the custom login.html file into the container
COPY custom_templates/login.html /usr/local/share/jupyterhub/custom_templates

# Copy the custom logo file into the container
COPY custom_templates/static/logo.png /usr/local/share/jupyterhub/custom_templates

RUN python3 -m pip install --no-cache-dir \
    jupyterhub-idle-culler \
    dockerspawner \
    oauthenticator==15.1.0 \
    jupyter_telemetry 


