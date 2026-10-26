FROM jupyterhub/jupyterhub:6.1.1

# Packages the base image lacks, each pinned by hash (see requirements.txt).
COPY requirements.txt /tmp/requirements.txt
RUN python3 -m pip install --no-cache-dir --no-deps --require-hashes -r /tmp/requirements.txt \
    && python3 -m pip check

# The configuration is mounted from ./jupyterhub at runtime (see compose.yaml).
CMD ["jupyterhub", "-f", "/srv/jupyterhub/config/jupyterhub_config.py"]
