import pathlib
import typing

import pydantic
import yaml

import builderer._documentation as docs
from builderer import builderer


class _BaseModel(pydantic.BaseModel):
    class Config:
        extra = pydantic.Extra.forbid


class Action(_BaseModel):
    type: typing.Literal["action"] = pydantic.Field(description=docs.step_type)
    name: str = pydantic.Field(description=docs.step_action_name)
    commands: list[list[str]] = pydantic.Field(description=docs.step_action_commands)
    post: bool = pydantic.Field(description=docs.step_action_post)

    def add_to(self, builderer: builderer.Builderer) -> None:
        builderer.action(name=self.name, commands=self.commands, post=self.post)


class BuildImage(_BaseModel):
    type: typing.Literal["build_image"] = pydantic.Field(description=docs.step_type)
    directory: str = pydantic.Field(description=docs.step_build_directory)
    dockerfile: str | None = pydantic.Field(default=None, description=docs.step_build_dockerfile)
    name: str | None = pydantic.Field(default=None, description=docs.step_build_name)
    push: bool = pydantic.Field(default=True, description=docs.step_build_push)
    qualified: bool = pydantic.Field(default=True, description=docs.step_build_qualified)

    def add_to(self, builderer: builderer.Builderer) -> None:
        builderer.build_image(
            directory=self.directory,
            dockerfile=self.dockerfile,
            name=self.name,
            push=self.push,
            qualified=self.qualified,
        )


class BuildImages(_BaseModel):
    type: typing.Literal["build_images"] = pydantic.Field(description=docs.step_type)
    directories: list[str] = pydantic.Field(description=docs.step_build_directories)
    push: bool = pydantic.Field(default=True, description=docs.step_build_push)
    qualified: bool = pydantic.Field(default=True, description=docs.step_build_qualified)

    def add_to(self, builderer: builderer.Builderer) -> None:
        for directory in self.directories:
            builderer.build_image(directory=directory, push=self.push, qualified=self.qualified)


class ExtractFromImage(_BaseModel):
    type: typing.Literal["extract_from_image"] = pydantic.Field(description=docs.step_type)
    image: str = pydantic.Field(description=docs.step_extract_image)
    path: str = pydantic.Field(description=docs.step_extract_path)
    dest: list[str] = pydantic.Field(description=docs.step_extract_dest)

    def add_to(self, builderer: builderer.Builderer) -> None:
        builderer.extract_from_image(self.image, self.path, *self.dest)


class ForwardImage(_BaseModel):
    type: typing.Literal["forward_image"] = pydantic.Field(description=docs.step_type)
    name: str = pydantic.Field(description=docs.step_forward_name)
    new_name: str | None = pydantic.Field(default=None, description=docs.step_forward_new_name)

    def add_to(self, builderer: builderer.Builderer) -> None:
        builderer.forward_image(name=self.name, new_name=self.new_name)


class PullImage(_BaseModel):
    type: typing.Literal["pull_image"] = pydantic.Field(description=docs.step_type)
    name: str = pydantic.Field(description=docs.step_pull_name)

    def add_to(self, builderer: builderer.Builderer) -> None:
        builderer.pull_image(name=self.name)


class PullImages(_BaseModel):
    type: typing.Literal["pull_images"] = pydantic.Field(description=docs.step_type)
    names: list[str] = pydantic.Field(description=docs.step_pull_names)

    def add_to(self, builderer: builderer.Builderer) -> None:
        for name in self.names:
            builderer.pull_image(name=name)


class Parameters(_BaseModel):
    registry: str | None = pydantic.Field(None, title=docs.arg_registry_title, description=docs.arg_registry_desc)
    prefix: str | None = pydantic.Field(None, title=docs.arg_prefix_title, description=docs.arg_prefix_desc)
    push: bool | None = pydantic.Field(None, title=docs.arg_push_title, description=docs.arg_push_desc)
    cache: bool | None = pydantic.Field(None, title=docs.arg_cache_title, description=docs.arg_cache_desc)
    verbose: bool | None = pydantic.Field(None, title=docs.arg_verbose_title, description=docs.arg_verbose_desc)
    tags: list[str] | None = pydantic.Field(None, title=docs.arg_tags_title, description=docs.arg_tags_desc)
    simulate: bool | None = pydantic.Field(None, title=docs.arg_simulate_title, description=docs.arg_simulate_desc)
    backend: typing.Literal["docker", "podman"] | None = pydantic.Field(
        None, title=docs.arg_backend_title, description=docs.arg_backend_desc
    )


class BuildererConfig(_BaseModel):
    steps: list[
        Action | BuildImage | BuildImages | ExtractFromImage | ForwardImage | PullImage | PullImages
    ] = pydantic.Field(description=docs.conf_steps)

    parameters: Parameters = pydantic.Field(
        default_factory=Parameters,  # pyright: ignore
        description=docs.conf_parameters,
    )

    @pydantic.validator("steps", pre=True, each_item=True)
    def parse_steps_by_type(cls, v: typing.Any) -> typing.Any:
        if not isinstance(v, dict):
            return v

        if "type" not in v:
            raise ValueError("malformed step: 'type' is required!")

        class_name = "".join(x.title() for x in v["type"].split("_"))

        for step_type in cls.__fields__["steps"].type_.__args__:
            if class_name == step_type.__name__:
                return step_type.parse_obj(v)

        raise ValueError(f"Unknown step type {v['type']}")

    @staticmethod
    def load(path: str | pathlib.Path) -> "BuildererConfig":
        with open(path, "rt") as f:
            return BuildererConfig.parse_obj(yaml.safe_load(f))
