import pytest
from pytest_mock import MockerFixture

from builderer.actions import ActionFactory


@pytest.fixture
def factory() -> ActionFactory:
    return ActionFactory()


def test_empty_factory(factory: ActionFactory) -> None:
    assert factory.backend == "docker"
    assert factory.cache is False
    assert factory.prefix is None
    assert factory.push is True
    assert factory.registry is None
    assert factory.tags == ["latest"]


@pytest.mark.parametrize("name", ["some_name", "nothing", "foo"])
@pytest.mark.parametrize("registry", ["localhost:3000/", "registry.example.com/", None])
@pytest.mark.parametrize("push", [True, False])
def test_build_image(factory: ActionFactory, name: str, registry: str | None, push: bool) -> None:
    factory.registry = registry
    main_action, post_action = factory.build_image(name, push=push)

    prefix = registry or ""

    assert main_action.name == f"Building image: {name}"
    assert main_action.commands == [
        ["docker", "build", "-t", f"{prefix}{name}:latest", "--no-cache", "-f", f"{name}/Dockerfile", f"{name}"]
    ]

    if push is False:
        assert post_action is None
    else:
        assert post_action is not None
        assert post_action.name == f"Pushing image: {name}"
        assert post_action.commands == [["docker", "push", f"{prefix}{name}:latest"]]


@pytest.mark.parametrize("push", [True, False])
def test_build_image_complex(factory: ActionFactory, push: bool) -> None:
    factory.push = push
    factory.tags = ["tag1", "3.14", "v3-alpine"]
    factory.registry = "some-reg.server.org:9001"
    factory.prefix = "my-prefix"

    main_action, post_action = factory.build_image(
        "myfrontend",
        dockerfile="path/to/docker-file",
        name="alternative-name",
        push=push,
        qualified=True,
        extra_tags=["extra-1", "more"],
    )

    assert main_action.name == "Building image: alternative-name"
    assert main_action.commands == [
        [
            "docker",
            "build",
            "-t",
            "some-reg.server.org:9001/my-prefix/alternative-name:tag1",
            "-t",
            "some-reg.server.org:9001/my-prefix/alternative-name:3.14",
            "-t",
            "some-reg.server.org:9001/my-prefix/alternative-name:v3-alpine",
            "-t",
            "some-reg.server.org:9001/my-prefix/alternative-name:extra-1",
            "-t",
            "some-reg.server.org:9001/my-prefix/alternative-name:more",
            "--no-cache",
            "-f",
            "path/to/docker-file",
            "myfrontend",
        ]
    ]

    if push is False:
        assert post_action is None
    else:
        assert post_action is not None
        assert post_action.name == "Pushing image: alternative-name"
        assert post_action.commands == [
            ["docker", "push", "some-reg.server.org:9001/my-prefix/alternative-name:tag1"],
            ["docker", "push", "some-reg.server.org:9001/my-prefix/alternative-name:3.14"],
            ["docker", "push", "some-reg.server.org:9001/my-prefix/alternative-name:v3-alpine"],
            ["docker", "push", "some-reg.server.org:9001/my-prefix/alternative-name:extra-1"],
            ["docker", "push", "some-reg.server.org:9001/my-prefix/alternative-name:more"],
        ]


def test_extract_from_image(factory: ActionFactory, mocker: MockerFixture) -> None:
    mocker.patch("uuid.uuid4", return_value="50f17813-ac32-4e69-9029-ea3f8e656125")

    action = factory.extract_from_image("localhost:3000/reg/some-image:42", "/build/result", "./a/", "b", "/opt/data")

    assert action.name == "Extracting from image: /build/result -> ./a/, b, /opt/data"
    assert action.commands == [
        [
            "docker",
            "container",
            "create",
            "--name",
            "50f17813-ac32-4e69-9029-ea3f8e656125",
            "localhost:3000/reg/some-image:42",
        ],
        ["docker", "container", "cp", "50f17813-ac32-4e69-9029-ea3f8e656125:/build/result", "./a/"],
        ["docker", "container", "cp", "50f17813-ac32-4e69-9029-ea3f8e656125:/build/result", "b"],
        ["docker", "container", "cp", "50f17813-ac32-4e69-9029-ea3f8e656125:/build/result", "/opt/data"],
        ["docker", "container", "rm", "-f", "50f17813-ac32-4e69-9029-ea3f8e656125"],
    ]


@pytest.mark.parametrize("push", [True, False])
def test_forward_image_simple(factory: ActionFactory, push: bool) -> None:
    factory.push = push
    main_action, post_action = factory.forward_image("registry.example.com:1234/foo/some-image:v123-test")

    assert main_action.name == "Forwarding image: registry.example.com:1234/foo/some-image:v123-test -> some-image"
    assert main_action.commands == [
        ["docker", "pull", "registry.example.com:1234/foo/some-image:v123-test"],
        ["docker", "tag", "registry.example.com:1234/foo/some-image:v123-test", "some-image:latest"],
    ]

    if push is False:
        assert post_action is None
    else:
        assert post_action is not None
        assert post_action.name == "Pushing image: some-image"
        assert post_action.commands == [["docker", "push", "some-image:latest"]]


@pytest.mark.parametrize("push", [True, False])
def test_forward_image_complex(factory: ActionFactory, push: bool) -> None:
    factory.push = push
    factory.tags = ["tag1", "3.14", "v3-alpine"]
    factory.registry = "some-reg.server.org:9001"
    factory.prefix = "my-prefix"

    main_action, post_action = factory.forward_image(
        "registry.example.com:3333/bar/remote-image:42",
        new_name="new-image-name",
        extra_tags=["extra-1", "more"],
    )

    assert main_action.name == "Forwarding image: registry.example.com:3333/bar/remote-image:42 -> new-image-name"
    assert main_action.commands == [
        ["docker", "pull", "registry.example.com:3333/bar/remote-image:42"],
        [
            "docker",
            "tag",
            "registry.example.com:3333/bar/remote-image:42",
            "some-reg.server.org:9001/my-prefix/new-image-name:tag1",
        ],
        [
            "docker",
            "tag",
            "registry.example.com:3333/bar/remote-image:42",
            "some-reg.server.org:9001/my-prefix/new-image-name:3.14",
        ],
        [
            "docker",
            "tag",
            "registry.example.com:3333/bar/remote-image:42",
            "some-reg.server.org:9001/my-prefix/new-image-name:v3-alpine",
        ],
        [
            "docker",
            "tag",
            "registry.example.com:3333/bar/remote-image:42",
            "some-reg.server.org:9001/my-prefix/new-image-name:extra-1",
        ],
        [
            "docker",
            "tag",
            "registry.example.com:3333/bar/remote-image:42",
            "some-reg.server.org:9001/my-prefix/new-image-name:more",
        ],
    ]

    if push is False:
        assert post_action is None
    else:
        assert post_action is not None
        assert post_action.name == "Pushing image: new-image-name"
        assert post_action.commands == [
            ["docker", "push", "some-reg.server.org:9001/my-prefix/new-image-name:tag1"],
            ["docker", "push", "some-reg.server.org:9001/my-prefix/new-image-name:3.14"],
            ["docker", "push", "some-reg.server.org:9001/my-prefix/new-image-name:v3-alpine"],
            ["docker", "push", "some-reg.server.org:9001/my-prefix/new-image-name:extra-1"],
            ["docker", "push", "some-reg.server.org:9001/my-prefix/new-image-name:more"],
        ]


@pytest.mark.parametrize("name", ["some_name", "localhost:3000/image", "ghcr.io/foo/bar"])
def test_pull_image(factory: ActionFactory, name: str) -> None:
    action = factory.pull_image(name)

    assert action.name == f"Pulling image: {name}"
    assert action.commands == [
        ["docker", "pull", name],
    ]
