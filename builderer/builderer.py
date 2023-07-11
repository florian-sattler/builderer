"""Builderers file config is a thin wrapper around this module as well as the action module."""

import concurrent.futures
import subprocess
import threading

from builderer.actions import Action, ActionGroup


class Builderer:
    """The Builderer class is used to issue collected actions."""

    def __init__(
        self,
        *,
        verbose: bool = False,
        simulate: bool = False,
        max_parallel: int | None = None,
    ) -> None:
        """Run commands inside in two queues. A action queue and a post queue.

        First the main actions gets handled (FIFO) then the corresponding post actions get called in reversed order (LIFO)
        Example:
            Building is done first, pushing is done as a post steps.
            This means a build is only pushed if all other main actions have been successful.

        Args:
            verbose (bool, optional): Verbose output. Defaults to False.
            simulate (bool, optional): Prevent issuing commands. Defaults to False.
            max_parallel (int, optional): Limit the maximum number of parallel jobs per step. By default the num_parallel argument of each individual step is used.
        """
        if max_parallel is not None and (not isinstance(max_parallel, int) or max_parallel < 1):
            raise ValueError("if set max_parallel needs to be a positive integer!")

        self.simulate = simulate
        self.verbose = verbose
        self.max_parallel = max_parallel

        self.actions_main: list[Action | ActionGroup] = []
        self.actions_post: list[Action | ActionGroup] = []

    def add_action_likes(self, main: Action | ActionGroup | None, post: Action | ActionGroup | None) -> None:
        """Add two Actions / ActionGroups to the main and the postprocessing queues.

        If None is passed for an argument it will be ignored.

        Args:
            main (Action | ActionGroup | None): A Action / ActionGroup to add to the main queue
            post (Action | ActionGroup | None): A Action / ActionGroup to add to the postprocessing queue
        """
        if main is not None:
            self.actions_main.append(main)
        if post is not None:
            self.actions_post.append(post)

    def run_cmd(self, command: list[str]) -> tuple[int, bytes]:
        """Run a single command.

        Output is only captured and returned if not running verbosely.

        Does nothing if self.simulate is True and returns (0, b"").

        Args:
            command (list[str]): Command to run.

        Raises:
            FileNotFoundError: if the executable was not found.

        Returns:
            tuple[int, bytes]: status code and command output if captured otherwise b"".
        """
        if self.simulate:
            return 0, b""

        if self.verbose:
            proc = subprocess.run(command)
        else:
            proc = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        return proc.returncode, proc.stdout or b""

    def run_action(self, action: Action) -> tuple[int, bytes]:
        """Run a single Action.

        The sequentialls runs each command of the given action.
        Stops if an error occurs and returns failed return code and
        command output. Output is only captured if not running verbosely.

        Does nothing if self.simulate is True and returns (0, b"").

        Args:
            action (Action): Action to run.

        Raises:
            FileNotFoundError: if any executable was not found.

        Returns:
            tuple[int, bytes]: status code and command output if an error occurred otherwise b"".
        """
        print(action.name, flush=True)

        for command in action.commands:
            if self.verbose:
                print(f"{command}", flush=True)

            returncode, stdout = self.run_cmd(command)

            if returncode != 0:
                return returncode, stdout

        return 0, b""

    def run_action_group(self, group: ActionGroup) -> tuple[int, bytes]:
        """Run an action group.

        Contained actions get started sequentially, they might however run in
        parallel as specified in the group and capped by self.max_parallel.
        Any exception encountered as well as any failed command will stop
        executing new actions and wait for all running actions to complete.

        Any encountered error is returned alongside the corresponding code.


        Args:
            group (ActionGroup): group to run.

        Returns:
            tuple[int, bytes]: status code and command output if an error occurred otherwise b"".
        """
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

        executor = concurrent.futures.ThreadPoolExecutor(
            group.num_parallel if self.max_parallel is None else min(group.num_parallel, self.max_parallel)
        )

        fs = [executor.submit(run_in_context, action) for action in group.actions]

        concurrent.futures.wait(fs, return_when=concurrent.futures.FIRST_EXCEPTION)
        if evt.is_set():
            executor.shutdown(wait=True, cancel_futures=True)
            assert error_data is not None
            return error_data

        return 0, b""

    def run(self) -> int:
        """Run queue actions and action groups. Stops when done or a command fails.

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
