import pathlib
import sys

import pytest
from pytest_mock import MockerFixture

from builderer.builderer import Builderer


@pytest.fixture
def empty_builderer() -> Builderer:
    return Builderer()


def test_empty_builderer(empty_builderer: Builderer) -> None:
    assert empty_builderer.tags == ["latest"]
    assert empty_builderer.registry is None
    assert empty_builderer.prefix is None
    assert empty_builderer.cache is False
    assert empty_builderer.backend == "docker"
    assert empty_builderer.simulate is False
    assert empty_builderer.verbose is False
    assert empty_builderer.push is True
    assert len(empty_builderer._actions) == 0
    assert len(empty_builderer._post) == 0


@pytest.fixture
def sim_builderer(empty_builderer: Builderer) -> Builderer:
    empty_builderer.simulate = True
    empty_builderer.verbose = True
    return empty_builderer


@pytest.mark.parametrize("name", ["some_name", "nothing", "foo"])
@pytest.mark.parametrize("registry", ["localhost:3000/", "registry.example.com/", None])
@pytest.mark.parametrize("push", [True, False])
def test_build_image(
    sim_builderer: Builderer, capsys: pytest.CaptureFixture[str], name: str, registry: str | None, push: bool
) -> None:
    sim_builderer.registry = registry
    sim_builderer.build_image(name, push=push)
    ret = sim_builderer.run()
    captured = capsys.readouterr()

    prefix = registry or ""

    push_output = [f"Pushing image: {name}", f"['docker', 'push', '{prefix}{name}:latest']"] if push else []

    assert ret == 0
    assert captured.err == ""
    assert captured.out.split("\n") == [
        f"Building image: {name}",
        f"['docker', 'build', '-t', '{prefix}{name}:latest', '--no-cache', '-f', '{name}/Dockerfile', '{name}']",
        *push_output,
        "",
    ]


def test_extract_from_image(
    sim_builderer: Builderer, capsys: pytest.CaptureFixture[str], mocker: MockerFixture
) -> None:
    mocker.patch("uuid.uuid4", return_value="50f17813-ac32-4e69-9029-ea3f8e656125")

    sim_builderer.extract_from_image("localhost:3000/reg/some-image:42", "/build/result", "./a/", "b", "/opt/data")
    ret = sim_builderer.run()
    captured = capsys.readouterr()

    assert ret == 0
    assert captured.err == ""
    assert captured.out.split("\n") == [
        "Extracting from image: /build/result -> ./a/, b, /opt/data",
        "['docker', 'container', 'create', '--name', '50f17813-ac32-4e69-9029-ea3f8e656125', 'localhost:3000/reg/some-image:42']",
        "['docker', 'container', 'cp', '50f17813-ac32-4e69-9029-ea3f8e656125:/build/result', './a/']",
        "['docker', 'container', 'cp', '50f17813-ac32-4e69-9029-ea3f8e656125:/build/result', 'b']",
        "['docker', 'container', 'cp', '50f17813-ac32-4e69-9029-ea3f8e656125:/build/result', '/opt/data']",
        "['docker', 'container', 'rm', '-f', '50f17813-ac32-4e69-9029-ea3f8e656125']",
        "",
    ]


@pytest.mark.parametrize("push", [True, False])
def test_forward_image_simple(sim_builderer: Builderer, capsys: pytest.CaptureFixture[str], push: bool) -> None:
    sim_builderer.push = push
    sim_builderer.forward_image("registry.example.com:1234/foo/some-image:v123-test")
    ret = sim_builderer.run()
    captured = capsys.readouterr()

    push_output = (
        [
            "Pushing image: some-image",
            "['docker', 'push', 'some-image:latest']",
        ]
        if push
        else []
    )

    assert ret == 0
    assert captured.err == ""
    assert captured.out.split("\n") == [
        "Forwarding image: registry.example.com:1234/foo/some-image:v123-test -> some-image",
        "['docker', 'pull', 'registry.example.com:1234/foo/some-image:v123-test']",
        "['docker', 'tag', 'registry.example.com:1234/foo/some-image:v123-test', 'some-image:latest']",
        *push_output,
        "",
    ]


@pytest.mark.parametrize("push", [True, False])
def test_forward_image_complex(sim_builderer: Builderer, capsys: pytest.CaptureFixture[str], push: bool) -> None:
    sim_builderer.push = push
    sim_builderer.tags = ["tag1", "3.14", "v3-alpine"]
    sim_builderer.registry = "some-reg.server.org:9001"
    sim_builderer.prefix = "my-prefix"
    sim_builderer.forward_image("registry.example.com:3333/bar/remote-image:42", new_name="new-image-name")
    ret = sim_builderer.run()
    captured = capsys.readouterr()

    push_output = (
        [
            "Pushing image: new-image-name",
            "['docker', 'push', 'some-reg.server.org:9001/my-prefix/new-image-name:tag1']",
            "['docker', 'push', 'some-reg.server.org:9001/my-prefix/new-image-name:3.14']",
            "['docker', 'push', 'some-reg.server.org:9001/my-prefix/new-image-name:v3-alpine']",
        ]
        if push
        else []
    )
    assert ret == 0
    assert captured.err == ""
    assert captured.out.split("\n") == [
        "Forwarding image: registry.example.com:3333/bar/remote-image:42 -> new-image-name",
        "['docker', 'pull', 'registry.example.com:3333/bar/remote-image:42']",
        "['docker', 'tag', 'registry.example.com:3333/bar/remote-image:42', 'some-reg.server.org:9001/my-prefix/new-image-name:tag1']",
        "['docker', 'tag', 'registry.example.com:3333/bar/remote-image:42', 'some-reg.server.org:9001/my-prefix/new-image-name:3.14']",
        "['docker', 'tag', 'registry.example.com:3333/bar/remote-image:42', 'some-reg.server.org:9001/my-prefix/new-image-name:v3-alpine']",
        *push_output,
        "",
    ]


@pytest.mark.parametrize("name", ["some_name", "localhost:3000/image", "ghcr.io/foo/bar"])
def test_pull_image(sim_builderer: Builderer, capsys: pytest.CaptureFixture[str], name: str) -> None:
    sim_builderer.pull_image(name)
    ret = sim_builderer.run()
    captured = capsys.readouterr()

    assert ret == 0
    assert captured.err == ""
    assert captured.out.split("\n") == [
        f"Pulling image: {name}",
        f"['docker', 'pull', '{name}']",
        "",
    ]


def test_run_error(empty_builderer: Builderer, capsys: pytest.CaptureFixture[str], tmp_path: pathlib.Path) -> None:
    empty_builderer.action(
        "Failing action", [[sys.executable, "-c", "print('example output'); raise SystemExit(42)"]], post=False
    )
    ret = empty_builderer.run()
    captured = capsys.readouterr()

    assert ret == 42
    assert captured.err == ""
    assert captured.out.split("\n") == [
        "Failing action",
        "Encountered error running:",
        "example output",
        "",
        "",
    ]
