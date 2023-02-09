# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Removed

- Removed `name` from build config

## [0.2.0] - 2023-02-08

### Added

- Added command line interface with config files using [Pydantic](https://docs.pydantic.dev/) and [Pydantic Argparse](https://pydantic-argparse.supimdos.com/)
- Updated README.md to reflect changes
- pin requirements and their dependencies using [pip compile](https://github.com/jazzband/pip-tools)
- Added link to this changelog in [README.md](README.md)
- Initial [PyPI release](https://pypi.org/project/builderer/)
- Improved package metadata

### Changed

- The `Builderer` object can now be imported directly from the package.

## [0.1.0] - 2023-02-07

### Added

- README
- LICENSE
- .gitignore
- Builderer-Package with [PEP 518 Metadata](https://peps.python.org/pep-0518/)
- Changelog
- Use bump2version
