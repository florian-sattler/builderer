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
            <img src="https://img.shields.io/github/license/florian-sattler/builderer.svg">
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

!!! quote

    builder let's you build your stack the __same way__ your build pipeline does so you won't get any suprises!

As often in life there are many ways to reach a goal.
_builderer_ is one such way when building repositories containing container based components (i.e. docker images).

_builderer_ makes it easy to build images both on any CI/CD plattform as well as your local machine.
<br>_(Obviously running builder requires python and either docker or podman)_

!!! tip

    builder let's you have only one build config for local and remote builds!

## Quickstart

Create `.builderer.yml` a the root of your project:

```yaml
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

Further configuration can be supplied via command line or in `.builderer.yml`.

!!! TIP

    See `builderer --help` and [docs](https://builderer.florian-sattler.de) to learn more.

## License

This project is licensed under the terms of the MIT license.
