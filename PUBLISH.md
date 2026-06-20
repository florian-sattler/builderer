# PUBLISH

This document describes the process of publishing a new version of `builderer`.

1. Run the following command to update the schema:

   ```bash
   python -c 'import json, builderer.config; print(json.dumps(builderer.config.BuildererConfig.model_json_schema(), indent=2))' > docs/schema.json
   ```

1. If anything changed: Add notice to CHANGELOG.md and commit **both** files.
1. Update CHANGELOG.md
   - Add header for new version
   - Add compare link for new version
   - Update compare link for _unreleased_
1. _Stage_ CHANGELOG.md
1. Bump the version using one of:

   ```bash
   bump2version major --allow-dirty
   bump2version minor --allow-dirty
   bump2version patch --allow-dirty
   ```

1. Push Update

   ```bash
   git push
   git push --tags
   ```

1. Create a new GitHub release. It will trigger a PYPI release via a github action.
