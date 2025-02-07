FROM jupyterhub/jupyterhub:4.0.0

# Create directories for custom templates and static files
RUN mkdir -p /usr/local/share/jupyterhub/custom_templates

# Copy configuration files
COPY jupyterhub_config.py .
COPY custom_templates/login.html /usr/local/share/jupyterhub/custom_templates/

# Copy image files
COPY custom_templates/static /usr/local/share/jupyterhub/static/

RUN python3 -m pip install --no-cache-dir \
    jupyterhub-idle-culler \
    dockerspawner \
    oauthenticator==15.1.0 \
    jupyter_telemetry 


