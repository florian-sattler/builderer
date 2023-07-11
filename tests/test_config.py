import typing
from functools import partial

import pydantic
import pytest
from pytest_mock import MockerFixture

import builderer
import builderer.config


class CallObserver:
    def __init__(self, observed: typing.Any) -> None:
        self.calls: list[tuple[typing.Any, ...]] = []
        self.observed = observed

    def _add_call(self, func_name: str, *args: typing.Any, **kwargs: typing.Any) -> None:
        self.calls.append((func_name, args, kwargs))
        return getattr(self.observed, func_name)(*args, **kwargs)

    def __getattr__(self, attr: str) -> typing.Any:
        if attr not in self.__dict__:
            return partial(self._add_call, attr)
        return super().__getattr__(attr)  # type: ignore


@pytest.fixture
def observed_factory() -> CallObserver:
    return CallObserver(builderer.ActionFactory())


@pytest.mark.parametrize("post", [True, False])
def test_action(observed_factory: CallObserver, post: bool) -> None:
    tester = builderer.config.Action(
        type="action",
        name="example",
        commands=[["command"], ["second", "--command", "foo"]],
        post=post,
    )
    result = tester.create(observed_factory)  # type: ignore

    action, empty = result[::-1] if post else result

    assert empty is None
    assert action == builderer.Action("example", [["command"], ["second", "--command", "foo"]])

    assert observed_factory.calls == [
        (
            "action",
            (),
            {"name": "example", "commands": [["command"], ["second", "--command", "foo"]]},
        )
    ]


@pytest.mark.parametrize("push", [True, False])
def test_build_image(observed_factory: CallObserver, push: bool) -> None:
    tester = builderer.config.BuildImage(
        type="build_image",
        directory="some folder",
        dockerfile="some/docker/file",
        name="custom-name",
        push=push,
        qualified=False,
        extra_tags=["additional_tag1", "extract-2"],
    )
    main, post = tester.create(observed_factory)  # type: ignore

    assert main == builderer.Action(
        "Building image: custom-name",
        [
            [
                "docker",
                "build",
                "-t",
                "custom-name:latest",
                "-t",
                "custom-name:additional_tag1",
                "-t",
                "custom-name:extract-2",
                "--no-cache",
                "-f",
                "some/docker/file",
                "some folder",
            ]
        ],
    )

    if not push:
        assert post is None
    else:
        assert post == builderer.Action(
            "Pushing image: custom-name",
            [
                ["docker", "push", "custom-name:latest"],
                ["docker", "push", "custom-name:additional_tag1"],
                ["docker", "push", "custom-name:extract-2"],
            ],
        )

    assert observed_factory.calls == [
        (
            "build_image",
            (),
            {
                "directory": "some folder",
                "dockerfile": "some/docker/file",
                "name": "custom-name",
                "push": push,
                "qualified": False,
                "extra_tags": ["additional_tag1", "extract-2"],
            },
        )
    ]


@pytest.mark.parametrize("push", [True, False])
def test_build_images(observed_factory: CallObserver, push: bool) -> None:
    tester = builderer.config.BuildImages(
        type="build_images",
        directories=["folder1", "folder2"],
        push=push,
        qualified=False,
        extra_tags=["additional_tag1", "extract-2"],
    )
    # TODO check all results in here
    # TODO prevent illegal parallel inputs
    main, post = tester.create(observed_factory)  # type: ignore

    assert main == builderer.ActionGroup(
        [
            builderer.Action(
                "Building image: folder1",
                [
                    [
                        "docker",
                        "build",
                        "-t",
                        "folder1:latest",
                        "-t",
                        "folder1:additional_tag1",
                        "-t",
                        "folder1:extract-2",
                        "--no-cache",
                        "-f",
                        "folder1/Dockerfile",
                        "folder1",
                    ]
                ],
            ),
            builderer.Action(
                "Building image: folder2",
                [
                    [
                        "docker",
                        "build",
                        "-t",
                        "folder2:latest",
                        "-t",
                        "folder2:additional_tag1",
                        "-t",
                        "folder2:extract-2",
                        "--no-cache",
                        "-f",
                        "folder2/Dockerfile",
                        "folder2",
                    ]
                ],
            ),
        ],
        num_parallel=1,
    )

    if not push:
        assert post is None
    else:
        assert post == builderer.ActionGroup(
            [
                builderer.Action(
                    "Pushing image: folder2",
                    [
                        ["docker", "push", "folder2:latest"],
                        ["docker", "push", "folder2:additional_tag1"],
                        ["docker", "push", "folder2:extract-2"],
                    ],
                ),
                builderer.Action(
                    "Pushing image: folder1",
                    [
                        ["docker", "push", "folder1:latest"],
                        ["docker", "push", "folder1:additional_tag1"],
                        ["docker", "push", "folder1:extract-2"],
                    ],
                ),
            ],
            num_parallel=1,
        )

    assert observed_factory.calls == [
        (
            "build_image",
            (),
            {
                "directory": "folder1",
                "push": push,
                "qualified": False,
                "extra_tags": ["additional_tag1", "extract-2"],
            },
        ),
        (
            "build_image",
            (),
            {
                "directory": "folder2",
                "push": push,
                "qualified": False,
                "extra_tags": ["additional_tag1", "extract-2"],
            },
        ),
    ]


def test_extract_from_image(observed_factory: CallObserver, mocker: MockerFixture) -> None:
    mocker.patch("uuid.uuid4", return_value="12345678-ac32-4e69-9029-ea3f8e656125")

    tester = builderer.config.ExtractFromImage(
        type="extract_from_image",
        image="some-image",
        path="/path/to/file",
        dest=["a", "b/c", "something"],
    )
    action, empty = tester.create(observed_factory)  # type: ignore

    assert empty is None

    assert action == builderer.Action(
        name="Extracting from image: /path/to/file -> a, b/c, something",
        commands=[
            [
                "docker",
                "container",
                "create",
                "--name",
                "12345678-ac32-4e69-9029-ea3f8e656125",
                "some-image",
            ],
            ["docker", "container", "cp", "12345678-ac32-4e69-9029-ea3f8e656125:/path/to/file", "a"],
            ["docker", "container", "cp", "12345678-ac32-4e69-9029-ea3f8e656125:/path/to/file", "b/c"],
            ["docker", "container", "cp", "12345678-ac32-4e69-9029-ea3f8e656125:/path/to/file", "something"],
            ["docker", "container", "rm", "-f", "12345678-ac32-4e69-9029-ea3f8e656125"],
        ],
    )

    assert observed_factory.calls == [
        (
            "extract_from_image",
            ("some-image", "/path/to/file", "a", "b/c", "something"),
            {},
        )
    ]


@pytest.mark.parametrize("push", [True, False])
def test_forward_image(observed_factory: CallObserver, push: bool) -> None:
    observed_factory.observed.push = push
    tester = builderer.config.ForwardImage(
        type="forward_image",
        name="image-name:3.14-alpine3.18",
        new_name="something-else",
        extra_tags=["additional_tag1", "extract-2"],
    )

    main, post = tester.create(observed_factory)  # type: ignore

    assert main == builderer.Action(
        "Forwarding image: image-name:3.14-alpine3.18 -> something-else",
        [
            ["docker", "pull", "image-name:3.14-alpine3.18"],
            ["docker", "tag", "image-name:3.14-alpine3.18", "something-else:latest"],
            ["docker", "tag", "image-name:3.14-alpine3.18", "something-else:additional_tag1"],
            ["docker", "tag", "image-name:3.14-alpine3.18", "something-else:extract-2"],
        ],
    )

    if not push:
        assert post is None
    else:
        assert post == builderer.Action(
            "Pushing image: something-else",
            [
                ["docker", "push", "something-else:latest"],
                ["docker", "push", "something-else:additional_tag1"],
                ["docker", "push", "something-else:extract-2"],
            ],
        )

    assert observed_factory.calls == [
        (
            "forward_image",
            (),
            {
                "name": "image-name:3.14-alpine3.18",
                "new_name": "something-else",
                "extra_tags": ["additional_tag1", "extract-2"],
            },
        )
    ]


@pytest.mark.parametrize("push", [True, False])
def test_forward_images(observed_factory: CallObserver, push: bool) -> None:
    observed_factory.observed.push = push
    tester = builderer.config.ForwardImages(
        type="forward_images", names=["image-name", "image-name-2"], extra_tags=["additional_tag1", "extract-2"]
    )
    main, post = tester.create(observed_factory)  # type: ignore

    assert main == builderer.ActionGroup(
        [
            builderer.Action(
                "Forwarding image: image-name -> image-name",
                [
                    ["docker", "pull", "image-name"],
                    ["docker", "tag", "image-name", "image-name:latest"],
                    ["docker", "tag", "image-name", "image-name:additional_tag1"],
                    ["docker", "tag", "image-name", "image-name:extract-2"],
                ],
            ),
            builderer.Action(
                "Forwarding image: image-name-2 -> image-name-2",
                [
                    ["docker", "pull", "image-name-2"],
                    ["docker", "tag", "image-name-2", "image-name-2:latest"],
                    ["docker", "tag", "image-name-2", "image-name-2:additional_tag1"],
                    ["docker", "tag", "image-name-2", "image-name-2:extract-2"],
                ],
            ),
        ],
        num_parallel=4,
    )
    if push is False:
        assert post is None
    else:
        assert post == builderer.ActionGroup(
            [
                builderer.Action(
                    "Pushing image: image-name-2",
                    [
                        ["docker", "push", "image-name-2:latest"],
                        ["docker", "push", "image-name-2:additional_tag1"],
                        ["docker", "push", "image-name-2:extract-2"],
                    ],
                ),
                builderer.Action(
                    "Pushing image: image-name",
                    [
                        ["docker", "push", "image-name:latest"],
                        ["docker", "push", "image-name:additional_tag1"],
                        ["docker", "push", "image-name:extract-2"],
                    ],
                ),
            ],
            num_parallel=4,
        )

    assert observed_factory.calls == [
        (
            "forward_image",
            (),
            {
                "name": "image-name",
                "new_name": None,
                "extra_tags": ["additional_tag1", "extract-2"],
            },
        ),
        (
            "forward_image",
            (),
            {
                "name": "image-name-2",
                "new_name": None,
                "extra_tags": ["additional_tag1", "extract-2"],
            },
        ),
    ]


def test_pull_image(observed_factory: CallObserver) -> None:
    tester = builderer.config.PullImage(type="pull_image", name="some-image-name")
    main, empty = tester.create(observed_factory)  # type: ignore

    assert main == builderer.Action(
        "Pulling image: some-image-name",
        [["docker", "pull", "some-image-name"]],
    )
    assert empty is None

    assert observed_factory.calls == [("pull_image", (), {"name": "some-image-name"})]


def test_pull_images(observed_factory: CallObserver) -> None:
    tester = builderer.config.PullImages(type="pull_images", names=["some-image-name", "second"])
    main, empty = tester.create(observed_factory)  # type: ignore

    assert main == builderer.ActionGroup(
        [
            builderer.Action(
                "Pulling image: some-image-name",
                [["docker", "pull", "some-image-name"]],
            ),
            builderer.Action(
                "Pulling image: second",
                [["docker", "pull", "second"]],
            ),
        ],
        num_parallel=4,
    )
    assert empty is None

    assert observed_factory.calls == [
        ("pull_image", (), {"name": "some-image-name"}),
        ("pull_image", (), {"name": "second"}),
    ]


def test_group_empty(observed_factory: CallObserver) -> None:
    tester = builderer.config.Group(type="group", num_parallel=1, steps=[])
    main, post = tester.create(observed_factory)  # type: ignore

    assert main is None
    assert post is None

    assert observed_factory.calls == []


def test_group(observed_factory: CallObserver) -> None:
    tester = builderer.config.Group(
        type="group",
        num_parallel=1,
        steps=[
            builderer.config.PullImage(type="pull_image", name="some-image-name"),
            builderer.config.BuildImage(
                type="build_image",
                directory="some folder",
                dockerfile="some/docker/file",
                name="custom-name",
                push=True,
                qualified=False,
                extra_tags=["additional_tag1", "extract-2"],
            ),
        ],
    )
    main, post = tester.create(observed_factory)  # type: ignore

    assert main == builderer.ActionGroup(
        [
            builderer.Action(
                "Pulling image: some-image-name",
                [["docker", "pull", "some-image-name"]],
            ),
            builderer.Action(
                "Building image: custom-name",
                [
                    [
                        "docker",
                        "build",
                        "-t",
                        "custom-name:latest",
                        "-t",
                        "custom-name:additional_tag1",
                        "-t",
                        "custom-name:extract-2",
                        "--no-cache",
                        "-f",
                        "some/docker/file",
                        "some folder",
                    ]
                ],
            ),
        ],
        num_parallel=1,
    )

    assert post == builderer.ActionGroup(
        [
            builderer.Action(
                "Pushing image: custom-name",
                [
                    ["docker", "push", "custom-name:latest"],
                    ["docker", "push", "custom-name:additional_tag1"],
                    ["docker", "push", "custom-name:extract-2"],
                ],
            )
        ],
        num_parallel=1,
    )

    assert observed_factory.calls == [
        (
            "pull_image",
            (),
            {"name": "some-image-name"},
        ),
        (
            "build_image",
            (),
            {
                "directory": "some folder",
                "dockerfile": "some/docker/file",
                "name": "custom-name",
                "push": True,
                "qualified": False,
                "extra_tags": ["additional_tag1", "extract-2"],
            },
        ),
    ]


@pytest.mark.parametrize(
    ("data", "error", "error_texts"),
    [
        ({}, pydantic.ValidationError, ["value_error.missing", "'loc': ('steps'"]),
        ({"steps": [{}]}, ValueError, ["'value_error'", "malformed step: 'type' is required!"]),
        ({"steps": [1]}, pydantic.ValidationError, ["'type_error.dict'", "value is not a valid dict"]),
        ({"steps": [{"type": "unknown"}]}, ValueError, ["'value_error'", "Unknown step type unknown"]),
    ],
)
def test_builderer_config_errors(data: typing.Any, error: type[Exception], error_texts: list[str]) -> None:
    with pytest.raises(error) as e:
        builderer.config.BuildererConfig.parse_obj(data)

    for text in error_texts:
        assert text in str(e)
