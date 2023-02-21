import typing
from functools import partial

import pydantic
import pytest

import builderer.config


class AnyCaller:
    def __init__(self) -> None:
        self.calls: list[tuple[typing.Any, ...]] = []

    def _add_call(self, func_name: str, *args: typing.Any, **kwargs: typing.Any) -> None:
        self.calls.append((func_name, args, kwargs))

    def __getattr__(self, attr: str) -> typing.Any:
        if attr not in self.__dict__:
            return partial(self._add_call, attr)
        return super().__getattr__(attr)  # type: ignore


@pytest.fixture
def dummy_builderer() -> AnyCaller:
    return AnyCaller()


def test_action(dummy_builderer: AnyCaller) -> None:
    tester = builderer.config.Action(
        type="action",
        name="example",
        commands=[["command"], ["second", "--command", "foo"]],
        post=True,
    )
    tester.add_to(dummy_builderer)  # type: ignore

    assert dummy_builderer.calls == [
        (
            "action",
            tuple(),
            {"name": "example", "commands": [["command"], ["second", "--command", "foo"]], "post": True},
        )
    ]


def test_build_image(dummy_builderer: AnyCaller) -> None:
    tester = builderer.config.BuildImage(
        type="build_image",
        directory="some folder",
        dockerfile="some/docker/file",
        name="custom-name",
        push=False,
        qualified=False,
    )
    tester.add_to(dummy_builderer)  # type: ignore

    assert dummy_builderer.calls == [
        (
            "build_image",
            tuple(),
            {
                "directory": "some folder",
                "dockerfile": "some/docker/file",
                "name": "custom-name",
                "push": False,
                "qualified": False,
            },
        )
    ]


def test_build_images(dummy_builderer: AnyCaller) -> None:
    tester = builderer.config.BuildImages(
        type="build_images",
        directories=["folder1", "folder2"],
        push=False,
        qualified=False,
    )
    tester.add_to(dummy_builderer)  # type: ignore

    assert dummy_builderer.calls == [
        (
            "build_image",
            tuple(),
            {
                "directory": "folder1",
                "push": False,
                "qualified": False,
            },
        ),
        (
            "build_image",
            tuple(),
            {
                "directory": "folder2",
                "push": False,
                "qualified": False,
            },
        ),
    ]


def test_extract_from_image(dummy_builderer: AnyCaller) -> None:
    tester = builderer.config.ExtractFromImage(
        type="extract_from_image",
        image="some-image",
        path="/path/to/file",
        dest=["a", "b/c", "something"],
    )
    tester.add_to(dummy_builderer)  # type: ignore

    assert dummy_builderer.calls == [
        (
            "extract_from_image",
            ("some-image", "/path/to/file", "a", "b/c", "something"),
            {},
        )
    ]


def test_forward_image(dummy_builderer: AnyCaller) -> None:
    tester = builderer.config.ForwardImage(
        type="forward_image",
        name="image-name",
        new_name="something-else",
    )
    tester.add_to(dummy_builderer)  # type: ignore

    assert dummy_builderer.calls == [
        (
            "forward_image",
            tuple(),
            {
                "name": "image-name",
                "new_name": "something-else",
            },
        )
    ]


def test_pull_image(dummy_builderer: AnyCaller) -> None:
    tester = builderer.config.PullImage(type="pull_image", name="some-image-name")
    tester.add_to(dummy_builderer)  # type: ignore

    assert dummy_builderer.calls == [("pull_image", tuple(), {"name": "some-image-name"})]


def test_pull_images(dummy_builderer: AnyCaller) -> None:
    tester = builderer.config.PullImages(type="pull_images", names=["some-image-name", "second"])
    tester.add_to(dummy_builderer)  # type: ignore

    assert dummy_builderer.calls == [
        ("pull_image", tuple(), {"name": "some-image-name"}),
        ("pull_image", tuple(), {"name": "second"}),
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
def test_builderer_config_errors(data: typing.Any, error: typing.Type[Exception], error_texts: list[str]) -> None:
    with pytest.raises(error) as e:
        builderer.config.BuildererConfig.parse_obj(data)

    for text in error_texts:
        assert text in str(e)
