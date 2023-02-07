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
        name: str | None = None,
        push: bool = True,
        qualified: bool = True,
    ) -> None:
        if name is None:
            name = os.path.basename(directory)

        image_name = self._full_image_name(name) if qualified else name

        self.action(
            name=f"Building image: {name}",
            commands=[[*self._build_cmd(image_name), "-f", posixpath.join(directory, "Dockerfile"), directory]],
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
        self.action(
            name=f"Pulling image: {name}",
            commands=[[self.backend, "pull", name]],
            post=False,
        )

    def run(self) -> int:
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
