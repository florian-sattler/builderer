import pathlib
import typing

import pydantic
import yaml

import builderer._documentation as docs
import builderer


class StepBase(pydantic.BaseModel, extra=pydantic.Extra.forbid):
    def create(
        self, factory: builderer.ActionFactory
    ) -> tuple[builderer.Action | builderer.ActionGroup | None, builderer.Action | builderer.ActionGroup | None]:
        raise NotImplementedError()  # pragma: no cover


class Action(StepBase):
    type: typing.Literal["action"] = pydantic.Field(description=docs.step_type)
    name: str = pydantic.Field(description=docs.step_action_name)
    commands: list[list[str]] = pydantic.Field(description=docs.step_action_commands)
    post: bool = pydantic.Field(description=docs.step_action_post)

    def create(self, factory: builderer.ActionFactory) -> tuple[builderer.Action | None, builderer.Action | None]:
        action = factory.action(name=self.name, commands=self.commands)

        if self.post:
            return None, action

        return action, None


class BuildImage(StepBase):
    type: typing.Literal["build_image"] = pydantic.Field(description=docs.step_type)
    directory: str = pydantic.Field(description=docs.step_build_directory)
    dockerfile: str | None = pydantic.Field(default=None, description=docs.step_build_dockerfile)
    name: str | None = pydantic.Field(default=None, description=docs.step_build_name)
    push: bool = pydantic.Field(default=True, description=docs.step_build_push)
    qualified: bool = pydantic.Field(default=True, description=docs.step_build_qualified)
    extra_tags: list[str] | None = pydantic.Field(default=None, description=docs.step_build_extra_tags)

    def create(self, factory: builderer.ActionFactory) -> tuple[builderer.Action, builderer.Action | None]:
        return factory.build_image(
            directory=self.directory,
            dockerfile=self.dockerfile,
            name=self.name,
            push=self.push,
            qualified=self.qualified,
            extra_tags=self.extra_tags,
        )


class BuildImages(StepBase):
    type: typing.Literal["build_images"] = pydantic.Field(description=docs.step_type)
    directories: list[str] = pydantic.Field(description=docs.step_build_directories)
    push: bool = pydantic.Field(default=True, description=docs.step_build_push)
    qualified: bool = pydantic.Field(default=True, description=docs.step_build_qualified)
    extra_tags: list[str] | None = pydantic.Field(default=None, description=docs.step_build_extra_tags)
    num_parallel: int = pydantic.Field(default=1, description=docs.step_num_parallel_tmpl)

    def create(self, factory: builderer.ActionFactory) -> tuple[builderer.ActionGroup, builderer.ActionGroup | None]:
        main = []
        post = []

        for directory in self.directories:
            m, p = factory.build_image(
                directory=directory,
                push=self.push,
                qualified=self.qualified,
                extra_tags=self.extra_tags,
            )
            main.append(m)
            if p:
                post.append(p)

        return (
            builderer.ActionGroup(main, self.num_parallel),
            builderer.ActionGroup(post[::-1], self.num_parallel) if post else None,
        )


class ExtractFromImage(StepBase):
    type: typing.Literal["extract_from_image"] = pydantic.Field(description=docs.step_type)
    image: str = pydantic.Field(description=docs.step_extract_image)
    path: str = pydantic.Field(description=docs.step_extract_path)
    dest: list[str] = pydantic.Field(description=docs.step_extract_dest)

    def create(self, factory: builderer.ActionFactory) -> tuple[builderer.Action, None]:
        return factory.extract_from_image(self.image, self.path, *self.dest), None


class ForwardImage(StepBase):
    type: typing.Literal["forward_image"] = pydantic.Field(description=docs.step_type)
    name: str = pydantic.Field(description=docs.step_forward_name)
    new_name: str | None = pydantic.Field(default=None, description=docs.step_forward_new_name)
    extra_tags: list[str] | None = pydantic.Field(default=None, description=docs.step_forward_extra_tags)

    def create(self, factory: builderer.ActionFactory) -> tuple[builderer.Action, builderer.Action | None]:
        return factory.forward_image(
            name=self.name,
            new_name=self.new_name,
            extra_tags=self.extra_tags,
        )


class ForwardImages(StepBase):
    type: typing.Literal["forward_images"] = pydantic.Field(description=docs.step_type)
    names: list[str] = pydantic.Field(description=docs.step_forward_names)
    extra_tags: list[str] | None = pydantic.Field(default=None, description=docs.step_forward_extra_tags)
    num_parallel: int = pydantic.Field(default=4, description=docs.step_num_parallel_tmpl.format(4))

    def create(self, factory: builderer.ActionFactory) -> tuple[builderer.ActionGroup, builderer.ActionGroup | None]:
        main = []
        post = []

        for name in self.names:
            m, p = factory.forward_image(
                name=name,
                new_name=None,
                extra_tags=self.extra_tags,
            )
            main.append(m)
            if p:
                post.append(p)

        return (
            builderer.ActionGroup(main, self.num_parallel),
            builderer.ActionGroup(post[::-1], self.num_parallel) if post else None,
        )


class PullImage(StepBase):
    type: typing.Literal["pull_image"] = pydantic.Field(description=docs.step_type)
    name: str = pydantic.Field(description=docs.step_pull_name)

    def create(self, factory: builderer.ActionFactory) -> tuple[builderer.Action, None]:
        return factory.pull_image(name=self.name), None


class PullImages(StepBase):
    type: typing.Literal["pull_images"] = pydantic.Field(description=docs.step_type)
    names: list[str] = pydantic.Field(description=docs.step_pull_names)
    num_parallel: int = pydantic.Field(default=4, description=docs.step_num_parallel_tmpl.format(4))

    def create(self, factory: builderer.ActionFactory) -> tuple[builderer.ActionGroup, None]:
        return builderer.ActionGroup([factory.pull_image(name=name) for name in self.names], self.num_parallel), None


class Group(StepBase):
    type: typing.Literal["group"] = pydantic.Field(description=docs.step_type)
    num_parallel: int = pydantic.Field(default=1, description=docs.step_num_parallel_tmpl)
    steps: list[Action | BuildImage | ExtractFromImage | ForwardImage | PullImage] = pydantic.Field(
        description=docs.conf_steps
    )

    def create(
        self, factory: builderer.ActionFactory
    ) -> tuple[builderer.ActionGroup | None, builderer.ActionGroup | None]:
        actions_main: list[builderer.Action] = []
        actions_post: list[builderer.Action] = []

        for step in self.steps:
            main, post = step.create(factory)
            if main:
                actions_main.append(main)
            if post:
                actions_post.append(post)

        return (
            builderer.ActionGroup(actions_main, self.num_parallel) if actions_post else None,
            builderer.ActionGroup(actions_post[::-1], self.num_parallel) if actions_post else None,
        )


class Parameters(pydantic.BaseModel, extra=pydantic.Extra.forbid):
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
    max_parallel: int | None = pydantic.Field(
        None, title=docs.arg_max_parallel_title, description=docs.arg_max_parallel_desc
    )


class BuildererConfig(pydantic.BaseModel, extra=pydantic.Extra.forbid):
    steps: list[
        Action
        | BuildImage
        | BuildImages
        | ExtractFromImage
        | ForwardImage
        | ForwardImages
        | PullImage
        | PullImages
        | Group
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
        with open(path) as f:
            return BuildererConfig.parse_obj(yaml.safe_load(f))
