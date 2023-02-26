# Usage

This document shows how to used a `.builderer.yml` file to configure your build.

Using the `builderer` python library is documented [here](library.md).

!!! Note

    builderer works great on projects containing multiple folder which need to be build, nested below a common root directory.

    ``` { .text .no-copy }
    example_workspace
    ├── backend
    │   ├── Dockerfile
    │   └── ...
    ├── frontend
    │   ├── Dockerfile
    │   └── ...
    ├── docker-compose.yml
    └── .builderer.yml
    ```

To get builderer up and running create a `.builderer.yml` file at the root of your project containing at least the following:

```yaml
steps: []
```

Now look below on how to fill the steps and how update default parameters.
When you are happy run

```bash
builderer
```

calling the [command line interface](cli.md) to run your build.

## BuildererConfig

This defines the config file, typically called `.builderer.yml`.

| Property                  | Type   | Required | Description                                                                                  |
| ------------------------- | ------ | -------- | -------------------------------------------------------------------------------------------- |
| [steps](#steps)           | array  | Yes      | List of steps to execute.                                                                    |
| [parameters](#parameters) | object | No       | Overwrite default parameters. Values set here will be overwritten by command line arguments. |

??? Example

    ```yaml
    parameters:
      registry: registry.example.com
      prefix: foo

    steps:
      - type: pull_images
        names:
        - docker.io/python:alpine
        - docker.io/nginx:alpine

      - type: forward_image
        name: docker.io/redis:alpine

      - type: build_images
        directories:
        - frontend
        - backend
    ```

### Steps

Each step may be one of

- [Action](#action)
- [BuildImage](#buildimage)
- [BuildImages](#buildimages)
- [ExtractFromImage](#extractfromimage)
- [ForwardImage](#forwardimage)
- [PullImage](#pullimage)
- [PullImages](#pullimages)

??? Example

    ```yaml
    steps:
      - type: build_image
        directory: frontend
    ```

#### Action

!!! TIP "Hint"

    Use this mechanism if other steps aren't sufficient for your usecase.

| Property | Type                     | Required | Description                                                                                |
| -------- | ------------------------ | -------- | ------------------------------------------------------------------------------------------ |
| type     | "action"                 | Yes      | Type of the step                                                                           |
| name     | string                   | Yes      | Name printed before running the action                                                     |
| commands | array of array of string | Yes      | List of commands. Each command is a list of strings: the executable followed by arguments. |
| post     | boolean                  | Yes      | Whether to add the action to the post queue                                                |

??? Example

    ```yaml
    steps:
      - type: action
        name: my custom action
        commands:
          - ["echo", "first", "step"]
          - ["/usr/bin/python3", "-c", "print('hello world')"]
        post: false
    ```

#### BuildImage

| Property   | Type            | Required | Description                                                                            |
| ---------- | --------------- | -------- | -------------------------------------------------------------------------------------- |
| type       | "build_image"   | Yes      | Type of the step                                                                       |
| directory  | string          | Yes      | Directory containing the Dockerfile. This is also used as the build context.           |
| dockerfile | string          | No       | Path to Dockerfile. Name of the resulting image. Defaults to `<directory>/Dockerfile`. |
| name       | string          | No       | Name of the resulting image. Defaults to the name of the Dockerfiles parent directory. |
| push       | boolean         | No       | Whether to push the image. Defaults to True.                                           |
| qualified  | boolean         | No       | Whether to add the registry path and prefix to the image name. Defaults to True.       |
| extra_tags | array of string | No       | Additional tags to use in this step. Defaults to None.                                 |

??? Example

    ```yaml
    steps:
      - type: build_image
        directory: frontend
    ```

#### BuildImages

| Property    | Type            | Required | Description                                                                      |
| ----------- | --------------- | -------- | -------------------------------------------------------------------------------- |
| type        | "build_images"  | Yes      | Type of the step                                                                 |
| directories | array of string | Yes      | Directories containing each containing Dockerfile.                               |
| push        | boolean         | No       | Whether to push the image. Defaults to True.                                     |
| qualified   | boolean         | No       | Whether to add the registry path and prefix to the image name. Defaults to True. |
| extra_tags  | array of string | No       | Additional tags to use in this step. Defaults to None.                           |

??? Example

    ```yaml
    steps:
      - type: build_images
        directories:
          - frontend
          - backend
    ```

#### ExtractFromImage

| Property | Type                 | Required | Description                                                                  |
| -------- | -------------------- | -------- | ---------------------------------------------------------------------------- |
| type     | "extract_from_image" | Yes      | Type of the step                                                             |
| image    | string               | Yes      | Name of the image to copy from.                                              |
| path     | string               | Yes      | Source path inside the image.                                                |
| dest     | array of string      | Yes      | Destination paths. The file will be copied to all destinations individually. |

??? Example

    ```yaml
    steps:
      - type: extract_from_image
        image: "registry.example.com:5000/some/image:latest"
        path: /etc/config.json
        dest:
          - frontend/
          - backend/docs/
    ```

#### ForwardImage

| Property   | Type            | Required | Description                                                                                        |
| ---------- | --------------- | -------- | -------------------------------------------------------------------------------------------------- |
| type       | "forward_image" | Yes      | Type of the step                                                                                   |
| name       | string          | Yes      | Image name to forward.                                                                             |
| new_name   | string          | No       | Set a new name for the image. By default the basename of the pulled image without the tag is used. |
| extra_tags | array of string | No       | Additional tags to use in this step. Defaults to None.                                             |

??? Example

    ```yaml
    steps:
      - type: forward_image
        name: "registry.example.com:5000/some/image:latest"
    ```

#### PullImage

| Property | Type         | Required | Description         |
| -------- | ------------ | -------- | ------------------- |
| type     | "pull_image" | Yes      | Type of the step    |
| name     | string       | Yes      | Image name to pull. |

??? Example

    ```yaml
    steps:
      - type: pull_image
        name: "registry.example.com:5000/some/image:latest"
    ```

#### PullImages

| Property | Type            | Required | Description          |
| -------- | --------------- | -------- | -------------------- |
| type     | "pull_images"   | Yes      | Type of the step     |
| names    | array of string | Yes      | Image names to pull. |

??? Example

    ```yaml
    steps:
      - type: pull_images
        names:
          - "registry.example.com:5000/some/image:latest"
          - "docker.io/nginx:alpine"
    ```

### Parameters

| Property | Type                 | Required | Description                                                                                                                                                 |
| -------- | -------------------- | -------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| registry | string               | No       | Set the registry url. You may include a port using the colon notation (example.com:3000/). This is needed when using a non standard port. Unset by default. |
| prefix   | string               | No       | Set the directory for all images. This is the image component between registry url and image name. For example on docker hub this is used for the username. |
| push     | boolean              | No       | Whether to allow pushing images.                                                                                                                            |
| cache    | boolean              | No       | Whether to allow using cached images. This is especially usefull for local builds.                                                                          |
| verbose  | boolean              | No       | Show issued commands and their live output.                                                                                                                 |
| tags     | array of string      | No       | One or multiple tags to use for each image. Defaults to ['latest']                                                                                          |
| simulate | boolean              | No       | Prevent issuing any commands just do the printing.                                                                                                          |
| backend  | "docker" or "podman" | No       | Overwrite the backend used to build, tag and pull images. Defaults to 'docker'                                                                              |

??? Example

    ```yaml
    parameters:
      registry: my-registry.example.com
      prefix: username
      push: false
      cache: true
      verbose: true
      tags:
        - custom
        - latest
      simulate: true
      backend: podman
    ```
