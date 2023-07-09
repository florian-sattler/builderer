"""Builderers file config is a thin wrapper around this library."""

import concurrent.futures
import subprocess
import threading

from builderer.actions import Action, ActionGroup


class Builderer:
    """The Runner class is used to issue collected build tasks."""

    def __init__(
        self,
        *,
        verbose: bool = False,
        simulate: bool = False,
        max_parallel: int = 1,  # TODO fix
    ) -> None:
        """Run commands inside in two queues. A action queue and a post queue.
        First the action queue gets handled (FIFO) then the corresponding post actions get called in reversed order (LIFO)
        Pushing is done as a post steps. This means a build is only pushed if builder of all images was successfull.

        Args:
            verbose (bool, optional): Verbose output. Defaults to False.
            simulate (bool, optional): Prevent issuing commands. Defaults to False.
            max_parallel (int, optional): Overwrite backend to use. Defaults to "docker".
        """
        if not isinstance(max_parallel, int) or max_parallel < 1:
            raise ValueError("max_parallel needs to be a positive integer!")

        self.simulate = simulate
        self.verbose = verbose
        self.max_parallel = max_parallel

        self.actions_main: list[Action | ActionGroup] = []
        self.actions_post: list[Action | ActionGroup] = []

    def add_action_likes(self, main: Action | ActionGroup | None, post: Action | ActionGroup | None) -> None:
        if main is not None:
            self.actions_main.append(main)
        if post is not None:
            self.actions_post.append(post)

    def run_cmd(self, command: list[str]) -> tuple[int, bytes]:
        if self.simulate:
            return 0, b""

        if self.verbose:
            proc = subprocess.run(command)
        else:
            proc = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        return proc.returncode, proc.stdout or b""

    def run_action(self, action: Action) -> tuple[int, bytes]:
        print(action.name, flush=True)

        for command in action.commands:
            if self.verbose:
                print(f"{command}", flush=True)

            returncode, stdout = self.run_cmd(command)

            if returncode != 0:
                return returncode, stdout

        return 0, b""

    def run_action_group(self, group: ActionGroup) -> tuple[int, bytes]:
        evt = threading.Event()
        error_data: tuple[int, bytes] | None = None

        # context is needed to stop executor from spawning new tasks when handling an exception
        def run_in_context(act: Action) -> None:
            nonlocal error_data

            if evt.is_set():
                return

            try:
                returncode, stdout = self.run_action(act)
            except Exception as e:
                error_data = (1, str(e).encode())
                evt.set()

                raise RuntimeError("Error execution action") from e

            if returncode != 0:
                error_data = (returncode, stdout)
                evt.set()

                raise RuntimeError("Error execution action")

        executor = concurrent.futures.ThreadPoolExecutor(min(group.num_parallel, self.max_parallel))

        fs = [executor.submit(run_in_context, action) for action in group.actions]

        concurrent.futures.wait(fs, return_when=concurrent.futures.FIRST_EXCEPTION)
        if evt.is_set():
            executor.shutdown(wait=True, cancel_futures=True)
            assert error_data is not None
            return error_data

        return 0, b""

    def run(self) -> int:
        """After adding all steps. This method will start to issue all commands. It stops when done or a command fails.

        Returns:
            int: return code. On success this will be zero. Otherwise it will be the return code of the failed command.
        """
        for queue in [self.actions_main, reversed(self.actions_post)]:
            for item in queue:
                if isinstance(item, Action):
                    returncode, stdout = self.run_action(item)
                elif isinstance(item, ActionGroup):
                    returncode, stdout = self.run_action_group(item)
                else:
                    raise ValueError(f"Unexpected queue entry: {item} of type {type(item)}")

                if returncode != 0:
                    print("Encountered error running:", flush=True)

                    if not self.verbose:
                        print(stdout.decode(), flush=True)

                    return returncode

        return 0
