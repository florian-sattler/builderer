import sys
import threading
import time
import typing
from unittest.mock import MagicMock, call, patch

import pytest
from pytest_mock import MockerFixture

from builderer import Action, ActionGroup, Builderer


@pytest.fixture
def builderer_sim() -> Builderer:
    return Builderer(verbose=False, simulate=True, max_parallel=2)


@pytest.fixture
def builderer() -> Builderer:
    return Builderer(verbose=False, simulate=False, max_parallel=2)


@pytest.fixture
def action_success_1() -> Action:
    return Action(name="Test Action", commands=[["echo", "Hello!"]])


@pytest.fixture
def action_success_2() -> Action:
    return Action(name="Test Action", commands=[["echo", "World!"]])


@pytest.fixture
def action_error() -> Action:
    return Action(name="Test Action", commands=[[sys.executable, "-c", "print('error'); raise SystemExit(1)"]])


@pytest.fixture
def action_invalid() -> Action:
    return Action(name="Test Action", commands=[["invalid_command"]])


@pytest.fixture
def action_group_success_success(action_success_1: Action, action_success_2: Action) -> ActionGroup:
    return ActionGroup(actions=[action_success_1, action_success_2], num_parallel=1)


@pytest.fixture
def action_group_success_error(action_success_1: Action, action_error: Action) -> ActionGroup:
    return ActionGroup(actions=[action_success_1, action_error], num_parallel=1)


@pytest.fixture
def action_group_success_invalid(action_success_1: Action, action_invalid: Action) -> ActionGroup:
    return ActionGroup(actions=[action_success_1, action_invalid], num_parallel=1)


def test_run_cmd_simulate(builderer_sim: Builderer) -> None:
    returncode, stdout = builderer_sim.run_cmd(["echo", "Hello, World!"])
    assert returncode == 0
    assert stdout == b""


@patch("subprocess.run")
def test_run_cmd_verbose(mock_subprocess_run: MagicMock, builderer: Builderer) -> None:
    mock_subprocess_run.return_value = MagicMock(returncode=0, stdout=b"Hello, World!")
    returncode, stdout = builderer.run_cmd(["echo", "Hello, World!"])

    assert returncode == 0
    assert stdout == b"Hello, World!"


def test_run_action_success_sim(builderer_sim: Builderer, action_success_1: Action) -> None:
    returncode, stdout = builderer_sim.run_action(action_success_1)

    assert returncode == 0
    assert stdout == b""


def test_run_action_success(builderer: Builderer, action_success_1: Action) -> None:
    returncode, stdout = builderer.run_action(action_success_1)

    assert returncode == 0
    assert stdout == b""


def test_run_action_failure_sim(builderer_sim: Builderer, action_error: Action) -> None:
    returncode, stdout = builderer_sim.run_action(action_error)

    assert returncode == 0
    assert stdout == b""


def test_run_action_failure(builderer: Builderer, action_error: Action) -> None:
    returncode, stdout = builderer.run_action(action_error)

    assert returncode != 0
    assert stdout == b"error\n"


def test_run_action_error(builderer: Builderer, action_invalid: Action) -> None:
    with pytest.raises(FileNotFoundError):
        builderer.run_action(action_invalid)


def test_run_action_group_success_sim(builderer_sim: Builderer, action_group_success_success: ActionGroup) -> None:
    returncode, stdout = builderer_sim.run_action_group(action_group_success_success)

    assert returncode == 0
    assert stdout == b""


def test_run_action_group_success(builderer: Builderer, action_group_success_success: ActionGroup) -> None:
    returncode, stdout = builderer.run_action_group(action_group_success_success)

    assert returncode == 0
    assert stdout == b""


def test_run_action_group_success_mocked(builderer: Builderer, action_group_success_success: ActionGroup) -> None:
    with patch.object(Builderer, "run_action", return_value=(0, b"")) as mock_run_action:
        returncode, stdout = builderer.run_action_group(action_group_success_success)

        assert returncode == 0
        assert stdout == b""
        assert mock_run_action.call_count == 2


def test_run_action_group_failure(builderer: Builderer, action_group_success_error: ActionGroup) -> None:
    returncode, stdout = builderer.run_action_group(action_group_success_error)

    assert returncode != 0
    assert stdout == b"error\n"


def test_run_action_group_failure_mocked(builderer: Builderer, action_group_success_error: ActionGroup) -> None:
    with patch.object(Builderer, "run_action", side_effect=[(0, b""), (1, b"Error")]) as mock_run_action:
        returncode, stdout = builderer.run_action_group(action_group_success_error)

        assert returncode == 1
        assert stdout == b"Error"
        assert mock_run_action.call_count == 2


@pytest.mark.parametrize("num_parallel", [1, 2, 3])
def test_run_action_group_exception_mocked(
    num_parallel: int, builderer: Builderer, action_group_success_success: ActionGroup
) -> None:
    action_group_success_success.num_parallel = num_parallel
    with patch.object(
        Builderer, "run_action", side_effect=[(0, b""), FileNotFoundError("Something went wrong")]
    ) as mock_run_action:
        returncode, stdout = builderer.run_action_group(action_group_success_success)

        assert returncode == 1
        assert stdout == b"Something went wrong"
        assert mock_run_action.call_count == 2


def test_run_action_group_no_further_actions(builderer: Builderer) -> None:
    action1 = Action(name="Action 1", commands=[["echo", "Hello"]])
    action2 = Action(name="Action 2", commands=[["false"]])
    action3 = Action(name="Action 3", commands=[["echo", "World"]])
    group = ActionGroup(actions=[action1, action2, action3], num_parallel=1)

    with patch.object(Builderer, "run_action") as mock_run_action:
        mock_run_action.side_effect = [(0, b""), (1, b"Error"), (0, b"")]

        returncode, stdout = builderer.run_action_group(group)

        assert returncode == 1
        assert stdout == b"Error"

        assert mock_run_action.call_count == 2
        assert call(action1) in mock_run_action.mock_calls
        assert call(action2) in mock_run_action.mock_calls

        assert call(action3) not in mock_run_action.mock_calls


def test_run_action_group_parallel_stops_on_error(builderer: Builderer) -> None:
    # With parallel execution the exact set of actions that get started is
    # scheduling dependent, so we cannot assert on individual actions. What is
    # guaranteed is that a failure stops new actions from starting, meaning not
    # all queued actions run. The barrier keeps the actions started alongside
    # the failing one from freeing their worker until the failure is recorded,
    # so the short-circuit is observed reliably regardless of thread timing.
    actions = [Action(name=f"Action {i}", commands=[["echo", str(i)]]) for i in range(6)]
    failing = actions[1]
    group = ActionGroup(actions=actions, num_parallel=2)

    failed = threading.Event()

    def side_effect(action: Action) -> tuple[int, bytes]:
        if action is failing:
            failed.set()
            return (1, b"Error")
        failed.wait(timeout=5)
        return (0, b"")

    with patch.object(Builderer, "run_action", side_effect=side_effect) as mock_run_action:
        returncode, stdout = builderer.run_action_group(group)

        assert returncode == 1
        assert stdout == b"Error"

        assert call(failing) in mock_run_action.mock_calls
        assert mock_run_action.call_count < len(actions)


def test_run_success(builderer_sim: Builderer, action_group_success_success: ActionGroup) -> None:
    builderer_sim.add_action_likes(main=action_group_success_success, post=None)
    returncode = builderer_sim.run()
    assert returncode == 0


def test_run_failure(builderer: Builderer, action_group_success_invalid: ActionGroup) -> None:
    builderer.add_action_likes(main=action_group_success_invalid, post=None)
    returncode = builderer.run()
    assert returncode != 0


def test_max_parallel_cores_allowed() -> None:
    assert Builderer(max_parallel="cores").max_parallel == "cores"


@pytest.mark.parametrize("value", ["all", "bogus"])
def test_max_parallel_invalid_keyword(value: typing.Any) -> None:
    with pytest.raises(ValueError) as e:
        Builderer(max_parallel=value)

    assert "max_parallel" in str(e.value)


@pytest.mark.parametrize(
    ("num_parallel", "max_parallel", "n_actions", "cpu", "expected"),
    [
        (3, None, 5, 4, 3),  # plain integer is used as-is
        ("cores", None, 5, 4, 4),  # "cores" -> CPU count
        ("all", None, 5, 4, 5),  # "all" -> number of actions in the group
        ("all", None, 0, 4, 1),  # empty group clamps to at least one worker
        (10, 2, 5, 4, 2),  # capped by an integer max_parallel
        ("all", "cores", 5, 4, 4),  # "all" capped by "cores" max_parallel
        ("cores", 2, 5, 8, 2),  # "cores" capped by an integer max_parallel
    ],
)
def test_num_workers_resolution(
    mocker: MockerFixture,
    num_parallel: typing.Any,
    max_parallel: typing.Any,
    n_actions: int,
    cpu: int,
    expected: int,
) -> None:
    mocker.patch("builderer.builderer.os.cpu_count", return_value=cpu)
    runner = Builderer(max_parallel=max_parallel)
    group = ActionGroup([Action(f"a{i}", []) for i in range(n_actions)], num_parallel)

    assert runner._num_workers(group) == expected


def test_max_parallel_caps_concurrency() -> None:
    # A group asking for more parallelism than max_parallel must be capped: no
    # more than max_parallel actions may run at the same time.
    runner = Builderer(max_parallel=2)

    lock = threading.Lock()
    current = 0
    peak = 0

    def tracking_action(_self: Builderer, action: Action) -> tuple[int, bytes]:
        nonlocal current, peak
        with lock:
            current += 1
            peak = max(peak, current)
        time.sleep(0.02)  # hold the slot so concurrent actions overlap
        with lock:
            current -= 1
        return 0, b""

    actions = [Action(name=f"Action {i}", commands=[]) for i in range(6)]
    group = ActionGroup(actions=actions, num_parallel=6)  # wants 6, capped to 2

    with patch.object(Builderer, "run_action", tracking_action):
        returncode, stdout = runner.run_action_group(group)

    assert returncode == 0
    assert stdout == b""
    assert peak == 2
