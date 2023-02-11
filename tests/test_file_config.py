import pathlib

import builderer.config


def test_load_minimal(datadir: pathlib.Path) -> None:
    file_config = builderer.config.BuildererConfig.load(datadir / "minimal.yml")

    assert file_config.dict() == {
        "steps": [],
        "parameters": {
            "registry": None,
            "prefix": None,
            "push": None,
            "cache": None,
            "verbose": None,
            "tags": None,
            "simulate": None,
            "backend": None,
        },
    }


def test_load_example(datadir: pathlib.Path) -> None:
    file_config = builderer.config.BuildererConfig.load(datadir / "example.yml")

    assert file_config.dict() == {
        "parameters": {
            "registry": "registry.example.com:12345",
            "prefix": "username",
            "push": False,
            "cache": False,
            "verbose": False,
            "tags": ["a", "b"],
            "simulate": True,
            "backend": "podman",
        },
        "steps": [],
    }


def test_load_example_workspace(datadir: pathlib.Path) -> None:
    file_config = builderer.config.BuildererConfig.load(datadir / "example_workspace" / ".builderer.yml")

    assert file_config.dict() == {
        "parameters": {
            "registry": "registry.example.com",
            "prefix": "foo",
            "push": None,
            "cache": None,
            "verbose": None,
            "tags": None,
            "simulate": None,
            "backend": None,
        },
        "steps": [
            {"type": "pull_images", "names": ["docker.io/python:alpine", "docker.io/nginx:alpine"]},
            {"type": "forward_image", "name": "docker.io/redis:alpine", "new_name": None},
            {"type": "build_images", "directories": ["frontend", "backend"], "push": True, "qualified": True},
        ],
    }
