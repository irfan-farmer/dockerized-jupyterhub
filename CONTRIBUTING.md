# Contributing

Bug reports, fixes and documentation improvements are welcome. Keep pull requests small and focused on one change.

## Making a change

1. Fork the repository and create a branch from `main`.
2. Make your change. If it affects people running the stack, add a line under **Unreleased** in [CHANGELOG.md](CHANGELOG.md).
3. Run the smoke test. It needs Docker and free ports 80 and 443:

   ```bash
   tests/smoke-test.sh
   ```

4. Open a pull request. CI runs the same test.

Write commit messages in the [Conventional Commits](https://www.conventionalcommits.org/) style, for example `fix: keep user servers running during hub restarts`.

## Versioning

The project follows [Semantic Versioning](https://semver.org/):

- **Major**: upgrading needs manual steps, for example a renamed `.env` variable or a volume change.
- **Minor**: new features that work without changes to an existing `.env`.
- **Patch**: fixes and dependency updates.

## Releasing

1. Check that the default `NOTEBOOK_IMAGE` in `jupyterhub/jupyterhub_config.py` and `.env.example` is recent. Dependabot updates everything else.
2. In CHANGELOG.md, move the **Unreleased** entries under a new version heading with today's date.
3. Commit, tag and push:

   ```bash
   git commit -am "chore(release): v1.2.3"
   git tag -a v1.2.3 -m "v1.2.3"
   git push origin main v1.2.3
   ```

4. Create a GitHub release from the tag and paste the changelog section as release notes.
