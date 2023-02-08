<div align="center">
    <a href="https://builderer.florian-sattler.de">
        <img src="https://builderer.florian-sattler.de/logo-color.svg" width="25%">
    </a>
    <h1>
        builderer
    </h1>
    <p>
        <em>Container based mono repo builder</em>
    </p>
    <a href="https://pypi.python.org/pypi/builderer">
        <img src="https://img.shields.io/pypi/v/builderer.svg">
    </a>
    <a href="https://pepy.tech/project/builderer">
        <img src="https://pepy.tech/badge/builderer">
    </a>
    <a href="https://github.com/florian-sattler/builderer">
        <img src="https://img.shields.io/pypi/pyversions/builderer.svg">
    </a>
    <a href="https://github.com/florian-sattler/builderer/blob/main/LICENSE">
        <img src="https://img.shields.io/github/license/florian-sattler/builderer.svg">
    </a>
    <img src="https://img.shields.io/github/v/tag/florian-sattler/builderer">
</div>

_builderer_ builds docker based projects both in ci/cd and locally omitting endless configuration and the need to restart ci/cd pipelines to get a running build.

## Help

See [documentation](https://builderer.florian-sattler.de) for help.

## Installation

```bash
pip install builderer
```

## Example

Create `.builderer.yml` a the root of your project:

```yaml
steps:
  - type: build_images
    directories:
      - database
      - frontend
      - backend
```

Run the configuration.

```shell
$ builderer
Building image: database
Building image: frontend
Building image: backend
Pushing image: backend
Pushing image: frontend
Pushing image: database
```

Further configuration can be supplied via command line or in `.builderer.yml`.
See `builderer --help` and [docs](https://builderer.florian-sattler.de) to learn more.

## Changelog

Interested in what's new? Take a look at the [Changelog](CHANGELOG.md)!

## License

This project is licensed under the terms of the MIT license.
