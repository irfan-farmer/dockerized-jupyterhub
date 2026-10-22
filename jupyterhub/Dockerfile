FROM jupyterhub/jupyterhub:6.1.1

COPY requirements.txt /tmp/requirements.txt
RUN python3 -m pip install --no-cache-dir -r /tmp/requirements.txt

# The configuration is mounted from ./jupyterhub at runtime (see compose.yaml).
CMD ["jupyterhub", "-f", "/srv/jupyterhub/config/jupyterhub_config.py"]
