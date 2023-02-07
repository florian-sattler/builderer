import pathlib
import typing

import pydantic
import yaml

from builderer import builderer, models


class _Step(pydantic.BaseModel):
    class Config:
        extra = "forbid"


class Action(_Step):
    type: typing.Literal["action"]
    name: str
    commands: list[list[str]]
    post: bool

    def add_to(self, builderer: builderer.Builderer) -> None:
        builderer.action(self.name, self.commands, self.post)


class BuildImage(_Step):
    type: typing.Literal["build_image"]
    directory: str
    name: str | None = None
    push: bool = True
    qualified: bool = True

    def add_to(self, builderer: builderer.Builderer) -> None:
        builderer.build_image(self.directory, name=self.name, push=self.push, qualified=self.qualified)


class BuildImages(_Step):
    type: typing.Literal["build_images"]
    directories: list[str]
    push: bool = True
    qualified: bool = True

    def add_to(self, builderer: builderer.Builderer) -> None:
        for directory in self.directories:
            builderer.build_image(directory, push=self.push, qualified=self.qualified)


class ExtractFromImage(_Step):
    type: typing.Literal["extract_from_image"]
    image: str
    path: str
    dest: list[str]

    def add_to(self, builderer: builderer.Builderer) -> None:
        builderer.extract_from_image(self.image, self.path, *self.dest)


class ForwardImage(_Step):
    type: typing.Literal["forward_image"]
    name: str
    new_name: str | None = None

    def add_to(self, builderer: builderer.Builderer) -> None:
        builderer.forward_image(self.name, new_name=self.new_name)


class PullImage(_Step):
    type: typing.Literal["pull_image"]
    name: str

    def add_to(self, builderer: builderer.Builderer) -> None:
        builderer.pull_image(self.name)


class PullImages(_Step):
    type: typing.Literal["pull_images"]
    names: list[str]

    def add_to(self, builderer: builderer.Builderer) -> None:
        for name in self.names:
            builderer.pull_image(name)


class BuildConfig(_Step):
    name: str
    steps: list[Action | BuildImage | BuildImages | ExtractFromImage | ForwardImage | PullImage | PullImages]

    parameters: models.Parameters = pydantic.Field(default_factory=models.Parameters)  # pyright: ignore

    @staticmethod
    def load(path: str | pathlib.Path) -> "BuildConfig":
        with open(path, "rt") as f:
            return BuildConfig.parse_obj(yaml.safe_load(f))
