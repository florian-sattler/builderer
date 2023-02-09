import pathlib
import typing

import pydantic
import yaml

from builderer import builderer


class _BaseModel(pydantic.BaseModel):
    class Config:
        extra = pydantic.Extra.forbid


class Action(_BaseModel):
    type: typing.Literal["action"]
    name: str
    commands: list[list[str]]
    post: bool

    def add_to(self, builderer: builderer.Builderer) -> None:
        builderer.action(self.name, self.commands, self.post)


class BuildImage(_BaseModel):
    type: typing.Literal["build_image"]
    directory: str
    name: str | None = None
    push: bool = True
    qualified: bool = True

    def add_to(self, builderer: builderer.Builderer) -> None:
        builderer.build_image(self.directory, name=self.name, push=self.push, qualified=self.qualified)


class BuildImages(_BaseModel):
    type: typing.Literal["build_images"]
    directories: list[str]
    push: bool = True
    qualified: bool = True

    def add_to(self, builderer: builderer.Builderer) -> None:
        for directory in self.directories:
            builderer.build_image(directory, push=self.push, qualified=self.qualified)


class ExtractFromImage(_BaseModel):
    type: typing.Literal["extract_from_image"]
    image: str
    path: str
    dest: list[str]

    def add_to(self, builderer: builderer.Builderer) -> None:
        builderer.extract_from_image(self.image, self.path, *self.dest)


class ForwardImage(_BaseModel):
    type: typing.Literal["forward_image"]
    name: str
    new_name: str | None = None

    def add_to(self, builderer: builderer.Builderer) -> None:
        builderer.forward_image(self.name, new_name=self.new_name)


class PullImage(_BaseModel):
    type: typing.Literal["pull_image"]
    name: str

    def add_to(self, builderer: builderer.Builderer) -> None:
        builderer.pull_image(self.name)


class PullImages(_BaseModel):
    type: typing.Literal["pull_images"]
    names: list[str]

    def add_to(self, builderer: builderer.Builderer) -> None:
        for name in self.names:
            builderer.pull_image(name)


class Parameters(_BaseModel):
    registry: str | None = None
    prefix: str | None = None
    push: bool | None = None
    cache: bool | None = None
    verbose: bool | None = None
    tags: list[str] | None = None
    simulate: bool | None = None
    backend: typing.Literal["docker", "podman"] | None = None


class BuildConfig(_BaseModel):
    steps: list[Action | BuildImage | BuildImages | ExtractFromImage | ForwardImage | PullImage | PullImages]

    parameters: Parameters = pydantic.Field(default_factory=Parameters)

    @staticmethod
    def load(path: str | pathlib.Path) -> "BuildConfig":
        with open(path, "rt") as f:
            return BuildConfig.parse_obj(yaml.safe_load(f))
