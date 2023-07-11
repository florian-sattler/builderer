# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Added step to forward multiple images

### Fixed

- Recompiled `requirements.txt`

## [v1.1.0] - 2023-02-28

### Added

- Allow specifying additional tags when building or forwarding an image on a per step basis.

### Changed

- `extract_from_image` now requires full image names allowing extraction from remote images.
- Documentation will now only be published for new releases.

### Fixed

- Documentation Typos

## [v1.0.0] - 2023-02-23

### Added

- Added publishing documentation.
- Added missing tests to push coverage to 100%. New code will need to be tested from now on.
- Require at least python 3.10
- Linting for PRs using [github actions](https://docs.github.com/en/actions/automating-builds-and-tests/building-and-testing-python)
- Automatically update documentation via gh actions.
- Extended Documentation

### Changed

- Configuration for [black](https://black.readthedocs.io/en/stable/) and [flake8](https://flake8.pycqa.org/en/latest/).
- Call `Builderer` methods using keyword arguments from file config when ever possible.
- Updated dependencies and merged into single `requirements.txt`

### Removed

- Deleted Python 3.9 package classifier.

### Fixed

- `dockerfile` argument was not honored when specified in file config.

## [v0.4.1] - 2023-02-18

### Added

- Option to specify which Dockerfile to use for `build_image` and `BuildImage`.
- Added usage documentation.
- Publish builderer to [PyPI](https://pypi.org/project/builderer/) via [github actions](https://github.com/marketplace/actions/pypi-publish).

### Fixed

- Up to date CLI docs
- Load license shields from pipy to reduce github token load

## [v0.4.0] - 2023-02-13

### Added

- Development requirements pinned using [pip compile](https://github.com/jazzband/pip-tools)
- Extended documentation configuration
  - added navigation to footer
  - added copyright notice to footer
  - added social links to footer
  - instant page loading
  - moved page table of contents (right) into main navigation (left)
  - added scroll to top button
- Added [editor integration](http://builderer.florian-sattler.de/editor-integration/) for `.builderer.yml`
- Added links for each release showing what changed using github's compare function.
- Improved config validation and error display
- Added docstrings in `builderer.builderer.Builderer`
- Added [mkdocstrings](https://github.com/mkdocstrings/mkdocstrings) to generated references.
- Added Documentation for json / yaml schema
- Extended CLI documentation:
- Documented usage as library

### Changed

- Renamed `BuildConfig` to builderer config for clarity and editor integration.
- Reworked shields in documentation and README.md

### Fixed

- PyPI project urls
- Fixed broken nested lists with two spaces using [mdx_truly_sane_lists](https://pypi.org/project/mdx-truly-sane-lists/) see [this issue](https://github.com/mkdocs/mkdocs/issues/545)

## [v0.3.0] - 2023-02-10

### Added

- Added example workspace containing a docker compose project with frontend backend and database
- Added tests using [pytest](https://docs.pytest.org/)
- Added [online documentation](https://builderer.florian-sattler.de) using [MkDocs](https://www.mkdocs.org/) and [Material for MkDocs](https://squidfunk.github.io/mkdocs-material)
- Additional URLs on [PyPI](https://pypi.org/project/builderer/) to documentation, changelog, code and issue tracker

### Changed

- Moved from _pydanctic argparse_ to pythons argparse

### Removed

- Removed `name` from build config

## [v0.2.0] - 2023-02-08

### Added

- Added command line interface with config files using [Pydantic](https://docs.pydantic.dev/) and [Pydantic Argparse](https://pydantic-argparse.supimdos.com/)
- Updated README.md to reflect changes
- pin requirements and their dependencies using [pip compile](https://github.com/jazzband/pip-tools)
- Added link to this changelog in [README.md](https://github.com/florian-sattler/builderer/blob/main/README.md)
- Initial [PyPI release](https://pypi.org/project/builderer/)
- Improved package metadata

### Changed

- The `Builderer` object can now be imported directly from the package.

## [v0.1.0] - 2023-02-07

### Added

- README
- LICENSE
- .gitignore
- Builderer-Package with [PEP 518 Metadata](https://peps.python.org/pep-0518/)
- Changelog
- Use bump2version

[unreleased]: https://github.com/florian-sattler/builderer/compare/v1.1.0...HEAD
[v1.1.0]: https://github.com/florian-sattler/builderer/compare/v1.0.0...v1.1.0
[v1.0.0]: https://github.com/florian-sattler/builderer/compare/v0.4.1...v1.0.0
[v0.4.1]: https://github.com/florian-sattler/builderer/compare/v0.4.0...v0.4.1
[v0.4.0]: https://github.com/florian-sattler/builderer/compare/v0.3.0...v0.4.0
[v0.3.0]: https://github.com/florian-sattler/builderer/compare/v0.2.0...v0.3.0
[v0.2.0]: https://github.com/florian-sattler/builderer/compare/v0.1.0...v0.2.0
[v0.1.0]: https://github.com/florian-sattler/builderer/releases/tag/v0.1.0
