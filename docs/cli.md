# Command Line Interface

_builderer_ is primarily intended to be invoked via command line.
Using it programmatically inside another program is possible via the [library interface](library.md).

## Overview

A short description of all the command line argument may be printed printed using `--help` as argument.

```{ .text .no-copy }
$ builderer --help
usage: builderer [-h] [--registry REGISTRY] [--prefix PREFIX]
                 [--tags TAGS [TAGS ...]] [--no-push] [--cache] [--verbose]
                 [--simulate] [--backend {docker,podman}]
                 [--max-parallel MAX_PARALLEL] [--config CONFIG] [--version]

Building and pushing containers. Command line arguments take precedence over
file configuration which in turn takes precedence over default values

options:
  -h, --help            show this help message and exit
  --registry REGISTRY   Set the registry url. You may include a port using the
                        colon notation (example.com:3000/). This is needed
                        when using a non standard port. Unset by default.
  --prefix PREFIX       Set the directory for all images. This is the image
                        component between registry url and image name. For
                        example on docker hub this is used for the username.
                        Unset by default.
  --tags TAGS [TAGS ...]
                        One or multiple tags to use for each image. Defaults
                        to ['latest']
  --no-push             Path to builderer yaml configuration file. Defaults to
                        '.builderer.yml'
  --cache               Whether to allow using cached images. This is
                        especially usefull for local builds.
  --verbose             Show issued commands and their live output.
  --simulate            Prevent issuing any commands just do the printing.
  --backend {docker,podman}
                        Overwrite the backend used to build, tag and pull
                        images. Defaults to 'docker'
  --max-parallel MAX_PARALLEL
                        Limit the maximum number of parallel jobs per step. By
                        default the num_parallel argument of each individual
                        step is used.
  --config CONFIG       Path to builderer yaml configuration file. Defaults to
                        '.builderer.yml'
  --version             show program's version number and exit

This program is intended to run locally as well as inside ci/cd jobs.
```

## Details

Detailed descriptions for all commands are shown below.

!!! INFO

    Command line arguments take precedence over file configuration which in turn takes precedence over default values.

### `-h` <br>`--help`

Show the help message and exit with return code `0`.

### `--registry` `url`

Set the registry url including a port if a non standard port is used.

Default: `''` (empty string)

??? Example

    ```
    builderer --registry registry.example.com:3000
    ```

!!! Warning

    An empty registry will lead to errors when pushing.
    Make sure to pass `--no-push` if needed.

### `--prefix` `prefix`

Set the folder for all images.
This is the image component between registry url and image name.
For example on docker hub this is used for the username.

Default: `''` (empty string)

??? Example

    ```
    builderer --prefix foo
    ```

    This will result in images tagged `<registry-url>/foo/<image-name>:<image-tag>`

### `--tags` `tags ...`

One or multiple tags to use for each image.
Multiple tags get separated as args. (i.e. by spaces in a shell environment)

Default: `latest`

??? Example

    ```
    builderer --tags foo bar baz
    ```

!!! TIP

    This is a great place to use environment variables or other shell variables such as build id or the current date.

    `builderer --tags "$(date --iso-8601)" "$BUILD_BUILDID" latest`

### `--no-push`

Prevent pushing images in all steps.

### `--cache`

Allow using cached images.
This is especially usefull for local builds.

### `--verbose`

Show issued commands and their output.

!!! INFO

    If an build error occurs and `--verbose` was **not** passed,
    the full output of the failed command will still be printed to standard out.

### `--simulate`

Prevent issuing any commands just do the printing.

!!! TIP

    Using `--simulate` alongside `--verbose` might be usefull for debugging.

### `--backend` `docker` or `podman`

Overwrite the backend used to build, tag and pull images.

Default: `docker`

??? Example

    ```
    builderer --backend podman
    ```

### `--max-parallel` `max_parallel`

Limit the maximum number of parallel jobs per step. By
default the num_parallel argument of each individual
step is used.

Default: No limit

??? Example

    ```
    builderer --max-parallel 1
    ```

### `--config` `path/to/config.yml`

Path to builderer config.

Default: `.builderer.yml`

??? Example

    ```
    builderer --config ./other-config.yaml
    ```

### `--version`

Show version number and exit with return code `0`.
