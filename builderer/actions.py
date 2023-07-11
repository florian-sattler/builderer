"""Builderers file config is a thin wrapper around this module as well as the builderer module."""

import dataclasses
import os
import posixpath
import typing
import uuid


@dataclasses.dataclass(frozen=True)
class Action:
    """A named sequence of commands."""

    name: str
    commands: list[list[str]]


@dataclasses.dataclass
class ActionGroup:
    """A sequence of actions with many or may not be run in parallel."""

    actions: list[Action]
    num_parallel: int


class ActionFactory:
    """The ActionFactory class is used to create build tasks."""

    def __init__(
        self,
        *,
        registry: str | None = None,
        prefix: str | None = None,
        push: bool = True,
        cache: bool = False,
        tags: list[str] = ["latest"],
        backend: typing.Literal["docker", "podman"] = "docker",
    ) -> None:
        """Create predefined or custom actions.

        Args:
            registry (str | None, optional): Registry URL. Defaults to None.
            prefix (str | None, optional): Registry folder / namespace / user. Defaults to None.
            push (bool, optional): Whether to allow pushing images. Defaults to True.
            cache (bool, optional): Allow using cached images. Defaults to False.
            tags (list[str], optional): Tags to use. Defaults to ["latest"].
            backend (typing.Literal["docker", "podman"], optional): Overwrite backend to use. Defaults to "docker".
        """
        self.tags = tags
        self.registry = registry
        self.prefix = prefix
        self.cache = cache
        self.backend = backend
        self.push = push

    def action(self, name: str, commands: list[list[str]]) -> Action:
        """Create a generic action with multiple commands.

        Hint: Use this mechanism if other commands aren't sufficient for your usecase.

        Args:
            name (str): Name of the action
            commands (list[list[str]]): List of commands. Each command is a list of strings: the executable followed by arguments.
        """
        return Action(name=name, commands=commands)

    def _full_image_name(self, name: str) -> str:
        return posixpath.join(self.registry or "", self.prefix or "", name)

    def _build_cmd(self, full_name: str, extra_tags: list[str]) -> list[str]:
        tags = [i for tag in (self.tags + extra_tags) for i in ["-t", f"{full_name}:{tag}"]]
        cache = ["--no-cache"] if not self.cache else []

        return [self.backend, "build", *tags, *cache]

    def build_image(
        self,
        directory: str,
        *,
        dockerfile: str | None = None,
        name: str | None = None,
        push: bool = True,
        qualified: bool = True,
        extra_tags: list[str] | None = None,
    ) -> tuple[Action, Action | None]:
        """Build a docker image and push it to the registry.

        Args:
            directory (str): Directory containing the build context.
            dockerfile (str | None, optional): Path to Dockerfile. Name of the resulting image. Defaults to <directory>/Dockerfile.
            name (str | None, optional): Name of the resulting image. Defaults to the name of the Dockerfiles parent directory.
            push (bool, optional): Whether to push the image. Defaults to True.
            qualified (bool, optional): Whether to add the registry path and prefix to the image name. Defaults to True.
            extra_tags: additional tags to use for this image. Defaults to None.
        """
        if dockerfile is None:
            dockerfile = os.path.join(directory, "Dockerfile")

        if name is None:
            name = os.path.basename(directory)

        if extra_tags is None:
            extra_tags = []

        image_name = self._full_image_name(name) if qualified else name

        action_main = self.action(
            name=f"Building image: {name}",
            commands=[[*self._build_cmd(image_name, extra_tags), "-f", dockerfile, directory]],
        )

        if not push or not self.push:
            return action_main, None

        action_post = self.action(
            name=f"Pushing image: {name}",
            commands=[[self.backend, "push", f"{image_name}:{tag}"] for tag in self.tags + extra_tags],
        )

        return action_main, action_post

    def extract_from_image(self, image: str, path: str, *dest: str) -> Action:
        """Copy a file from within a docker image.

        Args:
            image (str): Name of the image to copy from.
            path (str): Source path inside the image.
            dest (str): Destination paths. The file will be copied to all destinations individually.
        """
        container_name = str(uuid.uuid4())

        return self.action(
            name=f"Extracting from image: {path} -> {', '.join(dest)}",
            commands=[
                [self.backend, "container", "create", "--name", container_name, image],
                *[[self.backend, "container", "cp", f"{container_name}:{path}", dst] for dst in dest],
                [self.backend, "container", "rm", "-f", container_name],
            ],
        )

    def forward_image(
        self, name: str, *, new_name: str | None = None, extra_tags: list[str] | None = None
    ) -> tuple[Action, Action | None]:
        """Pull an image from a registry, retag it and push it using the new names.

        Args:
            name (str): image name to pull
            new_name (str | None, optional): Set a new name for the image. By default the basename of the pulled image without the tag is used. Defaults to None.
            extra_tags: additional tags to use for this image. Defaults to None.
        """
        if new_name is None:
            new_name = os.path.basename(name).split(":")[0]

        if extra_tags is None:
            extra_tags = []

        image_name = self._full_image_name(new_name)

        action_main = self.action(
            name=f"Forwarding image: {name} -> {new_name}",
            commands=[
                [self.backend, "pull", name],
                *[[self.backend, "tag", name, f"{image_name}:{tag}"] for tag in self.tags + extra_tags],
            ],
        )

        if not self.push:
            return action_main, None

        action_post = self.action(
            name=f"Pushing image: {new_name}",
            commands=[[self.backend, "push", f"{image_name}:{tag}"] for tag in self.tags + extra_tags],
        )

        return action_main, action_post

    def pull_image(self, name: str) -> Action:
        """Pull an image from a registry. This might be usefull to ensure a local image is up to date (e.g. for local builds).

        Args:
            name (str): image name to pull.
        """
        return self.action(
            name=f"Pulling image: {name}",
            commands=[[self.backend, "pull", name]],
        )
