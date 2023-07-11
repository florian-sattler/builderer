<div style="text-align:center">
    <a href="https://builderer.florian-sattler.de">
        <img src="logo-color.svg" width="25%">
    </a>
    <h1 style="margin-bottom:0;font-size:3em;">
        builderer
    </h1>
    <p style="margin-top:0;">
        <em>Container based mono repo builder</em>
    </p>
    <p>
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
            <img alt="PyPI - License" src="https://img.shields.io/pypi/l/builderer">
        </a>
        <a href="https://github.com/florian-sattler/builderer/releases">
            <img src="https://img.shields.io/github/v/release/florian-sattler/builderer?label=github">
        </a>
        <a href="https://builderer.florian-sattler.de">
            <img src="https://img.shields.io/badge/docs-yes-brightgreen">
        </a>
        <img src="https://img.shields.io/badge/made%20with-%E2%99%A5%EF%B8%8F-red">
    </p>
</div>

---

## But why?

_builderer_ let's you build your container stack the **same way** your build pipeline does so you won't get any surprises!

!!! quote "Quote by the author"

    Do you need more than a builder? Try _builderer_!

_builderer_ makes it easy to build images both on CI/CD platforms as well as your local machine using the same configuration and build command.
<br>_(Running builder requires python and either docker or podman)_

!!! tip

    __builderer__ let's you have only one build config for local and remote builds! Use the [cli](cli.md) for tweaking different environments.

## Quickstart

Create `.builderer.yml` a the root of your project:

```yaml
parameters:
  registry: registry.example.com

steps:
  - type: build_images
    directories:
      - database
      - frontend
      - backend
```

Run the configuration locally to check for potential issues.

```shell
$ builderer --no-push
Building image: database
Building image: frontend
Building image: backend
```

Now add builderer to your delivery pipeline and get a running build!

```shell
$ builderer
Building image: database
Building image: frontend
Building image: backend
Pushing image: backend
Pushing image: frontend
Pushing image: database
```

Further configuration can be supplied via [command line](cli.md) or in [`.builderer.yml`](usage.md).

!!! TIP

    Take a look at `builderer --help` to learn more or follow this documentation.

## License

This project is licensed under the terms of the MIT license.
