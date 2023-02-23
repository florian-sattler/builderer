# PUBLISH

This document describes the process of publishing a new version of `builderer`.

1. Make sure to clone a fresh copy of the repository.
1. Create a venv:

   ```
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

1. Run the following command to update the schema:

   ```
   python -c 'import builderer.config; print(builderer.config.BuildererConfig.schema_json(indent=2))' > docs/schema.json
   ```

1. If anything changed: Add notice to CHANGELOG.md and commit **both** files.
1. Run tests and make sure everything passes:

   ```
   black --check builderer tests
   flake8 builderer tests
   mypy builderer tests
   pytest tests/ --cov builderer
   ```

1. Update CHANGELOG.md
   - Add header for new version
   - Add compare link for new version
   - Update compare link for _unreleased_
1. _Stage_ CHANGELOG.md
1. Bump the version using one of:

   ```
   bump2version major --allow-dirty
   bump2version minor --allow-dirty
   bump2version patch --allow-dirty
   ```

1. Push Update

   ```
   git push
   git push --tags
   ```

1. Update documentation. A github action will automatically deploy it.

   ```
   ./venv/bin/mkdocs gh-deploy
   ```

1. Create a new GitHub release. It will trigger a PYPI release via a github action.
