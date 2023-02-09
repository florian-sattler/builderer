import pathlib

import pytest

import builderer.__main__


@pytest.mark.parametrize("verbose", [True, False])
def test_main_simulate_example_workspace(datadir: pathlib.Path, capsys: pytest.CaptureFixture, verbose: bool):
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
