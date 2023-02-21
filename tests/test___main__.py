import pathlib
import re
import subprocess
import typing
from unittest.mock import call

import pytest
from pytest_mock import MockerFixture

import builderer.__main__


@pytest.mark.parametrize(
    ("input_args", "expected_config", "expected_args"),
    [
        (
            [],
            ".builderer.yml",
            {},
        ),
        (
            [
                "--registry",
                "reg.examle.com:6789",
                "--prefix",
                "user",
                "--tags",
                "foo",
                "bar",
                "baz",
                "--no-push",
                "--cache",
                "--verbose",
                "--simulate",
                "--backend",
                "podman",
                "--config",
                "test.yaml",
            ],
            "test.yaml",
            {
                "registry": "reg.examle.com:6789",
                "prefix": "user",
                "tags": ["foo", "bar", "baz"],
                "push": False,
                "cache": True,
                "verbose": True,
                "simulate": True,
                "backend": "podman",
            },
        ),
    ],
)
def test_parse_args(input_args: list[str], expected_config: str, expected_args: dict[str, typing.Any]) -> None:
    actual_config, actual_args = builderer.__main__.parse_args(input_args)
    assert actual_config == expected_config
    assert actual_args == expected_args


@pytest.mark.parametrize(
    ("flag", "pattern"),
    [
        ("--help", "^usage: builderer.*options"),
        ("-h", "^usage: builderer.*options"),
        ("--version", r"^builderer \d+\.\d+\.\d+$"),
    ],
)
def test_parse_args_special_action(flag: str, pattern: str, capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit, match="^0$"):
        builderer.__main__.parse_args([flag])

    captured = capsys.readouterr()

    assert captured.err == ""
    assert re.match(pattern, captured.out, re.DOTALL) is not None


@pytest.mark.parametrize("verbose", [True, False])
def test_main_simulate_example_workspace(
    datadir: pathlib.Path, capsys: pytest.CaptureFixture[str], verbose: bool
) -> None:
    run_config = datadir / "example_workspace" / ".builderer.yml"
    arguments = ["--config", str(run_config), "--simulate"] + (["--verbose"] if verbose else [])

    return_code = builderer.__main__.main(arguments)
    captured = capsys.readouterr()

    assert return_code == 0
    assert captured.err == ""

    if verbose:
        assert captured.out.split("\n") == [
            "Pulling image: docker.io/python:alpine",
            "['docker', 'pull', 'docker.io/python:alpine']",
            "Pulling image: docker.io/nginx:alpine",
            "['docker', 'pull', 'docker.io/nginx:alpine']",
            "Forwarding image: docker.io/redis:alpine -> redis",
            "['docker', 'pull', 'docker.io/redis:alpine']",
            "['docker', 'tag', 'docker.io/redis:alpine', 'registry.example.com/foo/redis:latest']",
            "Building image: frontend",
            "['docker', 'build', '-t', 'registry.example.com/foo/frontend:latest', '--no-cache', '-f', 'frontend/Dockerfile', 'frontend']",
            "Building image: backend",
            "['docker', 'build', '-t', 'registry.example.com/foo/backend:latest', '--no-cache', '-f', 'backend/Dockerfile', 'backend']",
            "Pushing image: backend",
            "['docker', 'push', 'registry.example.com/foo/backend:latest']",
            "Pushing image: frontend",
            "['docker', 'push', 'registry.example.com/foo/frontend:latest']",
            "Pushing image: redis",
            "['docker', 'push', 'registry.example.com/foo/redis:latest']",
            "",
        ]

    else:
        assert captured.out.split("\n") == [
            "Pulling image: docker.io/python:alpine",
            "Pulling image: docker.io/nginx:alpine",
            "Forwarding image: docker.io/redis:alpine -> redis",
            "Building image: frontend",
            "Building image: backend",
            "Pushing image: backend",
            "Pushing image: frontend",
            "Pushing image: redis",
            "",
        ]


def test_main_run_example_workspace(
    datadir: pathlib.Path, capsys: pytest.CaptureFixture[str], mocker: MockerFixture
) -> None:
    run_patch = mocker.patch("subprocess.run", return_value=subprocess.CompletedProcess([], 0))

    arguments = ["--config", str(datadir / "example_workspace" / ".builderer.yml"), "--verbose"]
    return_code = builderer.__main__.main(arguments)
    captured = capsys.readouterr()

    assert return_code == 0
    assert captured.err == ""

    assert captured.out.split("\n") == [
        "Pulling image: docker.io/python:alpine",
        "['docker', 'pull', 'docker.io/python:alpine']",
        "Pulling image: docker.io/nginx:alpine",
        "['docker', 'pull', 'docker.io/nginx:alpine']",
        "Forwarding image: docker.io/redis:alpine -> redis",
        "['docker', 'pull', 'docker.io/redis:alpine']",
        "['docker', 'tag', 'docker.io/redis:alpine', 'registry.example.com/foo/redis:latest']",
        "Building image: frontend",
        "['docker', 'build', '-t', 'registry.example.com/foo/frontend:latest', '--no-cache', '-f', 'frontend/Dockerfile', 'frontend']",
        "Building image: backend",
        "['docker', 'build', '-t', 'registry.example.com/foo/backend:latest', '--no-cache', '-f', 'backend/Dockerfile', 'backend']",
        "Pushing image: backend",
        "['docker', 'push', 'registry.example.com/foo/backend:latest']",
        "Pushing image: frontend",
        "['docker', 'push', 'registry.example.com/foo/frontend:latest']",
        "Pushing image: redis",
        "['docker', 'push', 'registry.example.com/foo/redis:latest']",
        "",
    ]

    expected_calls = [
        call(["docker", "pull", "docker.io/python:alpine"]),
        call(["docker", "pull", "docker.io/nginx:alpine"]),
        call(["docker", "pull", "docker.io/redis:alpine"]),
        call(["docker", "tag", "docker.io/redis:alpine", "registry.example.com/foo/redis:latest"]),
        call(
            [
                "docker",
                "build",
                "-t",
                "registry.example.com/foo/frontend:latest",
                "--no-cache",
                "-f",
                "frontend/Dockerfile",
                "frontend",
            ]
        ),
        call(
            [
                "docker",
                "build",
                "-t",
                "registry.example.com/foo/backend:latest",
                "--no-cache",
                "-f",
                "backend/Dockerfile",
                "backend",
            ]
        ),
        call(["docker", "push", "registry.example.com/foo/backend:latest"]),
        call(["docker", "push", "registry.example.com/foo/frontend:latest"]),
        call(["docker", "push", "registry.example.com/foo/redis:latest"]),
    ]

    assert run_patch.call_count == len(expected_calls)
    run_patch.assert_has_calls(expected_calls, any_order=False)


def test_main_run_unknown_workspace(tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]) -> None:
    arguments = ["--config", str(tmp_path / ".builderer.yml")]

    return_code = builderer.__main__.main(arguments)
    captured = capsys.readouterr()

    assert return_code == 1
    assert captured.err == ""
    assert "No such file or directory:" in captured.out
