# PUBLISH

This document describes the process of publishing a new version of `builderer`.

1. Run the following command to update the schema:

   ```
   python -c 'import builderer.config; print(builderer.config.BuildererConfig.schema_json(indent=2))' > docs/schema.json
   ```

1. If anything changed: Add notice to CHANGELOG.md and commit **both** files.
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

1. Create a new GitHub release. It will trigger a PYPI release via a github action.
