"""Builderers file config is a thin wrapper around this library."""

import collections
import dataclasses
import os
import posixpath
import subprocess
import typing
import uuid


@dataclasses.dataclass(frozen=True)
class Action:
    name: str
    commands: list[list[str]]


class Builderer:
    """The Builderer class is used to collect build tasks and issue them afterwards."""

    def __init__(
        self,
        *,
        registry: str | None = None,
        prefix: str | None = None,
        push: bool = True,
        cache: bool = False,
        verbose: bool = False,
        tags: list[str] = ["latest"],
        simulate: bool = False,
        backend: typing.Literal["docker", "podman"] = "docker",
    ) -> None:
        """Builderer runs commands inside in two queues. A action queue and a post queue.
        First the action queue gets handled (FIFO) then the corresponding post actions get called in reversed order (LIFO)
        Pushing is done as a post steps. This means a build is only pushed if builder of all images was successfull.

        Args:
            registry (str | None, optional): Registry URL. Defaults to None.
            prefix (str | None, optional): Registry folder / namespace / user. Defaults to None.
            push (bool, optional): Whether to allow pushing images. Defaults to True.
            cache (bool, optional): Allow using cached images. Defaults to False.
            verbose (bool, optional): Verbose output. Defaults to False.
            tags (list[str], optional): Tags to use. Defaults to ["latest"].
            simulate (bool, optional): Prevent issuing commands. Defaults to False.
            backend (typing.Literal["docker", "podman"], optional): Overwrite backend to use. Defaults to "docker".
        """
        self.tags = tags
        self.registry = registry
        self.prefix = prefix
        self.cache = cache
        self.backend = backend
        self.simulate = simulate
        self.verbose = verbose
        self.push = push

        self._actions: collections.deque[Action] = collections.deque()
        self._post: collections.deque[Action] = collections.deque()

    def action(self, name: str, commands: list[list[str]], post: bool) -> None:
        """A generic action with multiple commands.

        Hint: Use this mechanism if other commands aren't sufficient for your usecase.

        Args:
            name (str): Name of the action
            commands (list[list[str]]): List of commands. Each command is a list of strings: the executable followed by arguments.
            post (bool): Whether to add the action to the post queue.
        """
        item = Action(name=name, commands=commands)

        if post:
            self._post.appendleft(item)
        else:
            self._actions.append(item)

    def _full_image_name(self, name: str) -> str:
        return posixpath.join(self.registry or "", self.prefix or "", name)

    def _build_cmd(self, full_name: str) -> list[str]:
        tags = [i for tag in self.tags for i in ["-t", f"{full_name}:{tag}"]]
        cache = ["--no-cache"] if not self.cache else []

        return [self.backend, "build", *tags, *cache]

    def _run_cmd(self, command: list[str]) -> tuple[int, bytes]:
        if self.simulate:
            return 0, b""

        if self.verbose:
            proc = subprocess.run(command)
        else:
            proc = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        return proc.returncode, proc.stdout or b""

    def build_image(
        self,
        directory: str,
        *,
        dockerfile: str | None = None,
        name: str | None = None,
        push: bool = True,
        qualified: bool = True,
    ) -> None:
        """Build a docker image and push it to the registry.

        Args:
            directory (str): Directory containing the build context.
            dockerfile (str | None, optional): Path to Dockerfile. Name of the resulting image. Defaults to <directory>/Dockerfile.
            name (str | None, optional): Name of the resulting image. Defaults to the name of the Dockerfiles parent directory.
            push (bool, optional): Whether to push the image. Defaults to True.
            qualified (bool, optional): Whether to add the registry path and prefix to the image name. Defaults to True.
        """
        if dockerfile is None:
            dockerfile = os.path.join(directory, "Dockerfile")

        if name is None:
            name = os.path.basename(directory)

        image_name = self._full_image_name(name) if qualified else name

        self.action(
            name=f"Building image: {name}",
            commands=[[*self._build_cmd(image_name), "-f", dockerfile, directory]],
            post=False,
        )

        if not push or not self.push:
            return

        self.action(
            name=f"Pushing image: {name}",
            commands=[[self.backend, "push", f"{image_name}:{tag}"] for tag in self.tags],
            post=True,
        )

    def extract_from_image(self, image: str, path: str, *dest: str) -> None:
        """Copy a file from within a docker image.

        Args:
            image (str): Name of the image to copy from.
            path (str): Source path inside the image.
            dest (str): Destination paths. The file will be copied to all destinations individually.
        """
        image_name = self._full_image_name(image)
        container_name = str(uuid.uuid4())

        self.action(
            name=f"Extracting from image: {path} -> {', '.join(dest)}",
            commands=[
                [self.backend, "container", "create", "--name", container_name, image_name],
                *[[self.backend, "container", "cp", f"{container_name}:{path}", dst] for dst in dest],
                [self.backend, "container", "rm", "-f", container_name],
            ],
            post=False,
        )

    def forward_image(self, name: str, *, new_name: str | None = None) -> None:
        """Pulls an image from a registry, retags it and pushes it using the new names.

        Args:
            name (str): image name to pull
            new_name (str | None, optional): Set a new name for the image. By default the basename of the pulled image without the tag is used. Defaults to None.
        """
        if new_name is None:
            new_name = os.path.basename(name).split(":")[0]

        image_name = self._full_image_name(new_name)

        self.action(
            name=f"Forwarding image: {name} -> {new_name}",
            commands=[
                [self.backend, "pull", name],
                *[[self.backend, "tag", name, f"{image_name}:{tag}"] for tag in self.tags],
            ],
            post=False,
        )

        if not self.push:
            return

        self.action(
            name=f"Pushing image: {new_name}",
            commands=[[self.backend, "push", f"{image_name}:{tag}"] for tag in self.tags],
            post=True,
        )

    def pull_image(self, name: str) -> None:
        """Pulls an image from a registry. This might be usefull to ensure a local image is up to date (e.g. for local builds)

        Args:
            name (str): image name to pull.
        """
        self.action(
            name=f"Pulling image: {name}",
            commands=[[self.backend, "pull", name]],
            post=False,
        )

    def run(self) -> int:
        """After adding all steps. This method will start to issue all commands. It stops when done or a command fails.

        Returns:
            int: return code. On success this will be zero. Otherwise it will be the return code of the failed command.
        """
        for queue in [self._actions, self._post]:
            for action in queue:
                print(action.name, flush=True)

                for command in action.commands:
                    if self.verbose:
                        print(f"{command}", flush=True)

                    returncode, stdout = self._run_cmd(command)

                    if returncode != 0:
                        print("Encountered error running:", flush=True)

                        if not self.verbose:
                            print(stdout.decode(), flush=True)

                        return returncode

        return 0
