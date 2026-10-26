# Environment template

Copy this folder into a repository of its own to give your hub's users a custom environment, for example for a course or a research project. GitHub Actions builds it into an image with [repo2docker](https://repo2docker.readthedocs.io/) and publishes it. The hub only downloads the finished image; nothing is built on the hub's server.

## Use it

1. Create a repository from these files, including `.github/workflows/build.yml`.
2. List your packages in `environment.yml`, keeping `jupyterhub-singleuser`. Add any notebooks or data the environment should start with; they appear in users' home folders.
3. Push to `main`. The workflow publishes `ghcr.io/<owner>/<repository>:<commit>`. On GitHub, set the package's visibility to **Public**, unless your hub has credentials for the registry.
4. Offer the image in the hub's `jupyterhub/jupyterhub_config.local.py`:

   ```python
   c.DockerSpawner.allowed_images = {
       "Python (SciPy)": "quay.io/jupyter/scipy-notebook:2026-10-19",
       "Course X": "ghcr.io/<owner>/<repository>:<commit>",
   }
   ```

5. Restart the hub: `docker compose restart jupyterhub`.

Users choose the environment when they start their server. Files they save outside `work/` are reset each time their server starts.

Pin images to a commit tag rather than `latest`, so everyone gets the same environment until you change it.

repo2docker also reads `requirements.txt`, `apt.txt`, `install.R` and other files. See its [list of configuration files](https://repo2docker.readthedocs.io/en/latest/configuration/).
